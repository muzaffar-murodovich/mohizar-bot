from __future__ import annotations

from mohizarbot.tools.base import Tool


class SendPhotoTool(Tool):
    name = "send_photo"
    description = "Send a photo to a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "photo": {"type": "string", "description": "file_id or URL"},
                "caption": {"type": "string"},
            },
            "required": ["chat_id", "photo"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["send_photo"]


class SendDocumentTool(Tool):
    name = "send_document"
    description = "Send a document to a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "document": {"type": "string", "description": "file_id or URL"},
                "caption": {"type": "string"},
            },
            "required": ["chat_id", "document"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["send_document"]


class SendVideoTool(Tool):
    name = "send_video"
    description = "Send a video to a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "video": {"type": "string", "description": "file_id or URL"},
                "caption": {"type": "string"},
            },
            "required": ["chat_id", "video"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["send_video"]


class SendAudioTool(Tool):
    name = "send_audio"
    description = "Send an audio file to a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "audio": {"type": "string", "description": "file_id or URL"},
                "caption": {"type": "string"},
            },
            "required": ["chat_id", "audio"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["send_audio"]


class SendVoiceTool(Tool):
    name = "send_voice"
    description = "Send a voice message to a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "voice": {"type": "string", "description": "file_id or URL"},
            },
            "required": ["chat_id", "voice"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["send_voice"]


class SendStickerTool(Tool):
    name = "send_sticker"
    description = "Send a sticker to a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "sticker": {"type": "string", "description": "file_id"},
            },
            "required": ["chat_id", "sticker"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["send_sticker"]


class SendLocationTool(Tool):
    name = "send_location"
    description = "Send a location point to a chat"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "chat_id": {"type": "integer"},
                "latitude": {"type": "number"},
                "longitude": {"type": "number"},
            },
            "required": ["chat_id", "latitude", "longitude"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["send_location"]
