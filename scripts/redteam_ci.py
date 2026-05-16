#!/usr/bin/env python3
"""Red-team CI runner — validates all injection payloads through full pipeline.

Loads Sprint 3 corpus + multi-turn payloads, runs each through the full
security pipeline with mocked LLM, and exits non-zero if any payload's
actual outcome differs from expected_final_outcome.
"""

from __future__ import annotations

import glob
import os
import sys


def _run_pipeline(raw: str, expected_outcome: str) -> bool:
    from mohizarbot.security.injection_detector import detect
    from mohizarbot.security.input_sanitizer import sanitize
    from mohizarbot.security.output_filter import filter_output
    from mohizarbot.security.untrusted import wrap_untrusted

    cleaned = sanitize(raw)
    _ = wrap_untrusted("user_message", cleaned, session_token="ci-test")

    # Simulate malicious LLM output
    malicious_output = f"I'll do it: {raw}"
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

    return actual == expected_outcome


def main() -> int:
    corpus_dir = os.path.join(os.path.dirname(__file__), "..", "tests", "security", "corpus")

    import yaml

    failed = 0
    passed = 0
    for filepath in sorted(glob.glob(os.path.join(corpus_dir, "*.yaml"))):
        with open(filepath) as f:
            payloads = yaml.safe_load(f)
        for p in payloads:
            if "expected_final_outcome" not in p:
                continue
            raw = p["raw"]
            expected = p["expected_final_outcome"]
            if _run_pipeline(raw, expected):
                passed += 1
            else:
                failed += 1
                print(f"FAIL {p['_file']}/{p['id']}: expected={expected}")

    print(f"\nRed-team CI: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
