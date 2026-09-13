"""Source catalog and byte-preserving acquisitions; never install or execute content."""
from datetime import date, datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler
import uuid

CATALOG = Path(__file__).parent / "data" / "sources.catalog.json"
CHUNK = 1024 * 1024
MAX_SOURCE_BYTES = 1024 ** 3
NETWORK_HOSTS = {"api.github.com", "codeload.github.com", "github.com"}


class SourceError(Exception):
    pass


def _https(url, hosts=None):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.port not in (None, 443) or (hosts and parsed.hostname not in hosts)):
        raise SourceError("Unsupported source address. Use the provider's HTTPS page.")
    return url


class SourceRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        _https(new_url, NETWORK_HOSTS)
        return super().redirect_request(request, response, code, message, headers, new_url)


def _open(url):
    _https(url, NETWORK_HOSTS)
    request = Request(url, headers={"User-Agent": "Hearthkeeper-source-archive",
                                   "Accept": "application/vnd.github+json"})
    try:
        return build_opener(SourceRedirects()).open(request, timeout=30)
    except HTTPError as error:
        raise SourceError(f"Source returned HTTP {error.code}. The branch may have changed, or GitHub's unauthenticated request limit may have been reached. Try the source page.") from error
    except (URLError, TimeoutError) as error:
        raise SourceError("Could not reach the source. Check the connection and try again.") from error


def load_catalog(path=CATALOG):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise SourceError("Unsupported source catalog version.")
    providers = data["providers"]
    provider_ids = {provider["id"] for provider in providers}
    if len(provider_ids) != len(providers):
        raise SourceError("Duplicate source provider.")
    for provider in providers:
        _https(provider["url"])
    seen = set()
    for offering in data["offerings"]:
        identity = offering["id"]
        if identity in seen or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identity):
            raise SourceError("Duplicate or invalid offering identifier.")
        seen.add(identity)
        if offering["provider"] not in provider_ids:
            raise SourceError("Offering has no source provider.")
        _https(offering["page_url"])
        for url in offering["evidence_urls"]:
            _https(url)
        date.fromisoformat(offering["reviewed_on"])
        if offering["acquisition"] not in ("github_snapshot", "download_page"):
            raise SourceError("Unsupported acquisition method.")
        client = offering["client"]
        if not client["family"] or not client["version"] or (client["build"] is not None
                and (type(client["build"]) is not int or client["build"] <= 0)):
            raise SourceError("Invalid client target.")
        if offering["acquisition"] == "github_snapshot":
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", offering["repository"]):
                raise SourceError("Invalid GitHub repository.")
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", offering["ref"]):
                raise SourceError("Invalid source revision.")
    return data


def offerings(catalog, *, provider="", era="", query=""):
    names = {row["id"]: row["name"] for row in catalog["providers"]}
    return [entry for entry in catalog["offerings"]
            if (not provider or entry["provider"] == provider)
            and (not era or entry["era"] == era)
            and query.casefold() in (names[entry["provider"]] + " " + json.dumps(entry)).casefold()]


def client_target(entry):
    client = entry["client"]
    build = str(client["build"]) if client["build"] else "check selected revision"
    return f"{client['family']} · {client['version']} · build {build}"


def _check_stop(stop):
    if stop and stop.is_set():
        raise SourceError("Source operation stopped. Any partial copy is marked incomplete; retry creates a new copy.")


