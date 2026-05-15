from __future__ import annotations

RISK_LEVELS: dict[str, str] = {
    # Low risk — auto-execute allowed
    "send_message": "low",
    "send_photo": "low",
    "send_document": "low",
    "send_video": "low",
    "send_audio": "low",
    "send_voice": "low",
    "send_sticker": "low",
    "send_location": "low",
    "set_message_reaction": "low",
    "memory_save": "low",
    "memory_delete": "low",
    # Medium risk — auto-execute if chat configured
    "edit_message": "medium",
    "send_poll": "medium",
    "stop_poll": "medium",
    "set_chat_title": "medium",
    "set_chat_description": "medium",
    "create_forum_topic": "medium",
    "edit_forum_topic": "medium",
    "close_forum_topic": "medium",
    "forward_message": "medium",
    "web_fetch": "medium",
    "web_search": "medium",
    # High risk — ALWAYS requires confirmation
    "delete_message": "high",
    "ban_chat_member": "high",
    "unban_chat_member": "high",
    "restrict_chat_member": "high",
    "promote_chat_member": "high",
    "set_chat_permissions": "high",
    "pin_chat_message": "high",
    "unpin_chat_message": "high",
    "delete_forum_topic": "high",
}

HIGH_RISK_ALWAYS_CONFIRM = {k for k, v in RISK_LEVELS.items() if v == "high"}


def is_high_risk(intent_type: str) -> bool:
    return RISK_LEVELS.get(intent_type, "medium") == "high"


def is_low_risk(intent_type: str) -> bool:
    return RISK_LEVELS.get(intent_type, "medium") == "low"
