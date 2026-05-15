from __future__ import annotations

from mohizarbot.tools.base import Tool


class SendPollTool(Tool):
    name = "send_poll"
    description = "Send a poll to a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "question": {"type": "string"},
                "options": {"type": "array", "items": {"type": "string"}},
                "is_anonymous": {"type": "boolean"},
                "allows_multiple_answers": {"type": "boolean"},
            },
            "required": ["chat_id", "question", "options"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["send_poll"]


class StopPollTool(Tool):
    name = "stop_poll"
    description = "Stop a running poll"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "message_id": {"type": "integer"},
            },
            "required": ["chat_id", "message_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["stop_poll"]
