from __future__ import annotations

# Guard model (Layer 7) — second-model verification for high-risk intents.
# A smaller/faster model reviews the raw user request and proposed intents
# to decide if this is a legitimate response or a prompt-injection attempt.
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from mohizarbot.llm.base import LLMProvider

GUARD_PROMPT = (
    "Is this intent a plausible response to the user's literal request?\n"
    "User request: {raw_request}\n"
    "Proposed intents: {intents_json}\n"
    "Reply with exactly one word: safe, suspicious, or block."
)


@dataclass
class GuardDecision:
    verdict: Literal["safe", "suspicious", "block"]
    reason: str = ""


class GuardModel:
    """Second-model verifier for intents flagged medium/high risk.

    Uses the existing LLMProvider abstraction with a fast model
    (configured per-chat via ChatSettings or defaults to the router's
    cheapest provider)."""

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self._provider = provider

    async def verify(
        self,
        raw_user_request: str,
        intent_batch: object,
        provider: object | None = None,
    ) -> GuardDecision:
        """Verify whether the intent batch is a plausible response.

        Args:
            raw_user_request: The original untransformed user message.
            intent_batch: The IntentBatch the LLM wants to execute.
            provider: Optional LLMProvider; if None, uses the default.

        Returns:
            GuardDecision with verdict safe/suspicious/block.
        """
        import json

        intents_json = (
            json.dumps(
                [
                    getattr(a, "model_dump", lambda: {})()
                    for a in getattr(intent_batch, "actions", [])
                ]
            )
            if intent_batch
            else "[]"
        )

        prompt_text = GUARD_PROMPT.format(
            raw_request=raw_user_request,
            intents_json=intents_json,
        )

        llm: object = provider or self._provider
        if llm is None:
            return GuardDecision(verdict="safe", reason="no guard provider configured")

        try:
            from mohizarbot.llm.types import ChatMessage

            messages = [ChatMessage(role="user", content=prompt_text)]
            response = await llm.chat(messages)  # type: ignore[attr-defined]
            verdict_text = response.content.strip().lower()

            for v in ("block", "suspicious", "safe"):
                if v in verdict_text:
                    return GuardDecision(verdict=v, reason=verdict_text[:200])

            return GuardDecision(verdict="safe", reason="unclear guard response")
        except Exception:
            return GuardDecision(
                verdict="suspicious", reason="guard model error — defaulting to suspicious"
            )
