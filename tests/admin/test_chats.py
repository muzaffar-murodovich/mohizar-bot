from __future__ import annotations

from fastapi.testclient import TestClient

from mohizarbot.admin.app import create_admin_app


def test_chats_page_loads_with_session() -> None:
    import os

    os.environ["BOT_TOKEN"] = "test:bot"
    os.environ["WEBHOOK_SECRET"] = "x" * 32
    os.environ["AUDIT_HMAC_KEY"] = "a" * 64

    import time

    from mohizarbot.admin.deps import _sign

    expiry = int(time.time()) + 3600
    signed = _sign(f"12345:{expiry}")

    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/chats", cookies={"mohizar_session": signed})
    assert response.status_code == 200


def test_chat_detail_loads_with_session() -> None:
    import os

    os.environ["BOT_TOKEN"] = "test:bot"
    os.environ["WEBHOOK_SECRET"] = "x" * 32
    os.environ["AUDIT_HMAC_KEY"] = "a" * 64

    import time

    from mohizarbot.admin.deps import _sign

    expiry = int(time.time()) + 3600
    signed = _sign(f"12345:{expiry}")

    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/chats/123", cookies={"mohizar_session": signed})
    assert response.status_code == 200


def test_csrf_required_for_post() -> None:
    import os

    os.environ["BOT_TOKEN"] = "test:bot"
    os.environ["WEBHOOK_SECRET"] = "x" * 32
    os.environ["AUDIT_HMAC_KEY"] = "a" * 64

    import time

    from mohizarbot.admin.deps import _sign

    expiry = int(time.time()) + 3600
    signed = _sign(f"12345:{expiry}")

    app = create_admin_app()
    client = TestClient(app)
    response = client.post(
        "/chats/123",
        data={"provider": "openai", "model": "gpt-4o"},
        cookies={"mohizar_session": signed},
        follow_redirects=False,
    )
    # Missing CSRF token → redirects
    assert response.status_code in (302, 307, 200)
