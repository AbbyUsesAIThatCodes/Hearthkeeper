"""Local Docker realm orchestration, independent of the desktop toolkit."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import queue
import re
import secrets
import shutil
import subprocess
import threading

from hearthkeeper.realm import read_lock

PACKAGE = Path(__file__).resolve().parents[1]


class RealmError(Exception):
    pass


def atomic_json(path, value):
    temporary = path.with_name(path.name + ".writing")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(0o600)
    os.replace(temporary, path)


def validate_server_data(path):
    path = Path(path)
    for name in ("dbc", "maps", "vmaps", "mmaps"):
        if not (path / name).is_dir() or not any((path / name).iterdir()):
            raise RealmError("Server data is missing a populated " + name + " folder.")
    for name in ("Map.dbc", "Spell.dbc", "CharStartOutfit.dbc"):
        dbc = path / "dbc" / name
        if not dbc.is_file():
            raise RealmError("Required data file is missing: dbc/" + name)
        with dbc.open("rb") as stream:
            if stream.read(4) != b"WDBC":
                raise RealmError("The data does not have an original client DBC header: " + name)
    if not any((path / "maps").glob("*.map")) or not any((path / "vmaps").glob("*.vmtree")):
        raise RealmError("Terrain or collision data is incomplete.")
    if not any((path / "mmaps").glob("*.mmtile")):
        raise RealmError("Navigation tiles are missing.")


def validate_source(path, kind):
    path = Path(path).resolve()
    if not path.is_dir():
        raise RealmError("Choose an existing game-data folder.")
    if kind == "client":
        if not (path / "Data" / "lichking.MPQ").is_file() or not (path / "Data" / "patch-3.MPQ").is_file():
            raise RealmError("Select the original 3.3.5a client root containing Data/lichking.MPQ and Data/patch-3.MPQ.")
    elif kind == "prepared":
        validate_server_data(path)
    else:
        raise RealmError("Unknown game-data format")
    return path


def validate_config(config):
    if config.get("schema") != 1 or not re.fullmatch(r"hearthkeeper-[0-9a-f]{12}", config.get("project", "")):
        raise RealmError("This is not a supported Hearthkeeper realm.")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _'-]{0,31}", config.get("name", "")):
        raise RealmError("Use a realm name of 1–32 letters, numbers, spaces, apostrophes, or dashes.")
    for name, low, high in (("xp_rate", 1, 10), ("random_bots", 0, 100), ("build_jobs", 1, 8)):
        if type(config.get(name)) is not int or not low <= config[name] <= high:
            raise RealmError("Invalid realm setting: " + name)
    if config.get("data_kind") not in ("client", "prepared"):
        raise RealmError("Unknown game-data format")
    if not isinstance(config.get("data_path"), str) or not config["data_path"]:
        raise RealmError("Game-data location is missing")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", config.get("docker_context", "")):
        raise RealmError("Invalid Docker context")
    if set(config.get("secrets", {})) != {"root", "server", "reader"} or any(
            not re.fullmatch(r"[0-9a-f]{64}", value) for value in config["secrets"].values()):
        raise RealmError("Realm credentials are missing or malformed")
    # A preview may only operate the source set it was tested with; upgrades need a separate workflow.
    if config.get("pins") != read_lock():
        raise RealmError("This realm uses a different source lock. Open it with its matching Hearthkeeper version.")


class Runner:
    def __init__(self, log=lambda line: None):
        self.log = log
        self.stop_after_step = threading.Event()
        self.redactions = []

    def run(self, arguments, *, cwd=None, payload=None, timeout=None):
        if self.stop_after_step.is_set():
            raise RealmError("Stopped between steps. Completed work is retained; use Install / Resume to continue.")
        kwargs = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        process = subprocess.Popen(arguments, cwd=cwd, stdin=subprocess.PIPE if payload is not None else subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                   encoding="utf-8", errors="replace", **kwargs)
        if payload is not None:
            process.stdin.write(json.dumps(payload))
            process.stdin.close()
        lines = queue.Queue()

        def read_output():
            for line in process.stdout:
                lines.put(line.rstrip())
            process.stdout.close()
            lines.put(None)

        thread = threading.Thread(target=read_output, daemon=True)
        thread.start()
        output = []
        import time
        started = time.monotonic()
        try:
            while True:
                if timeout and time.monotonic() - started > timeout:
                    process.kill()
                    raise RealmError("The prerequisite check timed out. Check Docker Desktop and try again.")
                try:
                    line = lines.get(timeout=0.2)
                except queue.Empty:
                    continue
                if line is None:
                    break
                for secret in self.redactions:
                    line = line.replace(secret, "[redacted]")
                output.append(line)
                if len(output) > 10000:
                    del output[:1000]
                self.log(line)
            if process.wait() != 0:
                raise RealmError("This step failed. Its output is shown in Activity; completed steps are retained.")
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait()
            thread.join(timeout=2)
        return "\n".join(output)


def local_docker(runner, context=None):
    if not shutil.which("docker"):
        raise RealmError("Docker was not found. Install Docker Desktop, select Linux containers, and reopen Hearthkeeper.")
    context = context or runner.run(["docker", "context", "show"], timeout=15).strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", context):
        raise RealmError("Docker context has an unsupported name")
    endpoint = runner.run(["docker", "context", "inspect", context, "--format", "{{.Endpoints.docker.Host}}"], timeout=15).strip()
    if not endpoint.startswith(("unix://", "npipe://")):
        raise RealmError("Select a local Docker Desktop/Unix-socket context. Remote Docker hosts are not supported.")
    docker = ["docker", "--context", context]
    result = runner.run(docker + ["info", "--format", "{{.OSType}} {{.MemTotal}}"], timeout=30).split()
    if not result or result[0] != "linux":
        raise RealmError("Docker must be running Linux containers.")
    runner.run(docker + ["compose", "version", "--short"], timeout=15)
    return {"context": context, "memory_gib": round(int(result[1]) / 2**30, 1)}


def create_realm(destination, *, name, data_path, data_kind, docker_context,
                 xp_rate=1, random_bots=0, build_jobs=2):
    destination = Path(destination).resolve()
    source = validate_source(data_path, data_kind)
    if destination == source or destination.is_relative_to(source) or source.is_relative_to(destination):
        raise RealmError("Keep the realm folder separate from the game-data folder.")
    config = {"schema": 1, "project": "hearthkeeper-" + secrets.token_hex(6), "name": name,
              "data_path": str(source), "data_kind": data_kind, "docker_context": docker_context,
              "xp_rate": xp_rate, "random_bots": random_bots, "build_jobs": build_jobs,
              "phase": "created", "pins": read_lock(),
              "secrets": {role: secrets.token_hex(32) for role in ("root", "server", "reader")}}
    validate_config(config)
    destination.mkdir(parents=True, exist_ok=False)
    destination.chmod(0o700)
    for name in ("etc", "logs", "temp", "server-data", "archives", "backups", "bundle"):
        (destination / name).mkdir()
    atomic_json(destination / "realm.json", config)
    return ManagedRealm(destination)


def compose_document(config):
    image = config["project"] + ":0.1.0a2"
    identity = f"{os.getuid()}:{os.getgid()}" if os.name != "nt" else "1000:1000"
    runtime = {"image": image, "user": identity, "init": True,
               "environment": {"PYTHONUNBUFFERED": "1"},
               "security_opt": ["no-new-privileges:true"], "cap_drop": ["ALL"]}
    database = {"image": "mysql:8.4", "environment": {"MYSQL_ROOT_PASSWORD": config["secrets"]["root"],
                "MYSQL_ROOT_HOST": "%"}, "volumes": ["database:/var/lib/mysql"],
                "healthcheck": {"test": ["CMD", "mysqladmin", "ping", "-h", "127.0.0.1", "--silent"],
                                "interval": "5s", "timeout": "5s", "retries": 60},
                "restart": "no"}
    volumes = ["./etc:/realm/etc:ro", "./server-data:/realm/server-data:ro", "./logs:/realm/logs", "./temp:/realm/temp"]
    services = {"database": database,
        "control": {**runtime, "profiles": ["tools"], "build": {"context": "./bundle", "args": {"BUILD_JOBS": str(config["build_jobs"])}},
                    "volumes": [".:/realm"], "command": ["configure"]},
        "extract": {**runtime, "profiles": ["tools"], "volumes": [".:/realm", {"type": "bind",
                    "source": config["data_path"], "target": "/game", "read_only": True}], "command": ["extract"]}}
    for service, port in (("auth", 3724), ("world", 8085)):
        services[service] = {**runtime, "command": [service], "volumes": volumes,
            "ports": [f"127.0.0.1:{port}:{port}"], "restart": "no", "stop_grace_period": "2m",
            "depends_on": {"database": {"condition": "service_healthy"}},
            "healthcheck": {"test": ["CMD", "python3", "-c", f"import socket; socket.create_connection(('127.0.0.1',{port}),2).close()"],
                            "interval": "10s", "timeout": "5s", "retries": 90, "start_period": "30s"}}
    return {"name": config["project"], "services": services, "volumes": {"database": {}}}


class ManagedRealm:
    def __init__(self, path, runner=None):
        self.path = Path(path).resolve()
        self.config = json.loads((self.path / "realm.json").read_text(encoding="utf-8"))
        validate_config(self.config)
        self.runner = runner or Runner()
        self.runner.redactions = list(self.config["secrets"].values())

    def save(self):
        atomic_json(self.path / "realm.json", self.config)

    def compose(self, *arguments, payload=None):
        return self.runner.run(["docker", "--context", self.config["docker_context"], "compose",
            "--project-name", self.config["project"], "--file", str(self.path / "compose.json"), *arguments],
            cwd=self.path, payload=payload)

    def prepare_bundle(self):
        bundle = self.path / "bundle"
        bundle.mkdir(exist_ok=True)
        for name in ("Dockerfile", "fetch_sources.py"):
            shutil.copyfile(PACKAGE / "server" / name, bundle / name)
        atomic_json(bundle / "realm.lock.json", self.config["pins"])
        package = bundle / "hearthkeeper"
        package.mkdir(exist_ok=True)
        for name in ("__init__.py", "archive.py", "database.py", "realm.py"):
            shutil.copyfile(PACKAGE / name, package / name)
        (package / "server").mkdir(exist_ok=True)
        for name in ("__init__.py", "manager.py", "container_entry.py", "accounts.py"):
            shutil.copyfile(PACKAGE / "server" / name, package / "server" / name)
        (package / "data").mkdir(exist_ok=True)
        atomic_json(package / "data" / "realm.lock.json", self.config["pins"])
        # Compose interpolates strings even in JSON; literal dollar signs in user paths must survive.
        text = json.dumps(compose_document(self.config), indent=2).replace("$", "$$")
        target = self.path / "compose.json"
        target.write_text(text, encoding="utf-8")
        target.chmod(0o600)

    def check(self):
        result = local_docker(self.runner, self.config["docker_context"])
        self.prepare_bundle()
        return result

    def control(self, command, payload=None):
        return self.compose("run", "--rm", "--no-deps", "-T", "control", command, payload=payload)

    def status(self):
        if not (self.path / "compose.json").is_file():
            return []
        output = self.compose("ps", "--all", "--format", "json")
        if not output.strip():
            return []
        # Compose versions return either JSONL objects or one JSON array.
        if output.lstrip().startswith("["):
            return json.loads(output)
        return [json.loads(line) for line in output.splitlines() if line.startswith("{")]

    def install(self):
        if self.config["phase"] == "installed":
            raise RealmError("This realm is already installed. Use Start realm.")
        validate_source(self.config["data_path"], self.config["data_kind"])
        self.check()
        if any(row.get("Service") in ("auth", "world") and row.get("State") == "running" for row in self.status()):
            raise RealmError("Stop auth and world before resuming setup.")
        tasks = [("Building the pinned core and both modules", lambda: self.compose("build", "control")),
                 ("Preparing realm configuration", lambda: self.control("configure")),
                 ("Starting the dedicated database", lambda: self.compose("up", "-d", "--wait", "--wait-timeout", "300", "database")),
                 ("Creating realm databases and service accounts", lambda: self.control("bootstrap")),
                 ("Importing core and module SQL", lambda: self.control("import")),
                 ("Registering the local realm", lambda: self.control("finalize")),
                 ("Preparing game data (navigation may take hours)", lambda: self.compose("run", "--rm", "--no-deps", "-T", "extract"))]
        for index, (label, task) in enumerate(tasks):
            self.runner.log(f"STEP {index + 1}/{len(tasks)} · {label}")
            task()
            self.config["phase"] = "step-" + str(index + 1)
            self.save()
        self.config["phase"] = "installed"
        self.save()
        self.runner.log("Installation steps completed. Create a game account, then Start realm.")

    def start(self):
        if self.config["phase"] != "installed":
            raise RealmError("Finish Install / Resume first.")
        validate_server_data(self.path / "server-data")
        self.check()
        self.compose("up", "-d", "--no-build", "--wait", "--wait-timeout", "900", "auth", "world")
        return "Auth and world ports are responding. In-game login remains a separate check."

    def stop(self):
        self.check()
        self.compose("stop", "--timeout", "120", "world", "auth", "database")
        return "Realm services stopped. Database volume and files are retained."

    def backup(self):
        self.check()
        self.compose("stop", "--timeout", "120", "world", "auth")
        states = self.status()
        if any(row.get("Service") in ("world", "auth") and row.get("State") not in ("exited", "created") for row in states):
            raise RealmError("Auth and world must be stopped before backup.")
        self.compose("up", "-d", "--wait", "--wait-timeout", "300", "database")
        return self.control("backup") + "\nAuth and world remain stopped. Use Start realm when ready."

    def create_account(self, username, password, administrator=False):
        from .accounts import registration
        registration(username, password)
        self.check()
        self.runner.redactions += [password, password.upper()]
        return self.control("account", {"username": username, "password": password, "administrator": administrator})

    def capture(self, guid):
        self.check()
        output = self.control("capture", {"guid": int(guid)})
        name = next((line.removeprefix("ARCHIVE:") for line in output.splitlines() if line.startswith("ARCHIVE:")), None)
        if not name or Path(name).name != name:
            raise RealmError("Capture did not return an archive filename.")
        return self.path / "archives" / name
