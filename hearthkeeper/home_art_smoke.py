"""Offline Home artwork/layout checks, repeated in the Windows executable."""
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QPoint, QRect
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QBoxLayout

from . import home_art
from .desktop import MainWindow as RealmWindow
from .six_worlds import MainWindow, ScenicHeader, accent_styles
from .world_themes import THEMES, REALM_NOTICE


def run(application, directory):
    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((home_art.ASSETS / "home-art.json").read_text(encoding="utf-8"))
    assert hashlib.sha256(home_art.read_home_art()).hexdigest() == manifest["sha256"]
    checks = []
    # Startup and navigation must not launch any real process.
    with patch("subprocess.Popen", side_effect=AssertionError("Unexpected process launch")):
        window = MainWindow(remember=False)
        window.show(); application.processEvents(); QTest.qWait(30)
        header = window.scene_headers[0]
        assert not header.painting.isNull(), "The source/packaged WebP artwork did not load"
        assert (header.painting.width(), header.painting.height()) == tuple(manifest["raster_size"])
        assert window.play.__func__ is RealmWindow.play
        assert window.update_play_state.__func__ is RealmWindow.update_play_state
        assert window.realm_path is None and window.worker is None
        assert [label.text() for label in window.card_values] == ["Choose a realm", "Not selected", "Not checked"]
        assert window.realm_badge.text() == REALM_NOTICE
        assert not window.play_button.isEnabled()
        for width, height in ((1440, 1000), (1240, 880), (980, 700)):
            window.resize(width, height)
            window.navigate(0)
            application.processEvents(); QTest.qWait(30); application.processEvents()
            scroll = window.pages.widget(0)
            scroll.verticalScrollBar().setValue(0)
            application.processEvents()
            assert scroll.horizontalScrollBar().maximum() == 0, f"Home overflow at {width}"
            for label in (header.kicker, header.heading, header.caption):
                assert label.height() >= label.heightForWidth(label.width()), "Home hero label clipped"
            assert window.grab().save(str(output / f"home-painted-{width}x{height}.png"))
            deck = window.home_launch_deck
            expected = QBoxLayout.Direction.LeftToRight if deck.width() >= 850 else QBoxLayout.Direction.TopToBottom
            assert deck.box.direction() == expected
            scroll.ensureWidgetVisible(window.play_button)
            application.processEvents()
            rect = QRect(window.play_button.mapTo(scroll.viewport(), QPoint(0, 0)), window.play_button.size())
            assert scroll.viewport().rect().contains(rect), "Play must be fully reachable by scrolling"
            assert window.grab().save(str(output / f"home-controls-{width}x{height}.png"))
            window.realm_tools_toggle.setChecked(True)
            application.processEvents()
            assert scroll.horizontalScrollBar().maximum() == 0, "Expanded tools overflow"
            scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
            application.processEvents()
            assert window.grab().save(str(output / f"home-tools-{width}x{height}.png"))
            window.realm_tools_toggle.setChecked(False)
            checks.append({"size": [width, height], "deck_width": deck.width(),
                           "layout": "side-by-side" if expected == QBoxLayout.Direction.LeftToRight else "stacked",
                           "horizontal_overflow": scroll.horizontalScrollBar().maximum()})
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
                   "responsive deck", "Home horizontal fit", "native wrapping hero labels",
                   "reachable Play", "expanded tools", "theme isolation", "missing-art fallback"]}, indent=2), encoding="utf-8")
