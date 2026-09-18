"""Tactile painting of existing widgets; their signals and behavior are untouched."""
from PySide6.QtCore import QObject, QEvent, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen, QPixmap
from .material_assets import REGIONS, read_material_atlas


class MaterialLibrary:
    def __init__(self, data=None):
        self.atlas = QPixmap()
        try:
            self.atlas.loadFromData(read_material_atlas() if data is None else data, "WEBP")
        except (OSError, ValueError, KeyError, TypeError):
            pass
        self.valid = not self.atlas.isNull() and self.atlas.width() == 1024 and self.atlas.height() == 544
        self.images = {key: self.atlas.copy(*rect) for key, rect in REGIONS.items()} if self.valid else {}

    def image(self, name):
        return self.images.get(name, QPixmap())


def tiled(painter, rect, image):
    if not image.isNull():
        painter.drawTiledPixmap(QRectF(rect), image, QPointF(0, 0))


def frame(painter, rect, image, source_inset=18, thickness=24):
    """Nine-slice the cleared frame. The center is intentionally never rendered."""
    if image.isNull() or rect.width() <= 0 or rect.height() <= 0:
        return
    d = min(thickness, rect.width() / 3, rect.height() / 3)
    sx = (0, source_inset, image.width() - source_inset, image.width())
    sy = (0, source_inset, image.height() - source_inset, image.height())
    dx = (rect.left(), rect.left() + d, rect.right() - d, rect.right())
    dy = (rect.top(), rect.top() + d, rect.bottom() - d, rect.bottom())
    for y in range(3):
        for x in range(3):
            if x == y == 1:
                continue
            target = QRectF(dx[x], dy[y], dx[x+1] - dx[x], dy[y+1] - dy[y])
            source = QRectF(sx[x], sy[y], sx[x+1] - sx[x], sy[y+1] - sy[y])
            painter.drawPixmap(target, image, source)


class MaterialSkin(QObject):
    """Paint only; Qt still owns input, focus, accessibility, and button signals."""
    def __init__(self, target, library, kind, window, medallion=None):
        super().__init__(target)
        self.library, self.kind, self.window, self.medallion = library, kind, window, medallion
        target.installEventFilter(self)
        target.setProperty("materialKind", kind)

    def eventFilter(self, target, event):
        if event.type() != QEvent.Type.Paint or not self.library.valid or self.window.pages.currentIndex() != 0:
            return False
        painter = QPainter(target)
        try:
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.paint(painter, target)
        finally:
            painter.end()
        return True

    def paint(self, p, widget):
        r = QRectF(widget.rect())
        art = self.library
        if self.kind == "desk":
            p.fillRect(r, QColor("#291b11"))
            tiled(p, r, art.image("wood"))
            p.fillRect(r, QColor(23, 14, 8, 185))
            return
        if self.kind == "parchment":
            p.fillRect(r, QColor("#ddbd80"))
            vellum = art.image("vellum")
            p.drawPixmap(r, vellum, QRectF(vellum.rect()))
            p.fillRect(r, QColor(233, 209, 158, 175))
            p.save()
            p.setOpacity(.23)
            map_art = art.image("parchment")
            h = max(1, r.height() - 30)
            w = h * map_art.width() / max(1, map_art.height())
            p.drawPixmap(QRectF(r.right()-w-14, 15, w, h), map_art, QRectF(map_art.rect()))
            p.restore()
        elif self.kind == "play":
            p.fillRect(r, QColor("#4c0b0b") if widget.isEnabled() else QColor("#343028"))
            if widget.isEnabled():
                tiled(p, r.adjusted(12, 10, -12, -10), art.image("red"))
                if widget.isDown():
                    p.fillRect(r, QColor(0, 0, 0, 95))
                elif widget.underMouse():
                    p.fillRect(r, QColor(255, 159, 65, 30))
            p.save()
            p.setOpacity(1 if widget.isEnabled() else .42)
            frame(p, r, art.image("plaque_frame"), 18, 13)
            p.restore()
            p.setPen(QColor("#ffe4a1") if widget.isEnabled() else QColor("#b2a48a"))
            text = r.adjusted(19, 10, -19, -10)
            font = widget.font()
            while QFontMetrics(font).horizontalAdvance(widget.text()) > text.width() and font.pixelSize() > 15:
                font.setPixelSize(font.pixelSize() - 1)
            p.setFont(font)
            if widget.isDown():
                text.translate(0, 1)
            p.drawText(text, int(Qt.AlignmentFlag.AlignCenter), widget.text())
            if widget.hasFocus():
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor("#fff2c0"), 2, Qt.PenStyle.DashLine))
                p.drawRect(r.adjusted(8, 8, -8, -8))
            return
        else:
            p.fillRect(r, QColor("#191a16"))
            tiled(p, r, art.image("stone"))
            if self.kind == "nav" and widget.isChecked():
                p.fillRect(r, QColor(53, 107, 31, 110))
            if self.kind in ("nav", "button") and widget.underMouse() and widget.isEnabled():
                p.fillRect(r, QColor(180, 144, 72, 28))
        frame(p, r, art.image("plaque_frame"), 18, 15 if self.kind not in ("nav", "button") else 9)
        if self.medallion:
            icon = art.image(self.medallion)
            p.drawPixmap(QRectF(12, (r.height()-34)/2, 34, 34), icon, QRectF(icon.rect()))
        if self.kind == "button":
            if not widget.isEnabled():
                p.fillRect(r.adjusted(2, 2, -2, -2), QColor(25, 25, 22, 160))
            elif widget.isDown():
                p.fillRect(r, QColor(0, 0, 0, 85))
            p.setFont(widget.font())
            p.setPen(QColor("#f3e7c7") if widget.isEnabled() else QColor("#9c988b"))
            p.drawText(r.adjusted(11, 5, -11, -5), int(Qt.AlignmentFlag.AlignCenter), widget.text().replace("&&", "&"))
            if widget.hasFocus():
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor("#fff2c0"), 2, Qt.PenStyle.DashLine))
                p.drawRect(r.adjusted(5, 5, -5, -5))
        if self.kind == "nav":
            p.setFont(widget.font())
            p.setPen(QColor("#fff0bc") if widget.isChecked() else QColor("#ded5bd"))
            icon = widget.icon().pixmap(24, 24)
            p.drawPixmap(QRectF(16, (r.height()-24)/2, 24, 24), icon, QRectF(icon.rect()))
            p.drawText(r.adjusted(50, 7, -12, -7), int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), widget.text())
            if widget.hasFocus():
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(QColor("#fff2c0"), 2, Qt.PenStyle.DashLine))
                p.drawRect(r.adjusted(5, 5, -5, -5))
