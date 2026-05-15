from __future__ import annotations

from mohizarbot.tools.base import Tool


class SendMessageTool(Tool):
    name = "send_message"
    description = "Send a text message to a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer", "description": "Target chat ID"},
                "text": {"type": "string", "description": "Message text"},
                "reply_to_message_id": {"type": "integer", "description": "Message to reply to"},
            },
            "required": ["chat_id", "text"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["send_message"]


class EditMessageTool(Tool):
    name = "edit_message"
    description = "Edit an existing message"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer", "description": "Target chat ID"},
                "message_id": {"type": "integer", "description": "Message ID to edit"},
                "text": {"type": "string", "description": "New text"},
            },
            "required": ["chat_id", "message_id", "text"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["edit_message"]


class DeleteMessageTool(Tool):
    name = "delete_message"
    description = "Delete a message"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer", "description": "Target chat ID"},
                "message_id": {"type": "integer", "description": "Message ID to delete"},
            },
            "required": ["chat_id", "message_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["delete_message"]


class ForwardMessageTool(Tool):
    name = "forward_message"
    description = "Forward a message to another chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "from_chat_id": {"type": "integer", "description": "Source chat ID"},
                "message_id": {"type": "integer", "description": "Message ID to forward"},
                "to_chat_id": {"type": "integer", "description": "Destination chat ID"},
            },
            "required": ["from_chat_id", "message_id", "to_chat_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["forward_message"]
