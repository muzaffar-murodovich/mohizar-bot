from __future__ import annotations

# Prometheus-compatible metrics for mohizarbot.
# Counters and histograms track intent execution, LLM calls,
# guard model decisions, and confirmation outcomes.
import time
from dataclasses import dataclass, field


@dataclass
class _Counter:
    _values: dict[str, float] = field(default_factory=dict)

    def inc(self, **labels: str) -> None:
        key = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        self._values[key] = self._values.get(key, 0) + 1

    def get(self, **labels: str) -> float:
        key = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return self._values.get(key, 0)

    def reset(self) -> None:
        self._values.clear()


@dataclass
class _Histogram:
    _values: list[float] = field(default_factory=list)

    def observe(self, value: float) -> None:
        self._values.append(value)

    def reset(self) -> None:
        self._values.clear()


# ── Counters ──
intents_total = _Counter()
llm_calls_total = _Counter()
guard_decisions_total = _Counter()
confirmations_total = _Counter()

# ── Histograms ──
llm_latency_seconds = _Histogram()
pipeline_latency_seconds = _Histogram()


def get_all_metrics() -> str:
    """Return Prometheus text format for all metrics."""
    lines = []
    for name, counter in [
        ("intents_total", intents_total),
        ("llm_calls_total", llm_calls_total),
        ("guard_decisions_total", guard_decisions_total),
        ("confirmations_total", confirmations_total),
    ]:
        for key, val in counter._values.items():
            lines.append(f"{name}{{{key}}} {val}")

    for name, hist in [
        ("llm_latency_seconds", llm_latency_seconds),
        ("pipeline_latency_seconds", pipeline_latency_seconds),
    ]:
        vals = hist._values
        if vals:
            lines.append(f"{name}_count {len(vals)}")
            lines.append(f"{name}_sum {sum(vals)}")
            sorted_vals = sorted(vals)
            p50 = sorted_vals[int(len(sorted_vals) * 0.5)] if sorted_vals else 0
            p95 = sorted_vals[int(len(sorted_vals) * 0.95)] if sorted_vals else 0
            lines.append(f"{name}_p50 {p50}")
            lines.append(f"{name}_p95 {p95}")

    return "\n".join(lines) + "\n"


class _Tracker:
    def __init__(self, hist: _Histogram) -> None:
        self._hist = hist
        self._start = 0.0

    def __enter__(self) -> _Tracker:
        self._start = time.monotonic()
        return self

    def __exit__(self, *args: object) -> None:
        self._hist.observe(time.monotonic() - self._start)


def track_latency(histogram: _Histogram) -> _Tracker:
    """Decorator/context manager factory for tracking latency."""
    return _Tracker(histogram)


def reset_all() -> None:
    intents_total.reset()
    llm_calls_total.reset()
    guard_decisions_total.reset()
    confirmations_total.reset()
    llm_latency_seconds.reset()
    pipeline_latency_seconds.reset()
