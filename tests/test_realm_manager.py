import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from hearthkeeper.server.manager import (ManagedRealm, RealmError, Runner, compose_document,
    create_realm, local_docker, operation_lock, validate_server_data)
from hearthkeeper.server.accounts import registration


class RealmManagerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "game $literal data"
        for folder in ("dbc", "maps", "vmaps", "mmaps"):
            (self.source / folder).mkdir(parents=True)
        for name in ("Map.dbc", "Spell.dbc", "CharStartOutfit.dbc"):
            (self.source / "dbc" / name).write_bytes(b"WDBC" + struct.pack("<4I", 1, 1, 4, 1) + bytes(5))
        for name in ("maps/test.map", "vmaps/test.vmtree", "mmaps/test.mmtile"):
            (self.source / name).write_bytes(b"fixture-only")
        self.realm = create_realm(self.root / "realm", name="Test Realm", data_path=self.source,
                                  data_kind="prepared", docker_context="default")

    def test_generated_compose_confines_services_and_never_mounts_docker_socket(self):
        document = compose_document(self.realm.config)
        services = document["services"]
        self.assertNotIn("ports", services["database"])
        for name in ("world", "auth"):
            self.assertTrue(all(port.startswith("127.0.0.1:") for port in services[name]["ports"]))
            self.assertNotIn(".:/realm", services[name]["volumes"])
            self.assertNotIn("privileged", services[name])
        self.assertTrue(services["extract"]["volumes"][1]["read_only"])
        self.assertNotIn("docker.sock", json.dumps(document))
        self.assertNotIn("client-data-init", json.dumps(document))

    def test_source_is_unchanged_and_existing_realms_are_not_replaced(self):
        before = {str(path): path.read_bytes() for path in self.source.rglob("*") if path.is_file()}
        self.realm.prepare_bundle()
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.source.rglob("*") if path.is_file()})
        self.assertIn("$$literal", (self.realm.path / "compose.json").read_text())
        with self.assertRaises(FileExistsError):
            create_realm(self.realm.path, name="Other", data_path=self.source, data_kind="prepared", docker_context="default")
        self.assertEqual(ManagedRealm(self.realm.path).config["name"], "Test Realm")
        self.assertFalse(any(path.name == "realm.json" for path in (self.realm.path / "bundle").rglob("*")))

    def test_different_source_revision_is_not_silently_upgraded(self):
        config = copy.deepcopy(self.realm.config)
        config["pins"]["sources"][0]["commit"] = "0" * 40
        (self.realm.path / "realm.json").write_text(json.dumps(config))
        with self.assertRaisesRegex(RealmError, "different source lock"):
            ManagedRealm(self.realm.path)

    def test_incomplete_dbc_and_unfinished_install_cannot_start(self):
        (self.source / "dbc/Map.dbc").write_bytes(b"WDBC")
        with self.assertRaisesRegex(RealmError, "Truncated"):
            validate_server_data(self.source)
        with patch.object(self.realm, "check") as check:
            with self.assertRaisesRegex(RealmError, "Finish Install"):
                self.realm.start()
            check.assert_not_called()

    def test_failed_import_never_reports_installed_or_runs_extraction(self):
        commands = []
        def control(command, payload=None):
            commands.append(command)
            if command == "import":
                raise RealmError("fixture import failure")
        with patch.object(self.realm, "check"), patch.object(self.realm, "status", return_value=[]), patch.object(self.realm, "compose") as compose, patch.object(self.realm, "control", side_effect=control):
            with self.assertRaisesRegex(RealmError, "fixture import failure"):
                self.realm.install()
            self.assertNotEqual(ManagedRealm(self.realm.path).config["phase"], "installed")
            self.assertFalse(any("extract" in call.args for call in compose.call_args_list))

    def test_backup_refuses_a_world_that_did_not_stop(self):
        with patch.object(self.realm, "check"), patch.object(self.realm, "compose"), patch.object(self.realm, "status", return_value=[{"Service": "world", "State": "running"}]), patch.object(self.realm, "control") as control:
            with self.assertRaisesRegex(RealmError, "must be stopped"):
                self.realm.backup()
            control.assert_not_called()

    def test_operation_lock_blocks_a_second_process_and_releases(self):
        code = "from hearthkeeper.server.manager import operation_lock\nimport sys\nwith operation_lock(sys.argv[1]): print('acquired')"
        with operation_lock(self.realm.path):
            blocked = subprocess.run([sys.executable, "-c", code, str(self.realm.path)], capture_output=True, text=True)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("Another Hearthkeeper", blocked.stderr)
        allowed = subprocess.run([sys.executable, "-c", code, str(self.realm.path)], capture_output=True, text=True)
        self.assertEqual(allowed.returncode, 0)

    def test_remote_docker_is_rejected_before_connecting(self):
        class FakeRunner:
            def run(self, args, **kwargs):
                if "show" in args:
                    return "remote"
                if "inspect" in args:
                    return "ssh://example.invalid"
                self.fail = True
                raise AssertionError("Should not connect")
        with patch("shutil.which", return_value="docker"), self.assertRaisesRegex(RealmError, "Remote Docker"):
            local_docker(FakeRunner())

    def test_runner_uses_argument_boundaries_redacts_and_stops_between_steps(self):
        lines = []
        runner = Runner(lines.append); runner.redactions = ["fictional-secret"]
        output = runner.run([sys.executable, "-c", "import sys;print(sys.argv[1])", "fictional-secret; $(never-execute)"])
        self.assertEqual(output, "[redacted]; $(never-execute)")
        runner.stop_after_step.set()
        with patch("subprocess.Popen") as launch, self.assertRaisesRegex(RealmError, "Stopped between"):
            runner.run(["never-execute"])
        launch.assert_not_called()

    def test_account_registration_rejects_unsupported_client_input(self):
        for username, password in (("bad name", "test"), ("valid", "x" * 17), ("valid", "password with spaces")):
            with self.assertRaises(ValueError):
                registration(username, password)


if __name__ == "__main__":
    unittest.main()
