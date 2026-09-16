"""Client identity, connection preservation, and launch gating with fictional files."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch
from hearthkeeper.client import (ClientError, EXPECTED_VERSION, inspect_client, prepare_realmlist,
                                 realm_address_matches, services_ready, start_for_play, launch_client,
                                 windows_file_version)


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'Client folder with spaces'
        (self.root / 'Data' / 'enUS').mkdir(parents=True)
        for path in ('Wow.exe', 'Data/lichking.MPQ', 'Data/patch-3.MPQ'):
            (self.root / path).write_bytes(b'Fictional fixture only')
        self.version = patch('hearthkeeper.client.windows_file_version', return_value=EXPECTED_VERSION)
        self.version.start(); self.addCleanup(self.version.stop)
        self.client = inspect_client(self.root / 'Wow.exe')
        self.ready = [{'Service': name, 'State': 'running', 'Health': 'healthy'} for name in ('auth', 'world', 'database')]

    def test_rejects_wrong_version_and_incomplete_data(self):
        with self.assertRaisesRegex(ClientError, 'needs 3.3.5a'):
            inspect_client(self.root / 'Wow.exe', version_reader=lambda path: (1, 12, 1, 5875))
        (self.root / 'Data' / 'patch-3.MPQ').unlink()
        with self.assertRaisesRegex(ClientError, 'missing Data'):
            inspect_client(self.root / 'Wow.exe')

    def test_multiple_locales_require_explicit_selection(self):
        (self.root / 'Data' / 'deDE').mkdir()
        with self.assertRaisesRegex(ClientError, 'language folder'):
            inspect_client(self.root / 'Wow.exe')
        self.assertEqual(inspect_client(self.root / 'Wow.exe', 'deDE').locale, 'deDE')
        with self.assertRaises(ClientError):
            inspect_client(self.root / 'Wow.exe', '../../outside')

    def test_original_connection_bytes_preserved_and_repeat_is_idempotent(self):
        original = b'\xef\xbb\xbfset realmlist other.example\r\nset patchlist other.example\r\n'
        self.client.realmlist.write_bytes(original)
        backup = prepare_realmlist(self.client)
        self.assertEqual(backup.read_bytes(), original)
        self.assertTrue(realm_address_matches(self.client))
        self.assertIsNone(prepare_realmlist(self.client))
        self.assertEqual(len(list(self.client.realmlist.parent.glob('*.bak'))), 1)

    def test_conflicting_addresses_are_not_treated_as_connected(self):
        self.client.realmlist.write_text('set realmlist 127.0.0.1\nset realmlist other.example\n')
        self.assertFalse(realm_address_matches(self.client))
        self.client.realmlist.write_text('SET realmlist "127.0.0.1"\n')
        self.assertTrue(realm_address_matches(self.client))

    def test_backup_failure_does_not_change_connection(self):
        self.client.realmlist.write_text('set realmlist other.example\n')
        with patch('hearthkeeper.client.shutil.copyfileobj', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                prepare_realmlist(self.client)
        self.assertEqual(self.client.realmlist.read_text(), 'set realmlist other.example\n')

    def realm(self, statuses):
        realm = Mock()
        realm.config = {'phase': 'installed'}
        realm.runner.stop_after_step = threading.Event()
        realm.status.side_effect = statuses
        return realm

    def test_starts_stopped_realm_and_waits_for_health(self):
        prepare_realmlist(self.client)
        realm = self.realm([[], self.ready])
        result = start_for_play(realm, self.client.executable, 'enUS')
        realm.start.assert_called_once_with()
        self.assertEqual(result, self.client)

    def test_healthy_realm_is_not_restarted(self):
        prepare_realmlist(self.client)
        realm = self.realm([self.ready, self.ready])
        start_for_play(realm, self.client.executable, 'enUS')
        realm.start.assert_not_called()

    def test_failure_or_cancel_never_reaches_launch(self):
        prepare_realmlist(self.client)
        realm = self.realm([[], []])
        with self.assertRaisesRegex(ClientError, 'not ready'):
            start_for_play(realm, self.client.executable, 'enUS')
        realm = self.realm([[]])
        realm.start.side_effect = RuntimeError('Docker unavailable')
        with self.assertRaisesRegex(RuntimeError, 'Docker unavailable'):
            start_for_play(realm, self.client.executable, 'enUS')
        realm = self.realm([self.ready])
        realm.runner.stop_after_step.set()
        with self.assertRaisesRegex(ClientError, 'cancelled'):
            start_for_play(realm, self.client.executable, 'enUS')

    def test_client_error_prevents_server_mutations(self):
        realm = self.realm([])
        with self.assertRaisesRegex(ClientError, 'Connect'):
            start_for_play(realm, self.client.executable, 'enUS')
        realm.status.assert_not_called(); realm.start.assert_not_called()

    def test_launch_has_correct_cwd_and_no_shell(self):
        prepare_realmlist(self.client)
        with patch('subprocess.Popen') as launch:
            launch_client(self.client)
        launch.assert_called_once_with([str(self.client.executable)], cwd=str(self.root),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.client.realmlist.write_text('set realmlist other.example\n')
        with patch('subprocess.Popen') as launch:
            with self.assertRaises(ClientError):
                launch_client(self.client)
            launch.assert_not_called()

    def test_all_services_must_be_healthy(self):
        self.assertTrue(services_ready(self.ready))
        self.assertFalse(services_ready(self.ready[:-1]))
        self.ready[0]['Health'] = 'starting'
        self.assertFalse(services_ready(self.ready))

    @unittest.skipUnless(os.name == 'nt', 'Windows version APIs')
    def test_reads_actual_python_executable_metadata_without_running_it(self):
        # Direct imported function is not the patched fixture reader.
        result = windows_file_version(Path(sys.executable))
        self.assertEqual(result[:2], sys.version_info[:2])
