from __future__ import annotations

import pytest

from mohizarbot.memory.search import search_memory
from mohizarbot.memory.store import MemoryStore


@pytest.fixture
def store() -> MemoryStore:
    return MemoryStore()


async def test_save_and_list(store: MemoryStore) -> None:
    await store.save("chat", 100, "test content", written_by=100, chat_id=1)
    results = await store.list_entries("chat", 100, chat_id=1)
    assert len(results) == 1
    assert results[0].content == "test content"


async def test_cross_user_read_denied(store: MemoryStore) -> None:
    await store.save("chat", 100, "alice content", written_by=100, chat_id=1)
    results = await store.list_entries("chat", 200, chat_id=1)
    assert len(results) == 0


async def test_delete(store: MemoryStore) -> None:
    e = await store.save("chat", 100, "temp", written_by=100, chat_id=1)
    deleted = await store.delete(e.id, 100)
    assert deleted
    results = await store.list_entries("chat", 100, chat_id=1)
    assert len(results) == 0


async def test_delete_wrong_user_fails(store: MemoryStore) -> None:
    e = await store.save("chat", 100, "mine", written_by=100, chat_id=1)
    deleted = await store.delete(e.id, 200)
    assert not deleted


async def test_fts_search(store: MemoryStore) -> None:
    await store.save("chat", 100, "the quick brown fox", written_by=100, chat_id=1)
    await store.save("chat", 100, "lazy dog", written_by=100, chat_id=1)
    results = await store.search("quick fox", "chat", 100)
    assert len(results) >= 1
    assert "quick" in results[0].content


async def test_fts_ranks_recent_higher(store: MemoryStore) -> None:
    import asyncio

    await store.save("chat", 100, "old fox entry", written_by=100, chat_id=1)
    await asyncio.sleep(0.01)
    await store.save("chat", 100, "new fox entry", written_by=100, chat_id=1)
    results = await search_memory(store, "fox entry", "chat", 100)
    assert len(results) >= 2
    assert results[0].content == "new fox entry"


async def test_unapproved_not_listed(store: MemoryStore) -> None:
    await store.save("chat", 100, "pending", written_by=100, chat_id=1, approved=False)
    results = await store.list_entries("chat", 100, chat_id=1)
    assert len(results) == 0


async def test_scoped_no_cross_chat(store: MemoryStore) -> None:
    await store.save("chat", 100, "chat 1 text", written_by=100, chat_id=1)
    await store.save("chat", 100, "chat 2 text", written_by=100, chat_id=2)
    results = await store.list_entries("chat", 100, chat_id=1)
    assert len(results) == 1
    assert results[0].content == "chat 1 text"
