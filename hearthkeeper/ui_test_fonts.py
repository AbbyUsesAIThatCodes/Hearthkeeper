"""Load the runner's own fonts for real offscreen glyph/layout validation.

No font files are copied, downloaded, bundled, or changed. Ordinary Windows
application startup uses its normal platform font database without this path.
"""
from pathlib import Path
from PySide6.QtGui import QFontDatabase, QRawFont, QFont


def prepare_offscreen_fonts(application):
    if application.platformName() != "offscreen":
        return
    font_dir = Path("C:/Windows/Fonts")
    if font_dir.is_dir():
        for filename in ("segoeui.ttf", "segoeuib.ttf", "georgia.ttf", "georgiab.ttf", "consola.ttf"):
            path = font_dir / filename
            if path.is_file():
                QFontDatabase.addApplicationFont(str(path))
    font = QFont("Segoe UI" if font_dir.is_dir() else "DejaVu Sans", 10)
    application.setFont(font)
    raw = QRawFont.fromFont(font)
    if not raw.isValid() or any(not raw.supportsCharacter(ord(ch)) for ch in "Hearthkeeper0123456789"):
        raise RuntimeError("Offscreen tests require real Latin glyphs, not missing-glyph boxes")
