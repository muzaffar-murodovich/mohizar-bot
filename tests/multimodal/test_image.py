from __future__ import annotations

import base64

import pytest

from mohizarbot.config import Settings
from mohizarbot.multimodal.image import ImageProcessor, _strip_exif, supports_mime


@pytest.fixture
def image_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


@pytest.fixture
def image_processor(image_settings: Settings) -> ImageProcessor:
    return ImageProcessor(image_settings)


@pytest.mark.asyncio
async def test_photo_produces_image_block(image_processor: ImageProcessor) -> None:
    """Photo input produces an ImageBlock with base64 data."""
    fake_jpeg = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00\x43\x00\xff\xda\x00\x08"
        + b"\x00" * 100
    )

    result = await image_processor.process(
        fake_jpeg,
        "image/jpeg",
        {"file_id": "photo123", "image_count": 1},
    )

    assert result.kind == "image_blocks"
    assert result.image_blocks is not None
    assert len(result.image_blocks) == 1
    img = result.image_blocks[0]
    assert img.media_type == "image/jpeg"
    assert img.source_uri == "photo123"

    # Verify base64 is valid
    decoded = base64.b64decode(img.base64)
    assert len(decoded) > 0
    assert decoded[:2] == b"\xff\xd8"  # JPEG SOI


@pytest.mark.asyncio
async def test_exif_stripped_from_jpeg(image_processor: ImageProcessor) -> None:
    """EXIF metadata is stripped from JPEG images (privacy)."""
    # JPEG with EXIF marker (0xFFE1) after SOI
    jpeg_body = b"\xff\xd8\xff\xe1\x00\x08EXIFDATA\xff\xda\x00\x08" + b"\x00" * 100

    result = await image_processor.process(
        jpeg_body,
        "image/jpeg",
        {"file_id": "exif1", "image_count": 1},
    )

    decoded = base64.b64decode(result.image_blocks[0].base64)
    # EXIF marker (0xFFE1) should be stripped
    assert b"EXIFDATA" not in decoded


def test_strip_exif_removes_exif_data() -> None:
    """_strip_exif removes EXIF segment from JPEG."""
    # JPEG with EXIF between SOI and SOS
    data = b"\xff\xd8\xff\xe1\x00\x08EXIFDATA\xff\xda\x00\x08" + b"\x00" * 20
    result = _strip_exif(data, "image/jpeg")
    assert b"EXIFDATA" not in result


def test_strip_exif_passthrough_non_jpeg() -> None:
    """_strip_exif passes through PNG and other formats unchanged."""
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    result = _strip_exif(png, "image/png")
    assert result == png


@pytest.mark.asyncio
async def test_too_many_images_rejected(image_processor: ImageProcessor) -> None:
    """More than 5 images per message are rejected."""
    with pytest.raises(ValueError, match="Too many images"):
        await image_processor.process(
            b"\xff\xd8\xff\xda\x00\x08" + b"\x00" * 10,
            "image/jpeg",
            {"file_id": "multi", "image_count": 6},
        )


@pytest.mark.asyncio
async def test_image_too_large_rejected(image_processor: ImageProcessor) -> None:
    """Images > 10MB are rejected."""
    oversized = b"\x00" * (10 * 1024 * 1024 + 1)

    with pytest.raises(ValueError, match="too large"):
        await image_processor.process(
            oversized,
            "image/jpeg",
            {"file_id": "huge", "image_count": 1},
        )


@pytest.mark.asyncio
async def test_png_image_processed(image_processor: ImageProcessor) -> None:
    """PNG image is also processed to an ImageBlock."""
    fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100

    result = await image_processor.process(
        fake_png,
        "image/png",
        {"file_id": "png1", "image_count": 1},
    )

    assert result.kind == "image_blocks"
    assert result.image_blocks[0].media_type == "image/png"


@pytest.mark.asyncio
async def test_image_metadata_populated(image_processor: ImageProcessor) -> None:
    """Result metadata includes source kind and file info."""
    fake_jpeg = b"\xff\xd8\xff\xda\x00\x08" + b"\x00" * 50
    result = await image_processor.process(
        fake_jpeg,
        "image/jpeg",
        {"file_id": "meta1", "image_count": 1},
    )

    assert result.metadata["source_kind"] == "image"
    assert result.metadata["file_id"] == "meta1"


def test_supports_mime_image() -> None:
    """supports_mime returns True for image/* types."""
    assert supports_mime("image/jpeg") is True
    assert supports_mime("image/png") is True
    assert supports_mime("image/webp") is True
    assert supports_mime("image/gif") is True


def test_supports_mime_non_image() -> None:
    """supports_mime returns False for non-image types."""
    assert supports_mime("audio/ogg") is False
    assert supports_mime("application/pdf") is False
