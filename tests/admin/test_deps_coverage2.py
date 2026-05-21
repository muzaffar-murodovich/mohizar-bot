from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException


def test_set_session_cookie_through_call() -> None:
    """Cover set_session_cookie lines 31-44."""
    from mohizarbot.admin.deps import set_session_cookie

    response = MagicMock()
    set_session_cookie(response, user_id=123)

    assert response.set_cookie.called
    kwargs = response.set_cookie.call_args.kwargs
    assert kwargs["key"] == "mohizar_session"
    assert kwargs["httponly"] is True


def test_require_admin_no_session() -> None:
    """require_admin raises HTTPException(302) when no session cookie."""
    from unittest.mock import MagicMock

    from mohizarbot.admin.deps import require_admin

    request = MagicMock()
    request.state = MagicMock()
    # No cookie → should redirect to /login
    with pytest.raises(HTTPException) as exc_info:
        require_admin(request, mohizar_session="")
    assert exc_info.value.status_code == 302


def test_require_admin_invalid_session() -> None:
    """require_admin raises 302 when session is invalid."""
    from unittest.mock import MagicMock

    from mohizarbot.admin.deps import require_admin

    request = MagicMock()
    request.state = MagicMock()
    with pytest.raises(HTTPException) as exc_info:
        require_admin(request, mohizar_session="not_a_valid_session_token")
    assert exc_info.value.status_code == 302
