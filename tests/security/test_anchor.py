from __future__ import annotations

from mohizarbot.llm.types import ChatMessage
from mohizarbot.security.anchor import re_anchor, reset_turns


def test_re_anchor_every_5_reinjects() -> None:
    reset_turns(1)
    system = "You are a helpful bot."

    # Turns 1-3: no re-anchor expected
    _turn_counters = __import__(
        "mohizarbot.security.anchor", fromlist=["_turn_counters"]
    )._turn_counters
    for turn_setup in range(1, 4):
        _turn_counters[1] = turn_setup
        msgs = re_anchor(
            [ChatMessage(role="user", content=f"msg {turn_setup}")], system, every_n=5, chat_id=1
        )
        system_in_msgs = any(
            getattr(m, "content", "") == system for m in msgs if getattr(m, "role", "") == "system"
        )
        assert not system_in_msgs, f"No re-anchor at turn setup {turn_setup}"

    # Turn 4: setting counter to 4, re_anchor increments to 5 → re-anchor
    _turn_counters[1] = 4
    msgs = re_anchor([ChatMessage(role="user", content="msg 5")], system, every_n=5, chat_id=1)
    has_system = any(
        getattr(m, "content", "") == system and getattr(m, "role", "") == "system" for m in msgs
    )
    assert has_system, (
        f"System should be re-anchored at turn 5. Roles: {[getattr(m, 'role', '') for m in msgs]}"
    )


def test_assistant_outputs_wrapped() -> None:
    reset_turns(2)
    system = "System prompt"
    messages = [
        ChatMessage(role="system", content=system),
        ChatMessage(role="user", content="Q"),
        ChatMessage(role="assistant", content="A"),
    ]
    result = re_anchor(messages, system, every_n=5, chat_id=2)
    # Assistant content should be wrapped
    assistant_contents = [
        getattr(m, "content", "") for m in result if getattr(m, "role", "") == "assistant"
    ]
    for content in assistant_contents:
        assert "<assistant_previous_output>" in content


def test_no_duplicate_system() -> None:
    reset_turns(3)
    system = "System prompt"
    msgs = [ChatMessage(role="system", content=system), ChatMessage(role="user", content="Q")]
    _turn_counters = __import__(
        "mohizarbot.security.anchor", fromlist=["_turn_counters"]
    )._turn_counters
    _turn_counters[3] = 5
    result = re_anchor(msgs, system, every_n=5, chat_id=3)
    system_msgs = [m for m in result if getattr(m, "role", "") == "system"]
    assert len(system_msgs) == 1
