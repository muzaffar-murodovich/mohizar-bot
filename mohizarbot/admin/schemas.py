from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ChatRow:
    chat_id: int
    provider: str = ""
    model: str = ""
    enabled_tools: str = ""
    auto_approve: bool = False
    last_activity: str = ""


@dataclass
class AuditRow:
    id: int
    timestamp: str
    chat_id: int
    user_id: int
    intent_json: str
    decision: str
    reasoning_summary: str
    previous_hmac: str = ""
    hmac: str = ""


@dataclass
class GuardRow:
    timestamp: str
    chat_id: str  # hashed
    verdict: str
    reason: str
    intent_type: str


@dataclass
class DashboardStats:
    total_chats: int = 0
    intents_24h: int = 0
    intents_7d: int = 0
    guard_safe_24h: int = 0
    guard_suspicious_24h: int = 0
    guard_block_24h: int = 0
    recent_confirmations: list[dict] = field(default_factory=list)
    rate_limited_1h: int = 0
