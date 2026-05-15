from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


async def test_create_chat_settings() -> None:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    from mohizarbot.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        from mohizarbot.db.models import ChatSettings

        cs = ChatSettings(chat_id=123, provider="openai", model="gpt-4o")
        session.add(cs)
        await session.commit()

        result = await session.get(ChatSettings, 123)
        assert result is not None
        assert result.chat_id == 123
        assert result.provider == "openai"
        assert result.model == "gpt-4o"

    await engine.dispose()


async def test_update_chat_settings() -> None:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    from mohizarbot.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        from mohizarbot.db.models import ChatSettings

        cs = ChatSettings(chat_id=456, provider="anthropic", model="claude-sonnet-4-6")
        session.add(cs)
        await session.commit()

        cs.provider = "deepseek"
        cs.model = "deepseek-chat"
        await session.commit()

        result = await session.get(ChatSettings, 456)
        assert result is not None
        assert result.provider == "deepseek"
        assert result.model == "deepseek-chat"

    await engine.dispose()


async def test_unique_constraint_on_chat_id() -> None:
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    from mohizarbot.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as session:
        from mohizarbot.db.models import ChatSettings

        cs1 = ChatSettings(chat_id=789, provider="anthropic", model="claude-sonnet-4-6")
        session.add(cs1)
        await session.commit()

        cs2 = ChatSettings(chat_id=789, provider="openai", model="gpt-4o")
        session.add(cs2)
        with pytest.raises(Exception):
            await session.commit()

    await engine.dispose()
