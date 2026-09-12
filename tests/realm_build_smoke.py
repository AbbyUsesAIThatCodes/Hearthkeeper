"""Dedicated CI realm: compile real sources, import real SQL, and test auth without game assets."""
import hashlib
import json
import os
from pathlib import Path
import secrets
import socket
import struct
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hearthkeeper.server.manager import ManagedRealm, RealmError, Runner, create_realm, local_docker

ROOT = Path("var/ci-realm")


def authenticate(username, password):
    """An independent wire-level client checks registration against the real authserver."""
    def sha(data):
        return hashlib.sha1(data).digest()

    with socket.create_connection(("127.0.0.1", 3724), timeout=20) as connection:
        def receive(count):
            result = b""
            while len(result) < count:
                part = connection.recv(count - len(result))
                if not part:
                    raise AssertionError("Auth connection closed early")
                result += part
            return result

        identity = username.upper().encode()
        challenge = (b"WoW\0" + bytes([3, 3, 5]) + struct.pack("<H", 12340) + b"68x\0niW\0SUne"
                     + bytes(8) + bytes([len(identity)]) + identity)
        connection.sendall(struct.pack("<BBH", 0, 0, len(challenge)) + challenge)
        assert receive(3) == bytes(3), "Auth challenge was rejected"
        public_b = receive(32)
        generator = receive(receive(1)[0])
        modulus_bytes = receive(receive(1)[0])
        salt = receive(32)
        receive(16)
        assert receive(1) == b"\0", "Unexpected account security flags"
        modulus = int.from_bytes(modulus_bytes, "little")
        private_a = int.from_bytes(secrets.token_bytes(32), "little")
        public_a = pow(int.from_bytes(generator, "little"), private_a, modulus).to_bytes(32, "little")
        secret_x = int.from_bytes(sha(salt + sha(identity + b":" + password.upper().encode())), "little")
        scramble = int.from_bytes(sha(public_a + public_b), "little")
        shared = pow((int.from_bytes(public_b, "little") - 3 * pow(7, secret_x, modulus)) % modulus,
                     private_a + scramble * secret_x, modulus).to_bytes(32, "little")
        offset = next((index for index, value in enumerate(shared) if value), len(shared))
        offset += offset % 2
        even, odd = sha(shared[offset::2]), sha(shared[offset + 1::2])
        session = bytes(value for pair in zip(even, odd) for value in pair)
        xor = bytes(left ^ right for left, right in zip(sha(modulus_bytes), sha(generator)))
        proof = sha(xor + sha(identity) + salt + public_a + public_b + session)
        connection.sendall(b"\x01" + public_a + proof + bytes(22))
        assert receive(2) == b"\x01\0", "Real authserver rejected the SRP account proof"
        assert receive(20) == sha(public_a + proof + session), "Authserver proof did not match"
        receive(10)
    print("Actual AzerothCore authentication passed (build 12340 SRP exchange).", flush=True)


def prepare():
    runner = Runner(print)
    prerequisites = local_docker(runner)
    data = Path("var/ci-placeholder-data")
    for name in ("dbc", "maps", "vmaps", "mmaps"):
        (data / name).mkdir(parents=True, exist_ok=True)
    for name in ("Map.dbc", "Spell.dbc", "CharStartOutfit.dbc"):
        (data / "dbc" / name).write_bytes(b"WDBC" + struct.pack("<4I", 1, 1, 4, 1) + bytes(5))
    for name in ("maps/placeholder.map", "vmaps/placeholder.vmtree", "mmaps/placeholder.mmtile"):
        (data / name).write_bytes(b"FICTIONAL CI PLACEHOLDER; NEVER LAUNCH A WORLD WITH THIS")
    realm = create_realm(ROOT, name="CI Only", data_path=data, data_kind="prepared",
                         docker_context=prerequisites["context"])
    realm.prepare_bundle()
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write("image=" + realm.config["project"] + ":0.1.0a2\n")


def probe():
    realm = ManagedRealm(ROOT, Runner(print))
    try:
        realm.control("configure")
        realm.compose("up", "-d", "--wait", "--wait-timeout", "300", "database")
        realm.control("bootstrap")
        realm.control("import")
        realm.control("finalize")
        realm.create_account("CITEST", "CI-proof-only")
        realm.compose("up", "-d", "--no-build", "--wait", "--wait-timeout", "180", "auth")
        authenticate("CITEST", "CI-proof-only")
        observed = []
        original_log = realm.runner.log
        realm.runner.log = lambda line: (observed.append(line), original_log(line))
        try:
            # No data is copied into /realm/server-data. The real world binary
            # must initialize the Playerbots database and then reject missing maps.
            realm.compose("run", "--rm", "--no-deps", "-T", "world")
        except RealmError:
            assert any("Failed to find map files for starting areas" in line for line in observed), "World failed before reaching the expected missing-map boundary"
        else:
            raise AssertionError("World unexpectedly accepted missing game data")
        finally:
            realm.runner.log = original_log
        print("World initialized its databases and correctly rejected missing game maps.")
        rows = realm.control("characters")
        assert "[]" in rows, "Expected an empty real character schema"
        result = realm.backup()
        assert "BACKUP:" in result
        print("Real core/module SQL import, account creation, authentication and backup completed.")
        print("No game assets used; extraction, world startup and in-game play remain unverified.")
    finally:
        realm.compose("logs", "--tail", "50", "auth")
        realm.compose("stop", "--timeout", "120")


if __name__ == "__main__":
    {"prepare": prepare, "probe": probe}[sys.argv[1]]()
