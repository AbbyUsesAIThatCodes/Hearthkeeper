"""CI-only MySQL integration using disposable databases and fictional fixture rows."""
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pymysql
from hearthkeeper.archive import write_archive, read_archive
from hearthkeeper.database import capture, identifier, mysql_reader, WORLD_TABLES
from hearthkeeper.demo import create_fixture


def main():
    if os.environ.get("HEARTHKEEPER_DISPOSABLE_MYSQL") != "1":
        raise SystemExit("This test writes fictional fixtures. Set HEARTHKEEPER_DISPOSABLE_MYSQL=1 only for a disposable CI MySQL service.")
    root_password = os.environ["HEARTHKEEPER_CI_MYSQL_PASSWORD"]
    read_password = "fictional-reader-ci-only"
    databases = {"characters": "hk_ci_characters", "world": "hk_ci_world"}
    with tempfile.TemporaryDirectory() as temporary:
        directory = Path(temporary)
        sqlite_path = create_fixture(directory / "source.sqlite")
        with closing(sqlite3.connect(sqlite_path)) as sqlite_connection:
            sqlite_connection.row_factory = sqlite3.Row
            with pymysql.connect(host="127.0.0.1", user="root", password=root_password, autocommit=True) as admin:
                with admin.cursor() as cursor:
                    for database in databases.values():
                        # Fail on an existing database; never replace a developer's data.
                        cursor.execute(f"CREATE DATABASE {identifier(database)} CHARACTER SET utf8mb4")
                    for table in sqlite_connection.execute("SELECT name FROM sqlite_master WHERE type='table'"):
                        name = table["name"]
                        namespace = "world" if name in WORLD_TABLES else "characters"
                        qualified = identifier(databases[namespace]) + "." + identifier(name)
                        columns = list(sqlite_connection.execute(f"PRAGMA table_info({identifier(name)})"))
                        types = {"INTEGER": "BIGINT", "TEXT": "TEXT", "REAL": "DOUBLE"}
                        definitions = ", ".join(identifier(column["name"]) + " " + types[column["type"]] for column in columns)
                        cursor.execute(f"CREATE TABLE {qualified} ({definitions}) ENGINE=InnoDB")
                        rows = list(sqlite_connection.execute(f"SELECT * FROM {identifier(name)}"))
                        if rows:
                            placeholders = ",".join(["%s"] * len(columns))
                            cursor.executemany(f"INSERT INTO {qualified} VALUES ({placeholders})", [tuple(row) for row in rows])
                    cursor.execute("CREATE USER 'hearthkeeper_reader'@%s IDENTIFIED BY %s", ("%", read_password))
                    for database in databases.values():
                        cursor.execute(f"GRANT SELECT ON {identifier(database)}.* TO 'hearthkeeper_reader'@'%'")
        with mysql_reader(host="127.0.0.1", port=3306, user="hearthkeeper_reader", password=read_password,
                          characters=databases["characters"], world=databases["world"]) as reader:
            try:
                reader.query("UPDATE hk_ci_characters.characters SET money = 0")
            except pymysql.MySQLError:
                pass
            else:
                raise AssertionError("Read-only identity/transaction allowed a write")
            snapshot = capture(reader, 7, "ci-fictional-realm", demo=True)
        archive = write_archive(directory / "mysql.hearth", snapshot)
        _, restored = read_archive(archive)
        assert restored["source"]["backend"] == "mysql"
        assert restored["tables"]["characters.characters"]["rows"][0]["money"] == 124506
        assert {row["guid"] for row in restored["tables"]["characters.item_instance"]["rows"]} == {101,102,103,104,105,106}
        assert len(restored["tables"]["characters.character_settings"]["rows"]) == 2
        assert "characters.custom_town_citizenship" in restored["coverage"]["unhandled_tables"]
    print("MySQL fixture integration passed: SELECT-only identity, read-only transaction, relational capture, archive validation.")
    print("This does not establish compatibility with a running WoW realm or full upstream schemas.")


if __name__ == "__main__":
    main()
