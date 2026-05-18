from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from respx import MockRouter

from mohizarbot.config import Settings
from mohizarbot.multimodal.voice import VoiceProcessor, supports_mime


@pytest.fixture
def voice_settings() -> Settings:
    return Settings(  # type: ignore[call-arg]
        whisper_api_key="test-whisper-key",
        whisper_base_url="https://api.openai.com/v1",
    )


@pytest.fixture
def voice_processor(voice_settings: Settings) -> VoiceProcessor:
    return VoiceProcessor(voice_settings)


@pytest.mark.asyncio
async def test_transcribe_oga_via_whisper(
    voice_processor: VoiceProcessor, respx_mock: MockRouter
) -> None:
    """OGA/Opus audio is transcribed via Whisper API."""
    respx_mock.post("https://api.openai.com/v1/audio/transcriptions").respond(
        json={"text": "Hello world", "language": "en", "duration": 3.5}
    )

    audio_bytes = b"\x00" * 1024  # fake OGA
    result = await voice_processor.process(
        audio_bytes,
        "audio/ogg",
        {"file_name": "voice.oga", "file_id": "abc123"},
    )

    assert result.kind == "text"
    assert "Hello world" in result.text
    assert 'source_kind="voice"' in result.text
    assert 'duration_sec="3.5"' in result.text
    assert 'lang="en"' in result.text
    assert result.metadata["lang"] == "en"


@pytest.mark.asyncio
async def test_transcribe_mp3_via_whisper(
    voice_processor: VoiceProcessor, respx_mock: MockRouter
) -> None:
    """MP3 audio is transcribed via Whisper API."""
    respx_mock.post("https://api.openai.com/v1/audio/transcriptions").respond(
        json={"text": "This is MP3 content", "language": "ru", "duration": 10.0}
    )

    audio_bytes = b"\xff\xfb\x90\x00" * 256  # fake MP3
    result = await voice_processor.process(
        audio_bytes,
        "audio/mpeg",
        {"file_name": "audio.mp3", "file_id": "mp3_1"},
    )

    assert result.kind == "text"
    assert "This is MP3 content" in result.text
    assert 'lang="ru"' in result.text
    assert 'duration_sec="10.0"' in result.text


@pytest.mark.asyncio
async def test_oversized_audio_rejected(voice_processor: VoiceProcessor) -> None:
    """Audio files > 25MB are rejected with ValueError."""
    oversized = b"\x00" * (25 * 1024 * 1024 + 1)

    with pytest.raises(ValueError, match="too large"):
        await voice_processor.process(
            oversized,
            "audio/ogg",
            {"file_name": "huge.ogg", "file_id": "big1"},
        )


@pytest.mark.asyncio
async def test_non_audio_mime_warns(
    voice_processor: VoiceProcessor, respx_mock: MockRouter
) -> None:
    """Unrecognized MIME type produces a warning but still attempts transcription."""
    respx_mock.post("https://api.openai.com/v1/audio/transcriptions").respond(
        json={"text": "still works", "language": "en", "duration": 1.0}
    )

    result = await voice_processor.process(
        b"\x00" * 100,
        "audio/x-unknown",
        {"file_name": "mystery.audio", "file_id": "unk1"},
    )

    assert len(result.warnings) >= 1
    assert "still works" in result.text


@pytest.mark.asyncio
async def test_language_detected(voice_processor: VoiceProcessor, respx_mock: MockRouter) -> None:
    """Whisper language detection is passed through to metadata."""
    respx_mock.post("https://api.openai.com/v1/audio/transcriptions").respond(
        json={"text": "Bonjour le monde", "language": "fr", "duration": 2.0}
    )

    result = await voice_processor.process(
        b"\x00" * 500,
        "audio/mp4",
        {"file_name": "french.m4a", "file_id": "fr1"},
    )

    assert result.metadata["lang"] == "fr"
    assert "Bonjour le monde" in result.text


@pytest.mark.asyncio
async def test_whisper_api_error_raises(
    voice_processor: VoiceProcessor, respx_mock: MockRouter
) -> None:
    """Whisper API errors are raised as RuntimeError."""
    respx_mock.post("https://api.openai.com/v1/audio/transcriptions").respond(
        status_code=500, json={"error": "Internal Server Error"}
    )

    with pytest.raises(RuntimeError, match="Whisper transcription failed"):
        await voice_processor.process(
            b"\x00" * 100,
            "audio/ogg",
            {"file_name": "fail.ogg", "file_id": "err1"},
        )


def test_supports_mime_audio() -> None:
    """supports_mime returns True for audio/* types."""
    assert supports_mime("audio/ogg") is True
    assert supports_mime("audio/mpeg") is True
    assert supports_mime("audio/mp4") is True
    assert supports_mime("audio/wav") is True


def test_supports_mime_voice() -> None:
    """supports_mime returns True for voice/* types."""
    assert supports_mime("voice/ogg") is True


def test_supports_mime_non_audio() -> None:
    """supports_mime returns False for non-audio types."""
    assert supports_mime("image/jpeg") is False
    assert supports_mime("text/plain") is False
    assert supports_mime("application/pdf") is False
