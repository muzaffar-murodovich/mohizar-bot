from __future__ import annotations

from mohizarbot.tools.base import Tool


class SetChatPermissionsTool(Tool):
    name = "set_chat_permissions"
    description = "Set default chat permissions for all members"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "permissions": {"type": "object"},
            },
            "required": ["chat_id", "permissions"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["set_chat_permissions"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_restrict_members"]


class PinChatMessageTool(Tool):
    name = "pin_chat_message"
    description = "Pin a message in a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "message_id": {"type": "integer"},
                "disable_notification": {"type": "boolean"},
            },
            "required": ["chat_id", "message_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["pin_chat_message"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_pin_messages"]


class UnpinChatMessageTool(Tool):
    name = "unpin_chat_message"
    description = "Unpin a message from a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "message_id": {"type": "integer"},
            },
            "required": ["chat_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["unpin_chat_message"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_pin_messages"]


class SetChatTitleTool(Tool):
    name = "set_chat_title"
    description = "Set a chat's title"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "title": {"type": "string"},
            },
            "required": ["chat_id", "title"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["set_chat_title"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_change_info"]


class SetChatDescriptionTool(Tool):
    name = "set_chat_description"
    description = "Set a chat's description"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "description": {"type": "string"},
            },
            "required": ["chat_id", "description"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["set_chat_description"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_change_info"]
