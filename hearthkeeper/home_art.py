"""Home-only presentation. No realm, account, process, or network operations."""
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (QBoxLayout, QFrame, QLabel, QLayout, QSizePolicy,
                              QVBoxLayout, QWidget)

from .art_assets import read_home_art

ASSETS = Path(__file__).parent / "assets"


def prepare_header(header):
    """Keep all hero text native; the image supplies scenery only."""
    header.painting = QPixmap()
    try:
        header.painting.loadFromData(read_home_art(), "WEBP")
    except (OSError, ValueError, KeyError, TypeError):
        pass  # Decorative resource errors must not block realm management.
    header.setObjectName("homePortalHero")
    header.setFixedHeight(280)
    header.kicker.setText("HOME / THE BURNING CRUSADE")
    header.heading.setText("Your next adventure\nbegins here.")
    header.heading.setStyleSheet('background: transparent; color: #f5e7be; font-family: Georgia, "DejaVu Serif"; font-size: 30px;')
    header.caption.setText("A familiar world. A hearth of your own.")
    header.kicker.setStyleSheet("background: transparent; color: #d1cf92; font-size: 10px; font-weight: bold;")
    # A missing image must not prevent the user accessing their realm tools.
    if header.painting.isNull():
        header.caption.setText("Artwork unavailable. Realm tools remain available.")


def paint_header(header):
    """Return False for the existing vector fallback if the raster is missing."""
    image = header.painting
    if image.isNull():
        return False
    painter = QPainter(header)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    width, height = header.width(), header.height()
    painter.fillRect(header.rect(), QColor("#0c1519"))
    target = QRectF(width * .27, 0, width * .73, height)
    # Cover without stretching. Centering retains the actual portal at both sizes.
    scale = max(target.width() / image.width(), target.height() / image.height())
    sw, sh = target.width() / scale, target.height() / scale
    source = QRectF((image.width() - sw) / 2, (image.height() - sh) / 2, sw, sh)
    painter.drawPixmap(target, image, source)
    shade = QLinearGradient(0, 0, width * .63, 0)
    shade.setColorAt(0, QColor("#0c1519"))
    shade.setColorAt(.58, QColor("#0c1519"))
    shade.setColorAt(.78, QColor(12, 21, 25, 235))
    shade.setColorAt(1, QColor(12, 21, 25, 0))
    painter.fillRect(header.rect(), shade)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    for inset, color, weight in ((2, "#17130d", 4), (5, "#b39155", 2), (10, "#5e5337", 1)):
        painter.setPen(QPen(QColor(color), weight))
        painter.drawRect(QRectF(inset, inset, width - inset * 2, height - inset * 2))
    # Restrained engraved corners, painted at device resolution rather than enlarged pixels.
    for x, y, sx, sy in ((8, 8, 1, 1), (width-8, 8, -1, 1),
                         (8, height-8, 1, -1), (width-8, height-8, -1, -1)):
        painter.setPen(QPen(QColor("#ddbd77"), 1.3))
        points = [QPointF(x + sx*px, y + sy*py) for px, py in ((0,27),(0,0),(27,0),(16,7),(7,16),(0,27))]
        painter.drawPolyline(QPolygonF(points))
        painter.setBrush(QColor("#d9b675"))
        painter.drawEllipse(QPointF(x+sx*9, y+sy*9), 2, 2)
        painter.setBrush(Qt.BrushStyle.NoBrush)
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


def styles():
    """Home-only chrome; callers remove this stylesheet when leaving Home."""
    frame = (ASSETS / "home-frame.svg").as_posix()
    return '''
QWidget#homeSanctum { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #101b20,stop:.6 #172429,stop:1 #10191d); }
QFrame#sidebar { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0a1217,stop:.8 #17232a,stop:1 #111a1e); border-right: 2px solid #967744; }
QLabel#brand { color: #f0d596; }
QPushButton#nav { border: 1px solid #394344; border-bottom: 2px solid #273437; padding: 13px 10px; }
QPushButton#nav:checked { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #2a4a28,stop:1 #18291c); color: #e6eab7; border: 1px solid #9dae55; }
QPushButton#nav:hover { background: #30402c; border-color: #c0b474; }
QPushButton#nav:focus { border: 2px solid #ffe6a1; }
QFrame#card { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #24333a,stop:1 #101a20); border: 10px solid transparent; border-image: url("FRAME") 24 24 24 24 stretch stretch; }
QLabel#cardTitle { color: #c3ae78; font-size: 10px; }
QLabel#cardValue { color: #f3e3ba; font-size: 18px; }
QFrame#parchment { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 #ead8a8,stop:.45 #d9c18d,stop:1 #bda273); border: 10px solid transparent; border-image: url("FRAME") 24 24 24 24 stretch stretch; }
QFrame#parchment QLabel { color: #392d1e; background: transparent; }
QFrame#parchment QLabel#clientTitle { color: #302619; font-size: 22px; }
QFrame#parchment QLabel#eyebrow { color: #61502f; }
QFrame#homeLaunchShrine { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #21352a,stop:.4 #10201e,stop:1 #121d21); border: 10px solid transparent; border-image: url("FRAME") 24 24 24 24 stretch stretch; }
QLabel#homeLaunchCaption { color: #d6bf80; background: transparent; font-family: Georgia, "DejaVu Serif"; font-size: 13px; }
QFrame#homeLaunchShrine QLabel#muted { color: #c3cfbd; background: transparent; font-size: 12px; }
QPushButton#play { color: #ffe7a1; background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #be4c2b,stop:.14 #9a291c,stop:.55 #721c1c,stop:.86 #56191a,stop:1 #8d4527); border: 3px solid #d2ad62; border-radius: 5px; font-family: Georgia, "DejaVu Serif"; font-size: 30px; font-weight: bold; padding: 15px 22px; min-height: 42px; }
QPushButton#play:hover { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #d35b35,stop:.5 #9b2b20,stop:1 #773020); border-color: #ffe1a0; }
QPushButton#play:pressed { background: #52191a; border-color: #b18a47; }
QPushButton#play:focus { border: 3px solid #fff0b3; }
QPushButton#play:disabled { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #46403a,stop:1 #292c29); color: #a59d89; border: 3px solid #756745; }
QPlainTextEdit#activity { background: #0b171b; color: #a2b5ad; }
QLabel#realmBadge { background: #101b1e; color: #c2caba; border: 1px solid #625c3d; padding: 9px; }
'''.replace("FRAME", frame)
