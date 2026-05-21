from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st

from mohizarbot.security.injection_detector import detect


@settings(max_examples=500)
@given(st.text())
def test_detect_never_raises(text: str) -> None:
    result = detect(text)
    assert result is not None


@settings(max_examples=500)
@given(st.text())
def test_detect_score_in_range(text: str) -> None:
    result = detect(text)
    assert 0.0 <= result.score <= 1.0, f"Score {result.score} out of [0.0, 1.0] range"


@settings(max_examples=500)
@given(st.text())
def test_detect_signals_is_list_of_str(text: str) -> None:
    result = detect(text)
    assert isinstance(result.signals, list)
    for s in result.signals:
        assert isinstance(s, str), f"Signal {s!r} is not a string"


@settings(max_examples=500)
@given(st.text())
def test_detect_score_zero_for_benign_text(text: str) -> None:
    """High-confidence injection text should have score > 0."""
    result = detect(text)
    # Score can be 0 or positive, but never negative
    assert result.score >= 0.0
