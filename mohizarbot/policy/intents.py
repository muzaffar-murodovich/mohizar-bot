from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class BaseIntent(BaseModel):
    type: str


class SendMessageIntent(BaseIntent):
    type: Literal["send_message"] = "send_message"
    chat_id: int
    text: str
    reply_to_message_id: int | None = None


class EditMessageIntent(BaseIntent):
    type: Literal["edit_message"] = "edit_message"
    chat_id: int
    message_id: int
    text: str


class DeleteMessageIntent(BaseIntent):
    type: Literal["delete_message"] = "delete_message"
    chat_id: int
    message_id: int


class ForwardMessageIntent(BaseIntent):
    type: Literal["forward_message"] = "forward_message"
    from_chat_id: int
    message_id: int
    to_chat_id: int


# Discriminated union
Intent = Annotated[
    SendMessageIntent | EditMessageIntent | DeleteMessageIntent | ForwardMessageIntent,
    Field(discriminator="type"),
]


class IntentBatch(BaseModel):
    actions: list[Intent]
    thought: str = ""

    @model_validator(mode="after")
    def check_empty(self) -> IntentBatch:
        if not self.actions:
            raise ValueError("IntentBatch must have at least one action")
        return self
