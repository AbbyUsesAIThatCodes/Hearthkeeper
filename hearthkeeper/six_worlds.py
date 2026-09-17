"""Six Worlds presentation layer; realm operations remain in desktop.MainWindow."""
import json
from pathlib import Path
import sys

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QAbstractScrollArea, QApplication, QFrame, QLabel,
                              QLayout, QScrollArea, QSizePolicy, QVBoxLayout, QWidget)

from .desktop import ASSETS, MainWindow as RealmWindow, label
from .world_themes import REALM_NOTICE, THEMES, scenic_svg
from . import home_art


class ScenicHeader(QWidget):
    """Static decorative art beneath accessible, wrapping native text labels."""
    def __init__(self, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("scenicHeader")
        self.setAccessibleName(theme.page + " — " + theme.expansion + " artwork")
        self.renderer = QSvgRenderer(QByteArray(scenic_svg(theme.key).encode("utf-8")), self)
        if not self.renderer.isValid():
            raise ValueError("Invalid built-in scene: " + theme.key)
        self.setFixedHeight(240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(9)
        self.kicker = label(theme.page.upper() + " / " + theme.expansion.upper())
        self.heading = label(theme.title)
        self.caption = label(theme.subtitle)
        self.kicker.setStyleSheet("background: transparent; color: " + theme.accent + "; font-size: 10px; font-weight: bold;")
        self.heading.setStyleSheet('background: transparent; color: #f7edda; font-family: Georgia, "DejaVu Serif"; font-size: 27px;')
        self.caption.setStyleSheet("background: transparent; color: #d0dcda; font-size: 13px;")
        layout.addWidget(self.kicker)
        layout.addWidget(self.heading)
        layout.addWidget(self.caption)
        layout.addStretch()
        self.setToolTip("Decorative " + theme.expansion + " theme. " + REALM_NOTICE)
        if theme.key == "home":
            home_art.prepare_header(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.theme.key == "home":
            home_art.resize_header(self)
            return
        text_width = max(230, int(self.width() * .52) - 52)
        for item in (self.kicker, self.heading, self.caption):
            item.setMaximumWidth(text_width)

    def paintEvent(self, event):
        if self.theme.key == "home" and home_art.paint_header(self):
            return
        painter = QPainter(self)
        self.renderer.render(painter, QRectF(self.rect()))
        painter.end()


def accent_styles(theme):
    """Only decorative accents change. Play, danger, and disabled styles stay put."""
    color = theme.accent
    return f'''
QPushButton#nav:checked {{ color: {color}; border: 1px solid {color}; background: #283338; }}
QLabel#title, QLabel#eyebrow {{ color: {color}; }}
QFrame#parchment QLabel#eyebrow {{ color: #725632; }}
QFrame#sidebar {{ border-right: 2px solid {color}; }}
QProgressBar::chunk {{ background: {color}; }}
QScrollBar::handle:vertical {{ background: {color}; }}
QPushButton#nav:focus {{ border: 2px solid {color}; }}
QLabel#realmBadge {{ color: #d0dcda; background: #172329; border: 1px solid #596e72; padding: 9px; font-size: 11px; }}
'''


class MainWindow(RealmWindow):
    """Reuse all a5 commands and state; replace only the page presentation."""
    def __init__(self, *, remember=True):
        self.worlds_ready = False
        super().__init__(remember=remember)
        self.scene_headers = []
        originals = [self.pages.widget(index) for index in range(self.pages.count())]
        if len(originals) != len(THEMES):
            raise RuntimeError("Page/theme mapping must be reviewed before adding a new page.")
        for index, (original, theme) in enumerate(zip(originals, THEMES)):
            scroll = original if isinstance(original, QScrollArea) else QScrollArea()
            content = original.widget() if isinstance(original, QScrollArea) else original
            layout = content.layout()
            if not isinstance(layout, QVBoxLayout):
                raise RuntimeError("Unexpected page layout: " + theme.key)
            # Remove the old visual heading only; preserve controls and descriptions.
            old_hero = content.findChild(QFrame, "hero") if index == 0 else None
            if old_hero is not None:
                layout.removeWidget(old_hero)
                old_hero.hide()
                old_hero.deleteLater()
            elif index != 0:
                # page() begins with a version eyebrow and title. Keep its description.
                for _ in range(2):
                    item = layout.takeAt(0)
                    if item and item.widget():
                        item.widget().hide()
                        item.widget().deleteLater()
            header = ScenicHeader(theme, content)
            layout.insertWidget(0, header)
            self.scene_headers.append(header)
            layout.setSizeConstraint(QLayout.SizeConstraint.SetMinAndMaxSize)
            # Give tables/trees an honest usable viewport inside the outer page scroll.
            for area in content.findChildren(QAbstractScrollArea):
                if not isinstance(area, QScrollArea):
                    area.setMinimumHeight(max(180, area.minimumHeight()))
            scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            scroll.setObjectName("worldPage_" + theme.key)
            if scroll is not original:
                self.pages.removeWidget(original)
                scroll.setWidget(content)
                self.pages.insertWidget(index, scroll)
        sidebar = self.findChild(QFrame, "sidebar")
        self.realm_badge = label(REALM_NOTICE, "realmBadge")
        self.realm_badge.setAccessibleName("Actual realm compatibility")
        sidebar.layout().insertWidget(sidebar.layout().count() - 2, self.realm_badge)
        home_art.prepare_layout(self)
        self.worlds_ready = True
        self.navigate(0)

    def navigate(self, index):
        super().navigate(index)
        if self.worlds_ready:
            self.setStyleSheet(accent_styles(THEMES[index]) + (home_art.styles() if index == 0 else ""))


def smoke(application, destination):
    """Exercise the actual themed window using no live realm or client data."""
    from unittest.mock import patch
    from .desktop import ManagedRealm
    from .world_themes import THEMES
    output = Path(destination)
    output.mkdir(parents=True, exist_ok=True)
    with patch.object(ManagedRealm, "start", side_effect=AssertionError("Unexpected realm start")), \
         patch.object(ManagedRealm, "backup", side_effect=AssertionError("Unexpected backup")):
        window = MainWindow(remember=False)
        window.show()
        application.processEvents()
        assert window.realm_path is None
        assert not window.play_button.isEnabled()
        assert window.pages.count() == 6
        results = []
        for width, height in ((1240, 880), (980, 700)):
            window.resize(width, height)
            application.processEvents()
            for index, theme in enumerate(THEMES):
                window.nav_buttons[index].click()
                application.processEvents()
                assert window.pages.currentIndex() == index
                assert sum(item.isChecked() for item in window.nav_buttons) == 1
                scroll = window.pages.widget(index)
                scroll.verticalScrollBar().setValue(0)
                application.processEvents()
                header = window.scene_headers[index]
                assert header.renderer.isValid() and header.isVisible()
                assert window.realm_badge.isVisible()
                assert not window.play_button.isEnabled()
                for text in (header.kicker, header.heading, header.caption):
                    assert text.height() >= text.heightForWidth(text.width()), (theme.key, text.text(), text.size())
                filename = f"six-worlds-{theme.key}-{width}x{height}.png"
                assert window.grab().save(str(output / filename))
                # Scroll to both limits; content must remain reachable rather than clipped.
                scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
                application.processEvents()
                results.append({"page": theme.page, "size": [width, height],
                                "vertical_scroll_max": scroll.verticalScrollBar().maximum(),
                                "horizontal_scroll_max": scroll.horizontalScrollBar().maximum()})
        window.navigate(0)
        window.realm_tools_toggle.setChecked(True)
        application.processEvents()
        scroll = window.pages.widget(0)
        scroll.ensureWidgetVisible(window.realm_tools_toggle)
        assert window.realm_tools_toggle.isChecked()
        assert window.realm_path is None and window.worker is None
        window.close()
    (output / "six-worlds-result.json").write_text(json.dumps({"passed": True, "views": results}, indent=2), encoding="utf-8")


def main():
    application = QApplication(sys.argv)
    application.setApplicationName("Hearthkeeper")
    application.setOrganizationName("Hearthkeeper")
    from .ui_test_fonts import prepare_offscreen_fonts
    prepare_offscreen_fonts(application)
    application.setStyleSheet((ASSETS / "desktop.qss").read_text(encoding="utf-8").replace("__ASSETS__", ASSETS.as_posix()))
    if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
        # Run the full existing acceptance suite against this themed subclass.
        from unittest.mock import patch
        from . import desktop_smoke
        with patch.object(desktop_smoke, "MainWindow", MainWindow):
            desktop_smoke.run(application, sys.argv[2])
        smoke(application, sys.argv[2])
        from .home_art_smoke import run as run_home_art
        run_home_art(application, sys.argv[2])
        return 0
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        import traceback
        if len(sys.argv) == 3 and sys.argv[1] == "--smoke-test":
            destination = Path(sys.argv[2]); destination.mkdir(parents=True, exist_ok=True)
            (destination / "smoke-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        traceback.print_exc()
        raise SystemExit(1)
