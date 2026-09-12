# Desktop distribution notices

Hearthkeeper's native interface uses **Qt for Python / PySide6 6.8.3** and
**Shiboken 6.8.3**, by The Qt Company and contributors. The applicable GNU LGPL v3
and GPL v3 texts are included in `licenses/`. Qt libraries are distributed as
separate dynamic libraries in the desktop package. Corresponding upstream source:

- https://github.com/qt/pyside-setup/tree/v6.8.3
- https://github.com/qt/qtbase/tree/v6.8.3
- https://github.com/qt/qtsvg/tree/v6.8.3
- https://www.qt.io/qt-licensing

The package uses CPython and, on Windows, pywin32 for shortcut creation. Packaging
uses PyInstaller, which permits bundling applications under its bootloader
exception. The packaging script retains available distribution metadata and
license files. Relevant projects:

- https://docs.python.org/3/license.html
- https://github.com/mhammond/pywin32
- https://pyinstaller.org/en/stable/license.html

Server software is fetched and built separately at the revisions recorded in
`hearthkeeper/data/realm.lock.json`. AzerothCore, Playerbots, and Individual
Progression retain their respective upstream licenses and authorship. No Blizzard
game assets are included in the desktop package. The Hearthkeeper icon is an
original vector asset created for this project.
