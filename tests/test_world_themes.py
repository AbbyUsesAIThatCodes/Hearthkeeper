"""Theme contracts stay testable without the optional Qt installation."""
import re
import unittest
import xml.etree.ElementTree as ET

from hearthkeeper.world_themes import REALM_NOTICE, SCENES, THEMES, scenic_svg


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in channels]
    return sum(c * w for c, w in zip(channels, (.2126, .7152, .0722)))


class WorldThemeTests(unittest.TestCase):
    def test_exact_approved_mapping(self):
        self.assertEqual([(t.page, t.expansion) for t in THEMES], [
            ("Home", "The Burning Crusade"), ("Characters", "Legion"),
            ("Archives", "Mists of Pandaria"), ("Backups", "Wrath of the Lich King"),
            ("Sources", "Warlords of Draenor"), ("Workshop", "Cataclysm")])

    def test_unique_scenes_and_keys(self):
        self.assertEqual(len({t.key for t in THEMES}), 6)
        self.assertEqual(set(SCENES), {t.key for t in THEMES})
        self.assertEqual(len({SCENES[t.key] for t in THEMES}), 6)

    def test_static_self_contained_svg(self):
        for theme in THEMES:
            with self.subTest(theme=theme.key):
                svg = scenic_svg(theme.key)
                root = ET.fromstring(svg)
                self.assertEqual(root.attrib["viewBox"], "0 0 1200 360")
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                ids = {node.attrib["id"] for node in root.iter() if "id" in node.attrib}
                self.assertTrue(set(re.findall(r"url\(#([^)]+)\)", svg)) <= ids)
                self.assertNotIn("href=", svg)
                self.assertNotIn("<script", svg)
                self.assertNotIn("<animate", svg)
                self.assertEqual(svg, scenic_svg(theme.key))

    def test_unknown_theme_fails_explicitly(self):
        with self.assertRaises(KeyError):
            scenic_svg("unknown")

    def test_text_palette_contrast(self):
        # Tests solid native-label surfaces, not an accessibility certification of the app.
        for background in ("#101920", "#283338"):
            for foreground in [t.accent for t in THEMES] + ["#f7edda", "#d0dcda"]:
                with self.subTest(background=background, foreground=foreground):
                    ratio = (luminance(foreground) + .05) / (luminance(background) + .05)
                    self.assertGreaterEqual(ratio, 4.5)

    def test_actual_realm_is_not_decoration(self):
        self.assertIn("Wrath 3.3.5a / build 12340", REALM_NOTICE)
        self.assertIn("does not switch realms", REALM_NOTICE)
        self.assertIn("still to come", THEMES[-1].subtitle)


if __name__ == "__main__":
    unittest.main()
