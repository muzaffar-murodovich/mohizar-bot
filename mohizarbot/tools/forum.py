from __future__ import annotations

from mohizarbot.tools.base import Tool


class CreateForumTopicTool(Tool):
    name = "create_forum_topic"
    description = "Create a new forum topic"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "name": {"type": "string"},
                "icon_color": {"type": "integer"},
                "icon_custom_emoji_id": {"type": "string"},
            },
            "required": ["chat_id", "name"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["create_forum_topic"]


class EditForumTopicTool(Tool):
    name = "edit_forum_topic"
    description = "Edit a forum topic name"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "message_thread_id": {"type": "integer"},
                "name": {"type": "string"},
            },
            "required": ["chat_id", "message_thread_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["edit_forum_topic"]


class CloseForumTopicTool(Tool):
    name = "close_forum_topic"
    description = "Close a forum topic"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "message_thread_id": {"type": "integer"},
            },
            "required": ["chat_id", "message_thread_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["close_forum_topic"]


class DeleteForumTopicTool(Tool):
    name = "delete_forum_topic"
    description = "Delete a forum topic"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "message_thread_id": {"type": "integer"},
            },
            "required": ["chat_id", "message_thread_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["delete_forum_topic"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_manage_topics"]
