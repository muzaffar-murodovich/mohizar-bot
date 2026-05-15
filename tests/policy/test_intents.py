from __future__ import annotations

import pytest
from pydantic import ValidationError

from mohizarbot.policy.intents import (
    DeleteMessageIntent,
    EditMessageIntent,
    ForwardMessageIntent,
    IntentBatch,
    SendMessageIntent,
)


def test_parse_send_message() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [{"type": "send_message", "chat_id": 1, "text": "hi"}],
            "thought": "greeting",
        }
    )
    assert len(batch.actions) == 1
    intent = batch.actions[0]
    assert isinstance(intent, SendMessageIntent)
    assert intent.type == "send_message"
    assert intent.chat_id == 1
    assert intent.text == "hi"


def test_parse_edit_message() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [{"type": "edit_message", "chat_id": 2, "message_id": 10, "text": "fixed"}],
        }
    )
    assert isinstance(batch.actions[0], EditMessageIntent)


def test_parse_delete_message() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [{"type": "delete_message", "chat_id": 3, "message_id": 20}],
        }
    )
    assert isinstance(batch.actions[0], DeleteMessageIntent)


def test_parse_forward_message() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {
                    "type": "forward_message",
                    "from_chat_id": 10,
                    "message_id": 50,
                    "to_chat_id": 20,
                }
            ],
        }
    )
    assert isinstance(batch.actions[0], ForwardMessageIntent)


def test_unknown_type_rejected() -> None:
    with pytest.raises(ValidationError):
        IntentBatch.model_validate(
            {
                "actions": [{"type": "ban_user", "chat_id": 1, "user_id": 99}],
            }
        )


def test_empty_actions_rejected() -> None:
    with pytest.raises(ValidationError):
        IntentBatch.model_validate({"actions": []})


def test_missing_required_field() -> None:
    with pytest.raises(ValidationError):
        IntentBatch.model_validate(
            {
                "actions": [{"type": "send_message", "chat_id": 1}],  # missing "text"
            }
        )


def test_multiple_actions() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [
                {"type": "send_message", "chat_id": 1, "text": "one"},
                {"type": "send_message", "chat_id": 2, "text": "two"},
            ],
        }
    )
    assert len(batch.actions) == 2


def test_thought_is_optional() -> None:
    batch = IntentBatch.model_validate(
        {
            "actions": [{"type": "send_message", "chat_id": 1, "text": "hi"}],
        }
    )
    assert batch.thought == ""
