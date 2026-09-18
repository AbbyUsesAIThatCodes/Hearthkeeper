"""Build-time source fetches from the bundled, reviewed lockfile."""
import json
from pathlib import Path
import re
import subprocess

destinations = {"core": "/src", "playerbots": "/src/modules/mod-playerbots",
                "progression": "/src/modules/mod-individual-progression"}
for source in json.loads(Path("/pins.json").read_text())["sources"]:
    if source["id"] not in destinations:
        continue
    if not re.fullmatch(r"[0-9a-f]{40}", source["commit"]) or not re.fullmatch(
            r"https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\.git", source["url"]):
        raise SystemExit("Invalid source lock")
    destination = destinations[source["id"]]
    subprocess.run(["git", "init", destination], check=True)
    git = ["git", "-c", "core.hooksPath=/dev/null", "-C", destination]
    subprocess.run(git + ["fetch", "--depth=1", source["url"], source["commit"]], check=True)
    subprocess.run(git + ["checkout", "--detach", "FETCH_HEAD"], check=True)
    actual = subprocess.check_output(git + ["rev-parse", "HEAD"], text=True).strip()
    if actual != source["commit"]:
        raise SystemExit("Source revision mismatch")
