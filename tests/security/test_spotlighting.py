from __future__ import annotations

from mohizarbot.security.spotlighting import spotlight, unspotlight


def test_spotlight_replaces_spaces() -> None:
    result = spotlight("hello world")
    assert result == "hello‹world"


def test_spotlight_replaces_all_spaces() -> None:
    result = spotlight("a b c d")
    assert result == "a‹b‹c‹d"


def test_spotlight_preserves_non_space_chars() -> None:
    result = spotlight("hello, world! 123")
    assert "," in result
    assert "!" in result
    assert "123" in result
    assert " " not in result


def test_spotlight_empty_string() -> None:
    assert spotlight("") == ""


def test_spotlight_no_spaces() -> None:
    assert spotlight("nospaces") == "nospaces"


def test_unspotlight_restores_spaces() -> None:
    original = "hello world from mohizarbot"
    assert unspotlight(spotlight(original)) == original


def test_unspotlight_empty_string() -> None:
    assert unspotlight("") == ""


def test_unspotlight_no_markers() -> None:
    assert unspotlight("nospaces") == "nospaces"


def test_roundtrip_preserves_original() -> None:
    original = "this is a test with multiple spaces"
    assert unspotlight(spotlight(original)) == original


def test_spotlight_char_is_u2039() -> None:
    assert "‹" == "‹"
