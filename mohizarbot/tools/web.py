from __future__ import annotations

import ipaddress
import socket

import httpx

from mohizarbot.tools.base import Tool

_MAX_SIZE = 5 * 1024 * 1024  # 5MB
_TIMEOUT = 10.0


def _is_private_ip(host: str) -> bool:
    """Check if resolved IP is private/loopback/link-local (DNS rebinding defense)."""
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def _resolve_and_check(url: str) -> bool:
    """Resolve the host and check for private IPs. Returns True if safe."""
    import urllib.parse

    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        return False
    try:
        addrs = socket.getaddrinfo(hostname, None)
        for addr in addrs:
            ip = str(addr[4][0])
            if _is_private_ip(ip):
                return False
    except socket.gaierror:
        return False
    return True


class WebFetchTool(Tool):
    name = "web_fetch"
    description = "Fetch content from a URL"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
                "max_size": {"type": "integer", "description": "Max bytes to read"},
            },
            "required": ["url"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["web_fetch"]

    @staticmethod
    async def execute(
        url: str, allowlisted_domains: list[str] | None = None, max_size: int = _MAX_SIZE
    ) -> str:
        import urllib.parse

        domain = urllib.parse.urlparse(url).hostname or ""
        if allowlisted_domains and domain not in allowlisted_domains:
            raise ValueError(f"Domain {domain} not allowlisted")

        if not _resolve_and_check(url):
            raise ValueError(f"URL resolves to private/loopback address: {url}")

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            body = response.read()[:max_size]
            return body.decode("utf-8", errors="replace")


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for information"

    @property
    def json_schema(self) -> dict[str, object]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results to return"},
            },
            "required": ["query"],
        }

    @property
    def produces_intent_types(self) -> list[str]:
        return ["web_search"]

    @staticmethod
    async def execute(query: str, max_results: int = 5) -> str:
        # Placeholder — real provider wired in Sprint 6
        return f"[WebSearch placeholder results for: {query}]"
