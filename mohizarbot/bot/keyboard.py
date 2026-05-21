from __future__ import annotations

import hashlib
import hmac
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class InlineButton:
    text: str
    callback_data: str  # raw (unsigned) payload — signed when building the keyboard
    url: str | None = None


def _sign_callback(payload: str, key: bytes) -> str:
    """HMAC-SHA256 sign a callback payload.

    Format: <signature_hex>:<base64url_payload>
    """
    sig = hmac.digest(key, payload.encode(), hashlib.sha256).hex()
    return f"{sig}:{payload}"


def verify_callback(signed: str, key: bytes) -> str | None:
    """Verify and extract the raw payload from a signed callback string.

    Returns the raw payload if valid, None if tampered/invalid.
    """
    parts = signed.split(":", 1)
    if len(parts) != 2:
        return None
    sig, payload = parts
    expected = hmac.digest(key, payload.encode(), hashlib.sha256).hex()
    if not hmac.compare_digest(expected, sig):
        return None
    return payload


def build_inline_keyboard(
    buttons: list[list[InlineButton]],
    hmac_key: bytes,
) -> dict[str, object]:
    """Build an InlineKeyboardMarkup dict from button rows.

    Every callback_data is HMAC-signed. Unsigned callbacks are never
    produced — the caller must provide a valid hmac_key.
    """
    inline_keyboard: list[list[dict[str, object]]] = []

    for row in buttons:
        row_buttons: list[dict[str, object]] = []
        for btn in row:
            btn_dict: dict[str, object] = {"text": btn.text}
            if btn.url is not None:
                btn_dict["url"] = btn.url
            if btn.callback_data:
                btn_dict["callback_data"] = _sign_callback(btn.callback_data, hmac_key)
            row_buttons.append(btn_dict)
        inline_keyboard.append(row_buttons)

    return {"inline_keyboard": inline_keyboard}
