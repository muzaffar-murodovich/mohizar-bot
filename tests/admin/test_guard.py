from __future__ import annotations

from fastapi.testclient import TestClient

from mohizarbot.admin.app import create_admin_app


def _signed_session() -> str:
    import time

    from mohizarbot.admin.deps import _sign

    expiry = int(time.time()) + 3600
    return _sign(f"12345:{expiry}")


def test_guard_page_loads() -> None:
    import os

    os.environ["BOT_TOKEN"] = "test:bot"
    os.environ["WEBHOOK_SECRET"] = "x" * 32
    os.environ["AUDIT_HMAC_KEY"] = "a" * 64

    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/guard", cookies={"mohizar_session": _signed_session()})
    assert response.status_code == 200


def test_guard_default_filter_suspicious_block() -> None:
    import os

    os.environ["BOT_TOKEN"] = "test:bot"
    os.environ["WEBHOOK_SECRET"] = "x" * 32
    os.environ["AUDIT_HMAC_KEY"] = "a" * 64

    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/guard", cookies={"mohizar_session": _signed_session()})
    assert response.status_code == 200


def test_guard_filter_by_verdict() -> None:
    import os

    os.environ["BOT_TOKEN"] = "test:bot"
    os.environ["WEBHOOK_SECRET"] = "x" * 32
    os.environ["AUDIT_HMAC_KEY"] = "a" * 64

    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/guard?verdict=block", cookies={"mohizar_session": _signed_session()})
    assert response.status_code == 200
