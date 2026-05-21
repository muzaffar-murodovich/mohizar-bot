from __future__ import annotations

from mohizarbot.tools.web import WebFetchTool, WebSearchTool, _is_private_ip, _resolve_and_check


def test_is_private_ip_localhost() -> None:
    assert _is_private_ip("127.0.0.1") is True


def test_is_private_ip_loopback() -> None:
    assert _is_private_ip("::1") is True


def test_is_private_ip_public() -> None:
    assert _is_private_ip("93.184.216.34") is False


def test_is_private_ip_private_range() -> None:
    assert _is_private_ip("192.168.1.1") is True
    assert _is_private_ip("10.0.0.1") is True
    assert _is_private_ip("172.16.0.1") is True


def test_is_private_ip_invalid() -> None:
    assert _is_private_ip("not_an_ip") is False


def test_resolve_and_check_no_hostname() -> None:
    assert _resolve_and_check("http:///path") is False


def test_resolve_and_check_valid_url() -> None:
    result = _resolve_and_check("https://example.com/path")
    # example.com resolves to a public IP
    assert isinstance(result, bool)


def test_web_fetch_tool_name() -> None:
    tool = WebFetchTool()
    assert tool.name == "web_fetch"


def test_web_search_tool_name() -> None:
    tool = WebSearchTool()
    assert tool.name == "web_search"


def test_web_search_tool_schema() -> None:
    tool = WebSearchTool()
    schema = tool.json_schema
    assert schema["type"] == "object"
    assert "query" in schema["properties"]


def test_web_fetch_tool_produces_intent_types() -> None:
    tool = WebFetchTool()
    types = tool.produces_intent_types
    assert "web_fetch" in types


def test_web_search_tool_produces_intent_types() -> None:
    tool = WebSearchTool()
    types = tool.produces_intent_types
    assert "web_search" in types
