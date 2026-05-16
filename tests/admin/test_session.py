from __future__ import annotations

import time

from mohizarbot.admin.deps import _sign, _verify


def test_sign_and_verify() -> None:
    expiry = int(time.time()) + 3600
    value = f"12345:{expiry}"
    signed = _sign(value)
    result = _verify(signed)
    assert result == 12345


def test_tampered_session_rejected() -> None:
    signed = _sign("12345:9999999999")
    tampered = signed[:-1] + ("0" if signed[-1] != "0" else "1")
    result = _verify(tampered)
    assert result is None


def test_expired_session_not_checked_by_verify() -> None:
    """verify() checks signature only — expiry is checked at a higher level."""
    value = f"12345:{int(time.time()) - 7200}"
    signed = _sign(value)
    result = _verify(signed)
    assert result == 12345


def test_invalid_format_rejected() -> None:
    assert _verify("not-valid") is None
    assert _verify("a:b:c") is None
