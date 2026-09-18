"""Expose one reduced real CI screenshot for review, never live realm data."""
import base64
from pathlib import Path
import sys
from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage

root = Path(sys.argv[1])
candidates = [root/'home-painted-1366x700.png', root/'home-painted-1280x650.png', root/'desktop-home-ready.png', root/'desktop-realm.png']
source = next((p for p in candidates if p.is_file()), None)
if source is None:
    print('No native screenshot was produced before failure.')
    raise SystemExit(0)
image = QImage(str(source))
if image.isNull():
    raise SystemExit('Cannot read native screenshot')
image = image.scaledToWidth(900, Qt.TransformationMode.SmoothTransformation)
data = QByteArray(); buffer = QBuffer(data)
buffer.open(QIODevice.OpenModeFlag.WriteOnly)
if not image.save(buffer, 'JPG', 32):
    raise SystemExit('Cannot encode review screenshot')
print('NATIVE_SCREENSHOT_SOURCE: ' + source.name)
print('HK_PREVIEW_JPEG_BEGIN')
encoded = base64.b64encode(bytes(data)).decode('ascii')
for offset in range(0, len(encoded), 8000):
    print(encoded[offset:offset+8000])
print('HK_PREVIEW_JPEG_END')
