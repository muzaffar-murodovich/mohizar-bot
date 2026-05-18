from __future__ import annotations

import pytest

from mohizarbot.config import Settings
from mohizarbot.multimodal.document import DocumentProcessor
from mohizarbot.multimodal.image import ImageProcessor
from mohizarbot.multimodal.registry import get_processor
from mohizarbot.multimodal.voice import VoiceProcessor


@pytest.fixture
def settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def test_audio_mime_returns_voice_processor(settings: Settings) -> None:
    """audio/ogg returns VoiceProcessor."""
    p = get_processor("audio/ogg", settings)
    assert isinstance(p, VoiceProcessor)


def test_audio_mpeg_returns_voice_processor(settings: Settings) -> None:
    """audio/mpeg returns VoiceProcessor."""
    p = get_processor("audio/mpeg", settings)
    assert isinstance(p, VoiceProcessor)


def test_voice_ogg_returns_voice_processor(settings: Settings) -> None:
    """voice/ogg returns VoiceProcessor."""
    p = get_processor("voice/ogg", settings)
    assert isinstance(p, VoiceProcessor)


def test_image_jpeg_returns_image_processor(settings: Settings) -> None:
    """image/jpeg returns ImageProcessor."""
    p = get_processor("image/jpeg", settings)
    assert isinstance(p, ImageProcessor)


def test_image_png_returns_image_processor(settings: Settings) -> None:
    """image/png returns ImageProcessor."""
    p = get_processor("image/png", settings)
    assert isinstance(p, ImageProcessor)


def test_application_pdf_returns_document_processor(settings: Settings) -> None:
    """application/pdf returns DocumentProcessor."""
    p = get_processor("application/pdf", settings)
    assert isinstance(p, DocumentProcessor)


def test_docx_returns_document_processor(settings: Settings) -> None:
    """DOCX MIME returns DocumentProcessor."""
    p = get_processor(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        settings,
    )
    assert isinstance(p, DocumentProcessor)


def test_text_plain_returns_document_processor(settings: Settings) -> None:
    """text/plain returns DocumentProcessor."""
    p = get_processor("text/plain", settings)
    assert isinstance(p, DocumentProcessor)


def test_text_csv_returns_document_processor(settings: Settings) -> None:
    """text/csv returns DocumentProcessor."""
    p = get_processor("text/csv", settings)
    assert isinstance(p, DocumentProcessor)


def test_unknown_mime_returns_none(settings: Settings) -> None:
    """Unknown MIME types return None."""
    p = get_processor("application/zip", settings)
    assert p is None


def test_octet_stream_returns_none(settings: Settings) -> None:
    """application/octet-stream returns None."""
    p = get_processor("application/octet-stream", settings)
    assert p is None


def test_empty_mime_returns_none(settings: Settings) -> None:
    """Empty MIME type returns None."""
    p = get_processor("", settings)
    assert p is None
