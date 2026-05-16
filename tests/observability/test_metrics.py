from __future__ import annotations

import pytest

from mohizarbot.observability.metrics import (
    confirmations_total,
    guard_decisions_total,
    intents_total,
    llm_calls_total,
    llm_latency_seconds,
    reset_all,
)


@pytest.fixture(autouse=True)
def reset() -> None:
    reset_all()


def test_intents_counter_increments() -> None:
    intents_total.inc(type="send_message", result="executed")
    assert intents_total.get(type="send_message", result="executed") == 1


def test_llm_calls_counter_increments() -> None:
    llm_calls_total.inc(provider="anthropic", result="success")
    assert llm_calls_total.get(provider="anthropic", result="success") == 1


def test_guard_decisions_counter_increments() -> None:
    guard_decisions_total.inc(verdict="block")
    guard_decisions_total.inc(verdict="safe")
    assert guard_decisions_total.get(verdict="block") == 1
    assert guard_decisions_total.get(verdict="safe") == 1


def test_confirmations_counter_increments() -> None:
    confirmations_total.inc(outcome="approved")
    confirmations_total.inc(outcome="denied")
    assert confirmations_total.get(outcome="approved") == 1


def test_histogram_observes() -> None:
    llm_latency_seconds.observe(0.5)
    llm_latency_seconds.observe(1.0)
    assert len(llm_latency_seconds._values) == 2


async def test_get_all_metrics_output() -> None:
    reset_all()
    intents_total.inc(type="send_message", result="executed")
    llm_calls_total.inc(provider="test", result="success")
    from mohizarbot.observability.metrics import get_all_metrics

    text = get_all_metrics()
    assert "intents_total" in text
    assert "llm_calls_total" in text
