from __future__ import annotations

import base64
import logging
from typing import TYPE_CHECKING

from mohizarbot.multimodal.base import ImageBlock, MultimodalProcessor, ProcessedContent

if TYPE_CHECKING:
    from mohizarbot.config import Settings

logger = logging.getLogger(__name__)

_IMAGE_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/bmp",
        "image/tiff",
    }
)

_MAX_IMAGES_PER_MESSAGE = 5
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class ImageProcessor(MultimodalProcessor):
    """Processes photo/image documents into ImageBlock list.

    Strips EXIF metadata for privacy. Returns vision-capable
    image blocks for multimodal LLM providers.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def process(
        self,
        file_bytes: bytes,
        mime_type: str,
        ctx: dict[str, object],
    ) -> ProcessedContent:
        """Convert image bytes to vision-compatible ImageBlock list.

        Args:
            file_bytes: Raw image bytes.
            mime_type: MIME type (must be image/*).
            ctx: May contain `image_count` (int) for multi-image tracking
                 and `file_id` (str) for provenance.

        Returns:
            ProcessedContent with kind="image_blocks" and image_blocks populated.
        """
        warnings: list[str] = []

        if len(file_bytes) > _MAX_FILE_SIZE_BYTES:
            mb = len(file_bytes) / (1024 * 1024)
            raise ValueError(f"Image file too large: {mb:.1f}MB (max 10MB)")

        image_count_raw = ctx.get("image_count", 1)
        image_count = int(image_count_raw) if isinstance(image_count_raw, int) else 1
        if image_count > _MAX_IMAGES_PER_MESSAGE:
            raise ValueError(f"Too many images: {image_count} (max {_MAX_IMAGES_PER_MESSAGE})")

        # Strip EXIF by re-encoding through a minimal parse
        # We detect JPEG EXIF and strip it; for other formats we pass through.
        cleaned_bytes = _strip_exif(file_bytes, mime_type)

        b64_data = base64.b64encode(cleaned_bytes).decode("ascii")
        file_id = str(ctx.get("file_id", ""))

        image_block = ImageBlock(
            base64=b64_data,
            media_type=mime_type,
            source_uri=file_id,
        )

        metadata = {
            "source_kind": "image",
            "file_id": file_id,
            "mime_type": mime_type,
        }

        return ProcessedContent(
            kind="image_blocks",
            text="",
            image_blocks=[image_block],
            metadata=metadata,
            warnings=warnings,
        )


def _strip_exif(data: bytes, mime_type: str) -> bytes:
    """Strip EXIF metadata from JPEG images. Other formats pass through."""
    if mime_type not in ("image/jpeg", "image/jpg"):
        return data

    # JPEG EXIF starts at byte 2 (after 0xFF 0xD8), marker 0xFF 0xE1
    # We strip everything between SOI (0xFFD8) and SOS markers, keeping only
    # the bare minimum header.
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return data

    pos = 2
    cleaned = bytearray(b"\xff\xd8")  # SOI

    while pos < len(data) - 1:
        if data[pos] != 0xFF:
            break
        marker = data[pos + 1]
        # SOS marker — start of scan, keep rest as-is
        if marker == 0xDA:
            cleaned.extend(data[pos:])
            return bytes(cleaned)
        # Standalone 0xFF, skip
        if marker == 0xFF:
            pos += 1
            continue
        # RST markers (0xD0-0xD7), skip
        if 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        # Variable-length markers — read length and skip
        if pos + 2 >= len(data):
            break
        length = (data[pos + 2] << 8) | data[pos + 3]
        pos += 2 + length

    return bytes(cleaned)


def supports_mime(mime_type: str) -> bool:
    """Check whether this processor can handle the given MIME type."""
    return mime_type.startswith("image/")
