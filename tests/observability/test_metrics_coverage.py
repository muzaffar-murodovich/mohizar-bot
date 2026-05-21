from __future__ import annotations

from mohizarbot.observability.metrics import (
    _Counter,
    _Histogram,
    confirmations_total,
    get_all_metrics,
    guard_decisions_total,
    intents_total,
    llm_calls_total,
    llm_latency_seconds,
    reset_all,
    track_latency,
)


def test_counter_inc_and_get() -> None:
    c = _Counter()
    c.inc(status="ok")
    assert c.get(status="ok") == 1.0
    c.inc(status="ok")
    assert c.get(status="ok") == 2.0
    assert c.get(status="err") == 0.0


def test_counter_reset() -> None:
    c = _Counter()
    c.inc(x="1")
    c.reset()
    assert c.get(x="1") == 0.0


def test_histogram_observe() -> None:
    h = _Histogram()
    h.observe(1.5)
    h.observe(2.5)
    assert len(h._values) == 2
    assert sum(h._values) == 4.0


def test_histogram_reset() -> None:
    h = _Histogram()
    h.observe(1.0)
    h.reset()
    assert len(h._values) == 0


def test_get_all_metrics_empty() -> None:
    reset_all()
    result = get_all_metrics()
    assert isinstance(result, str)


def test_get_all_metrics_with_data() -> None:
    reset_all()
    intents_total.inc(type="send_message", status="executed")
    intents_total.inc(type="send_message", status="executed")
    guard_decisions_total.inc(verdict="safe")
    llm_calls_total.inc(provider="anthropic")
    confirmations_total.inc(outcome="approved")
    result = get_all_metrics()
    assert "intents_total" in result
    assert "guard_decisions_total" in result
    assert "llm_calls_total" in result
    assert "confirmations_total" in result


def test_track_latency_context_manager() -> None:
    h = _Histogram()
    with track_latency(h):
        pass
    assert len(h._values) == 1


def test_reset_all_clears_everything() -> None:
    intents_total.inc(type="test")
    llm_latency_seconds.observe(0.5)
    reset_all()
    assert intents_total.get(type="test") == 0.0
    assert len(llm_latency_seconds._values) == 0
