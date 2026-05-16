from __future__ import annotations

from fastapi.testclient import TestClient

from mohizarbot.admin.app import create_admin_app


def test_dashboard_redirects_to_login() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code in (302, 307)
    assert "/login" in response.headers.get("location", "")


def test_chats_redirects_to_login() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/chats", follow_redirects=False)
    assert response.status_code in (302, 307)


def test_audit_redirects_to_login() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/audit", follow_redirects=False)
    assert response.status_code in (302, 307)


def test_guard_redirects_to_login() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/guard", follow_redirects=False)
    assert response.status_code in (302, 307)


def test_login_page_accessible() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 200


def test_healthz_accessible() -> None:
    app = create_admin_app()
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
