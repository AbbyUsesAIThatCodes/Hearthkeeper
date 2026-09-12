"""Bounded, data-only archive containers. No pickle, SQL execution, or ZIP extraction."""

import base64
import datetime
import decimal
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

from . import __version__

MAX_PAYLOAD = 64 * 1024 * 1024
MAX_MANIFEST = 16 * 1024
FORMAT = "hearthkeeper.character/1"


class ArchiveError(ValueError):
    """A user-facing validation error."""


def encode_value(value):
    if isinstance(value, bytes):
        return {"$type": "bytes", "value": base64.b64encode(value).decode("ascii")}
    if isinstance(value, decimal.Decimal):
        return {"$type": "decimal", "value": str(value)}
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return {"$type": type(value).__name__, "value": value.isoformat()}
    if isinstance(value, datetime.timedelta):
        return {"$type": "timedelta", "value": str(value)}
    raise TypeError(f"Unsupported database value type: {type(value).__name__}")


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False, default=encode_value).encode("utf-8")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ArchiveError("Duplicate JSON key")
        result[key] = value
    return result


def parse_json(data):
    def invalid_constant(_):
        raise ArchiveError("Non-finite JSON number")
    try:
        return json.loads(data, object_pairs_hook=_unique_object,
                          parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ArchiveError("Invalid archive JSON") from error


def write_new(path, content):
    """Create privately and exclusively; never truncate an existing deliverable."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def validate_snapshot(snapshot):
    if not isinstance(snapshot, dict):
        raise ArchiveError("Snapshot must be an object")
    source = snapshot.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("realm"), str):
        raise ArchiveError("Missing source realm")
    if not source["realm"] or type(source.get("character_guid")) is not int:
        raise ArchiveError("Invalid character identity")
    tables = snapshot.get("tables")
    if not isinstance(tables, dict) or len(tables) > 256:
        raise ArchiveError("Invalid table collection")
    for name, table in tables.items():
        if not isinstance(name, str) or not isinstance(table, dict):
            raise ArchiveError("Invalid table")
        rows = table.get("rows")
        columns = table.get("columns")
        if not isinstance(columns, list) or len(columns) > 1024 or any(
            not isinstance(column, dict) or not isinstance(column.get("name"), str)
            for column in columns
        ):
            raise ArchiveError("Invalid column metadata")
        column_names = [column["name"] for column in columns]
        if len(column_names) != len(set(column_names)):
            raise ArchiveError("Duplicate column metadata")
        if not isinstance(rows, list) or len(rows) > 100_000:
            raise ArchiveError("Invalid or oversized row collection")
        if any(not isinstance(row, dict) for row in rows):
            raise ArchiveError("Invalid database row")
        if any(set(row) != set(column_names) for row in rows):
            raise ArchiveError("Row columns do not match captured schema")
    characters = tables.get("characters.characters", {}).get("rows", [])
    if len(characters) != 1 or characters[0].get("guid") != source["character_guid"]:
        raise ArchiveError("Character identity does not match snapshot")
    if not isinstance(snapshot.get("warnings"), list) or any(
            not isinstance(warning, str) for warning in snapshot["warnings"]):
        raise ArchiveError("Invalid coverage warnings")
    coverage = snapshot.get("coverage")
    if not isinstance(coverage, dict) or any(
        not isinstance(coverage.get(key), list) or
        any(not isinstance(value, str) for value in coverage[key])
        for key in ("missing_tables", "unhandled_tables")
    ):
        raise ArchiveError("Invalid coverage metadata")


def write_archive(path, snapshot):
    validate_snapshot(snapshot)
    payload = json_bytes(snapshot)
    if len(payload) > MAX_PAYLOAD:
        raise ArchiveError("Snapshot exceeds the 64 MiB preview limit")
    manifest = {
        "format": FORMAT,
        "hearthkeeper_version": __version__,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "payload": "snapshot.json",
        "payload_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "completeness": "partial-character-archive",
        "signed": False,
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as container:
        container.writestr("manifest.json", json_bytes(manifest))
        container.writestr("snapshot.json", payload)
    return write_new(path, buffer.getvalue())


def read_archive(path):
    try:
        if Path(path).stat().st_size > MAX_PAYLOAD + MAX_MANIFEST + 1024 * 1024:
            raise ArchiveError("Archive exceeds the preview size limit")
        with zipfile.ZipFile(path) as container:
            names = container.namelist()
            if len(names) != 2 or set(names) != {"manifest.json", "snapshot.json"}:
                raise ArchiveError("Unexpected or duplicate archive members")
            for name, limit in (("manifest.json", MAX_MANIFEST), ("snapshot.json", MAX_PAYLOAD)):
                info = container.getinfo(name)
                if info.file_size > limit or info.flag_bits & 1:
                    raise ArchiveError("Oversized or encrypted archive member")
            manifest = parse_json(container.read("manifest.json"))
            if not isinstance(manifest, dict) or manifest.get("format") != FORMAT:
                raise ArchiveError("Unsupported archive format")
            if manifest.get("payload") != "snapshot.json":
                raise ArchiveError("Invalid payload name")
            payload = container.read("snapshot.json")
            if manifest.get("payload_bytes") != len(payload):
                raise ArchiveError("Payload size mismatch")
            if manifest.get("sha256") != hashlib.sha256(payload).hexdigest():
                raise ArchiveError("Payload checksum mismatch")
            snapshot = parse_json(payload)
            validate_snapshot(snapshot)
            return manifest, snapshot
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError) as error:
        raise ArchiveError("Unreadable archive container") from error


def compare_archives(first, second):
    _, previous = read_archive(first)
    _, current = read_archive(second)
    identity = lambda snapshot: (snapshot["source"]["realm"], snapshot["source"]["character_guid"])
    if identity(previous) != identity(current):
        raise ArchiveError("Comparison requires the same source realm and character GUID")
    changes = []
    for name in sorted(set(previous["tables"]) | set(current["tables"])):
        old = previous["tables"].get(name)
        new = current["tables"].get(name)
        if json_bytes(old) != json_bytes(new):
            changes.append({"table": name, "before_rows": len(old["rows"]) if old else None,
                            "after_rows": len(new["rows"]) if new else None,
                            "status": "added" if old is None else "removed" if new is None else "changed"})
    return {"character": identity(current), "tables": changes,
            "source_changed": previous["source"] != current["source"],
            "coverage_changed": previous["coverage"] != current["coverage"],
            "warnings_changed": previous["warnings"] != current["warnings"]}
