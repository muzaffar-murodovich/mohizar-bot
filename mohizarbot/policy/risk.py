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

# File-download risk levels (Sprint 9)
# File downloads from Telegram are LOW risk by default (they come from
# the user's own file transfer). However, if the downloaded file exceeds
# 5 MB OR the extracted text exceeds 20K characters, the resulting
# LLM call is escalated to MEDIUM risk — guard model is invoked to
# inspect the processed content before execution.
_FILE_SIZE_MEDIUM_THRESHOLD = 5 * 1024 * 1024  # 5 MB
_FILE_TEXT_MEDIUM_THRESHOLD = 20_000  # 20K chars


def file_call_risk_level(file_size: int, extracted_chars: int) -> str:
    """Determine risk level for an LLM call that includes file content.

    Args:
        file_size: Size of the downloaded file in bytes.
        extracted_chars: Number of characters extracted from the file.

    Returns:
        "low" if both file_size <= 5MB and extracted_chars <= 20K,
        "medium" otherwise.
    """
    if file_size > _FILE_SIZE_MEDIUM_THRESHOLD or extracted_chars > _FILE_TEXT_MEDIUM_THRESHOLD:
        return "medium"
    return "low"


def is_high_risk(intent_type: str) -> bool:
    return RISK_LEVELS.get(intent_type, "medium") == "high"


def is_low_risk(intent_type: str) -> bool:
    return RISK_LEVELS.get(intent_type, "medium") == "low"
