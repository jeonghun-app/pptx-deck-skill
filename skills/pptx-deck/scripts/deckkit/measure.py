"""Approximate text measurement.

python-pptx cannot measure rendered text, so the builder estimates line counts
to warn about overflow before rendering. The estimate is deliberately a little
pessimistic; the rendered contact sheet is still the final judge.
"""
from __future__ import annotations

import re
import unicodedata

# Average advance widths in em for a typical sans-serif face.
_NARROW = set("iljtfI.,:;'!|()[] ")
_WIDE = set("mwMW@%")


def char_em(ch: str) -> float:
    if ch == " ":
        return 0.28
    if unicodedata.east_asian_width(ch) in ("W", "F"):
        return 0.95
    if ch in _NARROW:
        return 0.3
    if ch in _WIDE:
        return 0.85
    if ch.isupper():
        return 0.66
    if ch.isdigit():
        return 0.57
    return 0.55  # slightly wide: substituted fonts often run wider than the brand font


def text_width(text: str, size: float) -> float:
    return sum(char_em(c) for c in text) * size


def strip_markup(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", str(text))


def count_lines(text: str, size: float, width: float) -> int:
    """Greedy word wrap, per paragraph (newline separated)."""
    if width <= 0:
        return 99
    total = 0
    for para in strip_markup(text).split("\n"):
        line = 0.0
        lines = 1
        for word in re.split(r"(\s+)", para):
            if not word:
                continue
            w = text_width(word, size)
            if word.isspace():
                line += w
                continue
            if line + w <= width or line == 0:
                if w > width:  # one long word wraps by itself
                    extra = int(w // width)
                    lines += extra
                    line = w - extra * width
                else:
                    line += w
            else:
                lines += 1
                line = w
        total += lines
    return total


def text_height(text: str, size: float, width: float, spacing: float = 1.2) -> float:
    return count_lines(text, size, width) * size * 1.2 * spacing
