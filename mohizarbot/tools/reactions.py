from __future__ import annotations

from mohizarbot.tools.base import Tool


class SetMessageReactionTool(Tool):
    name = "set_message_reaction"
    description = "Set a reaction on a message"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "message_id": {"type": "integer"},
                "reaction": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of emoji",
                },
                "is_big": {"type": "boolean"},
            },
            "required": ["chat_id", "message_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["set_message_reaction"]
