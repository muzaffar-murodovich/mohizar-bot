from __future__ import annotations

# Injection detector — flags known adversarial patterns in user input.
# All regexes are compiled at module load — no per-call recompilation.
import re
from dataclasses import dataclass, field

# ── Compiled patterns ────────────────────────────────────────────

# Ignore-previous / instruction override
_RE_IGNORE = re.compile(
    r"(?:ignore|disregard|forget|dismiss)\s+(?:all\s+)?(?:previous|above|prior|earlier|the\s+above)\s+(?:instructions?|messages?|directions?|commands?|context)",
    re.IGNORECASE,
)

# "You are now" / role reassignments
_RE_YOU_ARE_NOW = re.compile(
    r"you\s+are\s+(?:now|no\s+longer|currently)\s+(?:an?\s+)?(?:\w+\s+)?(?:assistant|system|bot|developer|admin|hacker|god|master|root|owner|operator|jailbreaker|DAN|unrestricted|compromised|evil)",
    re.IGNORECASE,
)

# Role-confusion prefixes
_RE_ROLE_PREFIX = re.compile(
    r"^\s*(?:system\s*:|assistant\s*:|human\s*:|user\s*:|admin\s*:|developer\s*:)\s*",
    re.IGNORECASE | re.MULTILINE,
)

# Base64 blocks >40 chars (common for smuggling prompts)
_RE_BASE64 = re.compile(r"[A-Za-z0-9+/]{25,}={0,2}")

# Suspicious tool names / intents that attackers try to invoke
_TOOL_NAMES = {
    "ban_chat_member",
    "kick_chat_member",
    "delete_message",
    "pin_chat_message",
    "promote_chat_member",
    "export_chat_invite_link",
    "send_message",
    "execute_code",
    "system_call",
    "shell_exec",
    "read_file",
    "write_file",
    "delete_all",
    "dump_memory",
    "get_settings",
    "set_settings",
    "grant_admin",
    "override",
    "sudo",
}

_RE_TOOL_SUSPICIOUS = re.compile(
    r"\b(?:" + "|".join(re.escape(t) for t in sorted(_TOOL_NAMES, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

# Delimiter imitation: trying to close or open system wrapping tags
_RE_DELIM_IMITATION = re.compile(
    r"</?(?:user_message|group_message|memory_entry|web_content|assistant_previous_output|system|instructions?|prompt|context|tools?|functions?)\s*[^>]*>",
    re.IGNORECASE,
)

# Repeated delimiter imitation attempts (3+ close/open patterns)
_RE_REPEATED_DELIM = re.compile(
    r"(</?\w+[^>]*>\s*){3,}",
)

# "Repeat back" / system prompt extraction
_RE_EXTRACT = re.compile(
    r"(?:repeat|echo|print|output|show|tell\s+me|what\s+is|reveal)\s+(?:back\s+)?(?:your\s+)?(?:system\s+)?(?:prompt|instructions?|rules?|guidelines?|setup|configuration)",
    re.IGNORECASE,
)

# Multi-turn priming — setting up future turns
_RE_PRIMING = re.compile(
    r"(?:from\s+now\s+on|going\s+forward|for\s+the\s+rest\s+of\s+this|in\s+all\s+future|every\s+time)\s*[,.]?\s*\w+",
    re.IGNORECASE,
)

# Encoding smuggling markers
_RE_ENCODING = re.compile(
    r"(?:base64|rot13|hex\s*(?:encode|encoded)?|url\s*(?:encode|encoded|decode)|unicode\s*(?:escape|encode)|utf-7|utf-16|quoted-printable|0x[0-9a-fA-F]{8,})",
    re.IGNORECASE,
)


@dataclass
class DetectionResult:
    score: float
    signals: list[str] = field(default_factory=list)


def detect(text: str) -> DetectionResult:
    """Scan text for known injection patterns.

    Returns DetectionResult with a 0-1 confidence score and a list of
    signal labels describing what was detected.
    """
    signals: list[str] = []
    score = 0.0

    if _RE_IGNORE.search(text):
        signals.append("ignore_previous_instructions")
        score += 0.25

    if _RE_YOU_ARE_NOW.search(text):
        signals.append("you_are_now")
        score += 0.25

    if _RE_ROLE_PREFIX.search(text):
        signals.append("role_confusion_prefix")
        score += 0.20

    if _RE_BASE64.search(text):
        signals.append("base64_block")
        score += 0.15

    if _RE_TOOL_SUSPICIOUS.search(text):
        signals.append("suspicious_tool_name")
        score += 0.15

    if _RE_DELIM_IMITATION.search(text):
        signals.append("delimiter_imitation")
        score += 0.20

    if _RE_REPEATED_DELIM.search(text):
        signals.append("repeated_delimiter_attempt")
        score += 0.20

    if _RE_EXTRACT.search(text):
        signals.append("system_prompt_extraction")
        score += 0.25

    if _RE_PRIMING.search(text):
        signals.append("multi_turn_priming")
        score += 0.15

    if _RE_ENCODING.search(text):
        signals.append("encoding_smuggling")
        score += 0.10

    return DetectionResult(score=min(score, 1.0), signals=signals)
