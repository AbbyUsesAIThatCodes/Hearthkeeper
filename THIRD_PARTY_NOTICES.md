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
game assets are included in the regular desktop package. The Hearthkeeper icon is an
original vector asset created for this project.

## Optional Dark Portal study

The separate **Hearthkeeper-Portal-Study** experimental build uses Qt Quick 3D
under GPL v3. Its source and complete build recipe are in the same Hearthkeeper
repository; the main desktop build does not depend on this experimental entry
point. Additional upstream corresponding source:

- https://github.com/qt/qtquick3d/tree/v6.8.3
- https://github.com/qt/qtdeclarative/tree/v6.8.3
- https://github.com/qt/qtshadertools/tree/v6.8.3
- https://github.com/qt/qtquicktimeline/tree/v6.8.3

The prepared housing Dark Portal scene in this study uses Blizzard Entertainment
geometry and textures from the public WoW model viewer. They retain their
original ownership and are not covered by Hearthkeeper code licensing. The
source repository stores the reproducible preparation adapter, provenance,
and screenshots; downloaded game files remain in ignored `var/`.

Preparation uses **wow.export** by Kruithne, Marlamin, and contributors, MIT
licensed, at revision `c2fd7bde36a712be78a5da896c995b84fbfa2545`:
https://github.com/Kruithne/wow.export/tree/c2fd7bde36a712be78a5da896c995b84fbfa2545
The app does not bundle or run the exporter. Details and known rendering
limitations are recorded in `docs/PORTAL_SCENE_STUDY.md` and the pack manifest.
