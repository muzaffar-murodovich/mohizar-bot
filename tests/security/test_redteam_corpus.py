from __future__ import annotations

import glob
import os

import pytest
import yaml


def _load_all_payloads() -> list[dict]:
    corpus_dir = os.path.join(os.path.dirname(__file__), "corpus")
    payloads: list[dict] = []
    for filepath in sorted(glob.glob(os.path.join(corpus_dir, "*.yaml"))):
        with open(filepath) as f:
            data = yaml.safe_load(f)
            if isinstance(data, list):
                for p in data:
                    p["_file"] = os.path.basename(filepath)
                payloads.extend(data)
    return payloads


ALL_PAYLOADS = _load_all_payloads()

SAMPLE_SECRETS = [
    "123456:ABCdefGHIJklmNOPqrsTUVwxyz",
    "supersecret-webhook-token-value",
    "sk-ant-api03-abc123def456ghi789jkl",
]

SAMPLE_PHRASES = [
    "you are mohizarbot a public telegram bot with multi-provider llm routing",
]


def _payload_id(payload: dict) -> str:
    return f"{payload['_file']}/{payload['id']}"


@pytest.mark.parametrize(
    "payload",
    ALL_PAYLOADS,
    ids=_payload_id,
)
async def test_sanitize_and_wrap_cannot_escape(payload: dict) -> None:
    """Sanitize + wrap_untrusted must not allow tag escape."""
    from mohizarbot.security.input_sanitizer import sanitize
    from mohizarbot.security.untrusted import wrap_untrusted

    raw = str(payload["raw"])
    cleaned = sanitize(raw)
    result = wrap_untrusted("user_message", cleaned, session_token="test-session")

    # Must have exactly one opening and closing user_message tag
    assert result.count("<user_message") == 1, f"Tag escape detected in: {raw[:80]}"
    assert result.count("</user_message>") == 1, f"Tag escape detected in: {raw[:80]}"

    # Session token must be on the outer tag
    assert 'session_token="test-session"' in result


@pytest.mark.parametrize(
    "payload",
    ALL_PAYLOADS,
    ids=_payload_id,
)
async def test_injection_detector_flags_expected(payload: dict) -> None:
    """Detector must flag at least the expected_signals."""
    from mohizarbot.security.injection_detector import detect

    raw = str(payload["raw"])
    result = detect(raw)

    expected = set(payload.get("expected_signals", []))
    if not expected:
        return  # No signals expected — skip assertion

    actual = set(result.signals)
    missing = expected - actual
    assert not missing, (
        f"Expected signals {sorted(missing)} not detected for {payload['id']}: {raw[:80]}"
    )


@pytest.mark.parametrize(
    "payload",
    ALL_PAYLOADS,
    ids=_payload_id,
)
async def test_output_filter_matches_expected(payload: dict) -> None:
    """Output filter blocked status must match expected_blocked."""
    from mohizarbot.security.output_filter import filter_output

    raw = str(payload["raw"])
    result = filter_output(
        raw,
        secrets=SAMPLE_SECRETS,
        system_prompt_phrases=SAMPLE_PHRASES,
        allowlisted_domains=["telegram.org", "github.com"],
    )

    expected_blocked = bool(payload.get("expected_blocked", False))
    if expected_blocked:
        assert result.blocked, (
            f"Expected blocked=True for {payload['id']} but got False. "
            f"Reasons: {result.reasons}. Raw: {raw[:80]}"
        )
    # Note: we don't assert the reverse — the filter may block things
    # that aren't in expected_blocked (e.g. secret leaks matching our
    # sample secrets), which is fine — it's defense-in-depth.
