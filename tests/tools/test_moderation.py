from __future__ import annotations

from mohizarbot.policy.risk import is_high_risk
from mohizarbot.tools.moderation import (
    BanChatMemberTool,
    PromoteChatMemberTool,
    RestrictChatMemberTool,
    UnbanChatMemberTool,
)
from mohizarbot.tools.registry import ToolRegistry


def test_ban_is_high_risk() -> None:
    assert is_high_risk("ban_chat_member")


def test_unban_is_high_risk() -> None:
    assert is_high_risk("unban_chat_member")


def test_restrict_is_high_risk() -> None:
    assert is_high_risk("restrict_chat_member")


def test_promote_is_high_risk() -> None:
    assert is_high_risk("promote_chat_member")


def test_ban_precheck_requires_rights() -> None:
    t = BanChatMemberTool()
    assert "can_restrict_members" in t.required_bot_rights


def test_unban_precheck_requires_rights() -> None:
    t = UnbanChatMemberTool()
    assert "can_restrict_members" in t.required_bot_rights


def test_restrict_precheck_requires_rights() -> None:
    t = RestrictChatMemberTool()
    assert "can_restrict_members" in t.required_bot_rights


def test_promote_precheck_requires_rights() -> None:
    t = PromoteChatMemberTool()
    assert "can_promote_members" in t.required_bot_rights


def test_registry_default_deny_for_moderation() -> None:
    reg = ToolRegistry()
    reg.register(BanChatMemberTool())
    reg.register(UnbanChatMemberTool())
    assert reg.get_for_chat() == []
    assert len(reg.get_for_chat(["ban_chat_member"])) == 1
