"""Explicit source preparation. Does not build, install, or start services."""

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from .archive import ArchiveError, write_new, json_bytes

SOURCE_PATHS = {"core": "azerothcore", "playerbots": "azerothcore/modules/mod-playerbots",
                "progression": "azerothcore/modules/mod-individual-progression", "wowee": "wowee"}


def read_lock():
    return json.loads((Path(__file__).parent / "data" / "realm.lock.json").read_text(encoding="utf-8"))


def plan():
    lock = read_lock()
    lines = ["Hearthkeeper realm candidate", "Protocol: 3.3.5a / build 12340 / WoWee wotlk",
             "Status: source identities pinned; combined build and gameplay NOT verified.", ""]
    for source in lock["sources"]:
        lines.append(f"{source['id']}: {source['repository']} ({source['branch']})")
        lines.append(f"  {source['commit']}")
    lines += ["", "Next: prepare sources in a dedicated development VM; build using the linked upstream guides.",
              "Supply matching game data, check module configs, then test login with both clients.",
              "No source downloads, builds, ports, or database changes occur with realm-plan."]
    return "\n".join(lines)


def doctor():
    return {"python": sys.version.split()[0], "python_supported": sys.version_info >= (3, 11),
            "git_available": shutil.which("git") is not None,
            "demo_requires": "Python 3.11+ only; no WoW files or database server",
            "realm_state": "Not inspected; no game data directories or personal folders scanned",
            "realm_dependencies": "See docs/REALM_SETUP.md; a build is not attempted by doctor"}


def prepare_sources(directory, include_client=False):
    if not shutil.which("git"):
        raise ArchiveError("Install Git in the development environment before preparing sources")
    directory = Path(directory).resolve()
    # Exclusive root creation prevents replacing an existing checkout or user's work.
    directory.mkdir(parents=True, exist_ok=False)
    empty_hooks = directory / "empty-git-hooks"
    empty_hooks.mkdir()
    selected = [source for source in read_lock()["sources"] if include_client or source["id"] != "wowee"]
    for source in selected:
        if not re.fullmatch(r"[0-9a-f]{40}", source["commit"]):
            raise ArchiveError("Invalid source commit in lock")
        if source["id"] not in SOURCE_PATHS or not re.fullmatch(
                r"https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", source["url"]):
            raise ArchiveError("Invalid source repository in lock")
        target = directory / SOURCE_PATHS[source["id"]]
        git = ["git", "-c", f"core.hooksPath={empty_hooks}", "-c", "protocol.file.allow=never"]
        commands = [git + ["init", str(target)],
                    git + ["-C", str(target), "remote", "add", "origin", source["url"]],
                    git + ["-C", str(target), "fetch", "--depth=1", "origin", source["commit"]],
                    git + ["-C", str(target), "checkout", "--detach", source["commit"]]]
        print(f"Preparing {source['id']} at {source['commit'][:12]}…", flush=True)
        for command in commands:
            try:
                subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=600)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as error:
                raise ArchiveError(f"Source preparation failed for {source['id']}. Partial files remain in {directory}; use a fresh directory to retry.") from error
        actual = subprocess.check_output(git + ["-C", str(target), "rev-parse", "HEAD"], text=True).strip()
        if actual != source["commit"]:
            raise ArchiveError("Prepared source did not match its pinned commit")
    write_new(directory / "hearthkeeper-sources.json", json_bytes({"sources": selected, "built": False}))
    return directory
