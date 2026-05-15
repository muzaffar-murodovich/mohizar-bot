from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class AuditEntry:
    timestamp: str
    chat_id: int
    user_id: int
    intent_json: str
    decision: str
    reasoning_summary: str
    previous_hmac: str = ""
    hmac: str = ""


def _make_message(entry: AuditEntry) -> bytes:
    """Build the byte-string that gets HMAC'd for this entry."""
    payload = (
        f"{entry.timestamp}|{entry.chat_id}|{entry.user_id}|"
        f"{entry.intent_json}|{entry.decision}|{entry.reasoning_summary}|"
        f"{entry.previous_hmac}"
    )
    return payload.encode("utf-8")


def compute_hmac(key: bytes, entry: AuditEntry) -> str:
    """Compute the HMAC-SHA256 for an audit entry, chaining from the previous entry."""
    if not entry.previous_hmac:
        raise ValueError("previous_hmac must be set before computing HMAC")
    return hmac.digest(key, _make_message(entry), hashlib.sha256).hex()


def create_entry(
    key: bytes,
    *,
    previous_hmac: str,
    chat_id: int,
    user_id: int,
    intent_json: str,
    decision: str,
    reasoning_summary: str,
) -> AuditEntry:
    """Create a new chained audit entry with HMAC."""
    entry = AuditEntry(
        timestamp=datetime.now(UTC).isoformat(),
        chat_id=chat_id,
        user_id=user_id,
        intent_json=intent_json,
        decision=decision,
        reasoning_summary=reasoning_summary,
        previous_hmac=previous_hmac,
    )
    entry.hmac = compute_hmac(key, entry)
    return entry


def verify_chain(key: bytes, entries: list[AuditEntry]) -> bool:
    """Verify an entire audit chain is intact.

    Returns True if every entry's HMAC is correct and the chain links properly.
    """
    if not entries:
        return True

    prev = entries[0].previous_hmac
    for entry in entries:
        if entry.previous_hmac != prev:
            return False
        expected = compute_hmac(key, entry)
        if not hmac.compare_digest(entry.hmac, expected):
            return False
        prev = entry.hmac
    return True


def genesis_hmac() -> str:
    """Return the HMAC seed for the first entry in a chain (all zeros)."""
    return "0" * 64
