from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable


@dataclass
class ImageBlock:
    """A vision-capable image block for LLM consumption.

    Attributes:
        base64: Base64-encoded image data (no data URI prefix).
        media_type: MIME type, e.g. "image/jpeg" or "image/png".
        source_uri: Optional Telegram file_id for provenance tracking.
    """

    base64: str
    media_type: str
    source_uri: str = ""


@dataclass
class ProcessedContent:
    """Result of processing a multimodal input.

    Attributes:
        kind: "text" for transcriptions/csv, "image_blocks" for photos.
        text: The extracted/transcribed text (may be empty for images).
        image_blocks: Vision-capable image blocks for multimodal LLM.
        metadata: Arbitrary key-value metadata about the input.
        warnings: Non-fatal issues encountered during processing.
    """

    kind: Literal["text", "image_blocks"]
    text: str
    image_blocks: list[ImageBlock] | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@runtime_checkable
class MultimodalProcessor(Protocol):
    """Protocol for multimodal processors (voice, image, document).

    Each processor handles a category of MIME types and returns
    ProcessedContent that is wrapped before being fed to the LLM.
    """

    async def process(
        self,
        file_bytes: bytes,
        mime_type: str,
        ctx: dict[str, object],
    ) -> ProcessedContent:
        """Process raw bytes into structured content.

        Args:
            file_bytes: Raw file content from Telegram download.
            mime_type: Detected MIME type.
            ctx: Context dict with keys like `file_name`, `file_id`,
                 `chat_id`, `user_id`, `settings`.
        """
        ...
