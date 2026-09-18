"""Read-only verified materials; no GUI, network, or persistent state."""
import base64
import hashlib
import json
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
PARTS = tuple(f"war-table.{i:02d}.b64" for i in range(1, 7))
REGIONS = {
    "panorama": (0, 0, 877, 258), "plaque_frame": (0, 272, 293, 166),
    "stone": (310, 272, 43, 81), "parchment": (370, 272, 135, 156),
    "wood": (0, 459, 166, 28), "realm_medallion": (633, 272, 78, 76),
    "client_medallion": (719, 272, 78, 78), "red": (810, 272, 37, 34),
    "vellum": (864, 272, 86, 44), "play_frame": (310, 441, 310, 90),
}


def read_material_atlas(directory=None):
    root = Path(directory) if directory is not None else ASSETS
    manifest = json.loads((root / "war-table.json").read_text(encoding="utf-8"))
    if tuple(manifest.get("parts", ())) != PARTS:
        raise ValueError("Unexpected material atlas parts")
    if manifest.get("size") != [1024, 544]:
        raise ValueError("Unexpected material atlas dimensions")
    if {key: tuple(value["rect"]) for key, value in manifest["regions"].items()} != REGIONS:
        raise ValueError("Unexpected material atlas regions")
    encoded = b"".join((root / part).read_bytes() for part in PARTS)
    if len(encoded) > 120_000:
        raise ValueError("Material atlas too large")
    data = base64.b64decode(encoded, validate=True)
    if data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("Unexpected material atlas format")
    if hashlib.sha256(data).hexdigest() != manifest["sha256"]:
        raise ValueError("Material atlas checksum mismatch")
    return data


def fit_scene(image_width, image_height, width, height):
    """Contain the entire image, returning x, y, width, height; never center-crop."""
    if min(image_width, image_height, width, height) <= 0:
        return (0.0, 0.0, 0.0, 0.0)
    scale = min(width / image_width, height / image_height)
    w, h = image_width * scale, image_height * scale
    return ((width - w) / 2, (height - h) / 2, w, h)
