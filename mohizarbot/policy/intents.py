from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class BaseIntent(BaseModel):
    type: str


# ── Sprint 4 messaging ──
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


# ── Sprint 5 media ──
class SendPhotoIntent(BaseIntent):
    type: Literal["send_photo"] = "send_photo"
    chat_id: int
    photo: str  # file_id or URL
    caption: str | None = None


class SendDocumentIntent(BaseIntent):
    type: Literal["send_document"] = "send_document"
    chat_id: int
    document: str
    caption: str | None = None


class SendVideoIntent(BaseIntent):
    type: Literal["send_video"] = "send_video"
    chat_id: int
    video: str
    caption: str | None = None


class SendAudioIntent(BaseIntent):
    type: Literal["send_audio"] = "send_audio"
    chat_id: int
    audio: str
    caption: str | None = None


class SendVoiceIntent(BaseIntent):
    type: Literal["send_voice"] = "send_voice"
    chat_id: int
    voice: str


class SendStickerIntent(BaseIntent):
    type: Literal["send_sticker"] = "send_sticker"
    chat_id: int
    sticker: str


class SendLocationIntent(BaseIntent):
    type: Literal["send_location"] = "send_location"
    chat_id: int
    latitude: float
    longitude: float


# ── Sprint 5 polls ──
class SendPollIntent(BaseIntent):
    type: Literal["send_poll"] = "send_poll"
    chat_id: int
    question: str
    options: list[str]
    is_anonymous: bool = True
    allows_multiple_answers: bool = False


class StopPollIntent(BaseIntent):
    type: Literal["stop_poll"] = "stop_poll"
    chat_id: int
    message_id: int


# ── Sprint 5 reactions ──
class SetMessageReactionIntent(BaseIntent):
    type: Literal["set_message_reaction"] = "set_message_reaction"
    chat_id: int
    message_id: int
    reaction: list[str] | None = None  # emoji list
    is_big: bool = False


# ── Sprint 5 moderation ──
class BanChatMemberIntent(BaseIntent):
    type: Literal["ban_chat_member"] = "ban_chat_member"
    chat_id: int
    user_id: int
    until_date: int | None = None  # Unix timestamp, 0 = forever
    revoke_messages: bool = True


class UnbanChatMemberIntent(BaseIntent):
    type: Literal["unban_chat_member"] = "unban_chat_member"
    chat_id: int
    user_id: int


class RestrictChatMemberIntent(BaseIntent):
    type: Literal["restrict_chat_member"] = "restrict_chat_member"
    chat_id: int
    user_id: int
    permissions: dict[str, bool]  # can_send_messages, can_send_media, etc.
    until_date: int | None = None


class PromoteChatMemberIntent(BaseIntent):
    type: Literal["promote_chat_member"] = "promote_chat_member"
    chat_id: int
    user_id: int
    can_manage_chat: bool = False
    can_delete_messages: bool = False
    can_restrict_members: bool = False
    can_promote_members: bool = False
    can_change_info: bool = False
    can_invite_users: bool = False
    can_pin_messages: bool = False
    can_post_messages: bool = False


# ── Sprint 5 chat admin ──
class SetChatPermissionsIntent(BaseIntent):
    type: Literal["set_chat_permissions"] = "set_chat_permissions"
    chat_id: int
    permissions: dict[str, bool]


class PinChatMessageIntent(BaseIntent):
    type: Literal["pin_chat_message"] = "pin_chat_message"
    chat_id: int
    message_id: int
    disable_notification: bool = False


class UnpinChatMessageIntent(BaseIntent):
    type: Literal["unpin_chat_message"] = "unpin_chat_message"
    chat_id: int
    message_id: int | None = None  # None = unpin all


class SetChatTitleIntent(BaseIntent):
    type: Literal["set_chat_title"] = "set_chat_title"
    chat_id: int
    title: str


class SetChatDescriptionIntent(BaseIntent):
    type: Literal["set_chat_description"] = "set_chat_description"
    chat_id: int
    description: str


# ── Sprint 5 forum ──
class CreateForumTopicIntent(BaseIntent):
    type: Literal["create_forum_topic"] = "create_forum_topic"
    chat_id: int
    name: str
    icon_color: int | None = None
    icon_custom_emoji_id: str | None = None


