"""Offline Home artwork/layout checks, repeated in the Windows executable."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QPoint, QRect, Qt, QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QBoxLayout, QLabel

from . import home_art
from .desktop import MainWindow as RealmWindow
from .six_worlds import MainWindow, ScenicHeader, accent_styles
from .world_themes import THEMES, REALM_NOTICE


def run(application, directory):
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((home_art.ASSETS / "war-table.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(home_art.read_home_art()).hexdigest() == manifest["sha256"]
    checks = []
    # Startup and navigation must not launch any real process.
    with patch("subprocess.Popen", side_effect=AssertionError("Unexpected process launch")):
        window = MainWindow(remember=False)
        window.show(); application.processEvents(); QTest.qWait(30)
        header = window.scene_headers[0]
        assert not header.painting.isNull(), "The source/packaged WebP artwork did not load"
        assert (header.painting.width(), header.painting.height()) == tuple(manifest["regions"]["panorama"]["rect"][2:])
        assert window.play.__func__ is RealmWindow.play
        assert window.update_play_state.__func__ is RealmWindow.update_play_state
        assert window.realm_path is None and window.worker is None
        assert [label.text() for label in window.card_values] == ["Choose a realm", "Not selected", "Not checked"]
        assert window.realm_badge.text() == REALM_NOTICE
        assert not window.play_button.isEnabled()
        # Logical client areas include space reserved for the OS title bar/taskbar.
        for width, height in ((1920, 1000), (1536, 790), (1366, 700), (1280, 650), (980, 640)):
            window.resize(width, height)
            window.navigate(0)
            application.processEvents(); QTest.qWait(30); application.processEvents()
            scroll = window.pages.widget(0)
            scroll.verticalScrollBar().setValue(0)
            application.processEvents()
            assert scroll.horizontalScrollBar().maximum() == 0, f"Home overflow at {width}"
            assert scroll.verticalScrollBar().maximum() == 0, f"Home needs scrolling at {width}x{height}"
            assert window.size().width() == width and window.size().height() == height, "Window grew beyond the requested work area"
            for label in (header.kicker, header.heading, header.caption):
                assert label.height() >= label.heightForWidth(label.width()), "Home hero label clipped"
            scene = header.scene_target
            assert scene.width() > header.width() * .48, "Panorama must remain substantial beside the title"
            assert header.rect().contains(scene.toRect()), "Scene outside header"
            assert abs(scene.width() / scene.height() - 877 / 258) < .01, "Full panorama aspect ratio must survive"
            assert header.caption.text() == "The Burning Crusade  ·  Some gates should never close."
            assert window.material_library.valid and len(window.material_skins) >= 15
            assert window.grab().save(str(output / f"home-painted-{width}x{height}.png"))
            deck = window.home_launch_deck
            expected = QBoxLayout.Direction.LeftToRight if deck.width() >= 650 else QBoxLayout.Direction.TopToBottom
            assert deck.box.direction() == expected
            for control in (window.play_button, window.choose_client_button, window.connect_client_button,
                            window.realm_tools_toggle, window.motion_toggle, window.host_value, *window.card_values):
                rect = QRect(control.mapTo(scroll.viewport(), QPoint(0, 0)), control.size())
                assert control.isVisible() and scroll.viewport().rect().contains(rect), f"Control outside Home: {control.text()}"
            for label in (window.client_title, window.client_notice, window.play_notice):
                assert label.height() >= label.heightForWidth(label.width()), f"Clipped text: {label.text()}"
            assert window.grab().save(str(output / f"home-controls-{width}x{height}.png"))
            window.realm_tools_toggle.setChecked(True)
            application.processEvents()
            assert window.tools_dialog.isVisible(), "Realm tools must open separately"
            assert scroll.verticalScrollBar().maximum() == 0, "Tools changed the Home fit"
            QTest.keyClick(window.tools_dialog, Qt.Key.Key_Escape)
            assert not window.realm_tools_toggle.isChecked()
            checks.append({"size": [width, height], "deck_width": deck.width(),
                           "layout": "side-by-side" if expected == QBoxLayout.Direction.LeftToRight else "stacked",
                           "horizontal_overflow": scroll.horizontalScrollBar().maximum(),
                           "vertical_overflow": scroll.verticalScrollBar().maximum(),
                           "device_pixel_ratio": window.devicePixelRatio()})
        window.resize(1280, 650)
        window.card_values[0].setText("A very long realm name — " * 12)
        window.client_notice.setText("Build 12340 · enUS\nC:/" + "long-client-path/" * 5)
        application.processEvents(); QTest.qWait(40)
        assert scroll.verticalScrollBar().maximum() == 0 and scroll.horizontalScrollBar().maximum() == 0
        assert window.card_values[0].toolTip() == window.card_values[0].text()
        window.activity.appendPlainText("Fictional operation: checking files")
        assert window.activity_summary.text() == "Fictional operation: checking files"
        window.activity_button.click(); application.processEvents()
        assert window.activity_dialog.isVisible() and window.stop_step.isVisible()
        window.activity_dialog.close()
        # Persistent reduced-motion switch and animation lifecycle, using isolated settings.
        window.preferences = QSettings(str(output / "motion-test.ini"), QSettings.Format.IniFormat)
        window.motion_toggle.setChecked(False)
        assert not window.home_presentation.motion_timer.isActive()
        assert not window.scene_headers[0].motion_enabled
        assert window.preferences.value("living_hearth/motion", True, type=bool) is False
        with patch("hearthkeeper.desktop.QSettings", return_value=window.preferences):
            reopened = MainWindow()
            assert not reopened.motion_toggle.isChecked(), "Still-scene preference was not restored"
            reopened.close()
        phase = header.motion_phase
        QTest.qWait(120)
        assert header.motion_phase == phase
        window.motion_toggle.setChecked(True)
        window.activateWindow(); application.processEvents(); QTest.qWait(150)
        assert window.home_presentation.motion_timer.isActive(), "Visible active scene should animate"
        assert header.motion_phase > phase
        window.navigate(1); application.processEvents(); QTest.qWait(20)
        assert not window.home_presentation.motion_timer.isActive(), "Hidden Home must stop rendering"
        window.navigate(0); window.showMinimized(); application.processEvents(); QTest.qWait(20)
        assert not window.home_presentation.motion_timer.isActive(), "Minimized window must stop rendering"
        window.showNormal()
        # Home-only chrome must not leak into the other five expansion pages.
        for index in range(1, 6):
            window.navigate(index); application.processEvents()
            assert window.styleSheet() == accent_styles(THEMES[index])
        assert window.realm_path is None and window.worker is None
        assert not window.play_button.isEnabled()
        window.close()
        with patch.object(home_art, "read_home_art", side_effect=OSError("Missing fixture art")):
            fallback = ScenicHeader(THEMES[0])
            fallback.resize(720, 280); fallback.show(); application.processEvents()
            assert fallback.painting.isNull() and fallback.renderer.isValid()
            assert "Artwork unavailable" in fallback.caption.text()
            fallback.grab()  # Exercise the actual vector fallback paint path.
            fallback.close()
    (output / "home-art-result.json").write_text(json.dumps({"passed": True, "views": checks,
        "asset_sha256": manifest["sha256"], "real_realm_used": False,
        "checks": ["packaged raster", "unmodified Play implementation", "honest startup statuses",
                   "responsive deck", "Home fits without scrolling", "native wrapping hero labels",
                   "all launch controls visible", "separate tools and activity", "long realm/client text",
                   "persisted motion toggle", "hidden/minimized animation pause", "theme isolation",
                   "missing-art fallback"]}, indent=2), encoding="utf-8")
