from __future__ import annotations

import hmac
import os
import secrets

from fastapi import APIRouter, Cookie, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from mohizarbot.admin.auth import TelegramLoginVerifier
from mohizarbot.admin.deps import _verify, set_session_cookie
from mohizarbot.admin.schemas import DashboardStats
from mohizarbot.config import Settings

router = APIRouter()
_tpl_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=_tpl_dir)


def _get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


def _require_admin(
    request: Request, session: str = Cookie(default="", alias="mohizar_session")
) -> bool:
    settings = _get_settings()
    user_id = _verify(session)
    if user_id is None:
        raise Exception("redirect:/login")
    if settings.admin_user_ids and user_id not in settings.admin_user_ids:
        raise Exception("redirect:/login")
    request.state.admin_user_id = user_id
    return True


def _csrf_token(request: Request) -> str:
    token = secrets.token_hex(16)
    request.state.csrf_token = token
    return token


def _check_csrf(request: Request, token: str = Form(default="")) -> None:
    expected = getattr(request.state, "csrf_token", "")
    if not token or not hmac.compare_digest(token, expected):
        raise Exception("redirect:/chats")


# ── Public routes ──


@router.get("/")
async def index(request: Request) -> RedirectResponse:
    return RedirectResponse(url="/dashboard")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "request": request,
            "bot_username": "mohizarbot",
            "csrf_token": _csrf_token(request),
        },
    )


@router.get("/login/callback")
async def login_callback(
    request: Request,
    id: str = "",
    first_name: str = "",
    username: str = "",
    photo_url: str = "",
    auth_date: str = "",
    hash: str = "",
) -> Response:
    settings = _get_settings()
    verifier = TelegramLoginVerifier(settings.bot_token)
    data = {
        "id": id,
        "first_name": first_name,
        "username": username,
        "photo_url": photo_url,
        "auth_date": auth_date,
        "hash": hash,
    }
    auth_data = verifier.verify(data)
    if auth_data is None:
        return HTMLResponse("Login verification failed", status_code=403)

    if settings.admin_user_ids and auth_data.user_id not in settings.admin_user_ids:
        return HTMLResponse("Not authorized", status_code=403)

    response = RedirectResponse(url="/dashboard", status_code=302)
    set_session_cookie(response, auth_data.user_id)
    return response


@router.get("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("mohizar_session")
    return response


# ── Protected routes ──


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    mohizar_session: str = Cookie(default=""),
) -> Response:
    try:
        _require_admin(request, mohizar_session)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

    stats = DashboardStats(total_chats=42, intents_24h=1337, intents_7d=8942)
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request": request,
            "stats": stats,
            "csrf_token": _csrf_token(request),
        },
    )


@router.get("/chats", response_class=HTMLResponse)
async def chats_list(
    request: Request,
    page: int = 1,
    search: str = "",
    mohizar_session: str = Cookie(default=""),
) -> Response:
    try:
        _require_admin(request, mohizar_session)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

    from mohizarbot.admin.schemas import ChatRow

    rows = [ChatRow(chat_id=123, provider="anthropic", model="claude-sonnet-4-6")]
    return templates.TemplateResponse(
        request,
        "chats.html",
        {
            "request": request,
            "rows": rows,
            "page": page,
            "csrf_token": _csrf_token(request),
        },
    )


@router.get("/chats/{chat_id}", response_class=HTMLResponse)
async def chat_detail(
    request: Request,
    chat_id: int,
    mohizar_session: str = Cookie(default=""),
) -> Response:
    try:
        _require_admin(request, mohizar_session)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

    return templates.TemplateResponse(
        request,
        "chat_detail.html",
        {
            "request": request,
            "chat_id": chat_id,
            "csrf_token": _csrf_token(request),
            "settings": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-6",
                "auto_approve": False,
            },
        },
    )


@router.post("/chats/{chat_id}")
async def chat_save(
    request: Request,
    chat_id: int,
    provider: str = Form(default="anthropic"),
    model: str = Form(default="claude-sonnet-4-6"),
    auto_approve: str = Form(default="off"),
    csrf_token: str = Form(default=""),
    mohizar_session: str = Cookie(default=""),
) -> RedirectResponse:
    try:
        _require_admin(request, mohizar_session)
        _check_csrf(request, csrf_token)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

    # Audit the change
    # In production: write to DB audit_log with diff
    return RedirectResponse(url=f"/chats/{chat_id}", status_code=302)


@router.get("/audit", response_class=HTMLResponse)
async def audit_list(
    request: Request,
    page: int = 1,
    chat_id: int = 0,
    mohizar_session: str = Cookie(default=""),
) -> Response:
    try:
        _require_admin(request, mohizar_session)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

    rows: list[object] = []
    return templates.TemplateResponse(
        request,
        "audit.html",
        {
            "request": request,
            "rows": rows,
            "page": page,
            "csrf_token": _csrf_token(request),
        },
    )


@router.get("/guard", response_class=HTMLResponse)
async def guard_list(
    request: Request,
    verdict: str = "suspicious,block",
    page: int = 1,
    mohizar_session: str = Cookie(default=""),
) -> Response:
    try:
        _require_admin(request, mohizar_session)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)

    rows: list[object] = []
    return templates.TemplateResponse(
        request,
        "guard.html",
        {
            "request": request,
            "rows": rows,
            "verdict": verdict,
            "page": page,
            "csrf_token": _csrf_token(request),
        },
    )
