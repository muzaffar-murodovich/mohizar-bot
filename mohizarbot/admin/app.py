from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

if TYPE_CHECKING:
    from fastapi.responses import Response

from mohizarbot.admin.routes import router


def add_security_headers(response: Response) -> None:
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://telegram.org; "
        "frame-src https://oauth.telegram.org; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://t.me; "
        "connect-src 'self'"
    )


def create_admin_app() -> FastAPI:
    app = FastAPI(title="mohizarbot-admin", version="0.1.0")

    # Security headers middleware
    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        add_security_headers(response)  # type: ignore[arg-type]
        return response

    app.include_router(router)
    app.mount("/static", StaticFiles(directory="mohizarbot/admin/static"), name="static")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app
