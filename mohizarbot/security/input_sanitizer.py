from __future__ import annotations

import re
import unicodedata

# Ranges compiled at module load
_ZERO_WIDTH_RE = re.compile("[​-‏⁠⁡⁢⁣⁤⁦-⁩﻿­]")

_BIDI_OVERRIDE_RE = re.compile("[‪-‮⁦-⁩]")

# Trojan-Source: RLO, LRO, PDF, etc. plus homoglyph ranges
_TROJAN_SOURCE_RE = re.compile("[‪-‮⁦-⁩  ‎‏]")

# Unicode confusable / homoglyph patterns (common ones used in attacks)
_HOMOGLYPH_TABLE = str.maketrans(
    {
        "а": "a",  # Cyrillic a
        "е": "e",  # Cyrillic e
        "о": "o",  # Cyrillic o
        "р": "p",  # Cyrillic r
        "с": "c",  # Cyrillic s
        "х": "x",  # Cyrillic h
        "ѕ": "s",  # Cyrillic dze
        "Ѐ": "E",  # Cyrillic IE with grave
        "А": "A",  # Cyrillic A
        "Е": "E",  # Cyrillic E
        "О": "O",  # Cyrillic O
        "Р": "P",  # Cyrillic R
        "С": "C",  # Cyrillic S
        "Х": "X",  # Cyrillic H
        "Α": "A",  # Greek Alpha
        "Ε": "E",  # Greek Epsilon
        "Ο": "O",  # Greek Omicron
        "Ρ": "P",  # Greek Rho
        "Υ": "Y",  # Greek Upsilon
        "Ν": "N",  # Greek Nu
    }
)

_DEDUP_RUN_RE = re.compile(r"(.)\1{50,}")


def sanitize(text: str, max_len: int = 4096) -> str:
    """Sanitize untrusted input text.

    Returns cleaned text safe for wrapping and LLM context inclusion.
    Processing order:
    1. Strip zero-width characters
    2. Strip bidi override characters
    3. Strip Trojan-Source patterns
    4. Replace common homoglyphs with ASCII equivalents
    5. NFC normalize
    6. Collapse deduplicated character runs (>50 identical chars)
    7. Truncate to max_len
    """
    # 1. Strip zero-width chars
    text = _ZERO_WIDTH_RE.sub("", text)

    # 2. Strip bidi overrides
    text = _BIDI_OVERRIDE_RE.sub("", text)

    # 3. Strip Trojan-Source patterns
    text = _TROJAN_SOURCE_RE.sub("", text)

    # 4. Replace common homoglyphs
    text = text.translate(_HOMOGLYPH_TABLE)

    # 5. NFC normalize
    text = unicodedata.normalize("NFC", text)

    # 6. Collapse runs of >50 identical chars
    text = _DEDUP_RUN_RE.sub(lambda m: m.group(1) * 50, text)

    # 7. Truncate
    if len(text) > max_len:
        text = text[:max_len]

    return text
