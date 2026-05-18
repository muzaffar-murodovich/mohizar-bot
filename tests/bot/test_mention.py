from __future__ import annotations

from datetime import datetime

from aiogram.types import Chat, Message, MessageEntity, User

from mohizarbot.bot.mention import is_bot_mentioned


def _make_msg(text: str, entities: list | None = None, reply: object = None) -> Message:
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test"),
        date=datetime(2024, 1, 1),
        chat=Chat(id=-100, type="group", first_name="Test Group"),
        text=text,
        entities=entities,
        reply_to_message=reply,
        forward_origin=None,
        sender_chat=None,
        author_signature=None,
        animation=None,
        audio=None,
        document=None,
        photo=None,
        sticker=None,
        story=None,
        video=None,
        video_note=None,
        voice=None,
        contact=None,
        dice=None,
        game=None,
        poll=None,
        venue=None,
        location=None,
        invoice=None,
        successful_payment=None,
        connected_website=None,
        passport_data=None,
        proximity_alert_triggered=None,
        boost_added=None,
        forum_topic_created=None,
        forum_topic_closed=None,
        forum_topic_reopened=None,
        forum_topic_edited=None,
        general_forum_topic_hidden=None,
        general_forum_topic_unhidden=None,
        write_access_allowed=None,
        users_shared=None,
        chat_shared=None,
        pinned_message=None,
        external_reply=None,
        quote=None,
        caption=None,
        caption_entities=None,
        new_chat_members=None,
        left_chat_member=None,
        new_chat_title=None,
        new_chat_photo=None,
        delete_chat_photo=None,
        group_chat_created=None,
        supergroup_chat_created=None,
        channel_chat_created=None,
        message_auto_delete_timer_changed=None,
        migrate_to_chat_id=None,
        migrate_from_chat_id=None,
        web_app_data=None,
        reply_markup=None,
    )


def test_at_mention_detected() -> None:
    entities = [MessageEntity(type="mention", offset=0, length=11)]
    msg = _make_msg("@mohizarbot hello", entities=entities)
    assert is_bot_mentioned(msg, "mohizarbot")


def test_command_at_bot_detected() -> None:
    entities = [MessageEntity(type="bot_command", offset=0, length=18)]
    msg = _make_msg("/start@mohizarbot", entities=entities)
    assert is_bot_mentioned(msg, "mohizarbot")


def test_reply_to_bot_detected() -> None:
    reply = _make_msg(
        "bot reply",
        reply=Message(
            message_id=42,
            from_user=User(id=999, is_bot=True, first_name="mohizarbot"),
            date=datetime(2024, 1, 1),
            chat=Chat(id=-100, type="group"),
        ),
    )
    assert is_bot_mentioned(reply, "mohizarbot")


def test_case_insensitive() -> None:
    entities = [MessageEntity(type="mention", offset=0, length=11)]
    msg = _make_msg("@MoHiZaRbOt hi", entities=entities)
    assert is_bot_mentioned(msg, "mohizarbot")


def test_non_bot_not_detected() -> None:
    entities = [MessageEntity(type="mention", offset=0, length=4)]
    msg = _make_msg("@bob hello", entities=entities)
    assert not is_bot_mentioned(msg, "mohizarbot")


def test_no_mention_no_reply_not_detected() -> None:
    msg = _make_msg("Hello everyone!")
    assert not is_bot_mentioned(msg, "mohizarbot")
