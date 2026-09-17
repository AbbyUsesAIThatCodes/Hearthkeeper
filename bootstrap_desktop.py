"""Repository launcher: prepare only the project's virtual environment, then open Qt."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    if not (3, 11) <= sys.version_info < (3, 14):
        raise RuntimeError("The source desktop launcher currently needs Python 3.11–3.13. Python 3.12 is recommended; the packaged app needs no Python installation.")
    if sys.argv[1:] == ["--check-python"]:
        print(json.dumps({"version": list(sys.version_info[:3]), "executable": sys.executable}))
        return
    environment = ROOT / ".venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        print("Creating Hearthkeeper's project-local Python environment…", flush=True)
        subprocess.run([sys.executable, "-m", "venv", str(environment)], check=True)
    # Entry points and metadata matter too, not just the dependency list.
    fingerprint = hashlib.sha256((ROOT / "pyproject.toml").read_bytes()).hexdigest()
    marker = environment / "hearthkeeper-desktop-dependencies.txt"
    if not marker.exists() or marker.read_text() != fingerprint:
        print("Installing the desktop toolkit into .venv. The first download is substantial…", flush=True)
        subprocess.run([str(python), "-m", "pip", "install", "-e", ".[desktop]"], cwd=ROOT, check=True)
        marker.write_text(fingerprint)
    executable = python.with_name("pythonw.exe") if os.name == "nt" else python
    subprocess.Popen([str(executable), "-m", "hearthkeeper.six_worlds"], cwd=ROOT)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("Hearthkeeper could not launch: " + str(error), file=sys.stderr)
        raise SystemExit(1)
