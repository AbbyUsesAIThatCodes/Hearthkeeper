"""Reproduce the Portal study using pinned wow.export and Qt's asset importer.

Game assets stay in ignored var/, outside the source repository. Preparation
needs Node 20+ and the desktop Python dependencies; the resulting app does not.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPORT_REVISION = "c2fd7bde36a712be78a5da896c995b84fbfa2545"


def restore_materials(directory):
    """Restore source blend flags and the two measured UV scroll periods."""
    metadata = json.loads((directory / "source-metadata.json").read_text())
    qml = directory / "qml" / "Portal.qml"
    source = qml.read_text()
    source = source.replace("id: node", "id: node\n    property real sceneSeconds: 0", 1)
    additions = []
    for unit in metadata["textureUnits"]:
        mesh = unit["skinSectionIndex"]
        material = metadata["materials"][unit["materialIndex"]]
        if material["blendingMode"] != 4:
            continue
        texture = metadata["textures"][metadata["textureCombos"][unit["textureComboIndex"]]]
        # Use the source lookup/track, rather than inventing a shimmer speed.
        transform_id = metadata["textureTransformsLookup"][unit["textureTransformComboIndex"]]
        period = None
        if transform_id != 65535:
            track = metadata["textureTransforms"][transform_id]["translation"]
            if track["values"][0][-1][0] != -1:
                raise ValueError("Review changed UV scroll track")
            period = track["timestamps"][0][-1] / 1000
        shift = f"-node.sceneSeconds / {period}" if period else "0"
        additions.append(f'''    CustomMaterial {{
        id: portalEffect{mesh}
        shadingMode: CustomMaterial.Unshaded
        sourceBlend: CustomMaterial.SrcAlpha
        destinationBlend: CustomMaterial.One
        cullMode: Material.NoCulling
        depthDrawMode: Material.NeverDepthDraw
        property real uShift: {shift}
        property real uGain: 1.0
        property TextureInput colorMap: TextureInput {{
            texture: Texture {{
                source: "maps/{texture}.png"
                tilingModeHorizontal: Texture.Repeat
                tilingModeVertical: Texture.Repeat
                generateMipmaps: true
                mipFilter: Texture.Linear
            }}
        }}
        vertexShader: "portal_layer.vert"
        fragmentShader: "portal_layer.frag"
    }}''')
        pattern = rf'(objectName: "portal_Geoset{mesh}".*?materials: \[)\s*\w+\s*(\])'
        source, count = re.subn(pattern, rf'\g<1> portalEffect{mesh} \g<2>', source, count=1, flags=re.S)
        if count != 1:
            raise ValueError(f"Qt import changed: missing Geoset {mesh}")
    source = source.replace("    // Nodes:", "\n".join(additions) + "\n    // Nodes:")
    qml.write_text(source, encoding="utf-8")
    shutil.copyfile(ROOT / "hearthkeeper/scene/portal_layer.frag", qml.parent / "portal_layer.frag")
    shutil.copyfile(ROOT / "hearthkeeper/scene/portal_layer.vert", qml.parent / "portal_layer.vert")
    return qml


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exporter", type=Path, help="Existing checkout of the pinned wow.export revision")
    parser.add_argument("--output", type=Path, default=ROOT / "var/portal-study")
    parser.add_argument("--adapt-only", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if not args.adapt_only:
        exporter = args.exporter or ROOT / "var/wow-export"
        if not (exporter / ".git").exists():
            subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", "https://github.com/Kruithne/wow.export.git", str(exporter)], check=True)
            subprocess.run(["git", "-C", str(exporter), "checkout", EXPORT_REVISION], check=True)
        revision = subprocess.check_output(["git", "-C", str(exporter), "rev-parse", "HEAD"], text=True).strip()
        if revision != EXPORT_REVISION:
            raise ValueError("Use wow.export revision " + EXPORT_REVISION)
        env = dict(os.environ, HEARTHKEEPER_PYTHON=sys.executable)
        subprocess.run(["node", str(ROOT / "tools/export_portal_study.cjs"), str(exporter.resolve()), str(output), "7476464"], env=env, check=True)
    import PySide6
    balsam = Path(PySide6.__file__).parent / ("balsam.exe" if os.name == "nt" else "balsam")
    subprocess.run([str(balsam), str(output / "portal.gltf"), "-o", str(output / "qml")],
                   env=dict(os.environ, QT_QPA_PLATFORM="offscreen"), check=True)
    qml = restore_materials(output)
    manifest = {
        "model": "12ph_misc_tbcdarkportal01", "file_data_id": 7476464,
        "source": "https://wow.zamimg.com/modelviewer/live/m2/7476464.m2",
        "exporter_revision": EXPORT_REVISION,
        "source_sha256": hashlib.sha256((output / "7476464.m2").read_bytes()).hexdigest(),
        "entrypoint": "qml/Portal.qml", "vertices": 16545, "submeshes": 23,
        "restored": ["additive effect materials", "two UV scroll tracks: 3333 and 6667 ms"],
        "limitations": ["No M2 particle emitters, ribbons, or texture-weight animation", "No surrounding world terrain", "No guarantee of exact in-game effect parity"],
        "files": {p.relative_to(output).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sorted(qml.parent.rglob("*")) if p.is_file()},
    }
    (output / "study.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Prepared", output / "study.json")


if __name__ == "__main__":
    main()
