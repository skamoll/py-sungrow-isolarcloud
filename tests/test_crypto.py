"""Tests for iSolarCloud wire cryptography."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from custom_components.py_sungrow_isolarcloud.api.crypto import (
    aes_decrypt_hex,
    aes_encrypt_hex,
    current_gmt_header,
    generate_aes_key,
    rsa_encrypt_base64,
)


def test_aes_roundtrip() -> None:
    """AES-256-ECB hex encryption and decryption roundtrip."""
    key = generate_aes_key()
    assert len(key) == 32
    assert key.startswith("web")

    plaintext = '{"ps_id":"6116893","lang":"_en_US"}'
    encrypted = aes_encrypt_hex(plaintext, key)
    assert encrypted != plaintext
    assert aes_decrypt_hex(encrypted, key) == plaintext


def test_rsa_encrypt_base64() -> None:
    """RSA PKCS#1 v1.5 encryption produces valid base64 ciphertext."""
    import base64

    key = generate_aes_key()
    out = rsa_encrypt_base64(key)
    raw = base64.b64decode(out)
    assert len(raw) == 128


def test_current_gmt_header() -> None:
    """Timezone header formats positive and negative UTC offsets."""
    pos = datetime(2026, 11, 23, 0, 0, tzinfo=timezone(timedelta(hours=2)))
    neg = datetime(2026, 11, 23, 0, 0, tzinfo=timezone(timedelta(hours=-5)))
    utc = datetime(2026, 11, 23, 0, 0, tzinfo=UTC)

    assert current_gmt_header(pos) == "GMT%2B2"
    assert current_gmt_header(neg) == "GMT-5"
    assert current_gmt_header(utc) == "GMT%2B0"
