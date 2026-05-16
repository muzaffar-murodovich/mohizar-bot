from __future__ import annotations

import hashlib
import hmac

from fastapi import Cookie, HTTPException, Request

_SESSION_SECRET = b"admin-session-hmac-key-32-bytes"


def _sign(value: str) -> str:
    sig = hmac.digest(_SESSION_SECRET, value.encode(), hashlib.sha256).hex()
    return f"{value}:{sig}"


def _verify(signed: str) -> int | None:
    parts = signed.rsplit(":", 1)
    if len(parts) != 2:
        return None
    value, sig = parts
    expected = hmac.digest(_SESSION_SECRET, value.encode(), hashlib.sha256).hex()
    if not hmac.compare_digest(expected, sig):
        return None
    parts2 = value.split(":")
    if len(parts2) < 1:
        return None
    return int(parts2[0])


def set_session_cookie(response: object, user_id: int) -> None:
    import time

    expiry = int(time.time()) + 28800  # 8h
    value = f"{user_id}:{expiry}"
    signed = _sign(value)
    # httponly + samesite=strict
    response.set_cookie = response.set_cookie
    response.set_cookie(  # type: ignore[union-attr]
        key="mohizar_session",
        value=signed,
        httponly=True,
        samesite="strict",
        max_age=28800,
    )


def require_admin(
    request: Request,
    mohizar_session: str = Cookie(default=""),
) -> bool:
    from mohizarbot.config import Settings

    settings = Settings()  # type: ignore[call-arg]
    admin_ids = settings.admin_user_ids

    if not mohizar_session:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

    user_id = _verify(mohizar_session)
    if user_id is None:
        raise HTTPException(status_code=302, headers={"Location": "/login"})

    if admin_ids and user_id not in admin_ids:
        raise HTTPException(status_code=403, detail="Not an admin")

    request.state.admin_user_id = user_id
    return True
