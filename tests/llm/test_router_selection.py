from __future__ import annotations

from mohizarbot.llm.router import Router
from mohizarbot.llm.types import ChatMessage, LLMResponse, StreamChunk


class _FakeProvider:
    def __init__(self, name: str, model: str = "") -> None:
        self.provider_name = name
        self._model = model or name

    async def chat(self, messages, tools=None, **opts):
        return LLMResponse(content="ok", model=self._model)

    async def stream(self, messages, tools=None, **opts):
        yield StreamChunk(content_delta="ok", model=self._model)


def test_short_prompt_selects_cheap_provider() -> None:
    router = Router(
        [
            _FakeProvider("anthropic"),
            _FakeProvider("openai"),
            _FakeProvider("deepseek"),
        ],
        default="anthropic",
    )

    # Short prompt should route to deepseek (cheap)
    provider = router.select([ChatMessage(role="user", content="Hello")])
    assert provider.provider_name == "deepseek"


def test_long_prompt_selects_default() -> None:
    router = Router(
        [
            _FakeProvider("anthropic"),
            _FakeProvider("deepseek"),
        ],
        default="anthropic",
    )

    # Long prompt bypasses cost routing
    long_text = "x" * 3000  # ~750 tokens > 500 threshold
    provider = router.select([ChatMessage(role="user", content=long_text)])
    assert provider.provider_name == "anthropic"


def test_vision_capability_routes_to_vision_provider() -> None:
    router = Router(
        [
            _FakeProvider("deepseek"),
            _FakeProvider("openai"),
        ],
        default="deepseek",
    )

    provider = router.select(
        [ChatMessage(role="user", content="Describe this")],
        capability_hints={"vision": True},
    )
    assert provider.provider_name == "openai"


def test_long_context_routes_to_capable_provider() -> None:
    router = Router(
        [
            _FakeProvider("deepseek"),
            _FakeProvider("anthropic"),
        ],
        default="deepseek",
    )

    provider = router.select(
        [ChatMessage(role="user", content="Summarize")],
        capability_hints={"long_context": True},
    )
    assert provider.provider_name == "anthropic"


def test_explicit_per_chat_override_wins() -> None:
    router = Router(
        [
            _FakeProvider("deepseek"),
            _FakeProvider("openai"),
        ],
        default="deepseek",
    )

    # Even with short prompt (which would favor deepseek), explicit wins
    provider = router.select(
        [ChatMessage(role="user", content="Hi")],
        capability_hints={"provider": "openai"},
    )
    assert provider.provider_name == "openai"


def test_explicit_override_overrides_vision() -> None:
    router = Router(
        [
            _FakeProvider("deepseek"),
            _FakeProvider("anthropic"),
            _FakeProvider("openai"),
        ],
        default="openai",
    )

    provider = router.select(
        [ChatMessage(role="user", content="Describe")],
        capability_hints={"vision": True, "provider": "deepseek"},
    )
    assert provider.provider_name == "deepseek"


def test_unknown_explicit_override_falls_through() -> None:
    router = Router(
        [_FakeProvider("deepseek"), _FakeProvider("anthropic")],
        default="anthropic",
    )

    # Unknown provider name — falls through to capability routing
    provider = router.select(
        [ChatMessage(role="user", content="Hi")],
        capability_hints={"provider": "nonexistent"},
    )
    # Falls back to deepseek (cheap, short prompt)
    assert provider.provider_name == "deepseek"
