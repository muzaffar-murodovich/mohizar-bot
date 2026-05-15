from __future__ import annotations

import time
from dataclasses import dataclass

# In-memory token bucket store (Redis-backed in production)
_buckets: dict[str, tuple[float, float]] = {}

RATE_LIMITS = {
    "send_message": 20.0,  # per minute per user
    "edit_message": 10.0,
    "delete_message": 5.0,
    "forward_message": 10.0,
    "global_chat": 60.0,  # total per chat per minute
}


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after: float = 0.0


def _get_bucket(key: str, rate: float, window: float = 60.0) -> RateLimitResult:
    now = time.monotonic()
    tokens, last = _buckets.get(key, (rate, now))
    # Refill
    elapsed = now - last
    tokens = min(rate, tokens + elapsed * (rate / window))
    _buckets[key] = (tokens, now)

    if tokens >= 1.0:
        _buckets[key] = (tokens - 1.0, now)
        return RateLimitResult(allowed=True)

    # Calculate retry_after
    deficit = 1.0 - tokens
    retry_after = deficit * (window / rate)
    return RateLimitResult(allowed=False, retry_after=retry_after)


def check_rate_limits(
    chat_id: int,
    user_id: int,
    action_class: str,
) -> RateLimitResult:
    """Check rate limits for an intent.

    Returns RateLimitResult with allowed=False and retry_after if over limit.
    """
    # Per-user per-action limit
    user_key = f"rl:user:{chat_id}:{user_id}:{action_class}"
    rate = RATE_LIMITS.get(action_class, 10.0)
    result = _get_bucket(user_key, rate)
    if not result.allowed:
        return result

    # Global chat limit
    chat_key = f"rl:chat:{chat_id}"
    global_rate = RATE_LIMITS["global_chat"]
    result = _get_bucket(chat_key, global_rate)
    if not result.allowed:
        return result

    return RateLimitResult(allowed=True)


def reset_buckets() -> None:
    """Reset all rate limit buckets (for tests)."""
    _buckets.clear()
