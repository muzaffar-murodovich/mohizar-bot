from __future__ import annotations

import asyncio
import math
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock

from mohizarbot.llm.streaming import DEBOUNCE_INTERVAL, stream_to_telegram
from mohizarbot.llm.types import StreamChunk

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


async def _chunk_stream(
    chunks: list[StreamChunk], delay: float = 0.05
) -> AsyncIterator[StreamChunk]:
    for chunk in chunks:
        await asyncio.sleep(delay)
        yield chunk


async def test_stream_chunks_accumulate_text() -> None:
    bot = AsyncMock()
    sent_msg = AsyncMock()
    sent_msg.message_id = 100
    bot.send_message.return_value = sent_msg
    bot.edit_message_text.return_value = None

    chunks = [
        StreamChunk(content_delta="Hello", index=0),
        StreamChunk(content_delta=" ", index=1),
        StreamChunk(content_delta="world", index=2, finish_reason="stop"),
    ]
    stream = _chunk_stream(chunks, delay=0.01)

    result = await stream_to_telegram(stream, bot, chat_id=123)
    assert result == "Hello world"
    assert bot.send_message.called or bot.edit_message_text.called


async def test_debounce_limits_edit_calls() -> None:
    """10 chunks over T seconds should produce ≤ ceil(T/1.2)+1 edit calls."""
    bot = AsyncMock()
    sent_msg = AsyncMock()
    sent_msg.message_id = 100
    bot.send_message.return_value = sent_msg
    bot.edit_message_text.return_value = None

    n_chunks = 10
    chunk_delay = 0.1  # total ~1s which is less than DEBOUNCE_INTERVAL
    chunks = [StreamChunk(content_delta="x", index=i) for i in range(n_chunks)]
    chunks[-1] = StreamChunk(content_delta="x", index=n_chunks - 1, finish_reason="stop")
    stream = _chunk_stream(chunks, delay=chunk_delay)

    await stream_to_telegram(stream, bot, chat_id=123)

    total_duration = n_chunks * chunk_delay
    max_edits = math.ceil(total_duration / DEBOUNCE_INTERVAL) + 1
    edit_count = bot.edit_message_text.call_count
    send_count = bot.send_message.call_count
    assert (edit_count + send_count) <= max_edits, (
        f"edit+sends ({edit_count + send_count}) > max {max_edits}"
    )


async def test_final_call_has_full_text() -> None:
    bot = AsyncMock()
    sent_msg = AsyncMock()
    sent_msg.message_id = 200
    bot.send_message.return_value = sent_msg
    bot.edit_message_text.return_value = None

    chunks = [
        StreamChunk(content_delta="AB", index=0),
        StreamChunk(content_delta="CD", index=1, finish_reason="stop"),
    ]
    stream = _chunk_stream(chunks, delay=0.01)

    await stream_to_telegram(stream, bot, chat_id=456)

    # Final edit should have complete text
    final_call = (
        bot.edit_message_text.call_args_list[-1] if bot.edit_message_text.call_args_list else None
    )
    if final_call:
        assert final_call.kwargs["text"] == "ABCD"


async def test_with_message_id_skips_send() -> None:
    bot = AsyncMock()
    bot.edit_message_text.return_value = None

    chunks = [
        StreamChunk(content_delta="X", index=0, finish_reason="stop"),
    ]
    stream = _chunk_stream(chunks, delay=0.01)

    await stream_to_telegram(stream, bot, chat_id=789, message_id=999)
    assert not bot.send_message.called
    assert bot.edit_message_text.called
