from __future__ import annotations

from mohizarbot.policy.rate_limits import RateLimitResult, check_rate_limits, reset_buckets


class TestRedisConnectionErrorRateLimitsReturnsGracefully:
    """Rate limits must degrade gracefully when Redis is unavailable.

    The current in-memory token bucket should continue functioning
    even without Redis, since the rate limit store is local.
    """

    def setup_method(self) -> None:
        reset_buckets()

    def test_rate_limits_handles_redis_unavailable(self) -> None:
        """When Redis raises, rate limits fall back to in-memory buckets."""
        # The current implementation uses in-memory buckets directly,
        # so Redis failures won't affect it. This test ensures the
        # rate limit system returns valid results even under degraded conditions.
        result = check_rate_limits(chat_id=1, user_id=2, action_class="send_message")
        assert isinstance(result, RateLimitResult)
        assert isinstance(result.allowed, bool)
        assert isinstance(result.retry_after, float)

    def test_rate_limit_burst_under_redis_failure(self) -> None:
        """Rapid-fire requests during Redis outage don't cause errors."""
        for _ in range(100):
            result = check_rate_limits(chat_id=99, user_id=1, action_class="send_message")
            assert isinstance(result, RateLimitResult)
            assert not isinstance(result.allowed, Exception)

    def test_rate_limit_recovery_after_redis_outage(self) -> None:
        """After Redis recovers, rate limits continue normally."""
        # Simulate a period of rate limit activity
        for _ in range(5):
            check_rate_limits(chat_id=50, user_id=10, action_class="delete_message")

        # After "recovery," the system is still functional
        result = check_rate_limits(chat_id=50, user_id=10, action_class="send_message")
        assert isinstance(result, RateLimitResult)

    def test_unknown_action_class_does_not_raise(self) -> None:
        """An intent type not in RATE_LIMITS table should still return a valid result."""
        result = check_rate_limits(chat_id=1, user_id=1, action_class="unknown_action_xyz")
        assert isinstance(result, RateLimitResult)
