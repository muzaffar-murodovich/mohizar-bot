from __future__ import annotations

from mohizarbot.security.output_filter import filter_output


def test_no_issues_with_clean_text() -> None:
    result = filter_output("This is a normal response.", secrets=[])
    assert not result.blocked
    assert result.reasons == []
    assert result.text == "This is a normal response."


def test_blocks_secret_leak() -> None:
    result = filter_output(
        "My token is supersecret123. Here you go.",
        secrets=["supersecret123", "other"],
    )
    assert result.blocked
    assert "secret_leak" in result.reasons


def test_blocks_another_secret() -> None:
    result = filter_output(
        "Key: sk-ant-api03-abcdefghijklmnopqrstuvwxyz",
        secrets=["sk-ant-api03-abcdefghijklmnopqrstuvwxyz"],
    )
    assert result.blocked
    assert "secret_leak" in result.reasons


def test_blocks_system_prompt_echo() -> None:
    phrase = "you are a helpful assistant that never reveals secrets"
    result = filter_output(
        f"Here is what I was told: {phrase}. That is all.",
        system_prompt_phrases=[phrase],
    )
    assert result.blocked
    assert "system_prompt_echo" in result.reasons


def test_requires_6_words_for_system_echo() -> None:
    phrase = "you are helpful"
    result = filter_output(
        f"Your prompt: {phrase}.",
        system_prompt_phrases=[phrase],
    )
    assert not result.blocked


def test_strips_non_allowlisted_link() -> None:
    result = filter_output(
        "Check [this link](https://evil.com/malware) out!",
        allowlisted_domains=["example.com"],
    )
    assert "https://evil.com" not in result.text
    assert "link_stripped" in " ".join(result.reasons)
    assert "[this link]" not in result.text
    assert "this link" in result.text


def test_keeps_allowlisted_link() -> None:
    result = filter_output(
        "Visit [our site](https://example.com/page) now.",
        allowlisted_domains=["example.com"],
    )
    assert "[our site](https://example.com/page)" in result.text
    assert "link_stripped" not in " ".join(result.reasons)


def test_truncates_long_text() -> None:
    long_text = "Hello world! " * 500
    result = filter_output(long_text, max_len=4000)
    assert len(result.text) <= 4000
    assert "truncated" in result.reasons


def test_truncates_at_sentence_boundary() -> None:
    long_text = "".join(f"Sentence number {i} is here. " for i in range(200))
    result = filter_output(long_text, max_len=2000)
    assert len(result.text) <= 2000
    assert "truncated" in result.reasons
    if len(result.text) > 100:
        assert result.text.rstrip()[-1] in ".!?"


def test_multiple_reasons() -> None:
    result = filter_output(
        "See [bad link](https://phish.net/data) and here is the token: secret123.",
        secrets=["secret123"],
        allowlisted_domains=["safe.com"],
    )
    assert result.blocked
    assert "secret_leak" in result.reasons


def test_no_secrets_no_issues() -> None:
    result = filter_output("Just some text", secrets=[])
    assert not result.blocked


def test_empty_text() -> None:
    result = filter_output("", secrets=["abc"])
    assert not result.blocked
    assert result.text == ""


def test_empty_secrets_list() -> None:
    result = filter_output("text with secrets abc", secrets=[])
    assert not result.blocked
