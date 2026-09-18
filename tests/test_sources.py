import gzip
from io import BytesIO
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from hearthkeeper.sources import (SourceError, fetch_snapshot, import_file, list_saved,
    load_catalog, offerings, read_saved, verify_saved)


class Response(BytesIO):
    def __init__(self, content, length=None):
        super().__init__(content)
        self.headers = {"Content-Length": str(len(content) if length is None else length)}

    def geturl(self):
        return "https://codeload.github.com/example/repo/legacy.tar.gz/" + "a" * 40


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.catalog = load_catalog()
        self.entry = next(row for row in self.catalog["offerings"] if row["id"] == "individual-progression")

    def test_catalog_preserves_source_hierarchy_and_client_families(self):
        self.assertEqual(len(self.catalog["providers"]), 7)
        self.assertTrue(all(row["provider"] == "chromiecraft" for row in offerings(self.catalog, provider="chromiecraft")))
        cata = offerings(self.catalog, era="Cataclysm")
        self.assertEqual({row["client"]["family"] for row in cata}, {"Original", "Classic re-release"})
        self.assertEqual({row["client"]["build"] for row in cata}, {15595, 60895})
        self.assertTrue(offerings(self.catalog, query="18414"))
        self.assertEqual(offerings(self.catalog, query="nonexistent offering"), [])

    def test_fetch_resolves_ref_once_then_downloads_immutable_commit(self):
        content = gzip.compress(b"fixture source bytes")
        with patch("hearthkeeper.sources._open", side_effect=[Response(json.dumps({"sha": "a" * 40}).encode()), Response(content)]) as opened:
            destination = fetch_snapshot(self.entry, self.root / "copies")
        self.assertTrue(opened.call_args_list[0].args[0].endswith("/commits/master"))
        self.assertTrue(opened.call_args_list[1].args[0].endswith("/tarball/" + "a" * 40))
        manifest = read_saved(destination)
        self.assertEqual(manifest["acquisition"]["commit"], "a" * 40)
        self.assertEqual((destination / "source.tar.gz").read_bytes(), content)
        self.assertIn("Bytes match", verify_saved(destination))
        self.assertNotIn("INCOMPLETE.txt", {path.name for path in destination.iterdir()})

    def test_short_transfer_does_not_become_completed_copy(self):
        with patch("hearthkeeper.sources._open", side_effect=[Response(b'{"sha":"' + b"a" * 40 + b'"}'), Response(b"short", length=200)]):
            with self.assertRaisesRegex(SourceError, "unexpected size"):
                fetch_snapshot(self.entry, self.root / "copies")
        self.assertEqual(list_saved(self.root / "copies"), ([], []))
        self.assertEqual(len(list((self.root / "copies").glob("*/INCOMPLETE.txt"))), 1)

    def test_wrong_download_format_and_oversize_are_not_completed(self):
        for content, limit, reason in [(b"<html>not a snapshot</html>", 1000, "gzip"), (b"too large", 2, "limit")]:
            with self.subTest(reason=reason):
                with patch("hearthkeeper.sources.MAX_SOURCE_BYTES", limit), patch("hearthkeeper.sources._open", side_effect=[Response(b'{"sha":"' + b"a" * 40 + b'"}'), Response(content)]):
                    with self.assertRaisesRegex(SourceError, reason):
                        fetch_snapshot(self.entry, self.root / "copies")
        self.assertEqual(list_saved(self.root / "copies"), ([], []))

    def test_client_page_cannot_be_mistaken_for_source_archive(self):
        entry = offerings(self.catalog, provider="chromiecraft")[0]
        with patch("hearthkeeper.sources._open", side_effect=AssertionError("Unexpected network")):
            with self.assertRaisesRegex(SourceError, "download page"):
                fetch_snapshot(entry, self.root / "copies")

    def test_import_preserves_bytes_and_never_replaces_an_existing_copy(self):
        source = self.root / "selected-client.zip"
        source.write_bytes(b"fictional client archive bytes")
        entry = offerings(self.catalog, provider="chromiecraft")[0]
        first = import_file(entry, source, self.root / "copies")
        second = import_file(entry, source, self.root / "copies")
        self.assertNotEqual(first, second)
        manifest = read_saved(first)
        self.assertEqual(manifest["acquisition"]["original_name"], source.name)
        self.assertIn("not been inspected", manifest["acquisition"]["coverage"])
        self.assertEqual((first / manifest["payload"]["filename"]).read_bytes(), source.read_bytes())
        self.assertIn("Bytes match", verify_saved(first))
        (first / manifest["payload"]["filename"]).write_bytes(b"damaged")
        with self.assertRaisesRegex(SourceError, "differs"):
            verify_saved(first)
        self.assertIn("Bytes match", verify_saved(second))

    def test_cancelled_and_partial_imports_do_not_appear_as_saved(self):
        source = self.root / "unfinished.crdownload"
        source.write_bytes(b"partial")
        with self.assertRaisesRegex(SourceError, "unfinished"):
            import_file(self.entry, source, self.root / "copies")
        source = self.root / "complete.zip"; source.write_bytes(b"complete")
        stop = threading.Event(); stop.set()
        with self.assertRaisesRegex(SourceError, "stopped"):
            import_file(self.entry, source, self.root / "copies", stop=stop)
        self.assertFalse((self.root / "copies").exists())

    def test_tampered_manifest_cannot_read_outside_saved_copy(self):
        source = self.root / "selected.zip"; source.write_bytes(b"content")
        destination = import_file(self.entry, source, self.root / "copies")
        manifest = read_saved(destination)
        manifest["payload"]["filename"] = "../../selected.zip"
        (destination / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(SourceError, "payload path"):
            verify_saved(destination)
        copies, errors = list_saved(self.root / "copies")
        self.assertEqual(copies, [])
        self.assertEqual(len(errors), 1)

    def test_catalog_rejects_executable_url_and_unknown_provider(self):
        for field, value in [("page_url", "file:///tmp/client.exe"), ("provider", "missing")]:
            with self.subTest(field=field):
                catalog = load_catalog()
                catalog["offerings"][0][field] = value
                path = self.root / "catalog.json"; path.write_text(json.dumps(catalog))
                with self.assertRaises(SourceError):
                    load_catalog(path)


if __name__ == "__main__":
    unittest.main()
