"""AES-256-ECB + RSA PKCS#1 v1.5 wire cryptography for iSolarCloud."""

from __future__ import annotations

import base64
import secrets
import string
from datetime import UTC, datetime

from cryptography.hazmat.primitives import padding as sym_padding
from cryptography.hazmat.primitives.asymmetric import padding as asym_padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.serialization import load_der_public_key

from .const import RSA_PUBLIC_KEY_B64URL

_ALPHANUM = string.ascii_lowercase + string.digits


def load_rsa_public_key(b64url_der: str = RSA_PUBLIC_KEY_B64URL) -> RSAPublicKey:
    """Load the iSolarCloud DER RSA public key from URL-safe base64."""
    padded = b64url_der + "=" * (-len(b64url_der) % 4)
    der = base64.urlsafe_b64decode(padded)
    key = load_der_public_key(der)
    if not isinstance(key, RSAPublicKey):
        raise TypeError("Expected an RSA public key")
    return key


def generate_aes_key() -> str:
    """Generate a 32-character AES key prefixed with 'web'."""
    suffix = "".join(secrets.choice(_ALPHANUM) for _ in range(29))
    return f"web{suffix}"


def generate_nonce(length: int = 32) -> str:
    """Generate a random alphanumeric nonce."""
    return "".join(secrets.choice(_ALPHANUM) for _ in range(length))


def generate_did() -> str:
    """Generate a 16-digit device identifier header value."""
    return "".join(secrets.choice(string.digits) for _ in range(16))


def aes_encrypt_hex(plaintext: str, key: str) -> str:
    """Encrypt UTF-8 plaintext with AES-ECB PKCS7 and return lowercase hex."""
    key_bytes = key.encode("utf-8")
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError(f"AES key must be 16/24/32 bytes, got {len(key_bytes)}")
    padder = sym_padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    encryptor = Cipher(algorithms.AES(key_bytes), modes.ECB()).encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return encrypted.hex()


def aes_decrypt_hex(cipher_hex: str, key: str) -> str:
    """Decrypt hex-encoded AES-ECB PKCS7 ciphertext to UTF-8 text."""
    key_bytes = key.encode("utf-8")
    if len(key_bytes) not in (16, 24, 32):
        raise ValueError(f"AES key must be 16/24/32 bytes, got {len(key_bytes)}")
    raw = bytes.fromhex(cipher_hex.strip())
    decryptor = Cipher(algorithms.AES(key_bytes), modes.ECB()).decryptor()
    padded = decryptor.update(raw) + decryptor.finalize()
    unpadder = sym_padding.PKCS7(128).unpadder()
    plain = unpadder.update(padded) + unpadder.finalize()
    return plain.decode("utf-8")


def rsa_encrypt_base64(plaintext: str, public_key: RSAPublicKey | None = None) -> str:
    """Encrypt plaintext using RSA PKCS#1 v1.5 and return standard base64."""
    key = public_key or load_rsa_public_key()
    encrypted = key.encrypt(plaintext.encode("utf-8"), asym_padding.PKCS1v15())
    return base64.b64encode(encrypted).decode("ascii")


def current_gmt_header(now: datetime | None = None) -> str:
    """Format the x-client-tz header matching iSolarCloud's expectation."""
    current = now or datetime.now().astimezone()
    offset = current.utcoffset()
    total_seconds = int(offset.total_seconds()) if offset is not None else 0
    hours = int(total_seconds / 3600)
    if hours >= 0:
        return f"GMT%2B{hours}"
    return f"GMT-{abs(hours)}"


def current_timestamp_ms(clock_offset_seconds: float = 0.0) -> int:
    """Return current UTC epoch milliseconds adjusted by any learned clock offset."""
    now_s = datetime.now(UTC).timestamp() + clock_offset_seconds
    return int(now_s * 1000)
