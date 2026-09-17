"""The Home atlas is a local, validated asset; geometry never crops the scene."""
import ast
import base64
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile
import unittest

from hearthkeeper.material_assets import PARTS, REGIONS, fit_scene, read_material_atlas

ASSETS = Path(__file__).resolve().parents[1] / 'hearthkeeper' / 'assets'


class MaterialAssetTests(unittest.TestCase):
    def test_exact_packaged_atlas(self):
        manifest = json.loads((ASSETS / 'war-table.json').read_text(encoding="utf-8"))
        data = read_material_atlas()
        self.assertEqual(hashlib.sha256(data).hexdigest(), manifest['sha256'])
        self.assertEqual(struct.unpack('<I', data[4:8])[0] + 8, len(data))
        self.assertEqual(data[8:12], b'WEBP')
        self.assertGreater(len(data), 40000)

    def test_regions_are_inside_the_atlas(self):
        for name, (x, y, width, height) in REGIONS.items():
            with self.subTest(region=name):
                self.assertGreater(width, 0)
                self.assertGreater(height, 0)
                self.assertGreaterEqual(x, 0)
                self.assertGreaterEqual(y, 0)
                self.assertLessEqual(x + width, 1024)
                self.assertLessEqual(y + height, 544)
        self.assertEqual(REGIONS['panorama'], (0, 0, 877, 258))

    def test_complete_scene_fits_wide_and_tall_viewports(self):
        for width, height in ((1200, 350), (580, 200), (1200, 100), (300, 600)):
            x, y, w, h = fit_scene(877, 258, width, height)
            self.assertAlmostEqual(w/h, 877/258)
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x+w, width+1e-9)
            self.assertLessEqual(y+h, height+1e-9)
            self.assertTrue(abs(w-width)<1e-9 or abs(h-height)<1e-9)

    def test_invalid_dimensions_fail_closed(self):
        for size in ((0,258,800,400), (877,0,800,400), (877,258,0,400), (877,258,800,-1)):
            self.assertEqual(fit_scene(*size), (0,0,0,0))

    def test_missing_corrupt_and_redirected_parts_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('war-table.json', *PARTS):
                shutil.copyfile(ASSETS / name, root / name)
            self.assertEqual(read_material_atlas(root), read_material_atlas())
            last = root / PARTS[-1]
            last.unlink()
            with self.assertRaises(OSError):
                read_material_atlas(root)
            last.write_text('not base64!', encoding='ascii')
            with self.assertRaises(ValueError):
                read_material_atlas(root)
            shutil.copyfile(ASSETS / PARTS[-1], last)
            data = bytearray(read_material_atlas(root)); data[-20] ^= 1
            text = base64.b64encode(data).decode('ascii')
            for index, name in enumerate(PARTS):
                (root/name).write_text(text[index*16000:(index+1)*16000], encoding='ascii')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                read_material_atlas(root)
            manifest = json.loads((root/'war-table.json').read_text(encoding="utf-8"))
            manifest['parts'] = ['../../outside']
            (root/'war-table.json').write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                read_material_atlas(root)

    def test_provenance_and_native_captions(self):
        manifest = json.loads((ASSETS/'war-table.json').read_text(encoding="utf-8"))
        self.assertEqual(manifest['regions']['panorama']['source_crop'], [640,43,1517,301])
        self.assertIn('not a running application', manifest['notice'])
        self.assertEqual(len(manifest['source_sha256']), 64)
        code = (ASSETS.parent/'home_art.py').read_text(encoding="utf-8")
        self.assertIn('The Burning Crusade  ·  Some gates should never close.', code)
        self.assertNotIn('QLinearGradient', code)
        for filename in ('material_assets.py', 'material_widgets.py', 'home_art.py'):
            tree = ast.parse((ASSETS.parent/filename).read_text(encoding="utf-8"))
            modules = [n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
            modules += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
            self.assertFalse(any(m.startswith(('subprocess', 'socket', 'urllib', 'requests')) for m in modules))


if __name__ == '__main__':
    unittest.main()
