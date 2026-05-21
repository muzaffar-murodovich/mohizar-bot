from __future__ import annotations

import asyncio
import json
import time


class FakeRedis:
    """In-memory Redis mock for scheduler tests."""

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def set(self, key: str, value: str) -> None:
        self._store[key] = value.encode()

    async def get(self, key: str) -> bytes | None:
        return self._store.get(key)

    async def delete(self, key: str) -> int:
        if key in self._store:
            del self._store[key]
            return 1
        return 0

    async def keys(self, pattern: str) -> list[bytes]:
        return [k.encode() for k in self._store if k.startswith("schedule:")]


class FakeBot:
    def __init__(self) -> None:
        self.sent_messages: list[dict[str, object]] = []

    async def send_message(self, **kwargs: object) -> None:
        self.sent_messages.append(kwargs)


async def test_create_job_in_redis() -> None:
    from mohizarbot.bot.scheduler import create_job, get_due_jobs

    redis = FakeRedis()
    await create_job(redis, "job1", -100123, "Scheduled post", int(time.time()) + 3600)

    # Job not due yet
    due = await get_due_jobs(redis)
    assert len(due) == 0


async def test_scheduler_fires_due_jobs() -> None:
    from mohizarbot.bot.scheduler import create_job, get_due_jobs

    redis = FakeRedis()
    past_ts = int(time.time()) - 60  # 1 minute ago
    await create_job(redis, "job_due", -100123, "Due post", past_ts)

    due = await get_due_jobs(redis)
    assert len(due) == 1
    assert due[0].job_id == "job_due"
    assert due[0].text == "Due post"


async def test_past_due_fires_immediately() -> None:
    from mohizarbot.bot.scheduler import create_job, get_due_jobs

    redis = FakeRedis()
    past_ts = int(time.time()) - 7200  # 2 hours ago
    await create_job(redis, "old_job", -100123, "Old post", past_ts)

    due = await get_due_jobs(redis)
    assert len(due) == 1


async def test_cancel_removes_job() -> None:
    from mohizarbot.bot.scheduler import cancel_job, create_job, get_due_jobs

    redis = FakeRedis()
    await create_job(redis, "job_x", -100123, "Will be cancelled", int(time.time()) - 60)
    assert len(await get_due_jobs(redis)) == 1

    result = await cancel_job(redis, "job_x")
    assert result is True
    assert len(await get_due_jobs(redis)) == 0


async def test_cancel_nonexistent_job() -> None:
    from mohizarbot.bot.scheduler import cancel_job

    redis = FakeRedis()
    result = await cancel_job(redis, "no_such_job")
    assert result is False


async def test_create_job_with_buttons() -> None:
    from mohizarbot.bot.scheduler import create_job, get_due_jobs

    redis = FakeRedis()
    buttons_json = json.dumps([[{"text": "Click", "callback_data": "abc"}]])
    past_ts = int(time.time()) - 60
    await create_job(redis, "job_btn", -100123, "Pick one", past_ts, buttons_json)

    due = await get_due_jobs(redis)
    assert len(due) == 1
    assert due[0].buttons_json == buttons_json


async def test_scheduler_executes_job() -> None:
    from mohizarbot.bot.scheduler import _execute_job, create_job, get_due_jobs

    redis = FakeRedis()
    bot = FakeBot()
    past_ts = int(time.time()) - 60
    await create_job(redis, "exec_job", -100123, "Execute me", past_ts)

    due = await get_due_jobs(redis)
    assert len(due) == 1

    await _execute_job(bot, redis, due[0])
    assert len(bot.sent_messages) == 1
    assert bot.sent_messages[0]["chat_id"] == -100123
    assert bot.sent_messages[0]["text"] == "Execute me"

    # Job should be removed after execution
    remaining = await get_due_jobs(redis)
    assert len(remaining) == 0


async def test_run_scheduler_stops_on_event() -> None:
    from mohizarbot.bot.scheduler import run_scheduler

    redis = FakeRedis()
    bot = FakeBot()
    stop = asyncio.Event()
    stop.set()  # Signal stop immediately

    await run_scheduler(bot, redis, stop_event=stop)
    # Should exit cleanly without hanging


async def test_multiple_jobs_due() -> None:
    from mohizarbot.bot.scheduler import create_job, get_due_jobs

    redis = FakeRedis()
    past = int(time.time()) - 60
    await create_job(redis, "a", -100123, "First", past)
    await create_job(redis, "b", -100123, "Second", past)
    await create_job(redis, "c", -100123, "Third", past)

    due = await get_due_jobs(redis)
    assert len(due) == 3


async def test_future_job_not_due() -> None:
    from mohizarbot.bot.scheduler import create_job, get_due_jobs

    redis = FakeRedis()
    future_ts = int(time.time()) + 86400  # tomorrow
    await create_job(redis, "future", -100123, "Later", future_ts)

    due = await get_due_jobs(redis)
    assert len(due) == 0
