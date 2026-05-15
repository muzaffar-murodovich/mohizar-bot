from __future__ import annotations

from mohizarbot.tools.media import (
    SendAudioTool,
    SendDocumentTool,
    SendLocationTool,
    SendPhotoTool,
    SendStickerTool,
    SendVideoTool,
    SendVoiceTool,
)
from mohizarbot.tools.registry import ToolRegistry


def test_photo_tool_schema() -> None:
    t = SendPhotoTool()
    assert t.name == "send_photo"
    assert "photo" in t.json_schema["required"]


def test_document_tool_schema() -> None:
    t = SendDocumentTool()
    assert t.name == "send_document"


def test_video_tool_schema() -> None:
    t = SendVideoTool()
    assert "video" in t.json_schema["required"]


def test_audio_tool_schema() -> None:
    t = SendAudioTool()
    assert "audio" in t.json_schema["required"]


def test_voice_tool_schema() -> None:
    t = SendVoiceTool()
    assert "voice" in t.json_schema["required"]


def test_sticker_tool_schema() -> None:
    t = SendStickerTool()
    assert "sticker" in t.json_schema["required"]


def test_location_tool_schema() -> None:
    t = SendLocationTool()
    assert t.name == "send_location"
    assert "latitude" in t.json_schema["required"]


def test_registry_knows_all_media_tools() -> None:
    reg = ToolRegistry()
    reg.register(SendPhotoTool())
    reg.register(SendDocumentTool())
    reg.register(SendVideoTool())
    reg.register(SendAudioTool())
    reg.register(SendVoiceTool())
    reg.register(SendStickerTool())
    reg.register(SendLocationTool())
    names = reg.get_all().keys()
    assert "send_photo" in names
    assert "send_document" in names


def test_default_deny_preserved() -> None:
    reg = ToolRegistry()
    reg.register(SendPhotoTool())
    assert reg.get_for_chat() == []
    assert len(reg.get_for_chat(["send_photo"])) == 1
