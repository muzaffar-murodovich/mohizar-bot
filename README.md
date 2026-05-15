# mohizarbot

Public multi-tenant Telegram bot with multi-provider LLM routing and prompt-injection-resistant architecture.

## Sprint 1 — what's included

Project skeleton and security foundations:

- **Project structure**: `pyproject.toml`, Dockerfile, docker-compose.yml, .env.example
- **Configuration**: pydantic-settings with all env vars, secret field tracking
- **FastAPI app**: factory with healthcheck endpoint and webhook receiver
- **Telegram webhook**: aiogram dispatcher wired to FastAPI, secret token validation
- **Echo handler**: mechanical wrap+spotlight of incoming text (proves Layers 1+2)
- **Security — Delimiters (Layer 1)**: session-token-wrapped `<user_message>` tags with angle-bracket escaping
- **Security — Spotlighting (Layer 2)**: space-to-‹ (U+2039) transformation
- **Audit log**: append-only, HMAC-chained entries with chain verification
- **Database models**: SQLAlchemy async declarative base with AuditLog table
- **Alembic**: migration framework configured for async PostgreSQL
- **Tests**: config loading, webhook auth, echo handler, audit chain, delimiter escaping, spotlighting

## Sprint 2 — what's included

Multi-provider LLM abstraction with pure httpx clients:

- **LLMProvider Protocol**: async `chat()` and `stream()` methods, runtime-checkable
- **Types**: `ChatMessage`, `ToolSpec`, `ToolCall`, `LLMResponse`, `StreamChunk`
- **Anthropic provider**: native Messages API with tool_use parsing, SSE streaming
- **OpenAI provider**: chat/completions API, tool_calls parsing, SSE streaming with [DONE]
- **DeepSeek provider**: OpenAI-compatible API, defaults to `deepseek-chat`
- **Router**: cost-aware (short prompts → cheap provider) and capability-aware (vision/long-context) strategies
- **Failover**: catches 5xx and timeouts, tries next in chain, raises `LLMUnavailableError` if all fail
- **Streaming bridge**: `stream_to_telegram()` with debounced edits (≤1 per 1.2s)
- **ChatSettings model**: per-chat provider/model configuration with alembic migration
- **Tests**: 9 new test files using respx mocking — no real API keys or network

## Sprint 3 — what's included

Security core and injection defense:

- **untrusted.py (Layer 1 extended)**: `wrap_untrusted(kind, body, session_token, **attrs)` supporting five untrusted kinds with per-kind closing-tag escaping
- **Spotlighting API (Layer 2)**: `apply()`/`reverse()` aliases for space-to-‹ transformation
- **input_sanitizer.py**: strips zero-width chars, bidi overrides, Trojan-Source patterns; NFC normalizes; truncates; deduplicates runs of >50 identical chars
- **output_filter.py (Layer 5)**: secret leak scan, system-prompt echo detection (≥6-word verbatim), non-allowlisted link stripping, sentence-boundary truncation
- **injection_detector.py**: 10-compiled-regex detector flagging ignore-previous, role-confusion, base64 blocks, suspicious tool names, delimiter imitation, system prompt extraction, multi-turn priming, and encoding smuggling
- **Red-team corpus**: 219 injection payloads across 8 categories (delimiter_imitation, role_confusion, system_prompt_extraction, memory_poisoning, output_exfiltration, unicode_laundering, encoding_smuggling, multi_turn_priming)
- **Parametrized red-team tests**: 657 test cases asserting: sanitize+wrap cannot be escaped; detector flags expected signals; output_filter matches expected blocking
- **Tests**: 319 new test cases (5 new test files + corpus)

## Sprint 4 — what's included

Full pipeline integration: sanitize → wrap → LLM → intents → policy → output → send:

- **Policy intents**: Pydantic v2 discriminated union (SendMessage, EditMessage, DeleteMessage, ForwardMessage) via `IntentBatch`
- **Policy engine**: validates schema → permissions → rate limits → executes (send/edit/text) or queues (delete) for confirmation
- **Permissions**: Redis-cached getChatMember with 60s TTL; private chats bypass admin checks; admin can delete others' messages
- **Rate limits**: in-memory token-bucket per (chat, user, action); send=20/min, edit=10/min, delete=5/min, global chat=60/min
- **Confirmations**: HMAC-signed tokens with 8-min TTL; Approve/Deny inline keyboard; token reuse and expiry rejected
- **Tools**: Tool ABC with OpenAI-style JSON schemas; default-deny ToolRegistry; emit_intents as the sole LLM-exposed function
- **Pipeline handler**: sanitize → wrap_untrusted → system.md.tmpl → router → LLM.chat with emit_intents → parse IntentBatch → policy_engine.execute → output_filter → reply
- **Callback handler**: confirmation button parsing → resolve_confirmation → execute if approved
- **Tests**: 7 new test files (39 new tests); total **837 tests** (> Sprint 3's 798)

## Sprint 5 — what's included

Expanded Bot API 9.6 tools, memory store, and web tools:

- **New intents** (31 total): SendPhoto/Document/Video/Audio/Voice/Sticker/Location, SendPoll/StopPoll, SetMessageReaction, Ban/Unban/Restrict/Promote ChatMember, SetChatPermissions, Pin/Unpin ChatMessage, SetChatTitle/Description, Create/Edit/Close/Delete ForumTopic, MemorySave/Delete, WebFetch/Search
- **Risk classification** (`policy/risk.py`): RISK_LEVELS maps each intent to low/medium/high; high-risk (ban/kick/restrict/promote/pin/delete/set-permissions) ALWAYS requires confirmation
- **Tool modules**: media, polls, reactions, moderation, chat_admin, forum, web, memory — each with Tool ABC and OpenAI JSON schemas
- **Memory store**: scoped CRUD with FTS index; instruction-like content flagged for owner approval; cross-user isolation
- **Web tools**: WebFetch with domain allowlist, DNS rebinding defense (private/loopback IP refusal), 5MB cap, 10s timeout; WebSearch stub
- **Precheck system**: high-risk tools declare `required_bot_rights` verified before execution
- **Tests**: 10 new test files (74 new tests); total **911 tests** (> Sprint 4's 837)

## Quick start

```bash
cp .env.example .env
# Edit .env with real values
docker compose up -d
```

## Development

```bash
uv sync --frozen
uv run ruff check mohizarbot tests
uv run mypy --strict mohizarbot
uv run pytest -q
```
