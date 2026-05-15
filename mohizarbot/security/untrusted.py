from __future__ import annotations

# Unified untrusted content wrapping (Layer 1 extended).
# Supports five kinds of untrusted input: user_message, group_message,
# memory_entry, web_content, assistant_previous_output.
import re
import secrets

_VALID_KINDS = [
    "user_message",
    "group_message",
    "memory_entry",
    "web_content",
    "assistant_previous_output",
]

ESCAPE_TABLE = str.maketrans({"<": "＜", ">": "＞"})

# Precompile per-kind regexes that match the closing tag for each kind
_END_TAG_RE = {k: re.compile(rf"</{re.escape(k)}[^>]*>", re.IGNORECASE) for k in _VALID_KINDS}


def generate_session_token() -> str:
    return secrets.token_hex(32)


def escape_content(text: str) -> str:
    """Replace angle brackets with Unicode look-alikes to prevent tag injection."""
    return text.translate(ESCAPE_TABLE)


def wrap_untrusted(
    kind: str,
    body: str,
    session_token: str | None = None,
    **attrs: str | int,
) -> str:
    """Wrap untrusted content in a tagged block.

    Args:
        kind: One of 'user_message', 'group_message', 'memory_entry',
              'web_content', 'assistant_previous_output'.
        body: Raw untrusted text (will be escaped and spotlighted).
        session_token: Optional session identifier.
        **attrs: Additional HTML-like attributes.

    Returns:
        A string like:
        <user_message session_token="abc" from_user_id="42">…escaped…</user_message>
    """
    if kind not in _END_TAG_RE:
        raise ValueError(f"Unknown untrusted kind: {kind}. Valid: {_VALID_KINDS}")

    # Escape closing tag for this specific kind within the body
    regex = _END_TAG_RE[kind]
    body = regex.sub(lambda m: m.group(0).translate(ESCAPE_TABLE), body)

    # Also escape any opening tags
    body = escape_content(body)

    attr_parts = []
    if session_token is not None:
        attr_parts.append(f'session_token="{session_token}"')
    for key, value in attrs.items():
        attr_parts.append(f'{key}="{value}"')

    attr_str = " " + " ".join(attr_parts) if attr_parts else ""
    return f"<{kind}{attr_str}>{body}</{kind}>"


def is_kind_valid(kind: str) -> bool:
    return kind in _END_TAG_RE
