"""Package the isolated Portal study; the regular desktop build stays unchanged."""
import os
from pathlib import Path
import shutil
import PyInstaller.__main__

pack = Path("var/portal-study")
if not (pack / "study.json").is_file():
    raise SystemExit("Run tools/prepare_portal_study.py first.")
PyInstaller.__main__.run([
    "launch_portal.py", "--noconfirm", "--clean", "--windowed", "--onedir",
    "--name", "Hearthkeeper-Portal-Study", "--collect-data", "hearthkeeper",
    "--hidden-import", "PySide6.QtQuick3D", "--hidden-import", "PySide6.QtShaderTools",
    "--hidden-import", "win32com.client", "--collect-data", "PySide6",
    "--exclude-module", "PySide6.QtWebEngineCore", "--exclude-module", "PySide6.QtWebEngineWidgets",
    "--exclude-module", "PySide6.QtWebEngineQuick",
    "--add-data", str(pack / "study.json") + os.pathsep + "portal-study",
    "--add-data", str(pack / "qml") + os.pathsep + "portal-study/qml",
])
destination = Path("dist/Hearthkeeper-Portal-Study")
shutil.copyfile("docs/PORTAL_SCENE_STUDY.md", destination / "READ-ME-FIRST.md")
shutil.copyfile("THIRD_PARTY_NOTICES.md", destination / "THIRD_PARTY_NOTICES.md")
shutil.copytree("licenses", destination / "licenses", dirs_exist_ok=True)
# Keep installer sources available exactly as in the ordinary desktop package.
from hearthkeeper.server.manager import PACKAGE
for relative in ("__init__.py", "archive.py", "database.py", "realm.py", "data/realm.lock.json",
                 "server/Dockerfile", "server/fetch_sources.py", "server/manager.py",
                 "server/container_entry.py", "server/accounts.py", "server/__init__.py"):
    path = destination / "_internal/hearthkeeper" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PACKAGE / relative, path)
