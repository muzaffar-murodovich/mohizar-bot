from __future__ import annotations

from mohizarbot.policy.risk import is_high_risk
from mohizarbot.tools.forum import (
    CloseForumTopicTool,
    CreateForumTopicTool,
    DeleteForumTopicTool,
    EditForumTopicTool,
)
from mohizarbot.tools.registry import ToolRegistry


def test_create_topic() -> None:
    t = CreateForumTopicTool()
    assert t.name == "create_forum_topic"


def test_edit_topic() -> None:
    t = EditForumTopicTool()
    assert "message_thread_id" in t.json_schema["required"]


def test_close_topic() -> None:
    t = CloseForumTopicTool()
    assert t.name == "close_forum_topic"


def test_delete_topic_is_high_risk() -> None:
    assert is_high_risk("delete_forum_topic")


def test_delete_topic_precheck() -> None:
    t = DeleteForumTopicTool()
    assert "can_manage_topics" in t.required_bot_rights


def test_registry_forum() -> None:
    reg = ToolRegistry()
    reg.register(CreateForumTopicTool())
    reg.register(EditForumTopicTool())
    reg.register(CloseForumTopicTool())
    reg.register(DeleteForumTopicTool())
    assert len(reg.get_for_chat(["create_forum_topic", "delete_forum_topic"])) == 2
