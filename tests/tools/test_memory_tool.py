from __future__ import annotations

from mohizarbot.tools.memory import MemoryDeleteTool, MemorySaveTool


def test_memory_save_tool_name() -> None:
    tool = MemorySaveTool()
    assert tool.name == "memory_save"


def test_memory_save_tool_description() -> None:
    tool = MemorySaveTool()
    assert isinstance(tool.description, str)


def test_memory_save_tool_json_schema() -> None:
    tool = MemorySaveTool()
    schema = tool.json_schema
    assert schema["type"] == "object"
    assert "scope" in schema["properties"]
    assert "content" in schema["properties"]


def test_memory_save_produces_intent_types() -> None:
    tool = MemorySaveTool()
    types = tool.produces_intent_types
    assert "memory_save" in types


def test_memory_delete_tool_name() -> None:
    tool = MemoryDeleteTool()
    assert tool.name == "memory_delete"


def test_memory_delete_tool_description() -> None:
    tool = MemoryDeleteTool()
    assert isinstance(tool.description, str)


def test_memory_delete_tool_json_schema() -> None:
    tool = MemoryDeleteTool()
    schema = tool.json_schema
    assert schema["type"] == "object"
    assert "entry_id" in schema["properties"]


def test_memory_delete_produces_intent_types() -> None:
    tool = MemoryDeleteTool()
    types = tool.produces_intent_types
    assert "memory_delete" in types
