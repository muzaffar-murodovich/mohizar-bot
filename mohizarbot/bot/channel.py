from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiogram import Bot

logger = logging.getLogger(__name__)


@dataclass
class ChannelInfo:
    channel_id: int
    title: str = ""
    member_count: int = 0
    bot_is_admin: bool = False


@dataclass
class PostResult:
    status: str  # executed, denied
    reason: str = ""
    message_id: int | None = None
    telegram_response: dict[str, Any] | None = None


@dataclass
class ChannelManager:
    """Manages channel posting with admin precheck.

    All channel posts are HIGH risk by policy. The channel manager
    runs pre-flight checks (bot admin status) before executing.
    """

    bot: Bot
    allowed_channel_ids: list[int] = field(default_factory=list)

    async def get_channel_info(self, channel_id: int) -> ChannelInfo:
        """Fetch channel metadata and bot admin status."""
        try:
            chat = await self.bot.get_chat(channel_id)
            title = getattr(chat, "title", "") or getattr(chat, "first_name", "") or ""
        except Exception as e:
            logger.warning("get_chat failed for channel %d: %s", channel_id, e)
            return ChannelInfo(channel_id=channel_id, bot_is_admin=False)

        is_admin = False
        try:
            bot_id = (await self.bot.get_me()).id
            member = await self.bot.get_chat_member(channel_id, bot_id)
            status = str(getattr(member, "status", ""))
            is_admin = status in ("administrator", "creator")
        except Exception as e:
            logger.warning("get_chat_member failed for channel %d: %s", channel_id, e)

        return ChannelInfo(
            channel_id=channel_id,
            title=title,
            member_count=getattr(chat, "member_count", 0) if hasattr(chat, "member_count") else 0,
            bot_is_admin=is_admin,
        )

    def _is_allowed_channel(self, channel_id: int) -> bool:
        """Check if channel_id is in the allowed list."""
        if not self.allowed_channel_ids:
            return True  # no restriction configured
        return channel_id in self.allowed_channel_ids

    async def post_to_channel(
        self,
        channel_id: int,
        text: str,
        buttons: list[list[dict[str, object]]] | None = None,
        schedule_ts: int | None = None,
    ) -> PostResult:
        """Post a message to a channel.

        Precheck: bot must be channel admin.
        Uses send_message with optional inline keyboard.
        schedule_ts is consumed by the scheduler, not here.
        """
        if not self._is_allowed_channel(channel_id):
            return PostResult(status="denied", reason="channel_not_in_allowlist")

        info = await self.get_channel_info(channel_id)
        if not info.bot_is_admin:
            return PostResult(status="denied", reason="bot_not_channel_admin")

        kwargs: dict[str, Any] = {"chat_id": channel_id, "text": text}
        if buttons:
            kwargs["reply_markup"] = {"inline_keyboard": buttons}

        try:
            msg = await self.bot.send_message(**kwargs)
            msg_id = msg.message_id if hasattr(msg, "message_id") else None
            return PostResult(
                status="executed",
                message_id=msg_id,
                telegram_response=msg.model_dump() if hasattr(msg, "model_dump") else None,
            )
        except Exception as e:
            logger.error("post_to_channel failed for %d: %s", channel_id, e)
            return PostResult(status="denied", reason=str(e))

    async def edit_channel_post(
        self,
        channel_id: int,
        message_id: int,
        text: str,
        buttons: list[list[dict[str, object]]] | None = None,
    ) -> PostResult:
        """Edit an existing channel post."""
        if not self._is_allowed_channel(channel_id):
            return PostResult(status="denied", reason="channel_not_in_allowlist")

        info = await self.get_channel_info(channel_id)
        if not info.bot_is_admin:
            return PostResult(status="denied", reason="bot_not_channel_admin")

        kwargs: dict[str, Any] = {"chat_id": channel_id, "message_id": message_id, "text": text}
        if buttons:
            kwargs["reply_markup"] = {"inline_keyboard": buttons}

        try:
            msg = await self.bot.edit_message_text(**kwargs)
            return PostResult(
                status="executed",
                message_id=message_id,
                telegram_response=msg.model_dump() if hasattr(msg, "model_dump") else None,
            )
        except Exception as e:
            logger.error("edit_channel_post failed for %d: %s", channel_id, e)
            return PostResult(status="denied", reason=str(e))
