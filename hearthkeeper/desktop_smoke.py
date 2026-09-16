"""Offline native-widget acceptance checks, also run inside the packaged executable."""
import json
import os
from pathlib import Path
import sys
import time
import webbrowser
from unittest.mock import Mock, patch

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
        exercise_home(application, window, directory)
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
        "checks": ["offline startup", "archive search", "module and coverage views", "literal archived text", "worker completion", "desktop sizes", "source filtering", "acquisition availability", "saved source copy", "client selection", "realmlist confirmation and backup", "Play success and failure", "duplicate Play prevention", "home minimum size"]}))


def exercise_home(application, window, directory):
    """Exercise real widgets/workers against a clearly fictional realm; never start Docker/WoW."""
    from .client import EXPECTED_VERSION
    from .server.manager import create_realm, ManagedRealm
    from .desktop import QFileDialog, QMessageBox
    game = directory / "fictional-client"
    (game / "Data" / "enUS").mkdir(parents=True)
    for relative in ("Wow.exe", "Data/lichking.MPQ", "Data/patch-3.MPQ"):
        (game / relative).write_bytes(b"Fictional test data only")
    connection = game / "Data" / "enUS" / "realmlist.wtf"
    original = b"set realmlist example.invalid\r\n"
    connection.write_bytes(original)
    realm = create_realm(directory / "fictional-realm", name="First Campfire - demo",
                         data_path=str(game), data_kind="client", docker_context="default")
    realm.config["phase"] = "installed"; realm.save()
    ready = [{"Service": name, "State": "running", "Health": "healthy"} for name in ("auth", "world", "database")]
    def finish_worker():
        deadline = time.monotonic() + 10
        while window.worker and time.monotonic() < deadline:
            application.processEvents(); QTest.qWait(5)
        assert window.worker is None, "Play worker did not complete"
    with patch("hearthkeeper.client.windows_file_version", return_value=EXPECTED_VERSION):
        assert not window.play_button.isEnabled()
        window.select_realm(realm.path)
        assert not window.play_button.isEnabled()
        with patch.object(QFileDialog, "getOpenFileName", return_value=(str(game / "Wow.exe"), "")):
            window.choose_client()
        assert window.client is not None and not window.play_button.isEnabled()
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No):
            window.connect_client()
        assert connection.read_bytes() == original
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
            window.connect_client()
        assert list(connection.parent.glob("*.bak"))[0].read_bytes() == original
        assert window.play_button.isEnabled()
        window.resize(1240, 880); application.processEvents(); QTest.qWait(30)
        window.grab().save(str(directory / "desktop-home-ready.png"))
        window.resize(980, 700); application.processEvents(); QTest.qWait(30)
        scroll = window.pages.widget(0)
        assert scroll.horizontalScrollBar().maximum() == 0, "Home overflows horizontally"
        scroll.ensureWidgetVisible(window.play_button); application.processEvents()
        window.grab().save(str(directory / "desktop-home-small.png"))
        process = Mock(); process.poll.return_value = None
        with patch.object(ManagedRealm, "status", return_value=ready), patch.object(ManagedRealm, "start") as start, patch("hearthkeeper.desktop.launch_client", return_value=process) as launch:
            QTest.mouseClick(window.play_button, Qt.MouseButton.LeftButton)
            window.play()  # A second request during startup must be ignored.
            finish_worker()
            launch.assert_called_once(); start.assert_not_called()
            assert not window.play_button.isEnabled() and window.play_button.text() == "GAME RUNNING"
            window.play(); launch.assert_called_once()
        process.poll.return_value = 0; window.game_tick()
        assert window.play_button.isEnabled()
        with patch.object(ManagedRealm, "status", side_effect=RuntimeError("Fictional Docker failure")), patch("hearthkeeper.desktop.launch_client") as launch, patch.object(QMessageBox, "warning") as warning:
            window.play(); finish_worker()
            launch.assert_not_called(); warning.assert_called_once()
            assert "Fictional Docker failure" in window.activity.toPlainText()
        # Cancellation after the worker returns but before Qt delivers finished must still suppress launch.
        late_launch = Mock()
        window.run_job("Late cancellation test", lambda runner: "complete", late_launch, cancel_callback_on_stop=True)
        assert window.worker.wait(10000)
        window.worker.runner.stop_after_step.set()
        finish_worker()
        late_launch.assert_not_called()
        # Reopening the same realm restores the saved executable and locale.
        window.select_realm(realm.path)
        assert window.client.executable == (game / "Wow.exe").resolve()
        window.resize(1240, 880); scroll.verticalScrollBar().setValue(0)
    # Other offline smoke checks must not read the fictional executable as a real PE file.
    window.realm_path = None; window.client = None; window.update_play_state()
