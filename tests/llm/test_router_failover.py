from __future__ import annotations

import httpx
import pytest

from mohizarbot.llm.router import LLMUnavailableError, Router
from mohizarbot.llm.types import ChatMessage, LLMResponse, StreamChunk


def _http_error(status_code: int) -> httpx.HTTPStatusError:
    request = httpx.Request("POST", "http://test")
    response = httpx.Response(status_code)
    return httpx.HTTPStatusError("boom", request=request, response=response)


class _FailingProvider:
    def __init__(self, name: str, fail_with: Exception | None = None) -> None:
        self.provider_name = name
        self._fail_with = fail_with
        self.called = False

    async def chat(self, messages, tools=None, **opts):
        self.called = True
        if self._fail_with:
            raise self._fail_with
        return LLMResponse(content=f"response from {self.provider_name}", model=self.provider_name)

    async def stream(self, messages, tools=None, **opts):
        self.called = True
        if self._fail_with:
            raise self._fail_with
        yield StreamChunk(content_delta="ok", model=self.provider_name)


async def test_first_provider_503_second_called() -> None:
    p1 = _FailingProvider("primary", fail_with=_http_error(503))
    p2 = _FailingProvider("fallback")

    router = Router([p1, p2], default="primary")
    router.set_failover_chain(["primary", "fallback"])

    result = await router.chat_with_failover([ChatMessage(role="user", content="Hi")])
    assert p1.called
    assert p2.called
    assert isinstance(result, LLMResponse)
    assert result.content == "response from fallback"


async def test_first_provider_timeout_second_called() -> None:
    p1 = _FailingProvider("primary", fail_with=httpx.TimeoutException("timeout"))
    p2 = _FailingProvider("fallback")

    router = Router([p1, p2], default="primary")
    router.set_failover_chain(["primary", "fallback"])

    result = await router.chat_with_failover([ChatMessage(role="user", content="Hi")])
    assert p1.called
    assert p2.called
    assert result.content == "response from fallback"


async def test_all_providers_fail_raises_llm_unavailable() -> None:
    p1 = _FailingProvider("p1", fail_with=_http_error(503))
    p2 = _FailingProvider("p2", fail_with=httpx.TimeoutException("timeout"))

    router = Router([p1, p2], default="p1")
    router.set_failover_chain(["p1", "p2"])

    with pytest.raises(LLMUnavailableError):
        await router.chat_with_failover([ChatMessage(role="user", content="Hi")])


async def test_failover_order_respected() -> None:
    call_order: list[str] = []

    class _OrderedProvider:
        provider_name: str

        def __init__(self, name: str, fail: bool = False) -> None:
            self.provider_name = name
            self._fail = fail

        async def chat(self, messages, tools=None, **opts):
            call_order.append(self.provider_name)
            if self._fail:
                raise _http_error(503)
            return LLMResponse(content="ok", model=self.provider_name)

        async def stream(self, messages, tools=None, **opts):
            yield StreamChunk(content_delta="ok")

    p1 = _OrderedProvider("first", fail=True)
    p2 = _OrderedProvider("second", fail=True)
    p3 = _OrderedProvider("third")

    router = Router([p1, p2, p3], default="first")
    router.set_failover_chain(["first", "second", "third"])

    await router.chat_with_failover([ChatMessage(role="user", content="Hi")])
    assert call_order == ["first", "second", "third"]


async def test_4xx_error_not_caught() -> None:
    p1 = _FailingProvider("bad-auth", fail_with=_http_error(401))
    p2 = _FailingProvider("fallback")

    router = Router([p1, p2], default="bad-auth")
    router.set_failover_chain(["bad-auth", "fallback"])

    # 4xx errors should NOT be caught by failover — they propagate
    with pytest.raises(httpx.HTTPStatusError):
        await router.chat_with_failover([ChatMessage(role="user", content="Hi")])
