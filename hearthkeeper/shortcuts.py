"""Create only Hearthkeeper's desktop shortcut, on explicit request."""
import os
from pathlib import Path
import sys

from PySide6.QtCore import QStandardPaths


def create_shortcut(*, desktop_path=None, data_path=None):
    if os.name != "nt":
        raise RuntimeError("Automatic shortcuts currently support Windows. You can pin the application using your desktop environment.")
    desktop = Path(desktop_path or QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DesktopLocation))
    target = desktop / "Hearthkeeper.lnk"
    if target.exists():
        raise FileExistsError("A Hearthkeeper desktop shortcut already exists; it has been kept.")
    package = Path(__file__).parent
    frozen = getattr(sys, "frozen", False)
    executable = Path(sys.executable) if frozen else Path(sys.executable).with_name("pythonw.exe")
    if not executable.is_file():
        raise RuntimeError("Run the Windows launcher once to prepare the desktop environment.")
    import win32com.client
    from PySide6.QtGui import QIcon
    icon = Path(data_path or QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)) / "hearthkeeper.ico"
    icon.parent.mkdir(parents=True, exist_ok=True)
    if not icon.exists() and not QIcon(str(package / "assets" / "hearthkeeper.svg")).pixmap(256, 256).save(str(icon), "ICO"):
        raise RuntimeError("Could not prepare the shortcut icon.")
    shortcut = win32com.client.Dispatch("WScript.Shell").CreateShortcut(str(target))
    shortcut.TargetPath = str(executable)
    shortcut.Arguments = "" if frozen else "-m hearthkeeper.desktop"
    shortcut.WorkingDirectory = str(executable.parent if frozen else package.parent)
    shortcut.Description = "Hearthkeeper - your own Azeroth"
    shortcut.IconLocation = str(icon)
    shortcut.Save()
    return target
