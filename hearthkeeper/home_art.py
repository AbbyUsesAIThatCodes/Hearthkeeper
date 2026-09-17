"""Home materials and composition only; the existing realm commands are reused."""
from pathlib import Path
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import (QBoxLayout, QFrame, QLabel, QLayout, QPushButton,
                              QSizePolicy, QVBoxLayout, QWidget)
from .material_assets import REGIONS, fit_scene, read_material_atlas as read_home_art
from .material_widgets import MaterialLibrary, MaterialSkin, frame, tiled

ASSETS = Path(__file__).parent / "assets"


def prepare_header(header):
    """Native captions surround an unobscured painting, never cover its statues."""
    try:
        header.materials = MaterialLibrary(read_home_art())
    except (OSError, ValueError, KeyError, TypeError):
        header.materials = MaterialLibrary(b"")
    header.painting = header.materials.image("panorama")
    header.setObjectName("homePortalHero")
    header.setFixedHeight(350)
    header.kicker.setText("HEARTHKEEPER / YOUR GATEWAY TO AZEROTH")
    header.heading.setText("Your next adventure begins here.")
    header.heading.setStyleSheet('background: transparent; color: #f7e4b4; font-family: Georgia, "DejaVu Serif"; font-size: 27px;')
    header.kicker.setStyleSheet("background: transparent; color: #c4ad77; font-size: 10px; font-weight: bold;")
    header.caption.setText("The Burning Crusade  ·  Some gates should never close.")
    header.caption.setStyleSheet('background: transparent; color: #eddaa3; font-family: Georgia, "DejaVu Serif"; font-size: 14px;')
    header.caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
    if header.painting.isNull():
        header.caption.setText("Artwork unavailable. Realm tools remain available.")
    layout = header.layout()
    while layout.count():
        layout.takeAt(0)
    layout.setContentsMargins(24, 18, 24, 18)
    layout.setSpacing(5)
    layout.addWidget(header.kicker)
    layout.addWidget(header.heading)
    layout.addStretch(1)
    layout.addWidget(header.caption)
    header.scene_target = QRectF()


def resize_header(header):
    """Width-only sizing converges; no font/height feedback inside resize events."""
    width = max(230, header.width() - 48)
    for text in (header.kicker, header.heading, header.caption):
        text.setMaximumWidth(width)
    height = max(290, round((header.width() - 28) * 258 / 877) + 116)
    if header.height() != height:
        header.setFixedHeight(height)


def paint_header(header):
    if header.painting.isNull():
        return False
    painter = QPainter(header)
    try:
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(header.rect(), QColor("#151713"))
        tiled(painter, header.rect(), header.materials.image("stone"))
        top = max(80, header.heading.geometry().bottom() + 10)
        bottom = max(top + 1, header.caption.geometry().top() - 8)
        area = QRectF(14, top, max(1, header.width()-28), bottom-top)
        x, y, w, h = fit_scene(header.painting.width(), header.painting.height(), area.width(), area.height())
        target = QRectF(area.x()+x, area.y()+y, w, h)
        painter.drawPixmap(target, header.painting, QRectF(header.painting.rect()))
        header.scene_target = target
        # No cover crop, no dark gradient, and no raster lettering to truncate.
        frame(painter, QRectF(header.rect()), header.materials.image("plaque_frame"), 18, 20)
    finally:
        painter.end()
    return True


class LaunchDeck(QWidget):
    """Reuse the existing client and Play widgets, side-by-side only when they fit."""
    def __init__(self, parchment, play, notice, parent=None):
        super().__init__(parent)
        self.setObjectName("homeLaunchDeck")
        self.box = QBoxLayout(QBoxLayout.Direction.TopToBottom, self)
        self.box.setContentsMargins(0, 0, 0, 0)
        self.box.setSpacing(14)
        # Do not let the current horizontal layout prevent the window narrowing.
        self.box.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.parchment = parchment
        self.box.addWidget(parchment, 3)
        shrine = QFrame(self); shrine.setObjectName("homeLaunchShrine")
        inside = QVBoxLayout(shrine); inside.setContentsMargins(20, 16, 20, 16)
        inside.setSpacing(12)
        caption = QLabel("YOUR ADVENTURE", shrine)
        caption.setTextFormat(Qt.TextFormat.PlainText)
        caption.setObjectName("homeLaunchCaption")
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inside.addWidget(caption)
        inside.addStretch(1)
        play.setMinimumWidth(200)
        play.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        inside.addWidget(play)
        notice.setWordWrap(True)
        notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        notice.setMinimumWidth(0)
        notice.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        inside.addWidget(notice)
        inside.addStretch(1)
        self.box.addWidget(shrine, 2)
        self.shrine = shrine

    def minimumSizeHint(self):
        return QSize(max(self.parchment.minimumSizeHint().width(),
                         self.shrine.minimumSizeHint().width()), self.box.minimumSize().height())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        direction = QBoxLayout.Direction.LeftToRight if self.width() >= 850 else QBoxLayout.Direction.TopToBottom
        if self.box.direction() != direction:
            self.box.setDirection(direction)
            self.updateGeometry()

