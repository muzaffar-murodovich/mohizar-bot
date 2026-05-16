from __future__ import annotations

from datetime import datetime

from aiogram.types import Chat, Message, Update, User


async def test_no_mention_skips() -> None:
    """Group message without mention should be silently skipped."""
    from mohizarbot.bot.mention import is_bot_mentioned

    msg = Message(
        message_id=1,
        from_user=User(id=456, is_bot=False, first_name="User"),
        date=datetime(2024, 1, 1),
        chat=Chat(id=-100, type="group", first_name="Test"),
        text="regular chat message",
    )
    assert not is_bot_mentioned(msg, "mohizarbot")


async def test_mention_triggers_group_handler() -> None:
    """@mention should trigger the group handler."""
    from aiogram.types import MessageEntity

    from mohizarbot.bot.mention import is_bot_mentioned

    entities = [MessageEntity(type="mention", offset=0, length=11)]
    msg = Message(
        message_id=2,
        from_user=User(id=789, is_bot=False, first_name="User"),
        date=datetime(2024, 1, 1),
        chat=Chat(id=-200, type="group", first_name="Test"),
        text="@mohizarbot help",
        entities=entities,
    )
    assert is_bot_mentioned(msg, "mohizarbot")


async def test_channel_post_noop() -> None:
    """Channel posts should be silently ignored."""
    update = Update(
        update_id=1,
        channel_post=Message(
            message_id=3,
            date=datetime(2024, 1, 1),
            chat=Chat(id=-300, type="channel", title="Channel"),
        ),
    )
    assert update.channel_post is not None
    assert update.message is None
