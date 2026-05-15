from __future__ import annotations

import hashlib
import hmac
import time

TOKEN_TTL = 480  # 8 minutes
_tokens: dict[str, dict[str, object]] = {}


def _sign(data: str, key: bytes) -> str:
    return hmac.digest(key, data.encode(), hashlib.sha256).hex()


def queue_confirmation(
    intent_json: str,
    chat_id: int,
    user_id: int,
    *,
    hmac_key: bytes,
) -> str:
    """Queue a high-risk intent for confirmation.

    Returns a signed HMAC token to embed in the callback button.
    """
    expires = time.monotonic() + TOKEN_TTL
    payload = f"{intent_json}|{chat_id}|{user_id}|{expires:.6f}"
    signature = _sign(payload, hmac_key)
    token = f"{signature}:{chat_id}:{user_id}:{int(expires)}"

    _tokens[token] = {
        "intent_json": intent_json,
        "chat_id": chat_id,
        "user_id": user_id,
        "expires": expires,
        "used": False,
    }
    return token


def resolve_confirmation(
    token: str,
    resolving_user_id: int,
    approved: bool,
    *,
    hmac_key: bytes,
) -> dict[str, object] | None:
    """Resolve a confirmation token.

    Returns the intent dict if approved and valid, None if denied/invalid.
    """
    if token not in _tokens:
        return None

    entry = _tokens[token]

    # Check expiry
    if time.monotonic() > float(str(entry["expires"])):
        _tokens.pop(token, None)
        return None

    # Check already used
    if entry["used"]:
        return None

    # Verify HMAC
    parts = token.split(":", 3)
    if len(parts) != 4:
        return None
    expected_sig = parts[0]
    payload = f"{entry['intent_json']}|{entry['chat_id']}|{entry['user_id']}|{entry['expires']:.6f}"
    actual_sig = _sign(payload, hmac_key)
    if not hmac.compare_digest(expected_sig, actual_sig):
        return None

    # Verify user is in the chat (always true for private chats, checked in group)
    chat_id_val = int(str(entry["chat_id"]))
    if chat_id_val == 0:
        return None

    if not approved:
        _tokens.pop(token, None)
        return None

    # Mark used
    entry["used"] = True
    _tokens.pop(token, None)

    import json

    result: dict[str, object] = json.loads(str(entry["intent_json"]))
    return result


def clear_tokens() -> None:
    """Clear all pending tokens (for tests)."""
    _tokens.clear()
