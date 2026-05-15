from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from mohizarbot.app import create_app


def _make_update_body(text: str = "hello") -> dict[str, object]:
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {"id": 123, "is_bot": False, "first_name": "Test"},
            "chat": {"id": 123, "type": "private", "first_name": "Test"},
            "date": 1700000000,
            "text": text,
        },
    }


def test_webhook_with_correct_secret_returns_200() -> None:
    with (
        patch.dict(
            os.environ,
            {
                "BOT_TOKEN": "111:test",
                "WEBHOOK_SECRET": "correct-secret-value",
                "AUDIT_HMAC_KEY": "aa" * 32,
            },
            clear=False,
        ),
        patch(
            "mohizarbot.bot.webhook.build_api_wrapper",
            return_value=AsyncMock(),
        ),
    ):
        app = create_app()
        client = TestClient(app)
        response = client.post(
            "/webhook",
            json=_make_update_body(),
            headers={"X-Telegram-Bot-Api-Secret-Token": "correct-secret-value"},
        )
        assert response.status_code == 200


def test_webhook_with_wrong_secret_returns_401() -> None:
    with patch.dict(
        os.environ,
        {
            "BOT_TOKEN": "111:test",
            "WEBHOOK_SECRET": "correct-secret-value",
            "AUDIT_HMAC_KEY": "aa" * 32,
        },
        clear=False,
    ):
        app = create_app()
        client = TestClient(app)
        response = client.post(
            "/webhook",
            json=_make_update_body(),
            headers={"X-Telegram-Bot-Api-Secret-Token": "wrong-secret"},
        )
        assert response.status_code == 401


def test_webhook_with_missing_secret_returns_401() -> None:
    with patch.dict(
        os.environ,
        {
            "BOT_TOKEN": "111:test",
            "WEBHOOK_SECRET": "correct-secret-value",
            "AUDIT_HMAC_KEY": "aa" * 32,
        },
        clear=False,
    ):
        app = create_app()
        client = TestClient(app)
        response = client.post("/webhook", json=_make_update_body())
        assert response.status_code == 401
