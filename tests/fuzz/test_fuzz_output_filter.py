from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from mohizarbot.security.output_filter import filter_output


@settings(max_examples=500)
@given(st.text(), st.lists(st.text(), max_size=3))
def test_filter_output_never_raises(text: str, secrets: list[str]) -> None:
    result = filter_output(text, secrets=secrets)
    assert result is not None


@settings(max_examples=500)
@given(st.text(), st.lists(st.text(), max_size=3))
def test_filter_output_blocked_is_bool(text: str, secrets: list[str]) -> None:
    result = filter_output(text, secrets=secrets)
    assert isinstance(result.blocked, bool)


@settings(max_examples=500)
@given(st.text(), st.lists(st.text(), max_size=3))
def test_filter_output_reasons_is_list_of_str(text: str, secrets: list[str]) -> None:
    result = filter_output(text, secrets=secrets)
    assert isinstance(result.reasons, list)
    for r in result.reasons:
        assert isinstance(r, str)


@settings(max_examples=500)
@given(st.text())
def test_filter_output_result_has_text(text: str) -> None:
    result = filter_output(text)
    assert isinstance(result.text, str)
