"""Text measurement.

python-pptx cannot measure rendered text, so the builder estimates line counts
to warn about overflow before rendering. When the brand's fonts can be found
(``fonts.<role>.file``, or fontconfig's match for the face name, which is the
font LibreOffice renders with), words are measured with the real glyph
advances; otherwise an average-width table is used. The rendered contact sheet
is still the final judge.
"""
from __future__ import annotations

import functools
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path

# role -> (latin font file, east-asian font file); filled by set_fonts()
_FILES: dict = {}

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


def _is_cjk(ch: str) -> bool:
    return unicodedata.east_asian_width(ch) in ("W", "F")


@functools.lru_cache(maxsize=None)
def _match(face: str) -> str | None:
    """Font fontconfig would use for ``face``, as ``file`` or ``file#index`` for a face
    inside a collection (.ttc). None without fontconfig."""
    if not face or not shutil.which("fc-match"):
        return None
    try:
        out = subprocess.run(["fc-match", "-f", "%{file}\n%{index}", face], capture_output=True,
                             text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    file, _, index = out.stdout.partition("\n")
    if not file.strip():
        return None
    index = index.strip()
    return f"{file.strip()}#{index}" if index.isdigit() and index != "0" else file.strip()


@functools.lru_cache(maxsize=None)
def _font(file: str):
    """ImageFont at 100 px for ``file`` or ``file#index``."""
    path, _, index = file.partition("#")
    try:
        from PIL import ImageFont
        return ImageFont.truetype(path, 100, index=int(index) if index.isdigit() else 0)
    except Exception:
        return None


def set_fonts(brand) -> None:
    """Register the brand's fonts for measurement (once per build or lint)."""
    _FILES.clear()
    for role in ("heading", "body", "mono"):
        spec = brand.get(f"fonts.{role}") or {}
        latin = brand.path(f"fonts.{role}.file") if spec.get("file") else None
        ea = brand.path(f"fonts.{role}.file_east_asian") if spec.get("file_east_asian") else None
        latin = str(latin) if latin and Path(latin).exists() else _match(spec.get("latin"))
        ea = str(ea) if ea and Path(ea).exists() else _match(spec.get("east_asian"))  # "file#index" for .ttc
        if latin and _font(latin):
            _FILES[role] = (latin, ea if ea and _font(ea) else latin)


@functools.lru_cache(maxsize=65536)
def _measured(run: str, file: str) -> float:
    return _font(file).getlength(run) / 100  # em


def text_width(text: str, size: float, role: str = "body") -> float:
    files = _FILES.get(role) or _FILES.get("body")
    if not files:
        return sum(char_em(c) for c in text) * size
    total = 0.0
    for run in re.findall(r"[\u1100-\u11ff\u2e80-\ua4cf\uac00-\ud7af\uf900-\ufaff\uff00-\uffef]+|[^\u1100-\u11ff\u2e80-\ua4cf\uac00-\ud7af\uf900-\ufaff\uff00-\uffef]+", text):
        total += _measured(run, files[1] if _is_cjk(run[0]) else files[0])
    return total * size * 1.02  # small margin for kerning and hinting differences


def strip_markup(text: str) -> str:
    return re.sub(r"\*\*(.+?)\*\*", r"\1", str(text))


def count_lines(text: str, size: float, width: float, role: str = "body") -> int:
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
            w = text_width(word, size, role)
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


def text_height(text: str, size: float, width: float, spacing: float = 1.2, role: str = "body") -> float:
    return count_lines(text, size, width, role) * size * 1.2 * spacing


# Average advance of running Latin text, spaces included. A CJK glyph (0.95 em)
# is about two of these, so a measure counted in Latin characters holds roughly
# half as many Hangul or Kanji characters per line.
LATIN_EM = 0.5


def chars_per_line(size: float, width: float) -> float:
    """How many average Latin characters fit on one line of ``width`` at ``size``."""
    return width / (LATIN_EM * size) if size > 0 else 0.0


def measure_width(size: float, chars: float) -> float:
    """Width of a line that holds ``chars`` average Latin characters at ``size``."""
    return chars * LATIN_EM * size
