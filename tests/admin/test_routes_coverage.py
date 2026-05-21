from __future__ import annotations

from unittest.mock import MagicMock


def test_admin_app_healthz() -> None:
    from mohizarbot.admin.app import create_admin_app

    app = create_admin_app()
    # Verify the app was created
    assert app is not None
    assert app.title == "mohizarbot-admin"


def test_admin_router_included() -> None:
    from mohizarbot.admin.app import create_admin_app

    app = create_admin_app()
    routes = [r.path for r in app.routes]
    assert "/healthz" in routes


def test_security_headers_added() -> None:
    from mohizarbot.admin.app import add_security_headers

    response = MagicMock()
    response.headers = {}
    add_security_headers(response)
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