def _copy(stream, destination, *, expected_size=None, limit=None, stop=None, log=lambda line: None):
    checksum = hashlib.sha256()
    total = 0
    report_at = 64 * CHUNK
    with destination.open("xb") as output:
        while True:
            _check_stop(stop)
            chunk = stream.read(CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if limit and total > limit:
                raise SourceError("Source snapshot exceeds the 1 GiB preview limit. Use the provider page for larger archives.")
            output.write(chunk)
            checksum.update(chunk)
            if total >= report_at:
                log(f"Copied {total // CHUNK:,} MiB")
                report_at += 64 * CHUNK
        output.flush()
        os.fsync(output.fileno())
    _check_stop(stop)
    if expected_size is not None and total != expected_size:
        raise SourceError("Transfer ended at an unexpected size. The incomplete copy has not been added to saved copies.")
    if total == 0:
        raise SourceError("The selected file or downloaded snapshot is empty.")
    return {"bytes": total, "sha256": checksum.hexdigest()}


def _begin(root, entry):
    identity = entry["id"]
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", identity):
        raise SourceError("Invalid offering identifier.")
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = root / f"{identity}-{stamp}-{uuid.uuid4().hex[:12]}"
    destination.mkdir()
    (destination / "INCOMPLETE.txt").write_text("This acquisition did not finish. It is not a verified saved copy. Retry creates a new folder.\n", encoding="utf-8")
    return destination


def _finish(destination, entry, payload, transfer, acquisition):
    manifest = {"schema_version": 1, "format": "hearthkeeper-source-copy",
                "saved_utc": datetime.now(timezone.utc).isoformat(), "offering": entry,
                "payload": {"filename": payload.name, **transfer}, "acquisition": acquisition,
                "verification": "Observed SHA-256 and size; not publisher authentication or a gameplay test."}
    temporary = destination / "manifest.json.writing"
    with temporary.open("x", encoding="utf-8") as output:
        json.dump(manifest, output, indent=2, ensure_ascii=False)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    # A complete marker appears only after the durable payload and metadata exist.
    (destination / "INCOMPLETE.txt").unlink()
    temporary.rename(destination / "manifest.json")
    return destination


def fetch_snapshot(entry, root, *, stop=None, log=lambda line: None):
    """Resolve a moving GitHub ref once, then fetch by immutable commit identity."""
    if entry["acquisition"] != "github_snapshot":
        raise SourceError("This offering uses its download page. Archive the completed download with Import file.")
    repository = entry["repository"]
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise SourceError("Invalid GitHub repository.")
    _check_stop(stop)
    log(f"Resolving {repository} at {entry['ref']}")
    with _open(f"https://api.github.com/repos/{repository}/commits/{quote(entry['ref'], safe='')}") as response:
        raw = response.read(2 * CHUNK + 1)
    if len(raw) > 2 * CHUNK:
        raise SourceError("Unexpectedly large source revision response.")
    try:
        commit = json.loads(raw)["sha"]
    except (ValueError, KeyError, TypeError) as error:
        raise SourceError("The provider did not return a source commit.") from error
    if not re.fullmatch(r"[0-9a-f]{40}", str(commit)):
        raise SourceError("The provider did not return a valid source commit.")
    _check_stop(stop)
    destination = _begin(root, entry)
    url = f"https://api.github.com/repos/{repository}/tarball/{commit}"
    log(f"Saving source revision {commit}. This does not build or install a realm.")
    payload = destination / "source.tar.gz"
    with _open(url) as response:
        final_url = _https(response.geturl(), NETWORK_HOSTS)
        length = response.headers.get("Content-Length")
        size = int(length) if length is not None else None
        if size is not None and size > MAX_SOURCE_BYTES:
            raise SourceError("Source snapshot exceeds the 1 GiB preview limit.")
        transfer = _copy(response, payload, expected_size=size, limit=MAX_SOURCE_BYTES, stop=stop, log=log)
    with payload.open("rb") as stream:
        if stream.read(2) != b"\x1f\x8b":
            raise SourceError("The provider returned something other than a gzip source snapshot.")
    _check_stop(stop)
    return _finish(destination, entry, payload, transfer,
                   {"method": "github_snapshot", "repository": repository,
                    "requested_ref": entry["ref"], "commit": commit, "url": url,
                    "resolved_url": final_url,
                    "coverage": "Tracked source snapshot only. Git history, submodule contents, external/LFS assets, client files, and separately released databases are not guaranteed to be included."})


def import_file(entry, source, root, *, stop=None, log=lambda line: None):
    """Copy one explicitly chosen completed download without unpacking or launching it."""
    source = Path(source).resolve()
    if not source.is_file():
        raise SourceError("Choose one completed downloaded file, not a folder.")
    if source.suffix.casefold() in (".part", ".crdownload", ".partial", ".download"):
        raise SourceError("This looks like an unfinished browser download. Let it finish first.")
    _check_stop(stop)
    size = source.stat().st_size
    if not size:
        raise SourceError("The selected file is empty.")
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(root).free < size + 16 * CHUNK:
        raise SourceError("The archive destination does not have enough free space for a copy.")
    destination = _begin(root, entry)
    suffix = source.suffix if re.fullmatch(r"\.[A-Za-z0-9]{1,12}", source.suffix) else ".bin"
    payload = destination / ("downloaded-file" + suffix)
    log(f"Archiving selected file: {source.name}")
    with source.open("rb") as stream:
        before = os.fstat(stream.fileno())
        transfer = _copy(stream, payload, expected_size=before.st_size, stop=stop, log=log)
        after = os.fstat(stream.fileno())
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise SourceError("The source file changed during copying. Wait until downloading has finished and retry.")
    return _finish(destination, entry, payload, transfer,
                   {"method": "user_selected_file", "original_name": source.name,
                    "claimed_source_page": entry["page_url"],
                    "coverage": "User-associated file. Origin, client build, contents, and compatibility have not been inspected or verified."})


def read_saved(directory):
    directory = Path(directory)
    manifest_path = directory / "manifest.json"
    if directory.is_symlink() or manifest_path.is_symlink() or manifest_path.stat().st_size > 2 * CHUNK:
        raise SourceError("Invalid saved-copy manifest.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != "hearthkeeper-source-copy" or manifest.get("schema_version") != 1:
        raise SourceError("This is not a Hearthkeeper source copy.")
    payload = manifest["payload"]
    name = payload["filename"]
    if not re.fullmatch(r"(?:source\.tar\.gz|downloaded-file\.[A-Za-z0-9]{1,12})", name):
        raise SourceError("Invalid saved payload path.")
    if not re.fullmatch(r"[0-9a-f]{64}", payload["sha256"]) or type(payload["bytes"]) is not int or payload["bytes"] <= 0:
        raise SourceError("Invalid saved checksum or size.")
    if (directory / name).is_symlink():
        raise SourceError("A saved payload must not be a symbolic link.")
    return manifest


def list_saved(root):
    copies, errors = [], []
    for path in sorted(Path(root).glob("*/manifest.json"), reverse=True):
        try:
            manifest = read_saved(path.parent)
            # Required display values are validated here so a corrupt copy cannot break the page.
            if not all(isinstance(value, str) for value in
                       (manifest["offering"]["name"], manifest["saved_utc"], manifest["acquisition"]["method"])):
                raise SourceError("Missing saved-copy details.")
            copies.append((path.parent, manifest))
        except (OSError, ValueError, KeyError, TypeError, SourceError) as error:
            errors.append(f"{path.parent.name}: {error}")
    return copies, errors


def verify_saved(directory, *, stop=None):
    manifest = read_saved(directory)
    payload = manifest["payload"]
    checksum, size = hashlib.sha256(), 0
    with (Path(directory) / payload["filename"]).open("rb") as stream:
        while chunk := stream.read(CHUNK):
            _check_stop(stop)
            checksum.update(chunk)
            size += len(chunk)
    _check_stop(stop)
    if size != payload["bytes"] or checksum.hexdigest() != payload["sha256"]:
        raise SourceError("Saved copy differs from its recorded checksum or size.")
    return f"Bytes match the saved SHA-256 ({size:,} bytes). This checks preservation, not origin, client build, or playability."
