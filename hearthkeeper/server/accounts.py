"""Original 3.3.5a account registration; matches AzerothCore's SRP6 parameters."""
import hashlib
import re
import secrets


def registration(username, password, salt=None):
    if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", username):
        raise ValueError("Account names need 1–16 letters, numbers, or underscores.")
    if not re.fullmatch(r"[\x21-\x7e]{1,16}", password):
        raise ValueError("This 3.3.5a client needs a password of 1–16 ASCII characters without spaces.")
    username = username.upper()
    salt = secrets.token_bytes(32) if salt is None else salt
    if len(salt) != 32:
        raise ValueError("SRP salt must be 32 bytes")
    identity = hashlib.sha1((username + ":" + password.upper()).encode("ascii")).digest()
    exponent = int.from_bytes(hashlib.sha1(salt + identity).digest(), "little")
    modulus = int("894B645E89E1535BBDAD5B8B290650530801B18EBFBF5E8FAB3C82872A3E9BB7", 16)
    verifier = pow(7, exponent, modulus).to_bytes(32, "little")
    return username, salt, verifier
