import base64
import copy
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
import warnings
from unittest.mock import patch
import zipfile

from hearthkeeper.archive import (ArchiveError, compare_archives, json_bytes, parse_json,
                                 read_archive, write_archive)
from hearthkeeper.cli import main
from hearthkeeper.database import capture, mysql_reader, sqlite_reader
from hearthkeeper.demo import create_fixture
from hearthkeeper.model import normalized
from hearthkeeper.realm import read_lock
from hearthkeeper.viewer import render_archive


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.database = create_fixture(self.directory / "fixture.sqlite")

    def snapshot(self):
        with sqlite_reader(self.database) as reader:
            return capture(reader, 7, "test-realm", demo=True)

    def archive(self, name="character.hearth", snapshot=None):
        return write_archive(self.directory / name, snapshot or self.snapshot())

    def test_relational_capture_includes_ownerless_mail_but_excludes_other_character(self):
        snapshot = self.snapshot()
        rows = snapshot["tables"]
        self.assertEqual({row["guid"] for row in rows["characters.item_instance"]["rows"]}, {101,102,103,104,105,106})
        self.assertEqual([row["id"] for row in rows["characters.mail"]["rows"]], [401])
        self.assertEqual([row["guid"] for row in rows["characters.pet_spell"]["rows"]], [301])
        self.assertNotIn(b"PRIVATE_FIXTURE_SENTINEL", json_bytes(snapshot))
        self.assertNotIn(b"must not be exported", json_bytes(snapshot))
        self.assertNotIn(b"OtherCharacter", json_bytes(snapshot))

    def test_capture_cannot_write_and_does_not_modify_source(self):
        original = self.database.read_bytes()
        with sqlite_reader(self.database) as reader:
            with self.assertRaises(sqlite3.OperationalError):
                reader.connection.execute("UPDATE characters SET money = 0")
            capture(reader, 7, "test-realm")
        self.assertEqual(self.database.read_bytes(), original)

    def test_online_character_and_wrong_guid_are_rejected(self):
        with sqlite_reader(self.database) as reader:
            with self.assertRaises(ArchiveError):
                capture(reader, 9, "test-realm")
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE characters SET online = 1 WHERE guid = 7")
        with self.assertRaisesRegex(ArchiveError, "Log this character out"):
            self.snapshot()

    def test_module_data_unknown_columns_and_binary_values_survive_roundtrip(self):
        with sqlite3.connect(self.database) as connection:
            connection.execute("UPDATE character_settings SET data = ? WHERE guid = 7 AND source = ?",
                               (b"\x00\xff\x80module-state", "hearthkeeper.demo.progression"))
        snapshot = self.snapshot()
        _, restored = read_archive(self.archive(snapshot=snapshot))
        self.assertEqual(json_bytes(snapshot), json_bytes(restored))
        row = next(row for row in restored["tables"]["characters.character_settings"]["rows"]
                   if row["source"] == "hearthkeeper.demo.progression")
        self.assertEqual(base64.b64decode(row["data"]["value"]), b"\x00\xff\x80module-state")
        self.assertIn("custom_story_note", restored["tables"]["characters.characters"]["rows"][0])

    def test_missing_references_and_unsupported_tables_are_visible(self):
        with sqlite3.connect(self.database) as connection:
            connection.execute("DELETE FROM item_instance WHERE guid = 101")
            connection.execute("DELETE FROM item_template WHERE entry = 900003")
        snapshot = self.snapshot()
        self.assertTrue(any("item instances missing" in warning for warning in snapshot["warnings"]))
        self.assertTrue(any("template IDs unresolved" in warning for warning in snapshot["warnings"]))
        self.assertIn("characters.custom_town_citizenship", snapshot["coverage"]["unhandled_tables"])
        self.assertIn("characters.character_talent", snapshot["coverage"]["missing_tables"])
        self.assertTrue(any(item["guid"] == 101 for item in normalized(snapshot)["items"]))

    def test_incompatible_schema_fails_instead_of_silently_dropping_records(self):
        with sqlite3.connect(self.database) as connection:
            connection.execute("ALTER TABLE character_settings RENAME COLUMN guid TO owner")
        with self.assertRaisesRegex(ArchiveError, "Unsupported schema"):
            self.snapshot()

    def test_existing_archive_and_html_are_never_overwritten(self):
        path = self.archive()
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            self.archive()
        self.assertEqual(path.read_bytes(), original)
        output = self.directory / "view.html"
        output.write_text("keep this", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            render_archive(path, output)
        self.assertEqual(output.read_text(), "keep this")

    def test_checksum_detects_changed_payload(self):
        source = self.archive()
        with zipfile.ZipFile(source) as container:
            manifest = container.read("manifest.json")
            payload = container.read("snapshot.json").replace(b"Brindle", b"Changed")
        broken = self.directory / "broken.hearth"
        with zipfile.ZipFile(broken, "w") as container:
            container.writestr("manifest.json", manifest)
            container.writestr("snapshot.json", payload)
        with self.assertRaisesRegex(ArchiveError, "checksum"):
            read_archive(broken)

    def test_unknown_version_duplicate_members_and_traversal_are_rejected(self):
        archive = self.archive()
        with zipfile.ZipFile(archive) as container:
            original = {name: container.read(name) for name in container.namelist()}
        for extra in ("../escaped.txt", "snapshot.json"):
            path = self.directory / ("duplicate.hearth" if extra == "snapshot.json" else "traversal.hearth")
            with zipfile.ZipFile(path, "w") as container:
                for name, data in original.items():
                    container.writestr(name, data)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    container.writestr(extra, b"bad")
            with self.assertRaises(ArchiveError):
                read_archive(path)
        original["manifest.json"] = original["manifest.json"].replace(b"character/1", b"character/9")
        path = self.directory / "future.hearth"
        with zipfile.ZipFile(path, "w") as container:
            for name, data in original.items():
                container.writestr(name, data)
        with self.assertRaisesRegex(ArchiveError, "Unsupported"):
            read_archive(path)
        self.assertFalse((self.directory.parent / "escaped.txt").exists())

    def test_zip_expansion_and_duplicate_json_keys_are_rejected(self):
        archive = self.archive()
        with patch("hearthkeeper.archive.MAX_PAYLOAD", 20):
            with self.assertRaises(ArchiveError):
                read_archive(archive)
        with self.assertRaises(ArchiveError):
            parse_json(b'{"source": 1, "source": 2}')
        with self.assertRaises(ArchiveError):
            parse_json(b'{"number": NaN}')

    def test_diff_finds_changes_without_confusing_characters(self):
        snapshot = self.snapshot()
        first = self.archive(snapshot=snapshot)
        changed = copy.deepcopy(snapshot)
        changed["tables"]["characters.characters"]["rows"][0]["level"] = 25
        second = self.archive("later.hearth", changed)
        self.assertEqual(compare_archives(first, second)["tables"], [
            {"table": "characters.characters", "before_rows": 1, "after_rows": 1, "status": "changed"}])
        changed["source"]["realm"] = "different-realm"
        third = self.archive("different.hearth", changed)
        with self.assertRaisesRegex(ArchiveError, "same source realm"):
            compare_archives(first, third)

    def test_table_row_order_does_not_create_a_false_diff(self):
        first = self.archive()
        second = self.archive("same.hearth")
        self.assertEqual(compare_archives(first, second)["tables"], [])

    def test_viewer_escapes_archived_markup_and_contains_no_remote_assets(self):
        snapshot = self.snapshot()
        snapshot["tables"]["characters.characters"]["rows"][0]["name"] = '<img src=x onerror="alert(1)">'
        snapshot["tables"]["world.item_template"]["rows"][0]["name"] = '</script><script>alert(1)</script>'
        path = render_archive(self.archive(snapshot=snapshot), self.directory / "view.html")
        document = path.read_text(encoding="utf-8")
        self.assertNotIn('<img src=x', document)
        self.assertNotIn('<script>alert(1)</script>', document)
        self.assertIn('&lt;img src=x', document)
        self.assertIn("default-src 'none'", document)
        self.assertNotIn('src="http', document)
        self.assertNotIn('href="http', document)

    def test_remote_mysql_requires_verified_tls_before_connecting(self):
        with self.assertRaisesRegex(ArchiveError, "tls-ca"):
            with mysql_reader(host="example.invalid", port=3306, user="reader", password="never-used",
                              characters="acore_characters", world="acore_world"):
                self.fail("Must not connect")

    def test_source_pins_are_exact_and_labelled_unverified(self):
        lock = read_lock()
        self.assertIn("not-build-or-gameplay-validated", lock["status"])
        self.assertEqual(lock["client"]["build"], 12340)
        self.assertEqual({source["id"] for source in lock["sources"]}, {"core", "playerbots", "progression", "wowee"})
        for source in lock["sources"]:
            self.assertRegex(source["commit"], r"^[0-9a-f]{40}$")

    def test_cli_demo_builds_an_offline_archive_without_network(self):
        with patch("socket.socket", side_effect=AssertionError("Network not allowed")), patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(main(["demo", "--directory", str(self.directory / "demo")]), 0)
        archives = list((self.directory / "demo").glob("*/*.hearth"))
        self.assertEqual(len(archives), 1)
        self.assertTrue(read_archive(archives[0])[1]["source"]["fictional_demo"])


if __name__ == "__main__":
    unittest.main()
