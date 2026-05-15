from __future__ import annotations

from mohizarbot.tools.base import Tool


class BanChatMemberTool(Tool):
    name = "ban_chat_member"
    description = "Ban a user from a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "user_id": {"type": "integer"},
                "until_date": {"type": "integer"},
                "revoke_messages": {"type": "boolean"},
            },
            "required": ["chat_id", "user_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["ban_chat_member"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_restrict_members"]


class UnbanChatMemberTool(Tool):
    name = "unban_chat_member"
    description = "Unban a user from a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "user_id": {"type": "integer"},
            },
            "required": ["chat_id", "user_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["unban_chat_member"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_restrict_members"]


class RestrictChatMemberTool(Tool):
    name = "restrict_chat_member"
    description = "Restrict a user's permissions in a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "user_id": {"type": "integer"},
                "permissions": {"type": "object"},
                "until_date": {"type": "integer"},
            },
            "required": ["chat_id", "user_id", "permissions"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["restrict_chat_member"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_restrict_members"]


class PromoteChatMemberTool(Tool):
    name = "promote_chat_member"
    description = "Promote a user to admin with specified rights"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "user_id": {"type": "integer"},
                "can_manage_chat": {"type": "boolean"},
                "can_delete_messages": {"type": "boolean"},
                "can_restrict_members": {"type": "boolean"},
                "can_promote_members": {"type": "boolean"},
                "can_change_info": {"type": "boolean"},
                "can_invite_users": {"type": "boolean"},
                "can_pin_messages": {"type": "boolean"},
            },
            "required": ["chat_id", "user_id"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["promote_chat_member"]

    @property
    def required_bot_rights(self) -> list[str]:
        return ["can_promote_members"]
