from __future__ import annotations

import pytest
from pydantic import ValidationError

from mohizarbot.policy.intents import (
    CallbackResponseIntent,
    CancelScheduledPostIntent,
    EditChannelPostIntent,
    EditReplyMarkupIntent,
    IntentBatch,
    PostToChannelIntent,
    SendMediaGroupIntent,
    SendMessageWithKeyboardIntent,
)


def test_parse_send_message_with_keyboard() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {
                    "type": "send_message_with_keyboard",
                    "chat_id": 1,
                    "text": "Choose:",
                    "buttons": [[{"text": "Yes", "callback_data": "yes"}]],
                }
            ]
        }
    )
    intent = batch.actions[0]
    assert isinstance(intent, SendMessageWithKeyboardIntent)
    assert intent.text == "Choose:"
    assert len(intent.buttons) == 1


def test_parse_edit_reply_markup() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {
                    "type": "edit_reply_markup",
                    "chat_id": 2,
                    "message_id": 42,
                    "buttons": [[{"text": "Updated", "callback_data": "u"}]],
                }
            ]
        }
    )
    intent = batch.actions[0]
    assert isinstance(intent, EditReplyMarkupIntent)
    assert intent.message_id == 42


def test_parse_send_media_group() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {
                    "type": "send_media_group",
                    "chat_id": 3,
                    "media": [
                        {"type": "photo", "file_id_or_url": "f1", "caption": "Look"},
                        {"type": "video", "file_id_or_url": "f2"},
                    ],
                }
            ]
        }
    )
    intent = batch.actions[0]
    assert isinstance(intent, SendMediaGroupIntent)
    assert len(intent.media) == 2
    assert intent.media[0].caption == "Look"
    assert intent.media[1].caption is None


def test_parse_post_to_channel() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {
                    "type": "post_to_channel",
                    "channel_id": -100123,
                    "text": "Announcement",
                }
            ]
        }
    )
    intent = batch.actions[0]
    assert isinstance(intent, PostToChannelIntent)
    assert intent.channel_id == -100123
    assert intent.schedule_ts is None
    assert intent.buttons is None


def test_parse_post_to_channel_scheduled() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {
                    "type": "post_to_channel",
                    "channel_id": -100123,
                    "text": "Later",
                    "schedule_ts": 1717200000,
                }
            ]
        }
    )
    intent = batch.actions[0]
    assert isinstance(intent, PostToChannelIntent)
    assert intent.schedule_ts == 1717200000


def test_parse_edit_channel_post() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {
                    "type": "edit_channel_post",
                    "channel_id": -100123,
                    "message_id": 5,
                    "text": "Corrected",
                    "buttons": [[{"text": "OK", "callback_data": "ok"}]],
                }
            ]
        }
    )
    intent = batch.actions[0]
    assert isinstance(intent, EditChannelPostIntent)
    assert intent.message_id == 5


def test_parse_cancel_scheduled_post() -> None:
    batch = IntentBatch.model_validate(
        {"actions": [{"type": "cancel_scheduled_post", "job_id": "post_123_1717200000_456"}]}
    )
    intent = batch.actions[0]
    assert isinstance(intent, CancelScheduledPostIntent)
    assert intent.job_id == "post_123_1717200000_456"


def test_parse_callback_response() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {
                    "type": "callback_response",
                    "callback_query_id": "cbq_abc123",
                    "text": "Got it!",
                    "show_alert": True,
                }
            ]
        }
    )
    intent = batch.actions[0]
    assert isinstance(intent, CallbackResponseIntent)
    assert intent.callback_query_id == "cbq_abc123"
    assert intent.show_alert is True


def test_callback_response_no_text() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {
                    "type": "callback_response",
                    "callback_query_id": "cbq_xyz",
                }
            ]
        }
    )
    intent = batch.actions[0]
    assert intent.text is None
    assert intent.show_alert is False


def test_unknown_type_rejected() -> None:
    with pytest.raises(ValidationError):
        IntentBatch.model_validate({"actions": [{"type": "unknown_intent_type"}]})


def test_post_to_channel_missing_required() -> None:
    with pytest.raises(ValidationError):
        IntentBatch.model_validate(
            {"actions": [{"type": "post_to_channel", "text": "Missing channel_id"}]}
        )


def test_media_group_empty_media() -> None:
    batch = IntentBatch.model_validate(
        {"actions": [{"type": "send_media_group", "chat_id": 1, "media": []}]}
    )
    intent = batch.actions[0]
    assert len(intent.media) == 0
