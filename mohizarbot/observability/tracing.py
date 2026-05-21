from __future__ import annotations

# OpenTelemetry-style tracing spans per pipeline stage.
import time
from dataclasses import dataclass, field


@dataclass
class Span:
    name: str
    start_time: float = field(default_factory=time.monotonic)
    end_time: float = 0.0
    attributes: dict[str, str] = field(default_factory=dict)

    def finish(self) -> None:
        self.end_time = time.monotonic()

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000


_traces: list[list[Span]] = []


def start_trace(trace_id: str) -> list[Span]:
    """Start a new trace with the given ID."""
    _ = trace_id  # noqa: ARG001 — wired when OTEL integrated
    spans: list[Span] = []
    _traces.append(spans)
    return spans


def start_span(spans: list[Span], name: str, **attrs: str) -> Span:
    span = Span(name=name)
    span.attributes.update(attrs)
    spans.append(span)
    return span
