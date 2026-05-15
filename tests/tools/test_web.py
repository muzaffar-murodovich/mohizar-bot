from __future__ import annotations

import pytest

from mohizarbot.tools.web import WebFetchTool, _is_private_ip


def test_allowlist_enforced() -> None:

    with pytest.raises(ValueError, match="not allowlisted"):
        import asyncio

        asyncio.get_event_loop().run_until_complete(
            WebFetchTool.execute("http://evil.com", allowlisted_domains=["safe.com"])
        )


def test_private_ip_is_detected() -> None:
    assert _is_private_ip("127.0.0.1")
    assert _is_private_ip("10.0.0.1")
    assert _is_private_ip("192.168.1.1")
    assert _is_private_ip("172.16.0.1")


def test_loopback_is_refused() -> None:
    assert _is_private_ip("::1")


def test_link_local_is_refused() -> None:
    assert _is_private_ip("169.254.1.1")


def test_public_ip_is_allowed() -> None:
    assert not _is_private_ip("8.8.8.8")
    assert not _is_private_ip("1.1.1.1")


def test_web_fetch_tool_schema() -> None:
    t = WebFetchTool()
    assert t.name == "web_fetch"
    assert "url" in t.json_schema["required"]


def test_web_search_tool_schema() -> None:
    from mohizarbot.tools.web import WebSearchTool

    t = WebSearchTool()
    assert t.name == "web_search"
    assert "query" in t.json_schema["required"]


async def test_search_execute() -> None:
    from mohizarbot.tools.web import WebSearchTool

    result = await WebSearchTool.execute("test query")
    assert "test query" in result
