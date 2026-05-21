from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Redis key prefix for scheduled jobs
_JOB_PREFIX = "schedule:"
_CHECK_INTERVAL = 60  # seconds


@dataclass
class ScheduledJob:
    job_id: str
    channel_id: int
    text: str
    schedule_ts: int  # Unix timestamp
    buttons_json: str = ""  # JSON serialized inline keyboard
    created_by: int = 0


def _job_key(job_id: str) -> str:
    return f"{_JOB_PREFIX}{job_id}"


async def create_job(
    redis: object,
    job_id: str,
    channel_id: int,
    text: str,
    schedule_ts: int,
    buttons_json: str = "",
    created_by: int = 0,
) -> ScheduledJob:
    """Create a scheduled job in Redis.

    Returns the ScheduledJob that was created.
    """
    job = ScheduledJob(
        job_id=job_id,
        channel_id=channel_id,
        text=text,
        schedule_ts=schedule_ts,
        buttons_json=buttons_json,
        created_by=created_by,
    )
    payload = json.dumps(
        {
            "job_id": job.job_id,
            "channel_id": job.channel_id,
            "text": job.text,
            "schedule_ts": job.schedule_ts,
            "buttons_json": job.buttons_json,
            "created_by": job.created_by,
        }
    )
    if hasattr(redis, "set"):
        await redis.set(_job_key(job_id), payload)
    else:
        redis.set(_job_key(job_id), payload)  # type: ignore[attr-defined]
    return job


async def cancel_job(redis: object, job_id: str) -> bool:
    """Remove a scheduled job from Redis. Returns True if it existed."""
    key = _job_key(job_id)
    if hasattr(redis, "delete"):
        deleted = await redis.delete(key)
        return bool(deleted)
    else:
        existed = redis.delete(key)  # type: ignore[attr-defined]
        return bool(existed)


async def get_due_jobs(redis: object, now_ts: int | None = None) -> list[ScheduledJob]:
    """Get all jobs that are due for execution (schedule_ts <= now)."""
    if now_ts is None:
        now_ts = int(time.time())

    due: list[ScheduledJob] = []
    pattern = f"{_JOB_PREFIX}*"

    # Support both async and sync Redis interfaces
    if hasattr(redis, "keys"):
        keys = await redis.keys(pattern)
    else:
        keys = list(redis.keys(pattern))  # type: ignore[attr-defined]

    for key_obj in keys:
        key = key_obj.decode() if isinstance(key_obj, bytes) else key_obj
        if hasattr(redis, "get"):
            raw = await redis.get(key)
        else:
            raw = redis.get(key)  # type: ignore[attr-defined]
        if raw is None:
            continue
        raw_str = raw.decode() if isinstance(raw, bytes) else raw
        try:
            data = json.loads(raw_str)
            if int(data.get("schedule_ts", 0)) <= now_ts:
                due.append(
                    ScheduledJob(
                        job_id=str(data["job_id"]),
                        channel_id=int(data["channel_id"]),
                        text=str(data["text"]),
                        schedule_ts=int(data["schedule_ts"]),
                        buttons_json=str(data.get("buttons_json", "")),
                        created_by=int(data.get("created_by", 0)),
                    )
                )
        except (json.JSONDecodeError, KeyError, ValueError):
            logger.warning("Corrupt job payload in key %s", key)
    return due


async def remove_job(redis: object, job_id: str) -> None:
    """Remove a job from Redis after execution."""
    key = _job_key(job_id)
    if hasattr(redis, "delete"):
        await redis.delete(key)
    else:
        redis.delete(key)  # type: ignore[attr-defined]


async def run_scheduler(
    bot: object,
    redis: object,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Run the scheduler loop, checking for due jobs every 60s.

    Args:
        bot: aiogram Bot instance for posting messages.
        redis: Redis client for job storage.
        stop_event: Optional asyncio.Event to signal shutdown.
    """
    logger.info("Scheduler started (interval=%ds)", _CHECK_INTERVAL)

    while stop_event is None or not stop_event.is_set():
        try:
            due_jobs = await get_due_jobs(redis)
            for job in due_jobs:
                await _execute_job(bot, redis, job)
        except Exception:
            logger.exception("Scheduler iteration failed")

        # Sleep with check for stop event
        if stop_event is not None:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=_CHECK_INTERVAL)
                break  # stop was set
            except TimeoutError:
                continue  # normal wake-up, check again
        else:
            await asyncio.sleep(_CHECK_INTERVAL)

    logger.info("Scheduler stopped")


async def _execute_job(bot: object, redis: object, job: ScheduledJob) -> None:
    """Execute a single scheduled job: post to channel, then remove."""
    logger.info("Executing scheduled job %s → channel %d", job.job_id, job.channel_id)

    try:
        kwargs: dict[str, object] = {"chat_id": job.channel_id, "text": job.text}
        if job.buttons_json:
            try:
                buttons = json.loads(job.buttons_json)
                kwargs["reply_markup"] = {"inline_keyboard": buttons}
            except json.JSONDecodeError:
                pass

        if hasattr(bot, "send_message"):
            await bot.send_message(**kwargs)
        else:
            bot.send_message(**kwargs)  # type: ignore[attr-defined]
    except Exception:
        logger.exception("Failed to execute job %s", job.job_id)
    finally:
        await remove_job(redis, job.job_id)
