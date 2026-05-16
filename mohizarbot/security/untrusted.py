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


def wrap_group_message(
    body: str,
    *,
    from_user_id: str = "",
    username: str = "",
    is_admin: str = "false",
    is_reply_to_bot: str = "false",
    reply_to_user_id: str = "",
    forwarded_from_id: str = "",
    forwarded_from_chat_id: str = "",
    ts: str = "",
    **extra_attrs: str,
) -> str:
    """Wrap a group chat message with full attribution attributes.

    All attributes always present (empty string if unknown).
    Escape rules from Sprint 3 apply.
    """
    attrs: dict[str, str | int] = {
        "from_user_id": from_user_id,
        "username": username,
        "is_admin": is_admin,
        "is_reply_to_bot": is_reply_to_bot,
        "reply_to_user_id": reply_to_user_id,
        "forwarded_from_id": forwarded_from_id,
        "forwarded_from_chat_id": forwarded_from_chat_id,
        "ts": ts,
    }
    attrs.update(extra_attrs)
    # Filter to only string-safe values for the wrapper
    str_attrs: dict[str, str | int] = {k: str(v) for k, v in attrs.items()}
    return wrap_untrusted("group_message", body, **str_attrs)  # type: ignore[arg-type]


def is_kind_valid(kind: str) -> bool:
    return kind in _END_TAG_RE
