from __future__ import annotations

SPOTLIGHT_CHAR = "‹"  # ‹ — single left-pointing angle quotation mark


def spotlight(text: str) -> str:
    """Replace every space character with the spotlight marker (U+2039).

    This implements the Microsoft Spotlighting research technique:
    spaces are replaced with ‹ so the LLM can visually distinguish
    external input from system instructions.
    """
    return text.replace(" ", SPOTLIGHT_CHAR)


def unspotlight(text: str) -> str:
    """Reverse the spotlight transformation: restore spaces from ‹ markers."""
    return text.replace(SPOTLIGHT_CHAR, " ")
