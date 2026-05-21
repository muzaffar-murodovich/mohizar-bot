from __future__ import annotations

from mohizarbot.policy.risk import (
    HIGH_RISK_ALWAYS_CONFIRM,
    RISK_LEVELS,
    is_high_risk,
    is_low_risk,
)


def test_post_to_channel_is_high_risk() -> None:
    assert is_high_risk("post_to_channel")
    assert "post_to_channel" in HIGH_RISK_ALWAYS_CONFIRM
    assert RISK_LEVELS["post_to_channel"] == "high"


def test_edit_channel_post_is_high_risk() -> None:
    assert is_high_risk("edit_channel_post")
    assert "edit_channel_post" in HIGH_RISK_ALWAYS_CONFIRM


def test_cancel_scheduled_post_is_high_risk() -> None:
    assert is_high_risk("cancel_scheduled_post")
    assert "cancel_scheduled_post" in HIGH_RISK_ALWAYS_CONFIRM


def test_send_message_with_keyboard_is_low_risk() -> None:
    assert is_low_risk("send_message_with_keyboard")
    assert RISK_LEVELS["send_message_with_keyboard"] == "low"


def test_send_media_group_is_low_risk() -> None:
    assert is_low_risk("send_media_group")
    assert RISK_LEVELS["send_media_group"] == "low"


def test_callback_response_is_low_risk() -> None:
    assert is_low_risk("callback_response")
    assert RISK_LEVELS["callback_response"] == "low"


def test_edit_reply_markup_is_medium() -> None:
    assert RISK_LEVELS["edit_reply_markup"] == "medium"


def test_channel_posts_always_high_regardless_of_auto_approve() -> None:
    """Channel posts are ALWAYS HIGH risk, no exceptions."""
    for intent_type in [
        "post_to_channel",
        "edit_channel_post",
        "cancel_scheduled_post",
    ]:
        assert is_high_risk(intent_type), f"{intent_type} must be high risk"
        assert intent_type in HIGH_RISK_ALWAYS_CONFIRM
