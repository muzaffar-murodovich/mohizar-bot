from __future__ import annotations

import re
import secrets

_SPAN_RE = re.compile(r"</?user_message[^>]*>", re.IGNORECASE)

_ESCAPE_TABLE = str.maketrans(
    {
        "<": "＜",  # Fullwidth less-than
        ">": "＞",  # Fullwidth greater-than
    }
)


def generate_session_token() -> str:
    """Return a 64-char hex session token used to identify this LLM invocation."""
    return secrets.token_hex(32)


def escape_user_content(text: str) -> str:
    """Replace angle brackets in user text with Unicode look-alikes.

    This prevents an attacker from closing the <user_message> wrapper
    by injecting "</user_message>" into the body.
    """
    return text.translate(_ESCAPE_TABLE)


def contains_wrapper_tags(text: str) -> bool:
    """Check if text contains raw <user_message> or </user_message> patterns."""
    return bool(_SPAN_RE.search(text))


def wrap_untrusted_content(
    content: str,
    tag: str,
    *,
    session_token: str | None = None,
    **attrs: str | int,
) -> str:
    """Wrap untrusted content in a tagged block with session token and attributes.

    Args:
        content: The (already-escaped) user text.
        tag: The tag name (e.g. "user_message", "group_message").
        session_token: Optional session token to include as an attribute.
        **attrs: Additional attributes rendered as key="value" pairs.

    Returns:
        A string like:
        <user_message session_token="abc123" from_user_id="42">...escaped content...</user_message>
    """
    attr_parts = []
    if session_token is not None:
        attr_parts.append(f'session_token="{session_token}"')
    for key, value in attrs.items():
        attr_parts.append(f'{key}="{value}"')

    attr_str = " " + " ".join(attr_parts) if attr_parts else ""
    return f"<{tag}{attr_str}>{content}</{tag}>"
