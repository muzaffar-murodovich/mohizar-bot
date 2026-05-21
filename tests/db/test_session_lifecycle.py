from __future__ import annotations

from mohizarbot.db.session import close_db


async def test_close_db_when_not_initialized() -> None:
    """close_db should not crash when the database was never initialized."""
    await close_db()
    # No exception means success
