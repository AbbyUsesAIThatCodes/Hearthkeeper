"""Commands inside the dedicated realm container. Never run against another realm."""
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

from .accounts import registration

ROOT = Path("/realm")
DATABASES = ("acore_auth", "acore_characters", "acore_world", "acore_playerbots")


def settings():
    return json.loads((ROOT / "realm.json").read_text())


def connect(role="server", database=None, autocommit=False):
    import pymysql
    config = settings()
    user = {"root": "root", "server": "hearthkeeper", "reader": "hearthkeeper_reader"}[role]
    return pymysql.connect(host="database", user=user, password=config["secrets"][role],
                           database=database, charset="utf8mb4", autocommit=autocommit,
                           connect_timeout=10, read_timeout=120, write_timeout=120,
                           cursorclass=pymysql.cursors.DictCursor, local_infile=False)


def configure():
    config = settings()
    destination = ROOT / "etc"
    destination.mkdir(exist_ok=True)
    (destination / "modules").mkdir(exist_ok=True)
    for template in Path("/defaults").rglob("*.conf.dist"):
        output = destination / template.relative_to("/defaults").with_suffix("")
        output.parent.mkdir(parents=True, exist_ok=True)
        if not output.exists():
            shutil.copyfile(template, output)

    def edit(name, values):
        path = destination / name
        if not path.exists():
            raise RuntimeError("The build did not install required configuration: " + name)
        text = path.read_text()
        for key, value in values.items():
            pattern = r"(?m)^\s*" + re.escape(key) + r"\s*=.*$"
            line = key + " = " + (json.dumps(value) if isinstance(value, str) else str(value))
            if re.search(pattern, text):
                text = re.sub(pattern, lambda match: line, text)
            else:
                text += "\n" + line + "\n"
        path.write_text(text)
        path.chmod(0o600)

    connections = {key: "database;3306;hearthkeeper;" + config["secrets"]["server"] + ";" + db
                   for key, db in zip(("LoginDatabaseInfo", "CharacterDatabaseInfo", "WorldDatabaseInfo"), DATABASES)}
    common = {"LogsDir": "/realm/logs", "TempDir": "/realm/temp", "SourceDirectory": "/src",
              "MySQLExecutable": "/usr/bin/mysql"}
    edit("dbimport.conf", {**common, **connections, "Updates.EnableDatabases": 7,
                           "Updates.AllowedModules": "all"})
    edit("authserver.conf", {**common, "LoginDatabaseInfo": connections["LoginDatabaseInfo"],
                             "Updates.EnableDatabases": 0, "BindIP": "0.0.0.0"})
    edit("worldserver.conf", {**common, **connections, "DataDir": "/realm/server-data",
                              "Updates.EnableDatabases": 0, "EnablePlayerSettings": 1,
                              "DBC.EnforceItemAttributes": 0, "Console.Enable": 0,
                              "SOAP.Enabled": 0, "Ra.Enable": 0, "BeepAtStart": 0,
                              "BindIP": "0.0.0.0", "RealmID": 1,
                              "Rate.XP.Kill": config["xp_rate"], "Rate.XP.Quest": config["xp_rate"],
                              "Rate.XP.Explore": config["xp_rate"]})
    edit("modules/individualProgression.conf", {"IndividualProgression.Enable": 1,
                                                "IndividualProgression.QuestXPFix": 0})
    bots = config["random_bots"]
    edit("modules/playerbots.conf", {
        "PlayerbotsDatabaseInfo": "database;3306;hearthkeeper;" + config["secrets"]["server"] + ";acore_playerbots",
        "AiPlayerbot.Enabled": 1, "AiPlayerbot.RandomBotAutologin": int(bots > 0),
        "AiPlayerbot.MinRandomBots": bots, "AiPlayerbot.MaxRandomBots": bots,
        "AiPlayerbot.RandomBotAccountCount": max(1, (bots * 2 + 9) // 10),
        "AiPlayerbot.RandomBotGuildCount": 0, "AiPlayerbot.RandomBotArenaTeam2v2Count": 0,
        "AiPlayerbot.RandomBotArenaTeam3v3Count": 0, "AiPlayerbot.RandomBotArenaTeam5v5Count": 0})
    print("Realm and module configuration prepared.", flush=True)


def bootstrap():
    config = settings()
    with connect("root", autocommit=True) as connection, connection.cursor() as cursor:
        for database in DATABASES:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        for role, user in (("server", "hearthkeeper"), ("reader", "hearthkeeper_reader")):
            cursor.execute("CREATE USER IF NOT EXISTS %s@%s IDENTIFIED BY %s", (user, "%", config["secrets"][role]))
        for database in DATABASES:
            cursor.execute(f"GRANT ALL ON `{database}`.* TO 'hearthkeeper'@'%'")
        for database in ("acore_characters", "acore_world"):
            cursor.execute(f"GRANT SELECT ON `{database}`.* TO 'hearthkeeper_reader'@'%'")
    print("Dedicated databases and service identities are ready.", flush=True)


def finalize():
    config = settings()
    with connect(database="acore_auth") as connection, connection.cursor() as cursor:
        cursor.execute("UPDATE realmlist SET name=%s,address='127.0.0.1',localAddress='127.0.0.1',"
                       "port=8085,gamebuild=12340 WHERE id=1", (config["name"],))
        connection.commit()
    print("Local realm registration is ready.", flush=True)


def run_tool(arguments, cwd=None):
    print("Running " + Path(arguments[0]).name + "…", flush=True)
    subprocess.run(arguments, cwd=cwd, stdin=subprocess.DEVNULL, check=True)


def extract():
    output = ROOT / "server-data"
    output.mkdir(exist_ok=True)
    config = settings()
    if config["data_kind"] == "prepared":
        for name in ("dbc", "maps", "vmaps", "mmaps", "Cameras"):
            source = Path("/game") / name
            if source.exists():
                # Host validation also checks links; enforce inside the container independently.
                if source.is_symlink() or any(path.is_symlink() for path in source.rglob("*")):
                    raise RuntimeError("Prepared data must not contain symbolic links")
                shutil.copytree(source, output / name, dirs_exist_ok=True)
    else:
        tasks = [
            ("maps", ["/opt/ac/bin/map_extractor", "-i", "/game", "-o", str(output)]),
            ("models", ["/opt/ac/bin/vmap4_extractor", "-d", "/game/Data"]),
            ("vmaps", ["/opt/ac/bin/vmap4_assembler", "Buildings", "vmaps"]),
            ("mmaps", ["/opt/ac/bin/mmaps_generator", "--config", "/opt/ac/bin/mmaps-config.yaml",
                        "--threads", str(config["build_jobs"]), "--silent"]),
        ]
        for name, command in tasks:
            marker = output / (".finished-" + name)
            if marker.exists():
                print("Keeping completed extraction step: " + name, flush=True)
                continue
            run_tool(command, cwd=output)
            marker.write_text("completed\n")
    from .manager import validate_server_data
    validate_server_data(output)
    (ROOT / "data-ready.json").write_text(json.dumps({"client_build": 12340, "validation": "required files and headers only; gameplay unverified"}))
    print("Required server data files are present. In-game validation is still required.", flush=True)


def account(request):
    username, salt, verifier = registration(request["username"], request["password"])
    with connect(database="acore_auth") as connection, connection.cursor() as cursor:
        cursor.execute("SELECT id FROM account WHERE username=%s", (username,))
        if cursor.fetchone():
            raise ValueError("That account already exists; its password has not been changed.")
        cursor.execute("INSERT INTO account (username,salt,verifier,expansion) VALUES (%s,%s,%s,2)",
                       (username, salt, verifier))
        if request.get("administrator") is True:
            cursor.execute("INSERT INTO account_access (id,gmlevel,RealmID,comment) VALUES (%s,3,-1,%s)",
                           (cursor.lastrowid, "Created in Hearthkeeper"))
        connection.commit()
    print("Account created: " + username, flush=True)


def characters():
    with connect("reader", "acore_characters") as connection, connection.cursor() as cursor:
        cursor.execute("SELECT guid,name,level,race,class,online FROM characters ORDER BY name LIMIT 1000")
        print(json.dumps(cursor.fetchall()))


def capture_character(request):
    from hearthkeeper.archive import write_archive
    from hearthkeeper.database import Reader, capture
    config = settings()
    with connect("reader") as connection, connection.cursor() as cursor:
        cursor.execute("SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ")
        cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY")
        reader = Reader(connection, "mysql", {"characters": "acore_characters", "world": "acore_world"})
        core = next(source["commit"] for source in config["pins"]["sources"] if source["id"] == "core")
        snapshot = capture(reader, int(request["guid"]), config["project"], core)
    path = ROOT / "archives" / (str(request["guid"]) + "-" + timestamp() + ".hearth")
    write_archive(path, snapshot)
    print("ARCHIVE:" + path.name, flush=True)


def timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")


def backup():
    """Caller stops auth and world and checks they stopped before requesting this."""
    destination = ROOT / "backups" / (timestamp() + ".incomplete")
    destination.mkdir(parents=True, exist_ok=False)
    config = settings()
    with tempfile.TemporaryDirectory(dir=ROOT / "temp") as temporary:
        credentials = Path(temporary) / "mysql.cnf"
        credentials.write_text("[client]\nhost=database\nuser=hearthkeeper\npassword=" + config["secrets"]["server"] + "\n")
        credentials.chmod(0o600)
        with tempfile.TemporaryFile() as errors, gzip.open(destination / "databases.sql.gz", "wb") as output:
            process = subprocess.Popen(["mysqldump", "--defaults-extra-file=" + str(credentials),
                "--single-transaction", "--quick", "--routines", "--events", "--hex-blob",
                "--no-tablespaces", "--column-statistics=0", "--set-gtid-purged=OFF",
                "--databases", *DATABASES], stdout=subprocess.PIPE, stderr=errors)
            try:
                shutil.copyfileobj(process.stdout, output)
            finally:
                process.stdout.close()
            if process.wait() != 0:
                raise RuntimeError("Database backup failed. The incomplete folder is retained; it is not a usable backup.")
    shutil.copytree(ROOT / "etc", destination / "configuration")
    shutil.copyfile(ROOT / "realm.json", destination / "realm.json")
    hashes = {str(path.relative_to(destination)): hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
              for path in destination.rglob("*") if path.is_file()}
    (destination / "manifest.json").write_text(json.dumps({"format": "hearthkeeper-realm-backup/1",
        "sha256": hashes, "includes": ["four SQL databases", "configuration", "source pins", "local credentials"],
        "excludes": ["client and extracted game assets", "Docker image"],
        "restore_tested": False}, indent=2))
    complete = destination.with_suffix("")
    destination.rename(complete)
    print("BACKUP:" + complete.name, flush=True)


def main():
    command = sys.argv[1]
    if command in ("auth", "world"):
        name = "authserver" if command == "auth" else "worldserver"
        os.execv("/opt/ac/bin/" + name, [name, "-c", "/realm/etc/" + name + ".conf"])
    elif command == "import":
        run_tool(["/opt/ac/bin/dbimport", "-c", "/realm/etc/dbimport.conf"])
    elif command in ("account", "capture"):
        request = json.loads(sys.stdin.read(8192))
        (account if command == "account" else capture_character)(request)
    else:
        {"configure": configure, "bootstrap": bootstrap, "finalize": finalize,
         "extract": extract, "characters": characters, "backup": backup}[command]()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr, flush=True)
        raise SystemExit(1)
    except Exception:
        # Never print database connection messages, credentials, or input requests.
        print("Realm operation failed. Check the service status and the operation stage.", file=sys.stderr, flush=True)
        raise SystemExit(1)
