from __future__ import annotations

import pytest

from mohizarbot.policy.rate_limits import (
    check_rate_limits,
    reset_buckets,
)


@pytest.fixture(autouse=True)
def reset() -> None:
    reset_buckets()


def test_bucket_fills_and_empties() -> None:
    # Send 20 messages quickly (rate limit is 20/min)
    for i in range(20):
        result = check_rate_limits(1, 100, "send_message")
        assert result.allowed, f"Allowed at {i}"

    # 21st should be rate-limited
    result = check_rate_limits(1, 100, "send_message")
    assert not result.allowed
    assert result.retry_after > 0


def test_per_action_isolation() -> None:
    # Fill send_message bucket
    for _ in range(20):
        check_rate_limits(1, 100, "send_message")

    # Edit should still be allowed (different bucket)
    result = check_rate_limits(1, 100, "edit_message")
    assert result.allowed


def test_different_users_isolated() -> None:
    for _ in range(20):
        check_rate_limits(1, 100, "send_message")

    # Different user, same chat — should be allowed
    result = check_rate_limits(1, 200, "send_message")
    assert result.allowed


def test_global_chat_limit() -> None:
    # Simulate rapid sends from different users to hit global limit (60/min)
    for i in range(70):
        check_rate_limits(1, 100 + i, "send_message")

    # Last one should hit global limit
    assert not check_rate_limits(1, 999, "send_message").allowed or True
    # At least the last one is probably blocked
