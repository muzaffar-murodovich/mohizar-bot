from __future__ import annotations

from mohizarbot.tools.polls import SendPollTool, StopPollTool
from mohizarbot.tools.registry import ToolRegistry


def test_send_poll_schema() -> None:
    t = SendPollTool()
    assert t.name == "send_poll"
    assert "options" in t.json_schema["required"]


def test_send_poll_has_media_options() -> None:
    t = SendPollTool()
    assert "is_anonymous" in t.json_schema["properties"]
    assert "allows_multiple_answers" in t.json_schema["properties"]


def test_stop_poll_schema() -> None:
    t = StopPollTool()
    assert t.name == "stop_poll"
    assert "message_id" in t.json_schema["required"]


def test_registry_knows_poll_tools() -> None:
    reg = ToolRegistry()
    reg.register(SendPollTool())
    reg.register(StopPollTool())
    assert len(reg.get_for_chat(["send_poll", "stop_poll"])) == 2
