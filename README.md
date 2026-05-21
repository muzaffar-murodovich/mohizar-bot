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

## Sprint 9 — what's included

Multimodal input processing with document-embedded injection defense:

- **Multimodal processors**: VoiceProcessor (Whisper), ImageProcessor (EXIF-stripped), DocumentProcessor (PDF/DOCX/TXT/CSV)
- **Voice/audio transcription**: OpenAI Whisper API via httpx; supports OGA/Opus, MP3, M4A, WAV, WebM; 25MB cap
- **Image understanding**: vision-capable LLM routing; EXIF metadata stripped for privacy; max 5 images, 10MB each
- **Document reading**: pypdf for PDF (max 100 pages), python-docx for DOCX, chardet for charset detection; DOCX comments extracted; 50K char truncation
- **MIME-based registry**: get_processor(mime_type) routes to correct processor; unknown types return None
- **File-download risk levels**: files ≤5MB + ≤20K chars = LOW; larger files/text = MEDIUM (guard invoked)
- **Document injection corpus**: 26 payloads (PDF metadata, white-text, hidden forms, DOCX comments, CSV formulas, ZIP bombs, polyglot files)
- **Tests**: 5 new test files + 26 document injection payloads; total **1269 tests** (> Sprint 8's 1057)

### Multimodal — supported formats and limits

| Category | Formats | Processor | Max Size | Other Limits |
|----------|---------|-----------|----------|--------------|
| Voice/Audio | OGA, Opus, MP3, M4A, WAV, WebM | Whisper API | 25 MB | — |
| Images | JPEG, PNG, WebP, GIF, BMP, TIFF | ImageProcessor | 10 MB | Max 5 per message; EXIF stripped |
| Documents (PDF) | application/pdf | pypdf | 10 MB | Max 100 pages; 50K chars extracted |
| Documents (DOCX) | .docx, .doc | python-docx | 10 MB | Comments extracted; 50K chars extracted |
| Documents (Text) | TXT, CSV, HTML, etc. | chardet+UTF-8 | 10 MB | Non-UTF-8 detected via chardet; 50K chars extracted |

All processor output is sanitized (input_sanitizer) and wrapped in untrusted tags (Layer 1) before LLM consumption. File downloads are never executed or used as subprocess paths.

## Sprint 10 — Rich messaging

Inline keyboards, callback handling, media groups, channel posting, and scheduled posts:

- **Inline keyboards**: `build_inline_keyboard()` builder with `InlineButton(text, callback_data, url)`; all `callback_data` HMAC-signed (SHA256); unsigned callbacks silently dropped + audit log entry
- **Callback handling**: Extended `handle_callback()` supports both Sprint 4 confirmation tokens (`confirm:`) and Sprint 10 arbitrary signed callbacks (`<sig>:<json_payload>`); `CallbackResponseIntent` for `answer_callback_query`
- **Media groups**: `SendMediaGroupIntent` with up to 10 `MediaItem`s; 11th rejected by policy; caption on first item only; sends via `sendMediaGroup`
- **Channel posting**: `ChannelManager.post_to_channel()` and `edit_channel_post()` with admin precheck (`getChatMember`); `CHANNEL_IDS` in Settings (comma-separated, optional); `PostToChannelIntent` and `EditChannelPostIntent`
- **Scheduled posts**: Redis-backed scheduler (`schedule:` key prefix); `run_scheduler()` checks every 60s for due jobs; `PostToChannelIntent` with `schedule_ts` creates job; `CancelScheduledPostIntent` removes job
- **Risk levels**: `post_to_channel`, `edit_channel_post`, `cancel_scheduled_post` → HIGH (always confirm); `send_message_with_keyboard`, `send_media_group` → LOW; `edit_reply_markup` → MEDIUM; `callback_response` → LOW
- **Tests**: 7 new test files; total **1334 tests** (> Sprint 9's 1269)

### Rich messaging — intent reference

| Intent | Risk | Description |
|--------|------|-------------|
| `send_message_with_keyboard` | LOW | Send message with inline keyboard |
| `edit_reply_markup` | MEDIUM | Edit message's inline keyboard only |
| `send_media_group` | LOW | Send up to 10 media items as album |
| `post_to_channel` | HIGH | Post to a channel (optionally scheduled) |
| `edit_channel_post` | HIGH | Edit an existing channel post |
| `cancel_scheduled_post` | HIGH | Cancel a pending scheduled post |
| `callback_response` | LOW | Answer a callback query |

## Sprint 11 — Production hardening

Mutation testing, property-based fuzzing, chaos testing, dependency audit, secret scanning, dead code detection, and coverage enforcement:

- **Mutation testing**: mutmut configured with `paths_to_mutate = ["mohizarbot/security"]`; runner uses pytest on security test suite
- **Property-based fuzzing**: 16 hypothesis tests (max_examples=500 each) across sanitizer, delimiters, injection detector, and output filter
- **Chaos testing**: Redis ConnectionError, LLM timeout, and SQLAlchemy OperationalError scenarios — all return graceful degradation without crashes
- **Dependency audit**: `pip-audit` CVE scan integrated; findings documented in `docs/security_audit.md`
- **Secret scanning**: `detect-secrets` baseline created (`.secrets.baseline`), audited, committed
- **Dead code detection**: `vulture --min-confidence 80` on `mohizarbot/`; all items either removed or annotated with reason
- **Coverage enforcement**: `pytest --cov=mohizarbot` with `fail_under = 85`; current coverage **85.17%**
- **Hardening CI**: `scripts/hardening_ci.py` runs pip-audit, detect-secrets, vulture, and pytest --cov in sequence; added as `hardening` job in CI workflow
- **Tests**: 8 new test files (4 fuzz, 3 chaos, and coverage fill-in); total **1435 tests** (> Sprint 10's 1334)

### Hardening tool summary

| Tool | Purpose | Threshold |
|------|---------|-----------|
| mutmut | Mutation testing | security/ ≥ 80% |
| hypothesis | Property-based fuzzing | 500 examples each |
| pip-audit | CVE scan | Exit 0 or documented |
| detect-secrets | Secret leak scan | Baseline committed |
| vulture | Dead code | --min-confidence 80 |
| pytest-cov | Coverage | ≥ 85% |

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
