"""Home materials and composition only; the existing realm commands are reused."""
from pathlib import Path
from math import sin
from PySide6.QtCore import QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap, QRadialGradient
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
    header.setFixedHeight(240)
    header.kicker.setText("YOUR GATEWAY TO AZEROTH")
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
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(5)
    row = QBoxLayout(QBoxLayout.Direction.LeftToRight)
    row.setSpacing(18)
    header.title_panel = QWidget(header)
    header.title_panel.setStyleSheet("background: transparent;")
    titles = QVBoxLayout(header.title_panel)
    titles.setContentsMargins(0, 0, 0, 0)
    titles.setSpacing(10)
    titles.addStretch()
    titles.addWidget(header.kicker)
    titles.addWidget(header.heading)
    titles.addStretch()
    header.scene_panel = QWidget(header)
    header.scene_panel.setStyleSheet("background: transparent;")
    scene_layout = QVBoxLayout(header.scene_panel)
    scene_layout.setContentsMargins(0, 0, 0, 0)
    scene_layout.addStretch()
    scene_layout.addWidget(header.caption)
    row.addWidget(header.title_panel)
    row.addWidget(header.scene_panel, 1)
    layout.addLayout(row)
    header.scene_target = QRectF()
    header.motion_phase = 0.0


def resize_header(header):
    """The viewport owns height; title and full panorama share the available width."""
    header.title_panel.setFixedWidth(200 if header.width() < 900 else 245)
    header.update()


def paint_header(header):
    if header.painting.isNull():
        return False
    painter = QPainter(header)
    try:
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.fillRect(header.rect(), QColor("#151713"))
        tiled(painter, header.rect(), header.materials.image("stone"))
        panel = header.scene_panel.geometry()
        area = QRectF(panel.x(), panel.y(), panel.width(),
                      max(1, header.caption.geometry().top() - 8))
        x, y, w, h = fit_scene(header.painting.width(), header.painting.height(), area.width(), area.height())
        target = QRectF(area.x()+x, area.y()+y, w, h)
        painter.drawPixmap(target, header.painting, QRectF(header.painting.rect()))
        header.scene_target = target
        # A soft, local shimmer; the complete source painting stays untouched.
        if getattr(header, "motion_enabled", False):
            glow = QRadialGradient(target.x() + target.width() * .42,
                                   target.y() + target.height() * .64, target.height() * .27)
            glow.setColorAt(0, QColor(165, 255, 81, round(12 + 10 * sin(header.motion_phase))))
            glow.setColorAt(1, QColor(130, 255, 80, 0))
            painter.fillRect(target, glow)
            painter.setPen(Qt.PenStyle.NoPen)
            for index in range(12):
                age = (header.motion_phase * .065 + index / 12) % 1
                px = target.x() + target.width() * (.34 + (index * .031) % .19 + .009 * sin(index + age * 5))
                py = target.bottom() - target.height() * (.10 + age * .66)
                painter.setBrush(QColor(218, 245, 130, round(100 * sin(age * 3.14159))))
                painter.drawEllipse(QRectF(px, py, 1.5 + index % 2, 1.5 + index % 2))
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
        self.box.setSpacing(10)
        # Do not let the current horizontal layout prevent the window narrowing.
        self.box.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.parchment = parchment
        self.box.addWidget(parchment, 3)
        shrine = QFrame(self); shrine.setObjectName("homeLaunchShrine")
        inside = QVBoxLayout(shrine); inside.setContentsMargins(18, 14, 18, 14)
        inside.setSpacing(7)
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
        direction = QBoxLayout.Direction.LeftToRight if self.width() >= 650 else QBoxLayout.Direction.TopToBottom
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
    from .living_hearth import prepare
    prepare(window, content)
    library = window.scene_headers[0].materials
    window.material_library = library
    window.material_skins = []
    def skin(widget, kind, medallion=None):
        window.material_skins.append(MaterialSkin(widget, library, kind, window, medallion))
    skin(content, "desk")
    skin(window.findChild(QFrame, "sidebar"), "stone")
    cards = content.findChildren(QFrame, "card")
    for index, card in enumerate(cards):
        card.setFixedHeight(78)
        card.layout().setSpacing(3)
        card.layout().setContentsMargins(50, 15, 12, 14)
        for text in card.findChildren(QLabel):
            text.setMinimumWidth(0)
            text.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        skin(card, "stone", "client_medallion" if index == 1 else "realm_medallion")
    parchment.layout().setContentsMargins(22, 17, 22, 17)
    parchment.layout().setSpacing(6)
    client_row = parchment.layout().itemAt(parchment.layout().count()-1).layout()
    client_row.removeWidget(window.connect_client_button)
    parchment.layout().addWidget(window.connect_client_button)
    skin(parchment, "parchment")
    skin(window.home_launch_deck.shrine, "stone")
    window.play_button.setMinimumHeight(64)
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
QPushButton#nav { padding: 11px 10px; border: 1px solid #685437; }
QFrame#card { background: #1c1c18; border: 0; border-image: none; }
QFrame#card QLabel { background: transparent; border: 0; }
QLabel#cardTitle { color: #e6c983; font-size: 10px; }
QLabel#cardValue { color: #efe3c8; font-size: 15px; }
QWidget#homeLaunchDeck { background: transparent; }
QFrame#parchment { background: #ddbd80; border: 0; border-image: none; }
QFrame#parchment QLabel { color: #302518; background: transparent; border: 0; }
QFrame#parchment QLabel#clientTitle { color: #251a10; font-size: 19px; }
QFrame#parchment QLabel#eyebrow { color: #5d4128; }
QFrame#homeLaunchShrine { background: #1c1c18; border: 0; border-image: none; }
QLabel#homeLaunchCaption { color: #e0c48a; background: transparent; font-family: Georgia, "DejaVu Serif"; font-size: 13px; }
QFrame#homeLaunchShrine QLabel#muted { color: #c8c1ab; background: transparent; font-size: 12px; }
QPushButton#play { color: #ffe4a1; background: #821e16; border: 2px solid #b89450; font-family: Georgia, "DejaVu Serif"; font-size: 25px; font-weight: bold; padding: 12px 14px; }
QPushButton#play:disabled { color: #a89b86; background: #343028; border-color: #675b44; }
QPushButton:focus { border: 2px solid #fff0b3; }
QPlainTextEdit#activity { background: #141813; color: #b3bba4; }
QLabel#realmBadge { background: #191b16; color: #c7c7b6; border: 1px solid #7f6944; padding: 9px; }
QFrame#hearthFooter { background: #191a16; border-top: 1px solid #80663c; }
QLabel#activitySummary { color: #c9bb99; font-size: 11px; }
QFrame#hearthFooter QPushButton { padding: 4px 12px; }
QCheckBox { background: transparent; color: #e8d4a2; }
"""
