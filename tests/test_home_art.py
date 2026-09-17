"""Home asset/provenance contracts, with no optional GUI dependency."""
import ast
import hashlib
import json
from pathlib import Path
import struct
import tomllib
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "hearthkeeper/assets"


class HomeArtTests(unittest.TestCase):
    def test_exact_raster_bytes(self):
        manifest = json.loads((ASSETS / "home-art.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["asset"], "home-portal.webp")
        from hearthkeeper.art_assets import read_home_art
        data = read_home_art()
        self.assertEqual(hashlib.sha256(data).hexdigest(), manifest["sha256"])
        self.assertEqual(data[:4], b"RIFF")
        self.assertEqual(data[8:12], b"WEBP")
        self.assertEqual(struct.unpack("<I", data[4:8])[0] + 8, len(data))
        self.assertGreater(len(data), 10000)

    def test_provenance_distinguishes_concept_from_state(self):
        manifest = json.loads((ASSETS / "home-art.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["crop_box"], [602, 49, 1525, 375])
        self.assertEqual(manifest["raster_size"], [736, 260])
        self.assertEqual(len(manifest["source_sha256"]), 64)
        self.assertIn("not a running application", manifest["notice"])
        self.assertIn("fictional", manifest["notice"])

    def test_frame_is_self_contained(self):
        text = (ASSETS / "home-frame.svg").read_text(encoding="utf-8")
        root = ET.fromstring(text)
        self.assertEqual(root.attrib["viewBox"], "0 0 96 96")
        self.assertNotIn("href=", text)
        self.assertNotIn("<script", text)
        self.assertNotIn("<text", text)

    def test_art_adapter_imports_no_realm_or_network_modules(self):
        # A structural boundary, supplemented by the real native acceptance suite.
        tree = ast.parse((ROOT / "hearthkeeper/home_art.py").read_text(encoding="utf-8"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        for forbidden in ("server", "client", "subprocess", "requests", "urllib", "socket"):
            self.assertFalse(any(forbidden in module for module in imports))
        self.assertFalse(any(isinstance(node, ast.Import) for node in ast.walk(tree)))

    def test_missing_corrupt_and_unexpected_parts_are_rejected(self):
        from hearthkeeper.art_assets import read_home_art, PARTS
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ("home-art.json", *PARTS):
                shutil.copyfile(ASSETS / name, root / name)
            self.assertEqual(read_home_art(root), read_home_art())
            part = root / PARTS[-1]
            part.unlink()
            with self.assertRaises(OSError):
                read_home_art(root)
            part.write_text("invalid bytes!", encoding="ascii")
            with self.assertRaises(ValueError):
                read_home_art(root)
            manifest = json.loads((root / "home-art.json").read_text())
            manifest["parts"] = ["../outside"]
            (root / "home-art.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "Unexpected Home artwork parts"):
                read_home_art(root)

    def test_version_and_asset_packaging(self):
        from hearthkeeper import __version__, CODENAME
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(__version__, "0.1.0a8")
        self.assertEqual(project["project"]["version"], __version__)
        self.assertEqual(CODENAME, "At the War Table")
        self.assertIn("assets/*", project["tool"]["setuptools"]["package-data"]["hearthkeeper"])


if __name__ == "__main__":
    unittest.main()
