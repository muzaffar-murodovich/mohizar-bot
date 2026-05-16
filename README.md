# mohizarbot

Public multi-tenant Telegram bot with multi-provider LLM routing and prompt-injection-resistant architecture.

## Security model — 7 defense layers

| Layer | Name | Sprint | Mechanism |
|-------|------|--------|-----------|
| 1 | Content/instruction separation | S1,S3 | `<untrusted_kind>` wrapping with escaped tags |
| 2 | Spotlighting | S1,S3 | Space→‹ (U+2039) in external input |
| 3 | Privilege separation | S4 | LLM emits intents, policy engine executes |
| 4 | Sandboxed memory | S5 | Scoped CRUD, instruction detection |
| 5 | Output filtering | S3 | Secret leak scan, echo detection, link stripping |
| 6 | Multi-turn anchoring | S6 | System prompt re-injection every N turns |
| 7 | Guard model | S6 | 2nd model verifies medium/high-risk intents |

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

## Sprint 6 — what's included

Security model closure and production readiness:

- **Guard model (Layer 7)**: 2nd-model verifier for medium/high-risk intents; safe/suspicious/block verdicts; block is fatal, suspicious forces confirmation
- **Multi-turn anchoring (Layer 6)**: system prompt re-injected every N=5 user turns; assistant outputs wrapped in `<assistant_previous_output>` tags
- **Observability**: Prometheus counters (intents, LLM calls, guard decisions, confirmations) and histograms (LLM latency, pipeline latency); OpenTelemetry-style tracing spans
- **Metrics endpoint**: `/metrics` exposed in Prometheus text format
- **CI/CD**: GitHub Actions workflow with lint, typecheck, unit-tests, redteam, build jobs
- **Red-team CI**: `scripts/redteam_ci.py` runs full pipeline over Sprint 3 corpus + multi-turn payloads; non-zero exit on outcome mismatch
- **Load test**: `scripts/load_test.py` simulates N concurrent webhooks with mocked LLM/Telegram
- **Deploy guide**: `docs/deploy.md` covers env vars, postgres/redis setup, webhook+secret_token rotation, certs, log shipping, prometheus scraping, audit-chain backup, rollback
- **Tests**: 35 new tests in 5 files + multi-turn integration; total **946 tests** (> Sprint 5's 911)

## Admin panel

Separate FastAPI app on port 8001 with Telegram Login Widget auth:

- **Authentication**: HMAC-SHA256 verification per Telegram spec; signed httponly cookies with 8h expiry; ADMIN_USER_IDS gate
- **Dashboard**: total chats, intents (24h/7d), guard verdict breakdown, recent confirmations, rate-limit count
- **Chats**: paginated ChatSettings list with search; edit form for provider/model/tools/auto_approve; changes audited
- **Audit log**: filterable by chat/user/date; paginated with expandable JSON; chain verification
- **Guard decisions**: default 24h suspicious+block filter; verdict/chat/date filtering
- **Security headers**: X-Frame-Options=DENY, CSP, no-referrer, nosniff; CSRF tokens on forms

## Sprint 7 — what's included

Admin web dashboard with Telegram Login Widget auth:

- **Admin app**: separate FastAPI on ADMIN_PORT (8001) sharing Settings/DB/Redis
- **Telegram Login Widget**: HMAC-SHA256 verification; auth_date freshness check; admin user gate
- **Session management**: signed httponly cookies with 8h TTL
- **Dashboard, Chats, Audit, Guard views**: Jinja2 templates with dark theme CSS
- **Security**: X-Frame-Options=DENY, CSP, CSRF tokens, referrer/no-sniff headers
- **Config**: ADMIN_USER_IDS env var (comma-separated)
- **Tests**: 7 new test files (30 tests); total **976 tests** (> Sprint 6's 946)

## Group chat support

mohizarbot can operate in groups and supergroups:

- **Mention detection**: responds to @mention, /command@BotUsername, and reply-to-bot
- **Group message wrapping**: rich `<group_message>` tags with from_user_id, username, is_admin, reply provenance, forward provenance
- **Reply-chain defense**: reply parents marked `is_reply_target="true"` and NEVER treated as authoritative
- **Non-admin moderation refusal**: moderation intents from non-admin users denied before guard model

## Sprint 8 — what's included

Group chat support with mention/reply detection and injection defense:

- **Group handler**: responds only when addressed; loads 10-message context; bot past responses wrapped as assistant_previous_output
- **Mention detection**: @mention, /cmd@bot, reply-to-bot; case-insensitive; non-bot rejected
- **Group message wrapping**: all attribution attributes always present; forward provenance tracked
- **Reply-chain defense**: reply parent with is_reply_target="true"; system prompt forbids treating parent as authoritative
- **GROUP_CHAT_RULES**: appended to system prompt for group contexts; never accept moderation from non-admin
- **Permissions**: non-admin moderation denied before guard model; admin still requires confirmation for high-risk
- **Tests**: 7 new test files + 20 group-chat injection payloads; total **1057 tests** (> Sprint 7's 976)

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
