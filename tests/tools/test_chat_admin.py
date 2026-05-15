from __future__ import annotations

from mohizarbot.policy.risk import is_high_risk
from mohizarbot.tools.chat_admin import (
    PinChatMessageTool,
    SetChatDescriptionTool,
    SetChatTitleTool,
    UnpinChatMessageTool,
)
from mohizarbot.tools.registry import ToolRegistry


def test_pin_is_high_risk() -> None:
    assert is_high_risk("pin_chat_message")


def test_unpin_is_high_risk() -> None:
    assert is_high_risk("unpin_chat_message")


def test_set_permissions_is_high_risk() -> None:
    assert is_high_risk("set_chat_permissions")


def test_set_title_is_medium_risk() -> None:
    assert not is_high_risk("set_chat_title")


def test_set_description_is_medium_risk() -> None:
    assert not is_high_risk("set_chat_description")


def test_pin_precheck_requires_rights() -> None:
    t = PinChatMessageTool()
    assert "can_pin_messages" in t.required_bot_rights


def test_unpin_precheck_requires_rights() -> None:
    t = UnpinChatMessageTool()
    assert "can_pin_messages" in t.required_bot_rights


def test_registry_chat_admin() -> None:
    reg = ToolRegistry()
    reg.register(SetChatTitleTool())
    reg.register(SetChatDescriptionTool())
    reg.register(PinChatMessageTool())
    assert len(reg.get_for_chat(["set_chat_title", "pin_chat_message"])) == 2
