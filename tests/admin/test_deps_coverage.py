from __future__ import annotations

from mohizarbot.admin.deps import _sign, _verify


def test_sign_and_verify_roundtrip() -> None:
    signed = _sign("42:1234567890")
    result = _verify(signed)
    assert result == 42


def test_verify_invalid_signature() -> None:
    signed = _sign("42:1234567890")
    # Tamper with the signature
    tampered = "aabbccddeeff00112233445566778899:" + signed.split(":", 1)[1]
    result = _verify(tampered)
    assert result is None


def test_verify_malformed_no_colon() -> None:
    result = _verify("just_a_string")
    assert result is None


def test_verify_malformed_empty_parts() -> None:
    signed = _sign("42:1234567890")
    # Just signature, no data
    result = _verify(signed.split(":", 1)[0] + ":")
    assert result is None
