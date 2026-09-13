"""Offline native-widget acceptance checks, also run inside the packaged executable."""
import json
import os
from pathlib import Path
import sys
import time
import webbrowser
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from .archive import write_archive
from .database import capture, sqlite_reader
from .demo import create_fixture
from .desktop import MainWindow


def run(application, directory):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    database = create_fixture(directory / "fictional.sqlite")
    with sqlite_reader(database) as reader:
        snapshot = capture(reader, 7, "copperleaf-demo", demo=True)
    archive = write_archive(directory / "brindle.hearth", snapshot)
    from .server.manager import PACKAGE
    if getattr(sys, "frozen", False):
        for relative in ("__init__.py", "archive.py", "database.py", "realm.py", "data/realm.lock.json",
                         "server/Dockerfile", "server/fetch_sources.py", "server/manager.py",
                         "server/container_entry.py", "server/accounts.py", "server/__init__.py"):
            assert (PACKAGE / relative).is_file(), "Missing installer resource: " + relative
    # Launching the desktop or reading its archive must never invoke Docker or a browser.
    with patch("subprocess.Popen", side_effect=AssertionError("Unexpected process launch")), patch.object(webbrowser, "open", side_effect=AssertionError("Unexpected browser")):
        window = MainWindow(remember=False)
        window.show(); application.processEvents(); QTest.qWait(50)
        assert window.pages.count() == 6
        brand = window.findChild(type(window.card_values[0]), "brand")
        assert brand.fontMetrics().horizontalAdvance(brand.text()) <= brand.width(), "Brand is clipped"
        window.grab().save(str(directory / "desktop-realm.png"))
        window.show_archive(archive); application.processEvents()
        assert window.pages.currentIndex() == 2 and window.nav_buttons[2].isChecked()
        panel = window.archive_panel
        assert "Brindle" in panel.heading.text()
        panel.tabs.setCurrentIndex(1)
        inventory = panel.tables[0]
        assert inventory.rowCount() == 6
        QTest.mouseClick(panel.search, Qt.MouseButton.LeftButton)
        QTest.keyClicks(panel.search, "Lantern")
        assert sum(not inventory.isRowHidden(row) for row in range(inventory.rowCount())) == 1
        panel.search.clear()
        assert all(not inventory.isRowHidden(row) for row in range(inventory.rowCount()))
        panel.tabs.setCurrentIndex(4)
        assert "hearthkeeper.demo.progression" in panel.tabs.widget(4).toPlainText()
        panel.tabs.setCurrentIndex(5)
        assert "custom_town_citizenship" in panel.tabs.widget(5).toPlainText()
        panel.tabs.setCurrentIndex(1); application.processEvents(); QTest.qWait(50)
        window.grab().save(str(directory / "desktop-archive.png"))
        window.resize(980, 700); application.processEvents(); QTest.qWait(50)
        window.grab().save(str(directory / "desktop-small.png"))
        # Sources are browsable offline; choosing a provider never fetches or installs content.
        window.navigate(4)
        window.source_provider.setCurrentIndex(window.source_provider.findData("chromiecraft"))
        application.processEvents()
        assert window.source_tree.topLevelItemCount() == 1
        assert window.source_tree.topLevelItem(0).childCount() == 2
        assert not window.source_fetch.isEnabled()
        assert window.source_open.isEnabled() and window.source_import.isEnabled()
        window.source_provider.setCurrentIndex(window.source_provider.findData("skyfire"))
        assert window.source_fetch.isEnabled()
        assert "18414" in window.source_detail_text
        window.source_search.setText("impossible-match")
        assert window.source_tree.topLevelItemCount() == 0
        assert not window.source_fetch.isEnabled() and not window.source_import.isEnabled()
        window.source_search.clear()
        application.processEvents(); QTest.qWait(50)
        window.grab().save(str(directory / "desktop-sources-small.png"))
        window.resize(1240, 880)
        window.source_provider.setCurrentIndex(0)
        application.processEvents(); QTest.qWait(50)
        window.grab().save(str(directory / "desktop-sources.png"))
        from .sources import import_file, verify_saved
        fixture_file = directory / "fictional-download.zip"
        fixture_file.write_bytes(b"Fictional bytes, not game data")
        window.source_root = directory / "source-copies"
        saved = import_file(window.selected_source(), fixture_file, window.source_root)
        window.source_saved_complete(saved)
        assert window.source_saved.rowCount() == 1 and window.selected_source_copy() == saved
        assert "Bytes match" in verify_saved(saved)
        application.processEvents(); QTest.qWait(50)
        window.grab().save(str(directory / "desktop-saved-sources.png"))
        window.navigate(2)
        snapshot["tables"]["characters.characters"]["rows"][0]["name"] = "<img src=x onerror=alert(1)>"
        malicious = write_archive(directory / "escaped.hearth", snapshot)
        panel.load(malicious)
        assert panel.heading.textFormat() == Qt.TextFormat.PlainText
        assert "<img" in panel.heading.text(), "Archived text must be displayed literally"
    complete = []
    window.run_job("Worker responsiveness check", lambda runner: "finished", complete.append)
    deadline = time.monotonic() + 10
    while window.worker and time.monotonic() < deadline:
        application.processEvents(); QTest.qWait(5)
    assert complete == ["finished"] and window.worker is None
    assert not any("QtWebEngine" in name for name in sys.modules)
    if os.name == "nt":
        from .shortcuts import create_shortcut
        import win32com.client
        desktop = directory / "test-desktop"; desktop.mkdir()
        shortcut = create_shortcut(desktop_path=desktop, data_path=directory / "test-appdata")
        assert shortcut.is_file()
        link = win32com.client.Dispatch("WScript.Shell").CreateShortcut(str(shortcut))
        assert Path(link.TargetPath).is_file()
        assert Path(link.IconLocation.split(",")[0]).is_file()
        try:
            create_shortcut(desktop_path=desktop, data_path=directory / "test-appdata")
        except FileExistsError:
            pass
        else:
            raise AssertionError("An existing shortcut was replaced")
    window.close(); application.processEvents()
    (directory / "result.json").write_text(json.dumps({"passed": True, "native_widgets": True,
        "checks": ["offline startup", "archive search", "module and coverage views", "literal archived text", "worker completion", "desktop sizes", "source filtering", "acquisition availability", "saved source copy"]}))
