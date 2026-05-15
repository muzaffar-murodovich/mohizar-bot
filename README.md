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
