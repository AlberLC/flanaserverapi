import hashlib
import math
import secrets
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from config import config


def create_id(length: int = config.id_length) -> str:
    return secrets.token_urlsafe(math.ceil(length * 3 / 4))[:length]


def decrypt(data: bytes, key: bytes | None = None) -> bytes:
    if not key:
        key = config.symmetric_key

    return Fernet(key).decrypt(data)


def encrypt(data: bytes, key: bytes | None = None) -> bytes:
    if not key:
        key = config.symmetric_key

    return Fernet(key).encrypt(data)


def hash_file(path: Path, algorithm: str = 'sha256') -> str:
    with path.open('rb') as file:
        return hashlib.file_digest(file, algorithm).hexdigest()


def sign(data: bytes, key: Ed25519PrivateKey | None = None) -> bytes:
    if not key:
        key = Ed25519PrivateKey.from_private_bytes(config.private_key)

    return key.sign(data)


def verify(data: bytes, signature: bytes, key: Ed25519PublicKey | None = None) -> None:
    if not key:
        key = Ed25519PublicKey.from_public_bytes(config.public_key)

    key.verify(signature, data)
