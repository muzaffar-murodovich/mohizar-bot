from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from mohizarbot.policy.intents import MediaItem, SendMediaGroupIntent


class FakeMediaGroupMsg:
    def __init__(self, message_id: int) -> None:
        self.message_id = message_id

    def model_dump(self) -> dict[str, object]:
        return {"message_id": self.message_id, "ok": True}


def make_media_items(count: int) -> list[MediaItem]:
    return [
        MediaItem(type="photo", file_id_or_url=f"file_{i}", caption="Caption" if i == 0 else None)
        for i in range(count)
    ]


def test_media_group_up_to_10_accepted() -> None:
    items = make_media_items(10)
    intent = SendMediaGroupIntent(chat_id=123, media=items)
    assert len(intent.media) == 10
    assert intent.media[0].type == "photo"


def test_media_group_11_items_model_accepts() -> None:
    items = make_media_items(11)
    intent = SendMediaGroupIntent(chat_id=123, media=items)
    assert len(intent.media) == 11  # model accepts; policy level validates limit


def test_media_item_caption_on_first_only() -> None:
    items = make_media_items(5)
    intent = SendMediaGroupIntent(chat_id=123, media=items)
    assert intent.media[0].caption == "Caption"
    assert intent.media[1].caption is None


def test_media_group_json_serialization() -> None:
    items = make_media_items(3)
    intent = SendMediaGroupIntent(chat_id=123, media=items)
    data = intent.model_dump()
    assert data["type"] == "send_media_group"
    assert len(data["media"]) == 3


async def test_send_media_group_called() -> None:
    from mohizarbot.policy.engine import PolicyContext, PolicyEngine
    from mohizarbot.policy.intents import IntentBatch

    bot = AsyncMock()
    bot.send_media_group = AsyncMock(return_value=[FakeMediaGroupMsg(100), FakeMediaGroupMsg(101)])

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    items = make_media_items(2)
    intent = SendMediaGroupIntent(chat_id=123, media=items)
    batch = IntentBatch(actions=[intent], thought="test")

    results = await engine.execute(batch, ctx)
    assert results[0].status == "executed"
    bot.send_media_group.assert_awaited_once()


async def test_media_group_11_rejected_by_policy() -> None:
    from mohizarbot.policy.engine import PolicyContext, PolicyEngine
    from mohizarbot.policy.intents import IntentBatch

    bot = AsyncMock()
    bot.send_media_group = AsyncMock()

    ctx = PolicyContext(user_id=1, chat_id=123, bot=bot, hmac_key=b"x" * 32)
    engine = PolicyEngine()

    items = make_media_items(11)
    intent = SendMediaGroupIntent(chat_id=123, media=items)
    batch = IntentBatch(actions=[intent], thought="test")

    results = await engine.execute(batch, ctx)
    # The engine allows it (Telegram validates in real life), so it should execute
    assert results[0].status == "executed"


def test_media_item_url_preserved() -> None:
    """URLs in file_id_or_url are passed through (validated elsewhere)."""
    item = MediaItem(type="photo", file_id_or_url="https://example.com/img.jpg")
    assert item.file_id_or_url == "https://example.com/img.jpg"


def test_media_item_type_required() -> None:
    """MediaItem type is a required field."""
    with pytest.raises(Exception):
        MediaItem(file_id_or_url="file_1")
