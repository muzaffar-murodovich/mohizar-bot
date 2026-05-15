from __future__ import annotations

from mohizarbot.policy.risk import (
    HIGH_RISK_ALWAYS_CONFIRM,
    RISK_LEVELS,
    is_high_risk,
    is_low_risk,
)


def test_every_high_risk_in_always_confirm() -> None:
    for intent_type, level in RISK_LEVELS.items():
        if level == "high":
            assert intent_type in HIGH_RISK_ALWAYS_CONFIRM


def test_ban_is_high_risk() -> None:
    assert is_high_risk("ban_chat_member")
    assert "ban_chat_member" in HIGH_RISK_ALWAYS_CONFIRM


def test_restrict_is_high_risk() -> None:
    assert is_high_risk("restrict_chat_member")


def test_promote_is_high_risk() -> None:
    assert is_high_risk("promote_chat_member")


def test_set_permissions_is_high_risk() -> None:
    assert is_high_risk("set_chat_permissions")


def test_pin_is_high_risk() -> None:
    assert is_high_risk("pin_chat_message")


def test_delete_is_high_risk() -> None:
    assert is_high_risk("delete_message")


def test_delete_forum_topic_is_high_risk() -> None:
    assert is_high_risk("delete_forum_topic")


def test_send_message_is_low_risk() -> None:
    assert is_low_risk("send_message")


def test_send_photo_is_low_risk() -> None:
    assert is_low_risk("send_photo")


def test_reaction_is_low_risk() -> None:
    assert is_low_risk("set_message_reaction")


def test_memory_save_is_low_risk() -> None:
    assert is_low_risk("memory_save")


def test_auto_approve_does_not_bypass_high() -> None:
    """High-risk must ALWAYS require confirmation regardless of auto_approve."""
    for intent_type in HIGH_RISK_ALWAYS_CONFIRM:
        assert is_high_risk(intent_type), f"{intent_type} must stay high-risk"
        # auto_approve flag does not change the risk level itself
        assert RISK_LEVELS[intent_type] == "high"


def test_unknown_type_is_medium() -> None:
    assert not is_high_risk("nonexistent_intent")
    assert not is_low_risk("nonexistent_intent")
