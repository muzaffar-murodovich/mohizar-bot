from __future__ import annotations

# Multi-turn anchoring (Layer 6) — prevents context-drift attacks.
# Re-injects the system prompt every N user turns to prevent gradual
# context erosion and multi-turn priming attacks.


# Counters stored in memory per chat
_turn_counters: dict[int, int] = {}


def re_anchor(
    messages: list[object],
    system_prompt: str,
    every_n: int = 5,
    chat_id: int | None = None,
) -> list[object]:
    """Re-inject system prompt if enough user turns have passed.

    Also wraps past assistant outputs in <assistant_previous_output> tags
    to prevent the LLM from treating its own past words as authoritative.

    Args:
        messages: Current message list (will be modified).
        system_prompt: The system prompt text to anchor with.
        every_n: Re-inject every N user turns.
        chat_id: Chat identifier for turn tracking.

    Returns:
        Modified messages list.
    """
    if chat_id is not None:
        _turn_counters[chat_id] = _turn_counters.get(chat_id, 0) + 1
        turn = _turn_counters[chat_id]

        if turn % every_n == 0 and turn > 0:
            # Check if system prompt is already first
            first_msg = messages[0] if messages else None
            first_content = getattr(first_msg, "content", "") if first_msg else ""
            if first_content != system_prompt:
                from mohizarbot.llm.types import ChatMessage

                messages.insert(0, ChatMessage(role="system", content=system_prompt))

    # Wrap past assistant outputs
    for i, msg in enumerate(messages):
        role = getattr(msg, "role", "")
        if role == "assistant":
            content = getattr(msg, "content", "")
            if isinstance(content, str) and not content.startswith("<assistant_previous_output"):
                from mohizarbot.llm.types import ChatMessage

                messages[i] = ChatMessage(
                    role="assistant",
                    content=f"<assistant_previous_output>{content}</assistant_previous_output>",
                )

    return messages


def reset_turns(chat_id: int | None = None) -> None:
    """Reset turn counters (for tests)."""
    if chat_id is not None:
        _turn_counters.pop(chat_id, None)
    else:
        _turn_counters.clear()
