"""Read the bundled Home painting without fetching or writing any files."""
import base64
import hashlib
import json
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
PARTS = tuple(f"home-portal.{index:02d}.b64" for index in (1, 2, 3))


def read_home_art(directory=None):
    """Decode and verify the text-packed WebP; callers may provide a GUI fallback."""
    root = Path(directory) if directory is not None else ASSETS
    manifest = json.loads((root / "home-art.json").read_text(encoding="utf-8"))
    if tuple(manifest.get("parts", ())) != PARTS:
        raise ValueError("Unexpected Home artwork parts")
    encoded = b"".join((root / name).read_bytes() for name in PARTS)
    if len(encoded) > 100_000:
        raise ValueError("Unexpected Home artwork size")
    data = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(data).hexdigest() != manifest["sha256"]:
        raise ValueError("Home artwork checksum mismatch")
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("Unexpected Home artwork format")
    return data
