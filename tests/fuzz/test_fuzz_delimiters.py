from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from mohizarbot.security.untrusted import generate_session_token, wrap_untrusted


@settings(max_examples=500)
@given(st.text())
def test_wrap_untrusted_always_has_exactly_one_opening_tag(text: str) -> None:
    kind = "user_message"
    token = generate_session_token()
    result = wrap_untrusted(kind, text, session_token=token, from_user_id=42)
    # Count the opening tag for this kind
    open_tag = f"<{kind}"
    assert result.count(open_tag) == 1, f"Expected exactly 1 opening tag, got: {result!r}"


@settings(max_examples=500)
@given(st.text())
def test_wrap_untrusted_always_has_exactly_one_closing_tag(text: str) -> None:
    kind = "user_message"
    token = generate_session_token()
    result = wrap_untrusted(kind, text, session_token=token, from_user_id=42)
    close_tag = f"</{kind}>"
    assert result.count(close_tag) == 1, f"Expected exactly 1 closing tag, got: {result!r}"


@settings(max_examples=500)
@given(st.text())
def test_wrap_untrusted_starts_with_opening_tag(text: str) -> None:
    kind = "group_message"
    result = wrap_untrusted(kind, text)
    assert result.startswith(f"<{kind}"), f"Expected to start with <{kind}>, got: {result[:50]!r}"


@settings(max_examples=500)
@given(st.text())
def test_wrap_untrusted_ends_with_closing_tag(text: str) -> None:
    kind = "web_content"
    result = wrap_untrusted(kind, text)
    assert result.endswith(f"</{kind}>"), f"Expected to end with </{kind}>, got: {result[-50:]!r}"
