from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.types import Message

    from mohizarbot.bot.api_wrapper import BotApiWrapper
    from mohizarbot.config import Settings
    from mohizarbot.multimodal.base import ProcessedContent

logger = logging.getLogger(__name__)


async def process_message_multimodal(
    message: Message,
    api: BotApiWrapper,
    settings: Settings,
) -> tuple[str, dict[str, object]]:
    """Check for multimodal content and process it.

    Returns (text_content, capability_hints) where:
      - text_content is the processed/extracted text (may be empty for images)
      - capability_hints may include {"vision": True} for image content

    If the message has no multimodal content, returns the text as-is.
    """
    from mohizarbot.multimodal.registry import get_processor

    mime_type, file_id, file_name = _detect_multimodal(message)

    if mime_type is None or file_id is None:
        # No multimodal content — plain text
        return message.text or "", {}

    logger.info(
        "Processing multimodal: mime=%s file_id=%s name=%s",
        mime_type,
        file_id,
        file_name,
    )

    processor = get_processor(mime_type, settings)
    if processor is None:
        logger.warning("No processor for MIME type: %s", mime_type)
        return message.text or "", {}

    # Download file
    try:
        file_bytes, actual_mime = await api.download_file(file_id)
    except Exception as e:
        logger.error("Failed to download file %s: %s", file_id, e)
        return message.text or "", {}

    # Use actual MIME from download if the declared one is generic
    if actual_mime and actual_mime != "application/octet-stream":
        mime_type = actual_mime
        # Re-resolve processor with actual mime
        processor = get_processor(mime_type, settings)
        if processor is None:
            logger.warning("No processor for actual MIME: %s", mime_type)
            return message.text or "", {}

    ctx: dict[str, object] = {
        "file_name": file_name,
        "file_id": file_id,
        "chat_id": message.chat.id,
        "user_id": message.from_user.id if message.from_user else 0,
        "settings": settings,
    }

    # For image messages with multiple photos, track the count
    if message.photo:
        ctx["image_count"] = len(message.photo)

    try:
        content: ProcessedContent = await processor.process(file_bytes, mime_type, ctx)
    except ValueError as e:
        logger.warning("Multimodal processing rejected: %s", e)
        return f"[File rejected: {e}]", {}
    except Exception as e:
        logger.error("Multimodal processing failed: %s", e)
        return f"[File processing error: {e}]", {}

    # Determine capability hints
    hints: dict[str, object] = {}
    if content.kind == "image_blocks" and content.image_blocks:
        hints["vision"] = True

    if content.warnings:
        logger.warning("Multimodal warnings: %s", content.warnings)

    return content.text, hints


def _detect_multimodal(message: Message) -> tuple[str | None, str | None, str]:
    """Detect the first multimodal content in a message.

    Returns (mime_type, file_id, file_name).
    Priority: voice > audio > photo > document.
    """
    # Voice message
    if message.voice:
        return (
            message.voice.mime_type or "audio/ogg",
            message.voice.file_id,
            "voice.ogg",
        )

    # Audio message
    if message.audio:
        return (
            message.audio.mime_type or "audio/mpeg",
            message.audio.file_id,
            message.audio.file_name or "audio.mp3",
        )

    # Photo (largest size)
    if message.photo:
        largest = sorted(message.photo, key=lambda p: p.width * p.height)[-1]
        return (
            "image/jpeg",
            largest.file_id,
            "photo.jpg",
        )

    # Document
    if message.document:
        doc = message.document
        return (
            doc.mime_type or "application/octet-stream",
            doc.file_id,
            doc.file_name or "document",
        )

    return None, None, ""


def build_multimodal_llm_content(
    processed_content: ProcessedContent,
    text: str,
) -> str | list[dict[str, object]]:
    """Build LLM-compatible content from processed multimodal data.

    For images: returns list of image blocks + text for vision-capable LLMs.
    For text-only: returns the text string.
    """
    if processed_content.kind == "image_blocks" and processed_content.image_blocks:
        parts: list[dict[str, object]] = []
        if text:
            parts.append({"type": "text", "text": text})
        for img in processed_content.image_blocks:
            parts.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": img.media_type,
                        "data": img.base64,
                    },
                }
            )
        return parts
    else:
        if text and processed_content.text:
            return f"{text}\n\n{processed_content.text}"
        return text or processed_content.text
