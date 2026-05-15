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
