from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import httpx

from mohizarbot.multimodal.base import MultimodalProcessor, ProcessedContent

if TYPE_CHECKING:
    from mohizarbot.config import Settings

logger = logging.getLogger(__name__)

# Supported audio MIME types and their extensions
_AUDIO_MIME_TYPES = frozenset(
    {
        "audio/ogg",
        "audio/opus",
        "audio/mpeg",
        "audio/mp4",
        "audio/wav",
        "audio/x-wav",
        "audio/webm",
        "audio/mp3",  # Some clients report this
        "audio/m4a",
        "audio/x-m4a",
    }
)

_MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


class VoiceProcessor(MultimodalProcessor):
    """Transcribes voice/audio via OpenAI Whisper API.

    Uses httpx directly — no OpenAI SDK dependency.
    Supports OGA/Opus, MP3, M4A, WAV, and WebM inputs.
    """

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.whisper_api_key
        self._base_url = settings.whisper_base_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0),
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
        return self._client

    async def process(
        self,
        file_bytes: bytes,
        mime_type: str,
        ctx: dict[str, object],
    ) -> ProcessedContent:
        """Transcribe audio/voice using Whisper API.

        Args:
            file_bytes: Raw audio file bytes.
            mime_type: MIME type of the audio.
            ctx: Must contain `file_name` (str) or `file_id` (str).

        Returns:
            ProcessedContent with kind="text" and transcription as text,
            wrapped in <transcription> tags.
        """
        warnings: list[str] = []

        if len(file_bytes) > _MAX_FILE_SIZE_BYTES:
            mb = len(file_bytes) / (1024 * 1024)
            raise ValueError(f"Audio file too large: {mb:.1f}MB (max 25MB)")

        if mime_type not in _AUDIO_MIME_TYPES:
            warnings.append(f"Unrecognized audio MIME type: {mime_type}")

        file_name = str(ctx.get("file_name", ctx.get("file_id", "audio.ogg")))

        # Determine extension for Whisper file upload
        ext_map = {
            "audio/ogg": "ogg",
            "audio/opus": "ogg",
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/mp4": "m4a",
            "audio/m4a": "m4a",
            "audio/x-m4a": "m4a",
            "audio/wav": "wav",
            "audio/x-wav": "wav",
            "audio/webm": "webm",
        }
        ext = ext_map.get(mime_type, "ogg")

        client = await self._get_client()
        try:
            response = await client.post(
                f"{self._base_url}/audio/transcriptions",
                files={"file": (f"audio.{ext}", file_bytes, mime_type)},
                data={"model": "whisper-1", "response_format": "verbose_json"},
            )
            response.raise_for_status()
            result = response.json()
        except httpx.HTTPStatusError as e:
            logger.error("Whisper API error: %s", e)
            raise RuntimeError(f"Whisper transcription failed: {e}") from e

        transcription = result.get("text", "")
        lang = result.get("language", "unknown")
        duration = result.get("duration", 0)

        metadata = {
            "source_kind": "voice",
            "duration_sec": str(duration),
            "lang": lang,
            "file_name": file_name,
        }

        wrapped = (
            f'<transcription source_kind="voice" duration_sec="{duration}" lang="{lang}">\n'
            f"{transcription}\n"
            f"</transcription>"
        )

        return ProcessedContent(
            kind="text",
            text=wrapped,
            metadata=metadata,
            warnings=warnings,
        )


def supports_mime(mime_type: str) -> bool:
    """Check whether this processor can handle the given MIME type."""
    return mime_type.startswith("audio/") or mime_type.startswith("voice/")
