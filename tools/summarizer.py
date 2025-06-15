from __future__ import annotations

"""Simple summarization utility."""

from typing import Optional


def summarize_text(text: Optional[str], *, max_words: int = 200) -> str:
    """Return a short summary of ``text`` limited to ``max_words`` words.

    The implementation naively truncates the input after ``max_words`` words.
    Empty or non-string input returns an empty string.
    """
    if not isinstance(text, str) or not text.strip():
        return ""

    words = text.split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words])
