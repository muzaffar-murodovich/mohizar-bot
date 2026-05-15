from __future__ import annotations

import contextlib
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from aiogram import Bot

    from mohizarbot.llm.types import StreamChunk

DEBOUNCE_INTERVAL = 1.2


async def stream_to_telegram(
    stream: AsyncIterator[StreamChunk],
    bot: Bot,
    chat_id: int,
    message_id: int | None = None,
) -> str:
    """Consume a stream of StreamChunks and edit a Telegram message in-place.

    Debounces edits to ≤1 per DEBOUNCE_INTERVAL seconds to avoid rate limits.
    If message_id is None, sends a new message first, then edits it.

    Returns the full accumulated text.
    """
    full_text = ""
    last_edit_time = 0.0

    async def _maybe_edit(force: bool = False) -> None:
        nonlocal last_edit_time, message_id
        now = time.monotonic()
        if not force and (now - last_edit_time) < DEBOUNCE_INTERVAL:
            return
        if message_id is not None and full_text:
            with contextlib.suppress(Exception):
                await bot.edit_message_text(
                    text=full_text,
                    chat_id=chat_id,
                    message_id=message_id,
                )
        last_edit_time = now

    async for chunk in stream:
        full_text += chunk.content_delta

        if message_id is None and full_text:
            sent = await bot.send_message(chat_id=chat_id, text=full_text)
            message_id = sent.message_id
            last_edit_time = time.monotonic()
        else:
            await _maybe_edit()

        if chunk.finish_reason:
            break

    # Final edit with full text
    if message_id is not None:
        with contextlib.suppress(Exception):
            await bot.edit_message_text(
                text=full_text,
                chat_id=chat_id,
                message_id=message_id,
            )

    return full_text
