from __future__ import annotations

from fastapi.testclient import TestClient

from mohizarbot.admin.app import create_admin_app


def test_x_frame_options_header() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/login")
    assert "X-Frame-Options" in response.headers
    assert response.headers["X-Frame-Options"] == "DENY"


def test_x_content_type_options_header() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/login")
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_referrer_policy_header() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/login")
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_csp_header_present() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/login")
    csp = response.headers.get("Content-Security-Policy", "")
    assert "default-src" in csp
    assert "frame-src" in csp


def test_x_frame_options_present_on_protected_route() -> None:
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
    assert response.headers["X-Frame-Options"] == "DENY"
