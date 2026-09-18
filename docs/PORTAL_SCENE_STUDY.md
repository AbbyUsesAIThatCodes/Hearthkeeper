# Dark Portal scene study

This is an optional, native 3D feasibility prototype layered over the Living
Hearth (a9). It does not replace the regular desktop Home or change realm
compatibility: managed realms still use **Wrath 3.3.5a / build 12340**.

## Try the Windows study

Download **Hearthkeeper-Dark-Portal-Study-Windows** from the successful
**Dark Portal scene study** workflow linked in the PR. Extract the entire ZIP to
a new folder and run **Hearthkeeper-Portal-Study.exe**, keeping `_internal`
beside it. This separate build includes the prepared scene and needs no Python,
Node, WoWExport, or Blender installed on your machine.

- **F11** switches fullscreen/windowed. **Escape** leaves fullscreen; a second
  Escape returns to ordinary desktop Home.
- Compare **Portal approach** and **Fortress overlook** in the camera selector.
  These are fixed camera positions; there is no moving camera to read against.
- **Scene motion** pauses the source texture scrolling and is remembered.
- **Open realm** uses an existing folder containing `realm.json`. Opening the
  prototype itself never starts services, downloads a client, or launches WoW.
- **Check services** explicitly reads database, login, and world status. The
  time of the check is shown. Unknown is never displayed as healthy.
- **Play** uses the existing validated asynchronous workflow. Once the game
  process is running, the scene minimizes and pauses. It returns when the
  process exits. Preparation or launch failure keeps Home available.
- Navigation opens the existing Characters, Archives, Backups, Sources, and
  Workshop pages. Their Home button returns to the scene. **Desktop Home**
  explicitly opens the regular Home; Realm tools also has **Return to 3D Home**.

Please judge information visibility, the camera, and the feeling of entering
WoW. The quiet background and simple panels are study scaffolding. This is not
the finished environmental composition or interface styling.

## What the investigation established

The actual housing model is
`world/expansion11/doodads/playerhousing/12ph_misc_tbcdarkportal01.m2`,
FileDataID **7476464**. This scene uses its geometry and textures, including both
statues, steps, arch, and portal layers: 16,545 source vertices and 23 submeshes.

The preparation script uses wow.export revision
`c2fd7bde36a712be78a5da896c995b84fbfa2545` to read the M2/skin and export glTF.
Its headless adapter supplies publicly served model-viewer files in place of
the normal CASC source and converts the viewer's WebP textures to PNG. It does
not patch the upstream exporter. Qt 6.8.3 Balsam then converts glTF into native
scene resources. Preparation is separate from app startup.

**A plain glTF import loses essential effects.** This model's additive materials
arrived as opaque surfaces, and its texture motion did not appear in the Qt
import. A small material adapter restores the additive layers and the two
source UV scroll periods (3,333 and 6,667 ms). The result is a real animated 3D
Portal, with ordinary, accessible Qt controls over it. Play is projected from
a 3D point in the Portal opening so it follows either camera.

Remaining fidelity gaps: particle emitters, ribbons, texture-weight animation,
and exact in-game blend/color behavior have not been reproduced. No surrounding
Blasted Lands/Hellfire terrain, fortress, sky, ambient audio, or cinematic
transition is included. “Fortress overlook” names a camera study, not an
imported fortress. The original world Portal is identified in the listfile but
has not yet received the same export/render comparison. The housing model is
the first proven candidate, not a final asset selection.

## Reproduce from source

Use Python 3.11–3.13, Git, and Node 20+. From the repository root, in the desktop
virtual environment:

```sh
python -m pip install -e ".[desktop]"
python tools/prepare_portal_study.py
python -m hearthkeeper.portal_scene --windowed
```

The preparation step downloads the pinned exporter and public model-viewer
assets to ignored `var/`. The repository contains the adapter and source
recipe, not the model or texture files. `study.json` records the original model
hash, exporter revision, limitations, and hashes of every prepared scene file.
The launcher validates those files before loading the pack. A missing or
damaged pack falls back to ordinary Home. Hashes detect accidental damage;
they are not signatures or a sandbox for untrusted QML. Only use packs you
prepared or obtained from a trusted source.

```sh
python -m hearthkeeper.portal_scene --smoke-test var/portal-test
python -m unittest discover -s tests -q
```

The scene acceptance test renders the actual asset, checks visible pixel motion
and reduced-motion freezing, verifies both cameras and logical window sizes
through 980×640, exercises real native controls with fictional service/client
fixtures, and checks successful/failed Play handoff and return. It does not
launch a real WoW client or Docker realm. CI also tests the separate packaged
Windows executable at 125% Qt scaling. Results include screenshots, actual DPR,
first-frame timing, observed frame intervals, and Qt diagnostics.

Local/CI rendering performance does not predict a specific gaming GPU. Final
GPU use, memory, driver behavior, and the actual Windows-to-WoW transition must
be measured on the target machine before promoting this to the main Home.

## Sources and distribution

- [wow.export source](https://github.com/Kruithne/wow.export/tree/c2fd7bde36a712be78a5da896c995b84fbfa2545)
- [WoW community listfile](https://github.com/wowdev/wow-listfile)
- [Public model-viewer source](https://wow.zamimg.com/modelviewer/live/m2/7476464.m2)
- [Qt Quick 3D](https://doc.qt.io/qt-6.8/qtquick3d-index.html)
- [Qt Balsam asset import](https://doc.qt.io/qt-6.8/qtquick3d-tool-balsam.html)
- [Qt custom materials](https://doc.qt.io/qt-6.8/qml-qtquick3d-custommaterial.html)

Warcraft model/texture authorship remains Blizzard Entertainment's; the
experimental prepared scene is not an original Hearthkeeper asset. wow.export
is MIT licensed. Qt Quick 3D is GPLv3/commercial, unlike the LGPL Qt Widgets
modules in the ordinary build. This prototype uses its GPLv3 option; source,
build recipe, upstream source links, and license texts accompany the study.
See `THIRD_PARTY_NOTICES.md`. The release build remains separate.
