"""Small local CLI; database passwords are prompted, never command-line arguments."""

import argparse
import datetime
import getpass
import json
from pathlib import Path
import sqlite3
import sys
import uuid
import webbrowser

from . import CODENAME, __version__
from .archive import ArchiveError, compare_archives, json_bytes, read_archive, write_archive
from .database import capture, mysql_reader, sqlite_reader
from .demo import create_fixture
from .model import normalized
from .realm import doctor, plan, prepare_sources
from .viewer import render_archive
from .sources import SourceError, fetch_snapshot, import_file, load_catalog, offerings, verify_saved


def parser():
    command = argparse.ArgumentParser(description=f"Hearthkeeper {__version__} — {CODENAME}")
    command.add_argument("--version", action="version", version=f"{__version__} — {CODENAME}")
    commands = command.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Create a fictional database, archive, and offline viewer")
    demo.add_argument("--directory", type=Path, default=Path("var/demo"))
    demo.add_argument("--open", action="store_true", help="Open the generated local HTML in your browser")
    for name in ("verify", "inspect"):
        child = commands.add_parser(name)
        child.add_argument("archive", type=Path)
    render = commands.add_parser("render", help="Create a self-contained offline HTML document")
    render.add_argument("archive", type=Path)
    render.add_argument("--output", type=Path, required=True)
    difference = commands.add_parser("diff", help="Compare tables in two snapshots of the same character")
    difference.add_argument("before", type=Path)
    difference.add_argument("after", type=Path)
    for name in ("capture-sqlite", "capture-mysql"):
        child = commands.add_parser(name, help="Read-only capture; currently a partial archive")
        child.add_argument("--guid", type=int, required=True)
        child.add_argument("--realm", required=True, help="Stable realm namespace, reused for future captures")
        child.add_argument("--core-commit", default="unrecorded")
        child.add_argument("--output", type=Path, required=True)
        if name == "capture-sqlite":
            child.add_argument("database", type=Path, help="AzerothCore-shaped fixture; not a WoW server database")
        else:
            child.add_argument("--host", default="127.0.0.1")
            child.add_argument("--port", type=int, default=3306)
            child.add_argument("--user", default="hearthkeeper_reader")
            child.add_argument("--characters", default="acore_characters")
            child.add_argument("--world", default="acore_world")
            child.add_argument("--tls-ca", type=Path)
    commands.add_parser("doctor", help="Check only Python and Git availability")
    commands.add_parser("realm-plan", help="Show candidate source pins without changing anything")
    sources = commands.add_parser("prepare-sources", help="Explicit network action: fetch pinned source checkouts")
    sources.add_argument("--directory", type=Path, default=Path("var/sources"))
    sources.add_argument("--include-client", action="store_true")
    catalog = commands.add_parser("source-catalog", help="List bundled source offerings without network access")
    catalog.add_argument("--provider", default="")
    catalog.add_argument("--era", default="")
    catalog.add_argument("--search", default="")
    for name in ("source-fetch", "source-import"):
        child = commands.add_parser(name, help="Preserve source code or one explicitly selected downloaded file")
        child.add_argument("offering", help="Offering ID from source-catalog")
        child.add_argument("--directory", type=Path, required=True)
        if name == "source-import":
            child.add_argument("file", type=Path)
    verify = commands.add_parser("source-verify", help="Check saved source-copy bytes against their manifest")
    verify.add_argument("directory", type=Path)
    return command


def main(arguments=None):
    args = parser().parse_args(arguments)
    try:
        if args.command == "demo":
            stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
            directory = args.directory / (stamp + "-" + uuid.uuid4().hex[:8])
            database = create_fixture(directory / "fictional-realm.sqlite")
            with sqlite_reader(database) as reader:
                snapshot = capture(reader, 7, "copperleaf-demo", demo=True)
            archive = write_archive(directory / "brindle.hearth", snapshot)
            page = render_archive(archive, directory / "brindle.html")
            print("Fictional demo generated. No WoW server or personal data accessed.")
            print(f"Archive: {archive.resolve()}\nViewer:  {page.resolve()}")
            print("Preview: partial capture; live restore and cross-server import are not implemented.")
            if args.open and not webbrowser.open(page.resolve().as_uri()):
                print("Open the HTML file above manually in your browser.")
        elif args.command == "verify":
            manifest, snapshot = read_archive(args.archive)
            print(f"Checksum and structure valid: {manifest['format']}")
            print(f"Captured {len(snapshot['tables'])} tables. Partial archive; unsigned; no authenticity guarantee.")
        elif args.command == "inspect":
            _, snapshot = read_archive(args.archive)
            print(json_bytes(normalized(snapshot)).decode("utf-8"))
        elif args.command == "render":
            print(render_archive(args.archive, args.output).resolve())
        elif args.command == "diff":
            print(json.dumps(compare_archives(args.before, args.after), indent=2))
        elif args.command == "capture-sqlite":
            with sqlite_reader(args.database) as reader:
                snapshot = capture(reader, args.guid, args.realm, args.core_commit)
            print(write_archive(args.output, snapshot).resolve())
        elif args.command == "capture-mysql":
            if args.output.exists():
                raise ArchiveError("Output already exists; choose a new filename")
            password = getpass.getpass("Read-only database password (never saved): ")
            with mysql_reader(host=args.host, port=args.port, user=args.user, password=password,
                              characters=args.characters, world=args.world, tls_ca=args.tls_ca) as reader:
                snapshot = capture(reader, args.guid, args.realm, args.core_commit)
            print(write_archive(args.output, snapshot).resolve())
            print("Partial character archive only. Review Coverage before relying on it.")
        elif args.command == "doctor":
            print(json.dumps(doctor(), indent=2))
        elif args.command == "realm-plan":
            print(plan())
        elif args.command == "prepare-sources":
            print(prepare_sources(args.directory, args.include_client))
            print("Sources prepared; no build, dependencies, game data, services, or submodules installed.")
        elif args.command == "source-catalog":
            print(json.dumps(offerings(load_catalog(), provider=args.provider, era=args.era, query=args.search), indent=2))
        elif args.command in ("source-fetch", "source-import"):
            entry = next((entry for entry in load_catalog()["offerings"] if entry["id"] == args.offering), None)
            if entry is None:
                raise SourceError("Unknown offering. Run source-catalog to see available IDs.")
            if args.command == "source-fetch":
                result = fetch_snapshot(entry, args.directory, log=print)
            else:
                result = import_file(entry, args.file, args.directory, log=print)
            print(result)
            print("Saved copy only. No client, database, or realm has been installed or changed.")
        elif args.command == "source-verify":
            print(verify_saved(args.directory))
        return 0
    except SourceError as error:
        print(f"Hearthkeeper sources: {error}", file=sys.stderr)
        return 1
    except (ArchiveError, OSError, sqlite3.Error, KeyError, TypeError, ValueError, RecursionError) as error:
        print(f"Hearthkeeper: {error if isinstance(error, (ArchiveError, OSError)) else 'Invalid database or archive structure'}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Hearthkeeper: stopped.", file=sys.stderr)
        return 130
