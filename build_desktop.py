"""Build the native app; run in the dedicated Windows packaging job."""
import os
from pathlib import Path
import shutil
from importlib.metadata import distribution
import sys
import PyInstaller.__main__
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
application = QApplication([])
Path("build").mkdir(exist_ok=True)
icon = Path("build/hearthkeeper.ico")
if not QIcon("hearthkeeper/assets/hearthkeeper.svg").pixmap(256, 256).save(str(icon), "ICO"):
    raise SystemExit("Could not create the application icon")
arguments = [
    "launch_desktop.py", "--noconfirm", "--clean", "--windowed", "--onedir", "--name", "Hearthkeeper",
    "--icon", str(icon), "--collect-data", "hearthkeeper", "--hidden-import", "win32com.client",
    "--exclude-module", "PySide6.QtWebEngineCore", "--exclude-module", "PySide6.QtWebEngineWidgets",
    "--exclude-module", "PySide6.QtWebEngineQuick", "--exclude-module", "PySide6.QtQml",
    "--copy-metadata", "PySide6", "--copy-metadata", "PySide6-Essentials",
    "--copy-metadata", "shiboken6", "--copy-metadata", "pywin32",
]
# The Docker build needs these Python sources as files, in addition to the
# modules embedded in PyInstaller's executable archive.
runtime_sources = ["__init__.py", "archive.py", "database.py", "realm.py",
                   "server/__init__.py", "server/manager.py", "server/accounts.py",
                   "server/container_entry.py", "server/fetch_sources.py"]
for relative in runtime_sources:
    source = Path("hearthkeeper") / relative
    arguments += ["--add-data", str(source) + os.pathsep + str(source.parent)]
PyInstaller.__main__.run(arguments)
destination = Path("dist/Hearthkeeper")
shutil.copyfile("THIRD_PARTY_NOTICES.md", destination / "THIRD_PARTY_NOTICES.md")
shutil.copytree("licenses", destination / "licenses", dirs_exist_ok=True)
for package in ("pywin32", "PySide6", "PySide6-Essentials", "shiboken6", "pyinstaller"):
    metadata = distribution(package)
    for source in metadata.files or []:
        if "license" in source.name.lower() or "copying" in source.name.lower():
            path = metadata.locate_file(source)
            if path.is_file():
                shutil.copyfile(path, destination / "licenses" / (package + "-" + source.name))
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.is_file():
    shutil.copyfile(python_license, destination / "licenses" / "Python-LICENSE.txt")
