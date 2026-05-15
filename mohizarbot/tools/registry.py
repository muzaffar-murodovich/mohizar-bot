from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mohizarbot.tools.base import Tool


class ToolRegistry:
    """Tool registry with default-deny.

    Chats opt in via ChatSettings.enabled_tools (list of tool names).
    Only the emit_intents function is exposed to the LLM; individual tools
    are internal — their schemas inform the LLM about available intents.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get_all(self) -> dict[str, Tool]:
        return dict(self._tools)

    def get_for_chat(self, enabled_tools: list[str] | None = None) -> list[Tool]:
        """Return tools enabled for a chat. Default-deny: require explicit opt-in."""
        if not enabled_tools:
            return []
        return [t for name, t in self._tools.items() if name in enabled_tools]

    def get_schemas_for_chat(
        self, enabled_tools: list[str] | None = None
    ) -> list[dict[str, object]]:
        """Get OpenAI-format tool schemas for enabled tools."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.json_schema,
                },
            }
            for t in self.get_for_chat(enabled_tools)
        ]

    def build_emit_intents_schema(
        self, enabled_tools: list[str] | None = None
    ) -> dict[str, object]:
        """Build the single emit_intents function schema exposed to the LLM.

        The LLM can ONLY call emit_intents, which takes a list of structured
        intent objects. This prevents the LLM from calling tools directly.
        """
        self.get_schemas_for_chat(enabled_tools)

        # Build the discriminated union of intent types
        return {
            "type": "function",
            "function": {
                "name": "emit_intents",
                "description": "Emit structured intents for the policy engine to execute.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "thought": {
                            "type": "string",
                            "description": "Brief reasoning about what intents to emit",
                        },
                        "actions": {
                            "type": "array",
                            "items": {
                                "anyOf": [
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {"const": "send_message"},
                                            "chat_id": {"type": "integer"},
                                            "text": {"type": "string"},
                                            "reply_to_message_id": {"type": "integer"},
                                        },
                                        "required": ["type", "chat_id", "text"],
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {"const": "edit_message"},
                                            "chat_id": {"type": "integer"},
                                            "message_id": {"type": "integer"},
                                            "text": {"type": "string"},
                                        },
                                        "required": ["type", "chat_id", "message_id", "text"],
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {"const": "delete_message"},
                                            "chat_id": {"type": "integer"},
                                            "message_id": {"type": "integer"},
                                        },
                                        "required": ["type", "chat_id", "message_id"],
                                    },
                                    {
                                        "type": "object",
                                        "properties": {
                                            "type": {"const": "forward_message"},
                                            "from_chat_id": {"type": "integer"},
                                            "message_id": {"type": "integer"},
                                            "to_chat_id": {"type": "integer"},
                                        },
                                        "required": [
                                            "type",
                                            "from_chat_id",
                                            "message_id",
                                            "to_chat_id",
                                        ],
                                    },
                                ]
                            },
                        },
                    },
                    "required": ["actions"],
                },
            },
        }
