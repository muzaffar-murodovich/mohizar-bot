# Deployment Guide

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BOT_TOKEN` | Yes | Telegram Bot API token |
| `WEBHOOK_SECRET` | Yes | Secret token for webhook validation (≥32 chars) |
| `WEBHOOK_URL` | No | Public webhook URL (set via Telegram API) |
| `DATABASE_URL` | No | PostgreSQL async connection string |
| `REDIS_URL` | No | Redis connection string |
| `AUDIT_HMAC_KEY` | Yes | HMAC key for audit chain integrity (≥32 bytes hex) |
| `LOG_LEVEL` | No | Logging level (default: INFO) |

## PostgreSQL Setup

```sql
CREATE DATABASE mohizarbot;
CREATE USER mohizar WITH PASSWORD 'mohizar';
GRANT ALL ON DATABASE mohizarbot TO mohizar;
```

Run migrations:
```bash
alembic upgrade head
```

## Redis Setup

Redis is used for rate limiting, permission caching, and confirmation tokens.
Ensure Redis ≥5 is running and accessible via `REDIS_URL`.

## Webhook Configuration

1. Set `WEBHOOK_URL` to your public endpoint (e.g., `https://bot.example.com/webhook`)
2. **secret_token rotation**: Generate a new random secret (≥32 chars) periodically:
   ```bash
   openssl rand -hex 32 > /etc/mohizarbot/webhook_secret
   ```
   Update both `WEBHOOK_SECRET` env var and Telegram's `setWebhook` call.
3. Telegram sends webhook updates with `X-Telegram-Bot-Api-Secret-Token` header.
4. mohizarbot validates this header against `WEBHOOK_SECRET` on every request.

## TLS Certificates

Use nginx or Caddy as reverse proxy:
```nginx
server {
    listen 443 ssl;
    server_name bot.example.com;
    ssl_certificate /etc/letsencrypt/live/bot.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/bot.example.com/privkey.pem;
    location / { proxy_pass http://127.0.0.1:8000; }
}
```

## Log Shipping

mohizarbot uses structlog with JSON output in production:
```bash
LOG_LEVEL=INFO uv run uvicorn mohizarbot.app:create_app --factory
```

Ship logs via your preferred collector (fluentd, vector, filebeat). Rotate logs daily.

## Prometheus Scraping

Metrics are exposed at `/metrics` in Prometheus text format.
Add to `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: mohizarbot
    metrics_path: /metrics
    static_configs:
      - targets: ['bot.example.com:8000']
```

Available metrics:
- `intents_total{type,result}` — Intent executions by type and result
- `llm_calls_total{provider,result}` — LLM API calls
- `guard_decisions_total{verdict}` — Guard model decisions
- `confirmations_total{outcome}` — Confirmation flow outcomes
- `llm_latency_seconds` — LLM call latency histogram
- `pipeline_latency_seconds` — Full pipeline latency histogram

## Audit Chain Backup

The audit log is stored in the `audit_log` PostgreSQL table.
Each entry is HMAC-chained — tampering is detectable.

Backup strategy:
```bash
pg_dump -t audit_log -t memory_entries -t chat_settings mohizarbot > backup.sql
```

Verify chain integrity periodically:
```bash
python scripts/replay_audit.py
```

## Rollback

1. Stop the service
2. Run `alembic downgrade -1` to revert the last migration
3. Restore database from backup if needed
4. Deploy previous Docker image tag
5. Restart the service
