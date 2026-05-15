from __future__ import annotations

from mohizarbot.tools.reactions import SetMessageReactionTool
from mohizarbot.tools.registry import ToolRegistry


def test_reaction_emoji_path() -> None:
    t = SetMessageReactionTool()
    assert t.name == "set_message_reaction"
    assert "reaction" in t.json_schema["properties"]


def test_reaction_custom_emoji_id() -> None:
    t = SetMessageReactionTool()
    # is_big supports paid reactions
    assert "is_big" in t.json_schema["properties"]


def test_registry_knows_reactions() -> None:
    reg = ToolRegistry()
    reg.register(SetMessageReactionTool())
    assert len(reg.get_for_chat(["set_message_reaction"])) == 1
