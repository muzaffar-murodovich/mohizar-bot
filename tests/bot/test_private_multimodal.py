from __future__ import annotations

from datetime import datetime

import pytest
from aiogram.types import Chat, Document, Message, PhotoSize, User, Voice

from mohizarbot.policy.risk import file_call_risk_level


def _make_voice_message(file_id: str = "voice_1", mime: str = "audio/ogg") -> Message:
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test"),
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=Chat(id=123, type="private", first_name="Test"),
        voice=Voice(
            file_id=file_id,
            file_unique_id="unique_v",
            duration=3,
            mime_type=mime,
            file_size=1024,
        ),
        text=None,  # type: ignore[arg-type]
    )


def _make_photo_message(file_id: str = "photo_1") -> Message:
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test"),
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=Chat(id=123, type="private", first_name="Test"),
        photo=[
            PhotoSize(
                file_id=f"{file_id}_small",
                file_unique_id="u_small",
                width=100,
                height=100,
            ),
            PhotoSize(
                file_id=file_id,
                file_unique_id="u_large",
                width=800,
                height=800,
            ),
        ],
        text=None,  # type: ignore[arg-type]
    )


def _make_document_message(
    file_id: str = "doc_1", mime: str = "application/pdf", filename: str = "test.pdf"
) -> Message:
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test"),
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=Chat(id=123, type="private", first_name="Test"),
        document=Document(
            file_id=file_id,
            file_unique_id="unique_d",
            file_name=filename,
            mime_type=mime,
            file_size=2048,
        ),
        text=None,  # type: ignore[arg-type]
    )


def _make_text_message(text: str = "hello") -> Message:
    return Message(
        message_id=1,
        from_user=User(id=123, is_bot=False, first_name="Test"),
        date=datetime(2024, 1, 1, 12, 0, 0),
        chat=Chat(id=123, type="private", first_name="Test"),
        text=text,
    )


class TestPrivateMultimodalDetection:
    """Tests for multimodal detection in private handler helper."""

    def test_voice_message_detected(self) -> None:
        """Voice messages are detected as multimodal."""
        from mohizarbot.bot.handlers.multimodal_helper import _detect_multimodal

        msg = _make_voice_message()
        mime_type, file_id, file_name = _detect_multimodal(msg)
        assert mime_type == "audio/ogg"
        assert file_id == "voice_1"
        assert file_name == "voice.ogg"

    def test_photo_message_detected(self) -> None:
        """Photo messages are detected, largest size chosen."""
        from mohizarbot.bot.handlers.multimodal_helper import _detect_multimodal

        msg = _make_photo_message()
        mime_type, file_id, file_name = _detect_multimodal(msg)
        assert mime_type == "image/jpeg"
        assert file_id == "photo_1"  # largest
        assert file_name == "photo.jpg"

    def test_document_message_detected(self) -> None:
        """Document messages are detected with their MIME type."""
        from mohizarbot.bot.handlers.multimodal_helper import _detect_multimodal

        msg = _make_document_message()
        mime_type, file_id, file_name = _detect_multimodal(msg)
        assert mime_type == "application/pdf"
        assert file_id == "doc_1"
        assert file_name == "test.pdf"

    def test_text_message_not_multimodal(self) -> None:
        """Plain text messages return None for MIME/file_id."""
        from mohizarbot.bot.handlers.multimodal_helper import _detect_multimodal

        msg = _make_text_message()
        mime_type, file_id, file_name = _detect_multimodal(msg)
        assert mime_type is None
        assert file_id is None


class TestMultimodalIntegration:
    """Integration tests for multimodal → LLM pipeline."""

    @pytest.mark.asyncio
    async def test_voice_to_transcription_wrapped_sanitized(self) -> None:
        """Voice message → transcription → sanitized → wrapped → LLM."""
        from mohizarbot.security.input_sanitizer import sanitize
        from mohizarbot.security.untrusted import generate_session_token, wrap_untrusted

        transcription = (
            '<transcription source_kind="voice" duration_sec="5.0" lang="en">\n'
            "Hello world\n"
            "</transcription>"
        )

        cleaned = sanitize(transcription)
        session_token = generate_session_token()
        wrapped = wrap_untrusted(
            "user_message", cleaned, session_token=session_token, from_user_id=123, chat_id=123
        )

        assert "<user_message" in wrapped
        assert "</user_message>" in wrapped
        assert "Hello world" in wrapped
        # Opening/closing tags should not have been escaped by sanitize
        assert wrapped.count("<user_message") == 1
        assert wrapped.count("</user_message>") == 1

    @pytest.mark.asyncio
    async def test_vision_provider_selected_for_image(self) -> None:
        """Image content triggers vision-capable provider selection."""
        from mohizarbot.llm.providers.anthropic_ import AnthropicProvider
        from mohizarbot.llm.providers.deepseek_ import DeepSeekProvider
        from mohizarbot.llm.providers.openai_ import OpenAIProvider
        from mohizarbot.llm.router import Router
        from mohizarbot.llm.types import ChatMessage

        providers = [
            AnthropicProvider(api_key="test"),
            OpenAIProvider(api_key="test"),
            DeepSeekProvider(api_key="test"),
        ]
        router = Router(providers, default="deepseek")  # type: ignore[arg-type]

        messages = [ChatMessage(role="user", content="describe this")]
        provider = router.select(messages, capability_hints={"vision": True})

        # Should pick Anthropic or OpenAI (vision-capable), not DeepSeek
        assert provider.provider_name in ("anthropic", "openai")


class TestRiskLevels:
    """Tests for file-call risk assessment."""

    def test_small_file_low_risk(self) -> None:
        """Small files with short text are LOW risk."""
        assert file_call_risk_level(1024, 500) == "low"

    def test_large_file_medium_risk(self) -> None:
        """Files > 5MB are MEDIUM risk."""
        assert file_call_risk_level(6 * 1024 * 1024, 100) == "medium"

    def test_long_text_medium_risk(self) -> None:
        """Extracted text > 20K chars is MEDIUM risk."""
        assert file_call_risk_level(1024, 25_000) == "medium"

    def test_boundary_small_file_low(self) -> None:
        """Files at exactly 5MB with 20K chars are LOW risk."""
        assert file_call_risk_level(5 * 1024 * 1024, 20_000) == "low"
