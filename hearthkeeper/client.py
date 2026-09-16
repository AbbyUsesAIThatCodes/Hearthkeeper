"""Inspect and launch an original Windows WoW client without executing it to identify it."""
from dataclasses import dataclass
from datetime import datetime, timezone
import ctypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

EXPECTED_VERSION = (3, 3, 5, 12340)
LOCALES = ('enUS', 'enGB', 'deDE', 'frFR', 'esES', 'esMX', 'ruRU', 'koKR', 'zhCN', 'zhTW')


class ClientError(ValueError):
    pass


@dataclass(frozen=True)
class GameClient:
    executable: Path
    locale: str
    version: tuple

    @property
    def realmlist(self):
        return self.executable.parent / 'Data' / self.locale / 'realmlist.wtf'


def windows_file_version(path):
    """Read PE version metadata using Windows APIs; never run the selected program."""
    if os.name != 'nt':
        raise ClientError('Game launching currently supports Windows. Realm and archive tools remain available here.')
    from ctypes import wintypes
    version = ctypes.WinDLL('version', use_last_error=True)
    version.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
    version.GetFileVersionInfoSizeW.restype = wintypes.DWORD
    version.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    version.GetFileVersionInfoW.restype = wintypes.BOOL
    version.VerQueryValueW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT)]
    version.VerQueryValueW.restype = wintypes.BOOL
    size = version.GetFileVersionInfoSizeW(str(path), None)
    if not size or size > 16 * 1024 * 1024:
        raise ClientError('The executable has no readable Windows version information. Choose the original Wow.exe.')
    buffer = ctypes.create_string_buffer(size)
    pointer, length = ctypes.c_void_p(), wintypes.UINT()
    if not version.GetFileVersionInfoW(str(path), 0, size, buffer) or not version.VerQueryValueW(buffer, '\\', ctypes.byref(pointer), ctypes.byref(length)) or length.value < 52:
        raise ClientError('Could not read the executable version. Choose the original Wow.exe.')
    fields = ctypes.cast(pointer, ctypes.POINTER(wintypes.DWORD))
    if fields[0] != 0xFEEF04BD:
        raise ClientError('The executable version record is invalid.')
    return (fields[2] >> 16, fields[2] & 65535, fields[3] >> 16, fields[3] & 65535)


def inspect_client(executable, locale=None, *, version_reader=None):
    path = Path(executable).expanduser().resolve()
    if not path.is_file() or path.name.casefold() != 'wow.exe':
        raise ClientError('Choose Wow.exe inside your original Wrath of the Lich King installation.')
    version = (version_reader or windows_file_version)(path)
    if tuple(version) != EXPECTED_VERSION:
        raise ClientError('This realm needs 3.3.5a / build 12340. Selected executable reports ' + '.'.join(map(str, version)) + '.')
    for name in ('lichking.MPQ', 'patch-3.MPQ'):
        if not (path.parent / 'Data' / name).is_file():
            raise ClientError('The client is missing Data/' + name + '. Select a complete installation.')
    locales = [name for name in LOCALES if (path.parent / 'Data' / name).is_dir()]
    if locale is None:
        if len(locales) != 1:
            raise ClientError('Choose the language folder for this client; more than one or no supported locale was found.')
        locale = locales[0]
    if locale not in locales:
        raise ClientError('The selected language folder is missing from this installation.')
    return GameClient(path, locale, tuple(version))


def realm_address_matches(client):
    try:
        content = client.realmlist.read_text(encoding='utf-8-sig')
    except (OSError, UnicodeError):
        return False
    addresses = re.findall(r'^\s*set\s+realmlist\s+([^\r\n]+)', content, re.I | re.M)
    return bool(addresses) and all(value.strip().strip('"').casefold() == '127.0.0.1' for value in addresses)


def prepare_realmlist(client):
    """Explicit UI action: preserve the exact old bytes before setting local connection."""
    path = client.realmlist
    if realm_address_matches(client):
        return None
    backup = None
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        backup = path.with_name(path.name + '.hearthkeeper-' + stamp + '.bak')
        # Exclusive creation: an existing backup is never replaced.
        with backup.open('xb') as output:
            try:
                with path.open('rb') as source:
                    shutil.copyfileobj(source, output)
                output.flush()
                os.fsync(output.fileno())
            except BaseException:
                output.close()
                backup.unlink(missing_ok=True)
                raise
    descriptor, temporary = tempfile.mkstemp(prefix='realmlist-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8', newline='\n') as output:
            output.write('set realmlist 127.0.0.1\n')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return backup


def services_ready(rows):
    states = {row.get('Service'): row for row in rows}
    return all(states.get(name, {}).get('State') == 'running' and states.get(name, {}).get('Health') == 'healthy'
               for name in ('database', 'auth', 'world'))


def start_for_play(realm, executable, locale):
    """Validate again at click time, then use the existing start/health-check workflow."""
    client = inspect_client(executable, locale)
    if not realm_address_matches(client):
        raise ClientError('Connect this game installation to the local realm before playing.')
    if realm.config['phase'] != 'installed':
        raise ClientError('Finish installing this realm first. Use Install / Resume in Realm tools.')
    realm.runner.log('Checking realm services…')
    if not services_ready(realm.status()):
        realm.runner.log('Starting the realm; waiting for database, login, and world services…')
        realm.start()
    if realm.runner.stop_after_step.is_set():
        raise ClientError('Play was cancelled before launching the game. The realm may still be running.')
    if not services_ready(realm.status()):
        raise ClientError('The realm is not ready yet. Check Activity or refresh its status; the game was not launched.')
    return client


def launch_client(client):
    # Re-check immediately before launch in case files or version changed during startup.
    current = inspect_client(client.executable, client.locale)
    if not realm_address_matches(current):
        raise ClientError('The realm address changed during startup. Connect the installation again.')
    return subprocess.Popen([str(current.executable)], cwd=str(current.executable.parent),
                            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
