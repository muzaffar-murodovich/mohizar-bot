from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mohizarbot.multimodal.document import DocumentProcessor
from mohizarbot.multimodal.document import supports_mime as doc_supports
from mohizarbot.multimodal.image import ImageProcessor
from mohizarbot.multimodal.image import supports_mime as img_supports
from mohizarbot.multimodal.voice import VoiceProcessor
from mohizarbot.multimodal.voice import supports_mime as voice_supports

if TYPE_CHECKING:
    from mohizarbot.config import Settings
    from mohizarbot.multimodal.base import MultimodalProcessor

logger = logging.getLogger(__name__)


def get_processor(mime_type: str, settings: Settings) -> MultimodalProcessor | None:
    """Return the appropriate MultimodalProcessor for a given MIME type.

    Resolution order:
      - audio/* and voice/* → VoiceProcessor
      - image/* → ImageProcessor
      - application/pdf, docx, text/* → DocumentProcessor
      - Everything else → None

    Args:
        mime_type: The MIME type string (e.g. "audio/ogg", "image/jpeg").
        settings: Application settings (for API keys, limits, etc.).

    Returns:
        A MultimodalProcessor instance or None if unrecognized.
    """
    if voice_supports(mime_type):
        return VoiceProcessor(settings)
    if img_supports(mime_type):
        return ImageProcessor(settings)
    if doc_supports(mime_type):
        return DocumentProcessor(settings)
    return None
