"""Brand profile loading.

A brand profile is a YAML file (see ``brand/brand.yaml``). Missing keys fall
back to the neutral defaults shipped with the skill, so an organization can
start with a profile that only overrides colors and fonts.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

import yaml
from pptx.dml.color import RGBColor

SKILL_DIR = Path(__file__).resolve().parents[2]
DEFAULT_BRAND = SKILL_DIR / "brand" / "brand.yaml"
HEX = re.compile(r"^#?[0-9A-Fa-f]{6}$")


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (over or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _merge(out[key], value)
        else:
            out[key] = value
    return out


class Brand:
    """Read-only view over a merged brand profile."""

    def __init__(self, data: dict, root: Path):
        self.data = data
        self.root = root  # directory of the brand file; relative asset paths start here

    # -- generic access -------------------------------------------------
    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def __getitem__(self, dotted: str) -> Any:
        value = self.get(dotted, KeyError)
        if value is KeyError:
            raise KeyError(f"brand profile has no key '{dotted}'")
        return value

    @property
    def width(self) -> float:
        return float(self["canvas.width"])

    @property
    def height(self) -> float:
        return float(self["canvas.height"])

    @property
    def content_left(self) -> float:
        return float(self["layout.margin_left"])

    @property
    def content_right(self) -> float:
        return self.width - float(self["layout.margin_right"])

    @property
    def content_width(self) -> float:
        return self.content_right - self.content_left

    # -- colors -----------------------------------------------------------
    def hex(self, key_or_hex: str | None) -> str | None:
        """Resolve a color token (``accent``) or a literal hex to 'RRGGBB'."""
        if key_or_hex is None:
            return None
        value = str(key_or_hex)
        colors = self.data.get("colors", {})
        if value in colors:
            value = str(colors[value])
        if not HEX.match(value):
            raise ValueError(f"unknown color token or hex: {key_or_hex!r}")
        return value.lstrip("#").upper()

    def rgb(self, key_or_hex: str) -> RGBColor:
        return RGBColor.from_string(self.hex(key_or_hex))

    def series(self, index: int) -> str:
        palette = self.get("colors.series") or [self.hex("accent")]
        return self.hex(palette[index % len(palette)])

    def is_dark(self, key_or_hex: str) -> bool:
        return luminance(self.hex(key_or_hex)) < 0.4

    def tint(self, key_or_hex: str, amount: float) -> str:
        """Mix a color toward white. amount=0.9 gives a very light tint."""
        r, g, b = (int(self.hex(key_or_hex)[i:i + 2], 16) for i in (0, 2, 4))
        mix = lambda c: round(c + (255 - c) * amount)
        return f"{mix(r):02X}{mix(g):02X}{mix(b):02X}"

    # -- paths ------------------------------------------------------------
    def path(self, dotted: str) -> Path | None:
        value = self.get(dotted)
        if not value:
            return None
        p = Path(value)
        return p if p.is_absolute() else (self.root / p)


def luminance(hex6: str) -> float:
    """WCAG relative luminance."""
    def channel(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex6[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def load_brand(path: str | Path | None = None) -> Brand:
    defaults = yaml.safe_load(DEFAULT_BRAND.read_text(encoding="utf-8"))
    if path is None or Path(path).resolve() == DEFAULT_BRAND:
        return Brand(defaults, DEFAULT_BRAND.parent)
    path = Path(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Brand(_merge(defaults, data), path.resolve().parent)
