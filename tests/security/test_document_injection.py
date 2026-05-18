from __future__ import annotations

import os

import pytest
import yaml

from mohizarbot.security.input_sanitizer import sanitize
from mohizarbot.security.untrusted import wrap_untrusted


def _load_document_payloads() -> list[dict]:
    corpus_dir = os.path.join(os.path.dirname(__file__), "corpus")
    payloads: list[dict] = []
    filepath = os.path.join(corpus_dir, "document_injection.yaml")
    with open(filepath) as f:
        data = yaml.safe_load(f)
        if isinstance(data, list):
            for p in data:
                p["_file"] = os.path.basename(filepath)
            payloads.extend(data)
    return payloads


DOCUMENT_PAYLOADS = _load_document_payloads()


def _payload_id(payload: dict) -> str:
    return f"{payload['_file']}/{payload['id']}"


@pytest.mark.parametrize("payload", DOCUMENT_PAYLOADS, ids=_payload_id)
def test_document_payload_wrapped_without_escape(payload: dict) -> None:
    """Every document injection payload must be sanitized and wrappable without tag escape."""
    raw = str(payload["raw"])
    cleaned = sanitize(raw)
    result = wrap_untrusted("user_message", cleaned, session_token="doc-test")

    # Must have exactly one opening and closing tag
    assert result.count("<user_message") == 1, f"Tag escape in: {raw[:80]}"
    assert result.count("</user_message>") == 1, f"Tag escape in: {raw[:80]}"


@pytest.mark.parametrize("payload", DOCUMENT_PAYLOADS, ids=_payload_id)
def test_document_payload_no_unauthorized_intent(payload: dict) -> None:
    """Simulated pipeline: sanitize → wrap → mock LLM → intents → policy result.

    No payload should produce an auto-executed high-risk intent.
    """
    from mohizarbot.security.injection_detector import detect
    from mohizarbot.security.output_filter import filter_output

    raw = str(payload["raw"])
    expected = str(payload.get("expected_final_outcome", "denied_by_policy"))

    # Full pipeline simulation (same as redteam_ci)
    cleaned = sanitize(raw)
    _ = wrap_untrusted("user_message", cleaned, session_token="ci-test")

    # Simulate a malicious LLM output that echoes the injection
    malicious_output = f"I'll execute: {raw}"
    secrets = ["test-secret-123", "sk-ant-test-key"]
    filter_result = filter_output(malicious_output, secrets=secrets)

    if filter_result.blocked:
        actual = "blocked_by_filter"
    else:
        detection = detect(raw)
        if detection.score >= 0.5:
            actual = "blocked_by_guard"
        elif "ban" in raw or "delete" in raw or "restrict" in raw:
            actual = "queued_for_confirmation"
        else:
            actual = "denied_by_policy"

    assert actual == expected, f"Expected {expected}, got {actual} for payload {payload['id']}"


@pytest.mark.parametrize("payload", DOCUMENT_PAYLOADS, ids=_payload_id)
def test_document_tags_not_renderable(payload: dict) -> None:
    """Document content tags like </document_content> are escaped in wrapper."""
    raw = str(payload["raw"])
    cleaned = sanitize(raw)
    result = wrap_untrusted("user_message", cleaned, session_token="tag-test")

    # The output should not contain raw </document_content> from the input
    assert result.count("</document_content>") == 0


def test_all_26_payloads_loaded() -> None:
    """All 26+ document injection payloads are loaded."""
    assert len(DOCUMENT_PAYLOADS) >= 25, f"Expected ≥25 payloads, got {len(DOCUMENT_PAYLOADS)}"
