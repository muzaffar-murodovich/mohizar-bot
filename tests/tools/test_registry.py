from __future__ import annotations

from mohizarbot.tools.base import Tool
from mohizarbot.tools.messaging import (
    DeleteMessageTool,
    EditMessageTool,
    ForwardMessageTool,
    SendMessageTool,
)
from mohizarbot.tools.registry import ToolRegistry


class _MockTool(Tool):
    name = "mock"
    description = "mock tool"
    json_schema = {"type": "object", "properties": {}}
    produces_intent_types = ["mock_intent"]


def test_default_deny_returns_empty() -> None:
    reg = ToolRegistry()
    reg.register(SendMessageTool())
    tools = reg.get_for_chat()
    assert tools == []


def test_opt_in_shows_enabled_tools() -> None:
    reg = ToolRegistry()
    reg.register(SendMessageTool())
    reg.register(DeleteMessageTool())
    tools = reg.get_for_chat(["send_message"])
    assert len(tools) == 1
    assert tools[0].name == "send_message"


def test_schema_matches_openai_shape() -> None:
    reg = ToolRegistry()
    reg.register(SendMessageTool())
    schemas = reg.get_schemas_for_chat(["send_message"])
    assert len(schemas) == 1
    assert schemas[0]["type"] == "function"
    assert "function" in schemas[0]
    assert schemas[0]["function"]["name"] == "send_message"
    assert "parameters" in schemas[0]["function"]


def test_emit_intents_schema() -> None:
    reg = ToolRegistry()
    reg.register(SendMessageTool())
    reg.register(DeleteMessageTool())
    schema = reg.build_emit_intents_schema(["send_message", "delete_message"])
    assert schema["function"]["name"] == "emit_intents"
    assert "actions" in schema["function"]["parameters"]["properties"]


def test_all_tools_registered() -> None:
    reg = ToolRegistry()
    reg.register(SendMessageTool())
    reg.register(EditMessageTool())
    reg.register(DeleteMessageTool())
    reg.register(ForwardMessageTool())
    reg.register(_MockTool())
    assert len(reg.get_all()) == 5


def test_produces_intent_types() -> None:
    assert SendMessageTool().produces_intent_types == ["send_message"]
    assert EditMessageTool().produces_intent_types == ["edit_message"]
    assert DeleteMessageTool().produces_intent_types == ["delete_message"]
    assert ForwardMessageTool().produces_intent_types == ["forward_message"]
