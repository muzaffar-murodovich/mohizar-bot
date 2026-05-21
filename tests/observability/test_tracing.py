from __future__ import annotations

from mohizarbot.observability.tracing import Span, start_span, start_trace


def test_start_trace_returns_list() -> None:
    spans = start_trace("trace-001")
    assert isinstance(spans, list)
    assert len(spans) == 0


def test_span_creation() -> None:
    span = Span(name="test-span")
    assert span.name == "test-span"
    assert span.end_time == 0.0
    assert isinstance(span.attributes, dict)


def test_span_finish() -> None:
    span = Span(name="test")
    span.finish()
    assert span.end_time > 0.0


def test_span_with_attributes() -> None:
    span = Span(name="attr-span", attributes={"key": "value"})
    assert span.attributes["key"] == "value"


def test_start_span_adds_to_trace() -> None:
    spans = start_trace("trace-002")
    span = start_span(spans, "child-span", foo="bar")
    assert len(spans) == 1
    assert spans[0] is span
    assert span.attributes["foo"] == "bar"
    assert span.name == "child-span"


def test_span_duration() -> None:
    span = Span(name="dur")
    span.finish()
    duration = span.end_time - span.start_time
    assert duration >= 0
