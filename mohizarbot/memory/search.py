from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mohizarbot.memory.store import MemoryEntry, MemoryStore


async def search_memory(
    store: MemoryStore,
    query: str,
    scope: str,
    owner_user_id: int,
    limit: int = 10,
) -> list[MemoryEntry]:
    """Full-text search across scoped memory entries, ranking recent higher."""
    results: list[MemoryEntry] = await store.search(query, scope, owner_user_id, limit)
    results.sort(key=lambda e: e.written_at, reverse=True)
    return results[:limit]
