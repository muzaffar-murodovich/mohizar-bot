from __future__ import annotations

# Output filter (Layer 5) — blocks secret leaks, system-prompt echos,
# unauthorized links, and over-long text in LLM outputs before they reach Telegram.
import re
from dataclasses import dataclass, field

# ── Compiled patterns ────────────────────────────────────────────

_URL_RE = re.compile(
    r"\[([^\]]*)\]\((\s*(?:https?|ftp)://\S+)\)",  # markdown link
)

_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class FilterResult:
    text: str
    blocked: bool
    reasons: list[str] = field(default_factory=list)


def _build_secret_matcher(secrets: list[str]) -> _SecretScanner:
    """Build a sorted-prefix quick-lookup for secrets.

    Returns an object with a .contains(text) -> str|None method.
    Uses linear scan over sorted list with prefix short-circuit.
    This is simpler than Aho-Corasick and fast enough for typical ~10 secrets.
    """
    sorted_secrets = sorted(set(secrets), key=len, reverse=True)
    return _SecretScanner(sorted_secrets)


class _SecretScanner:
    def __init__(self, secrets: list[str]) -> None:
        self._secrets = secrets

    def contains_any(self, text: str) -> str | None:
        for s in self._secrets:
            if s and s in text:
                return s
        return None


def filter_output(
    text: str,
    secrets: list[str] | None = None,
    system_prompt_phrases: list[str] | None = None,
    allowlisted_domains: list[str] | None = None,
    max_len: int = 4000,
) -> FilterResult:
    """Filter LLM output before delivery to Telegram.

    Returns a FilterResult with (possibly modified) text, blocked flag,
    and reasons for any actions taken.

    Detects:
    - Secret value leaks (any secret substring match)
    - System-prompt echos (≥6-word verbatim phrases)
    - Links to non-allowlisted domains (stripped to plain text)
    - Over-length text (split at sentence boundaries)
    """
    reasons: list[str] = []
    blocked = False
    secrets = secrets or []
    system_prompt_phrases = system_prompt_phrases or []
    allowlisted = allowlisted_domains or []

    # (a) Secret leak scan
    if secrets:
        scanner = _build_secret_matcher(secrets)
        hit = scanner.contains_any(text)
        if hit:
            reasons.append("secret_leak")
            blocked = True
            msg = "[BLOCKED: potential secret leak]"
            return FilterResult(text=msg, blocked=True, reasons=reasons)

    # (b) System-prompt echo scan
    if system_prompt_phrases:
        import re as _re

        # Strip leading/trailing punctuation from each word for comparison
        words = [_re.sub(r"^[^\w]+|[^\w]+$", "", w) for w in _re.split(r"\s+", text)]
        for phrase in system_prompt_phrases:
            phrase_words = [_re.sub(r"^[^\w]+|[^\w]+$", "", w) for w in _re.split(r"\s+", phrase)]
            if len(phrase_words) >= 6:
                for i in range(len(words) - len(phrase_words) + 1):
                    window = words[i : i + len(phrase_words)]
                    if window == phrase_words:
                        reasons.append("system_prompt_echo")
                        blocked = True
                        msg = "[BLOCKED: system prompt echo]"
                        return FilterResult(text=msg, blocked=True, reasons=reasons)

    # (c) Link filtering
    def _replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        url = match.group(2).strip()
        # Extract domain
        domain = _extract_domain(url)
        if domain and domain in allowlisted:
            return match.group(0)
        reasons.append(f"link_stripped:{domain or url}")
        return label  # Strip to plain text

    text = _URL_RE.sub(_replace_link, text)

    # (d) Length cap with sentence-boundary split
    if len(text) > max_len:
        # Try to split on sentence boundary before max_len
        split_pos = max_len
        # Search backwards for sentence boundary within last 500 chars
        search_start = max(0, max_len - 500)
        m = list(_SPLIT_RE.finditer(text, search_start, max_len))
        if m:
            split_pos = m[-1].end()
        text = text[:split_pos].rstrip()
        reasons.append("truncated")

    return FilterResult(text=text, blocked=blocked, reasons=reasons)


def _extract_domain(url: str) -> str:
    m = re.search(r"://([^/:\s]+)", url)
    return m.group(1).lower() if m else ""
