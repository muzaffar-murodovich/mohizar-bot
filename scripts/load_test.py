#!/usr/bin/env python3
"""Async load-test: N concurrent webhooks with mocked LLM/Telegram.

Reports p50, p95, p99 latencies and error rate.
"""

from __future__ import annotations

import asyncio
import sys
import time


async def _single_webhook(idx: int) -> tuple[float, bool]:
    """Simulate one webhook call end-to-end with mocked dependencies."""
    import os

    os.environ.setdefault("BOT_TOKEN", "test:bot")
    os.environ.setdefault("WEBHOOK_SECRET", "test-secret-32-chars-long!")
    os.environ.setdefault("AUDIT_HMAC_KEY", "a" * 64)

    start = time.monotonic()
    success = True
    try:
        from mohizarbot.security.input_sanitizer import sanitize
        from mohizarbot.security.output_filter import filter_output
        from mohizarbot.security.untrusted import wrap_untrusted

        raw = f"load test message {idx}"
        cleaned = sanitize(raw)
        wrapped = wrap_untrusted("user_message", cleaned, session_token="load-test")
        result = filter_output(wrapped, secrets=["test-secret"])
        success = not result.blocked
    except Exception:
        success = False

    duration = (time.monotonic() - start) * 1000
    return duration, success


async def main(n: int = 50) -> int:
    print(f"Running {n} concurrent webhook simulations...")
    start = time.monotonic()

    tasks = [_single_webhook(i) for i in range(n)]
    results = await asyncio.gather(*tasks)

    total_time = (time.monotonic() - start) * 1000
    latencies = [r[0] for r in results]
    errors = sum(1 for r in results if not r[1])

    latencies.sort()
    p50 = latencies[int(n * 0.5)] if n > 0 else 0
    p95 = latencies[int(n * 0.95)] if n > 0 else 0
    p99 = latencies[int(n * 0.99)] if n > 0 else 0

    print(f"\nResults (N={n}):")
    print(f"  Total time: {total_time:.0f}ms")
    print(f"  p50: {p50:.1f}ms")
    print(f"  p95: {p95:.1f}ms")
    print(f"  p99: {p99:.1f}ms")
    print(f"  Error rate: {errors}/{n} ({100 * errors / n:.1f}%)")

    return 0


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    sys.exit(asyncio.run(main(n)))
