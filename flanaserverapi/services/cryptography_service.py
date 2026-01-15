from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from config import config


def decrypt(data: bytes, key: bytes | None = None) -> bytes:
    if not key:
        key = config.symmetric_key

    return Fernet(key).decrypt(data)


def encrypt(data: bytes, key: bytes | None = None) -> bytes:
    if not key:
        key = config.symmetric_key

    return Fernet(key).encrypt(data)


def sign(data: bytes, key: Ed25519PrivateKey | None = None) -> bytes:
    if not key:
        key = Ed25519PrivateKey.from_private_bytes(config.private_key)

    return key.sign(data)
