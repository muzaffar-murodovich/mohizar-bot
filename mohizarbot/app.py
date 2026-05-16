from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import Response

from mohizarbot.bot.webhook import router as webhook_router


def create_app() -> FastAPI:
    app = FastAPI(title="mohizarbot", version="0.1.0")
    app.include_router(webhook_router)

    @app.get("/healthcheck")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics() -> Response:
        from mohizarbot.observability.metrics import get_all_metrics

        return Response(content=get_all_metrics(), media_type="text/plain")

    return app
