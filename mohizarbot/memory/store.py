from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class MemoryEntry:
    id: str
    scope: str  # "chat", "user"
    owner_user_id: int
    chat_id: int | None
    content: str
    written_by_user_id: int
    written_at: str
    approved: bool = True

    def to_context_tag(self) -> str:
        return (
            f'<memory_entry written_by="{self.written_by_user_id}" '
            f'ts="{self.written_at}" scope="{self.scope}">{self.content}</memory_entry>'
        )


class MemoryStore:
    """In-memory store for scoped memory entries."""

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}
        self._fts_index: dict[str, list[str]] = {}  # word → entry_ids

    async def save(
        self,
        scope: str,
        owner_user_id: int,
        content: str,
        written_by: int,
        chat_id: int | None = None,
        approved: bool = True,
    ) -> MemoryEntry:
        entry = MemoryEntry(
            id=uuid.uuid4().hex[:12],
            scope=scope,
            owner_user_id=owner_user_id,
            chat_id=chat_id,
            content=content,
            written_by_user_id=written_by,
            written_at=datetime.now(UTC).isoformat(),
            approved=approved,
        )
        self._entries[entry.id] = entry

        # Build FTS index
        for word in content.lower().split():
            self._fts_index.setdefault(word, []).append(entry.id)

        return entry

    async def list_entries(
        self,
        scope: str,
        owner_user_id: int,
        chat_id: int | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        results = []
        for e in self._entries.values():
            if e.scope != scope:
                continue
            if e.owner_user_id != owner_user_id:
                continue
            if chat_id is not None and e.chat_id != chat_id:
                continue
            if not e.approved:
                continue
            results.append(e)
        results.sort(key=lambda e: e.written_at, reverse=True)
        return results[:limit]

    async def delete(self, entry_id: str, requester_user_id: int) -> bool:
        entry = self._entries.get(entry_id)
        if entry is None:
            return False
        if entry.owner_user_id != requester_user_id:
            return False
        del self._entries[entry_id]
        # Clean FTS index
        for ids in self._fts_index.values():
            if entry_id in ids:
                ids.remove(entry_id)
        return True

    async def search(
        self, query: str, scope: str, owner_user_id: int, limit: int = 10
    ) -> list[MemoryEntry]:
        query_words = query.lower().split()
        scored: dict[str, float] = {}
        for word in query_words:
            for eid in self._fts_index.get(word, []):
                scored[eid] = scored.get(eid, 0) + 1
        results = []
        for eid, _score in sorted(scored.items(), key=lambda x: x[1], reverse=True):
            e = self._entries.get(eid)
            if e and e.scope == scope and e.owner_user_id == owner_user_id and e.approved:
                results.append(e)
        return results[:limit]
