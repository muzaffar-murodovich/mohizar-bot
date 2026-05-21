from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from mohizarbot.security.input_sanitizer import sanitize

ZERO_WIDTH_CHARS = set("​‌‍‎‏⁠⁡⁢⁣⁤⁦⁧⁨⁩﻿­")


@settings(max_examples=500)
@given(st.text())
def test_sanitize_never_raises(text: str) -> None:
    result = sanitize(text)
    assert isinstance(result, str)


@settings(max_examples=500)
@given(st.text())
def test_sanitize_output_not_longer_than_input(text: str) -> None:
    result = sanitize(text)
    assert len(result) <= max(len(text), 4096)


@settings(max_examples=500)
@given(st.text())
def test_sanitize_no_zero_width_chars(text: str) -> None:
    result = sanitize(text)
    for ch in result:
        assert ch not in ZERO_WIDTH_CHARS, f"Zero-width char U+{ord(ch):04X} found in output"


@settings(max_examples=500)
@given(st.text())
def test_sanitize_respects_max_len(text: str) -> None:
    result = sanitize(text, max_len=100)
    assert len(result) <= 100