class EditForumTopicIntent(BaseIntent):
    type: Literal["edit_forum_topic"] = "edit_forum_topic"
    chat_id: int
    message_thread_id: int
    name: str | None = None


class CloseForumTopicIntent(BaseIntent):
    type: Literal["close_forum_topic"] = "close_forum_topic"
    chat_id: int
    message_thread_id: int


class DeleteForumTopicIntent(BaseIntent):
    type: Literal["delete_forum_topic"] = "delete_forum_topic"
    chat_id: int
    message_thread_id: int


# ── Sprint 5 memory ──
class MemorySaveIntent(BaseIntent):
    type: Literal["memory_save"] = "memory_save"
    scope: str = "chat"
    content: str
    chat_id: int | None = None
    requires_owner_approval: bool = False


class MemoryDeleteIntent(BaseIntent):
    type: Literal["memory_delete"] = "memory_delete"
    entry_id: str


# ── Sprint 5 web ──
class WebFetchIntent(BaseIntent):
    type: Literal["web_fetch"] = "web_fetch"
    url: str
    max_size: int = 500000


class WebSearchIntent(BaseIntent):
    type: Literal["web_search"] = "web_search"
    query: str
    max_results: int = 5


# ── Sprint 10 inline keyboards ──
class SendMessageWithKeyboardIntent(BaseIntent):
    type: Literal["send_message_with_keyboard"] = "send_message_with_keyboard"
    chat_id: int
    text: str
    buttons: list[list[dict[str, object]]]  # serialized InlineButton rows


class EditReplyMarkupIntent(BaseIntent):
    type: Literal["edit_reply_markup"] = "edit_reply_markup"
    chat_id: int
    message_id: int
    buttons: list[list[dict[str, object]]]


# ── Sprint 10 media groups ──
class MediaItem(BaseModel):
    type: str  # photo, video, audio, document
    file_id_or_url: str
    caption: str | None = None


class SendMediaGroupIntent(BaseIntent):
    type: Literal["send_media_group"] = "send_media_group"
    chat_id: int
    media: list[MediaItem]


# ── Sprint 10 channel & scheduling ──
class PostToChannelIntent(BaseIntent):
    type: Literal["post_to_channel"] = "post_to_channel"
    channel_id: int
    text: str
    buttons: list[list[dict[str, object]]] | None = None
    schedule_ts: int | None = None  # Unix timestamp, None = post immediately


class EditChannelPostIntent(BaseIntent):
    type: Literal["edit_channel_post"] = "edit_channel_post"
    channel_id: int
    message_id: int
    text: str
    buttons: list[list[dict[str, object]]] | None = None


class CancelScheduledPostIntent(BaseIntent):
    type: Literal["cancel_scheduled_post"] = "cancel_scheduled_post"
    job_id: str


# ── Sprint 10 callback response ──
class CallbackResponseIntent(BaseIntent):
    type: Literal["callback_response"] = "callback_response"
    callback_query_id: str
    text: str | None = None
    show_alert: bool = False


# Discriminated union
Intent = Annotated[
    SendMessageIntent
    | EditMessageIntent
    | DeleteMessageIntent
    | ForwardMessageIntent
    | SendPhotoIntent
    | SendDocumentIntent
    | SendVideoIntent
    | SendAudioIntent
    | SendVoiceIntent
    | SendStickerIntent
    | SendLocationIntent
    | SendPollIntent
    | StopPollIntent
    | SetMessageReactionIntent
    | BanChatMemberIntent
    | UnbanChatMemberIntent
    | RestrictChatMemberIntent
    | PromoteChatMemberIntent
    | SetChatPermissionsIntent
    | PinChatMessageIntent
    | UnpinChatMessageIntent
    | SetChatTitleIntent
    | SetChatDescriptionIntent
    | CreateForumTopicIntent
    | EditForumTopicIntent
    | CloseForumTopicIntent
    | DeleteForumTopicIntent
    | MemorySaveIntent
    | MemoryDeleteIntent
    | WebFetchIntent
    | WebSearchIntent
    | SendMessageWithKeyboardIntent
    | EditReplyMarkupIntent
    | SendMediaGroupIntent
    | PostToChannelIntent
    | EditChannelPostIntent
    | CancelScheduledPostIntent
    | CallbackResponseIntent,
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
