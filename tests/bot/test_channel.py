from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from mohizarbot.bot.channel import ChannelManager


class FakeMessage:
    def __init__(self, message_id: int) -> None:
        self.message_id = message_id

    def model_dump(self) -> dict[str, object]:
        return {"message_id": self.message_id, "ok": True}


class FakeChat:
    def __init__(self, chat_id: int, title: str = "TestChannel") -> None:
        self.id = chat_id
        self.title = title
        self.first_name = title
        self.member_count = 42


class FakeChatMember:
    def __init__(self, status: str) -> None:
        self.status = status


class FakeBotMe:
    def __init__(self, bot_id: int) -> None:
        self.id = bot_id


@pytest.fixture
def bot_admin() -> AsyncMock:
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=FakeBotMe(999))
    bot.get_chat = AsyncMock(return_value=FakeChat(-100123, "MyChannel"))
    bot.get_chat_member = AsyncMock(return_value=FakeChatMember("administrator"))
    bot.send_message = AsyncMock(return_value=FakeMessage(42))
    bot.edit_message_text = AsyncMock(return_value=FakeMessage(42))
    return bot


@pytest.fixture
def bot_not_admin() -> AsyncMock:
    bot = AsyncMock()
    bot.get_me = AsyncMock(return_value=FakeBotMe(999))
    bot.get_chat = AsyncMock(return_value=FakeChat(-100123, "MyChannel"))
    bot.get_chat_member = AsyncMock(return_value=FakeChatMember("member"))
    return bot


async def test_post_to_channel_success(bot_admin: AsyncMock) -> None:
    mgr = ChannelManager(bot=bot_admin)
    result = await mgr.post_to_channel(-100123, "Hello world!")
    assert result.status == "executed"
    assert result.message_id == 42
    bot_admin.send_message.assert_awaited_once_with(chat_id=-100123, text="Hello world!")


async def test_post_to_channel_bot_not_admin(bot_not_admin: AsyncMock) -> None:
    mgr = ChannelManager(bot=bot_not_admin)
    result = await mgr.post_to_channel(-100123, "Hello!")
    assert result.status == "denied"
    assert result.reason == "bot_not_channel_admin"


async def test_get_channel_info_admin(bot_admin: AsyncMock) -> None:
    mgr = ChannelManager(bot=bot_admin)
    info = await mgr.get_channel_info(-100123)
    assert info.bot_is_admin is True
    assert info.title == "MyChannel"


async def test_get_channel_info_not_admin(bot_not_admin: AsyncMock) -> None:
    mgr = ChannelManager(bot=bot_not_admin)
    info = await mgr.get_channel_info(-100123)
    assert info.bot_is_admin is False


async def test_post_to_channel_with_keyboard(bot_admin: AsyncMock) -> None:
    mgr = ChannelManager(bot=bot_admin)
    buttons = [[{"text": "Click", "callback_data": "abc"}]]
    result = await mgr.post_to_channel(-100123, "Choose:", buttons)
    assert result.status == "executed"
    call_args = bot_admin.send_message.call_args
    assert call_args is not None
    kwargs = call_args.kwargs
    assert "reply_markup" in kwargs


async def test_post_to_channel_not_in_allowlist(bot_admin: AsyncMock) -> None:
    mgr = ChannelManager(bot=bot_admin, allowed_channel_ids=[-100999])
    result = await mgr.post_to_channel(-100123, "Hello!")
    assert result.status == "denied"
    assert result.reason == "channel_not_in_allowlist"


async def test_post_to_channel_in_allowlist(bot_admin: AsyncMock) -> None:
    mgr = ChannelManager(bot=bot_admin, allowed_channel_ids=[-100123])
    result = await mgr.post_to_channel(-100123, "Hello!")
    assert result.status == "executed"


async def test_edit_channel_post(bot_admin: AsyncMock) -> None:
    mgr = ChannelManager(bot=bot_admin)
    result = await mgr.edit_channel_post(-100123, 42, "Updated text")
    assert result.status == "executed"
    bot_admin.edit_message_text.assert_awaited_once_with(
        chat_id=-100123, message_id=42, text="Updated text"
    )


async def test_edit_channel_post_not_admin(bot_not_admin: AsyncMock) -> None:
    mgr = ChannelManager(bot=bot_not_admin)
    result = await mgr.edit_channel_post(-100123, 42, "Updated")
    assert result.status == "denied"
    assert result.reason == "bot_not_channel_admin"