def prepare_layout(window):
    """Presentation rearrangement only; keep the original buttons and their signals."""
    content = window.pages.widget(0).widget()
    content.setObjectName("homeSanctum")
    layout = content.layout()
    layout.setSpacing(14)
    parchment = content.findChild(QFrame, "parchment")
    if parchment is None:
        raise RuntimeError("The Home client panel changed; review the presentation adapter.")
    position = layout.indexOf(parchment)
    play_row = next((i for i in range(layout.count())
                     if layout.itemAt(i).layout() is not None
                     and layout.itemAt(i).layout().indexOf(window.play_button) >= 0), None)
    if position < 0 or play_row is None or play_row <= position:
        raise RuntimeError("The Home Play layout changed; review the presentation adapter.")
    removed = layout.takeAt(play_row).layout()
    # Detach items before putting the exact same buttons/labels in the responsive deck.
    while removed.count():
        removed.takeAt(0)
    removed.deleteLater()
    layout.removeWidget(parchment)
    window.home_launch_deck = LaunchDeck(parchment, window.play_button, window.play_notice, content)
    layout.insertWidget(position, window.home_launch_deck)


    library = window.scene_headers[0].materials
    window.material_library = library
    window.material_skins = []
    def skin(widget, kind, medallion=None):
        window.material_skins.append(MaterialSkin(widget, library, kind, window, medallion))
    skin(content, "desk")
    skin(window.findChild(QFrame, "sidebar"), "stone")
    cards = content.findChildren(QFrame, "card")
    for index, card in enumerate(cards):
        card.setMinimumHeight(136)
        card.layout().setContentsMargins(83, 25, 20, 22)
        skin(card, "stone", "client_medallion" if index == 1 else "realm_medallion")
    parchment.layout().setContentsMargins(24, 23, 24, 23)
    skin(parchment, "parchment")
    skin(window.home_launch_deck.shrine, "stone")
    window.play_button.setMinimumHeight(78)
    skin(window.play_button, "play")
    for item in window.nav_buttons:
        skin(item, "nav")
    for item in content.findChildren(QPushButton):
        if item is not window.play_button:
            skin(item, "button")


def styles():
    """The material painters are Home-only; all other pages keep their own styles."""
    return """
QWidget#homeSanctum { background: #291b11; }
QFrame#sidebar { background: #191a16; border-right: 2px solid #977645; }
QLabel#brand { color: #f4dba0; }
QPushButton#nav { padding: 14px 10px; border: 1px solid #685437; }
QFrame#card { background: #1c1c18; border: 0; border-image: none; }
QFrame#card QLabel { background: transparent; border: 0; }
QLabel#cardTitle { color: #e6c983; font-size: 10px; }
QLabel#cardValue { color: #efe3c8; font-size: 17px; }
QWidget#homeLaunchDeck { background: transparent; }
QFrame#parchment { background: #ddbd80; border: 0; border-image: none; }
QFrame#parchment QLabel { color: #302518; background: transparent; border: 0; }
QFrame#parchment QLabel#clientTitle { color: #251a10; font-size: 22px; }
QFrame#parchment QLabel#eyebrow { color: #5d4128; }
QFrame#homeLaunchShrine { background: #1c1c18; border: 0; border-image: none; }
QLabel#homeLaunchCaption { color: #e0c48a; background: transparent; font-family: Georgia, "DejaVu Serif"; font-size: 13px; }
QFrame#homeLaunchShrine QLabel#muted { color: #c8c1ab; background: transparent; font-size: 12px; }
QPushButton#play { color: #ffe4a1; background: #821e16; border: 2px solid #b89450; font-family: Georgia, "DejaVu Serif"; font-size: 29px; font-weight: bold; padding: 16px 20px; }
QPushButton#play:disabled { color: #a89b86; background: #343028; border-color: #675b44; }
QPushButton:focus { border: 2px solid #fff0b3; }
QPlainTextEdit#activity { background: #141813; color: #b3bba4; }
QLabel#realmBadge { background: #191b16; color: #c7c7b6; border: 1px solid #7f6944; padding: 9px; }
"""
