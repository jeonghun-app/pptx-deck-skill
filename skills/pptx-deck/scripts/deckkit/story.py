"""Reading structure: delivery mode, section tracker, summary and next-steps bands.

These pieces connect slides to each other rather than drawing one exhibit:
the deck's ``meta.mode`` fixes how many headline lines the title band reserves,
the tracker and ``eyebrow: auto`` tell the reader which chapter a page belongs
to, the ``summary`` layout states every chapter's conclusion on one page, and
the ``next_steps`` band closes a page with what the reader should do with it.
"""
from __future__ import annotations

from . import measure
from .brand import Brand, _merge
from .canvas import Canvas
from .layouts import (check_bottom, columns, draw_bullets, eyebrow_text, grid_span, headline,
                      layout, reading_width, source_line)

MODES = ("present", "read")
TRACKERS = ("none", "tabs", "dots")
MAX_TABS = 6  # more chapter labels than this cannot be read across one band when projected


# -- deck frame ----------------------------------------------------------------

def mode(meta: dict) -> str:
    return str((meta or {}).get("mode") or "present")


def title_lines(brand: Brand, meta: dict) -> int:
    """Headline lines the title band reserves: the brand's value, at least two when read."""
    lines = int(brand.get("layout.title_lines") or 1)
    return max(lines, 2) if mode(meta) == "read" else lines


def with_layout(brand: Brand, **values) -> Brand:
    """The same brand with some ``layout`` values replaced (the original stays untouched)."""
    return Brand(_merge(brand.data, {"layout": values}), brand.root)


def frame_brand(brand: Brand, meta: dict) -> Brand:
    """Brand whose title band holds ``title_lines(brand, meta)`` lines.

    ``title_h``, ``rule_y`` and ``body_top`` describe the band for the brand's own
    ``layout.title_lines``. Each extra line moves the rule and the body start down by
    one headline line height on every content slide of the deck, so the body starts
    at the same y whether a headline uses one line or two.
    """
    have = int(brand.get("layout.title_lines") or 1)
    want = title_lines(brand, meta)
    if want <= have:
        return brand
    line = float(brand["type.title"]) * 1.2 * float(brand.get("type.heading_line_spacing", 1.05))
    shift = (want - have) * line
    values = {"title_lines": want, "title_h": float(brand["layout.title_h"]) + shift,
              "body_top": float(brand["layout.body_top"]) + shift}
    if brand.get("layout.rule_y") is not None:
        values["rule_y"] = float(brand["layout.rule_y"]) + shift
    return with_layout(brand, **values)


# -- sections and the tracker ----------------------------------------------------

def number_label(number) -> str:
    """Section numbers render as on the section slide: 1 -> "01", "A" stays "A"."""
    return f"{number:0>2}" if str(number).isdigit() else str(number)


def sections(slides: list) -> list[dict]:
    """Section slides in deck order: slide index, number label, title, short label, thesis."""
    out = []
    for i, s in enumerate(slides, start=1):
        if s.get("layout") != "section":
            continue
        title = str(s.get("title", ""))
        out.append({"slide": i, "number": number_label(s.get("number", len(out) + 1)),
                    "title": title, "short": str(s.get("short") or title),
                    "subtitle": s.get("subtitle")})
    return out


def tracker_style(brand: Brand, meta: dict) -> str:
    return str((meta or {}).get("tracker") or brand.get("chrome.tracker") or "none")


def prepare(ctx, slides: list, meta: dict):
    """Attach the deck-level reading structure to the build context."""
    ctx.meta = meta or {}
    ctx.sections = sections(slides)
    ctx.section_at = {sec["slide"]: k for k, sec in enumerate(ctx.sections)}
    ctx.section = None  # index into ctx.sections of the chapter being built
    style = tracker_style(ctx.brand, meta)
    if style not in TRACKERS:
        ctx.warnings.add(0, f"unknown tracker '{style}' (use {', '.join(TRACKERS)}); no tracker drawn")
        style = "none"
    if style != "none" and len(ctx.sections) < 2:
        ctx.warnings.add(0, f"tracker '{style}' needs two or more section slides; no tracker drawn")
        style = "none"
    if style == "tabs" and len(ctx.sections) > MAX_TABS:
        ctx.warnings.add(0, f"{len(ctx.sections)} sections are too many tabs to read; tracker drawn as dots")
        style = "dots"
    if style == "tabs":
        b = ctx.brand
        n = len(ctx.sections)
        tab_w = (b.content_width - float(b["layout.gutter"]) * (n - 1)) / n
        for sec in ctx.sections:
            label = tab_label(b, sec)
            if measure.text_width(label, float(b["type.label"])) > tab_w:
                ctx.warnings.add(sec["slide"], f"tracker tab '{label}' is wider than its tab "
                                 f"({tab_w:.0f}pt); give the section a shorter `short:` label")
    ctx.tracker = style


def tab_label(brand: Brand, sec: dict) -> str:
    text = f"{sec['number']} {sec['short']}"
    return text.upper() if brand.get("type.eyebrow_uppercase") else text


def eyebrow(c: Canvas, spec: dict, ctx) -> str | None:
    """The slide's eyebrow text; ``auto`` becomes the enclosing section's number and name."""
    text = spec.get("eyebrow")
    if text != "auto":
        return text
    current = getattr(ctx, "section", None)
    if current is None:
        c.warn("eyebrow: auto on a slide before the first section; no eyebrow drawn")
        return None
    sec = ctx.sections[current]
    return f"{sec['number']} · {sec['short']}"


def tracker(c: Canvas, spec: dict, ctx) -> float:
    """Draw the section tracker in the eyebrow band. Returns the width left for the eyebrow.

    Tabs replace the eyebrow: the highlighted tab already names the chapter, and a
    second label in the same band would compete with it. Dots sit at the right end of
    the band and leave the eyebrow to its left. Slides before the first section, and
    the agenda (which is itself the map), get no tracker.
    """
    b = c.brand
    width = b.content_width
    style = getattr(ctx, "tracker", "none")
    current = getattr(ctx, "section", None)
    if style == "none" or current is None or spec.get("layout") == "agenda":
        return width
    if style == "tabs":
        _tabs(c, ctx.sections, current)
        return 0.0
    left = _dots(c, ctx.sections, current)
    return left - b.content_left - float(b["layout.gutter"])


def _tabs(c: Canvas, secs: list, current: int):
    b = c.brand
    size = float(b["type.label"])
    y = float(b["layout.eyebrow_y"]) - size * 0.6
    h = size * 1.4
    base = y + h + 1
    c.line(b.content_left, base, b.content_right, base, color="line", width=0.75, name="Tracker rule")
    for k, ((x, w), sec) in enumerate(zip(columns(c, len(secs)), secs)):
        active = k == current
        c.text(x, y, w, h, tab_label(b, sec), size="label", font="mono",
               color="accent" if active else c.muted, check_fit=False, name=f"Tracker tab {k + 1}")
        if active:
            c.box(x, base - 1, w, 2, fill="accent", radius=0, name="Tracker current")


def _dots(c: Canvas, secs: list, current: int) -> float:
    """Dots right-aligned in the eyebrow band. Returns their left edge."""
    b = c.brand
    size = float(b["type.label"])
    d = size * 0.6
    step = d * 2.4
    right = b.content_right
    if b.path("chrome.logo.path") and b.get("chrome.logo.position") == "top-right":
        right -= float(b.get("chrome.logo.width", 64)) + 16  # keep clear of the logo
    left = right - (len(secs) - 1) * step - d
    cy = float(b["layout.eyebrow_y"]) + size * 0.7
    c.line(left + d / 2, cy, right - d / 2, cy, color="line", width=0.75, name="Tracker line")
    for k in range(len(secs)):
        x = left + k * step
        if k == current:
            c.box(x, cy - d / 2, d, d, shape="oval", fill="accent", name=f"Tracker dot {k + 1}")
        else:
            c.box(x, cy - d / 2, d, d, shape="oval", fill="dark" if c.dark else "surface",
                  line=c.muted, line_width=0.75, name=f"Tracker dot {k + 1}")
    return left


# -- tinted bands -----------------------------------------------------------------

def _band_inner(c: Canvas, w: float) -> tuple[float, float]:
    pad = float(c.brand["layout.gutter"]) * 2 / 3
    rule = float(c.brand.get("layout.rule_h") or 2)
    return pad, w - 2 * pad - rule


def band_height(c: Canvas, w: float, text: str, size="lead") -> float:
    pad, inner = _band_inner(c, w)
    return c.text_height(text, size, reading_width(c, size, inner)) + 2 * pad


def band(c: Canvas, x: float, y: float, w: float, text: str, size="lead", name="Band") -> float:
    """Full-width tinted band with an accent rule on the left. Returns its height.

    Used for the answer under a question headline (``lead_style: band``) and the
    summary's closing ``so_what``. The text keeps the reading measure; the tint runs
    the full width so the band reads as one unit across the slide.
    """
    pad, inner = _band_inner(c, w)
    rule = w - inner - 2 * pad
    tw = reading_width(c, size, inner)
    th = c.text_height(text, size, tw)
    h = th + 2 * pad
    c.box(x, y, w, h, fill="surface_alt", radius=0, name=name)
    c.box(x, y, rule, h, fill="accent", radius=0, name=f"{name} rule")
    c.text(x + rule + pad, y + pad, tw, th, text, size=size, color="ink", name=f"{name} text")
    return h


# -- next steps band -----------------------------------------------------------------

def _next_steps(c: Canvas, spec: dict) -> tuple[str, list]:
    ns = spec.get("next_steps") or {}
    if isinstance(ns, list):
        ns = {"items": ns}
    label = ns.get("label") or c.brand.get("copy.next_steps_label") or (
        "시사점" if getattr(c, "language", "en") == "ko" else "What this means")
    return str(label), [str(item) for item in ns.get("items", [])]


def _next_steps_geometry(c: Canvas, items: list):
    b = c.brand
    pad = float(b["layout.gutter"]) * 2 / 3
    lx, lw = grid_span(c, 0, 2)
    ix = lx + lw + float(b["layout.gutter"])
    cols = columns(c, max(1, len(items)), x=ix, w=b.content_right - ix - pad)
    num_w = c.size("body") * 2
    heights = [c.text_height(item, "body", w - num_w) for (_, w), item in zip(cols, items)]
    return pad, (lx + pad, lw - pad), cols, num_w, max(heights or [0]) + 2 * pad


def reserve_next_steps(c: Canvas, spec: dict):
    """Take the next_steps band's height out of the body before the layout draws.

    The canvas brand gets a smaller ``layout.body_bottom`` while the layout runs, so
    every layout (built-in or custom) sees the shorter body and the source line moves
    up with it. Returns what ``draw_next_steps`` needs, or None without a band.
    """
    if not spec.get("next_steps"):
        return None
    label, items = _next_steps(c, spec)
    if not 2 <= len(items) <= 4:
        c.warn(f"next_steps has {len(items)} items; keep 2–4")
    *_, h = _next_steps_geometry(c, items)
    original = c.brand
    top = float(original["layout.body_bottom"]) - h
    c.brand = with_layout(original, body_bottom=top - float(original["layout.gutter"]))
    return original, top


def draw_next_steps(c: Canvas, spec: dict, reserved):
    original, top = reserved
    c.brand = original
    label, items = _next_steps(c, spec)
    pad, (lx, lw), cols, num_w, h = _next_steps_geometry(c, items)
    b = c.brand
    c.box(b.content_left, top, b.content_width, h, fill="surface_alt", radius=0, name="Next steps")
    c.box(b.content_left, top, float(b.get("layout.rule_h") or 2), h, fill="accent", radius=0,
          name="Next steps rule")
    drop = (c.size("body") - c.size("label")) * 0.9  # share the first baseline with the items
    c.text(lx, top + pad + drop, lw, h - 2 * pad - drop, eyebrow_text(c, label), size="label",
           font="mono", color="accent", name="Next steps label")
    for k, ((x, w), item) in enumerate(zip(cols, items), start=1):
        c.text(x, top + pad, num_w, c.size("body") * 1.5, f"{k:02}", size="body", font="mono",
               color="accent", check_fit=False, name=f"Next step {k} number")
        c.text(x + num_w, top + pad, w - num_w, h - 2 * pad, item, size="body", color="ink",
               name=f"Next step {k}")


# -- summary layout -------------------------------------------------------------------

def summary_block(c: Canvas, block, k: int, ctx) -> dict:
    """Resolve a summary block: ``section: n`` pulls the n-th section's title and thesis."""
    block = block if isinstance(block, dict) else {"heading": str(block)}
    out = {"number": f"{k + 1:02}", "heading": block.get("heading"), "thesis": block.get("thesis"),
           "points": block.get("points", [])}
    if block.get("section") is not None:
        secs = getattr(ctx, "sections", [])
        n = int(block["section"])
        if not 1 <= n <= len(secs):
            c.warn(f"summary block {k + 1} refers to section {n}; the deck has {len(secs)}", "ERROR")
        else:
            sec = secs[n - 1]
            out["number"] = sec["number"]
            out["heading"] = out["heading"] or sec["title"]
            out["thesis"] = out["thesis"] or sec["subtitle"]
    return out


@layout("summary")
def summary(c: Canvas, spec, ctx):
    """Executive summary: one column per chapter conclusion, then the ask in a band."""
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    if spec.get("so_what"):
        h = band_height(c, b.content_width, spec["so_what"])
        top = limit - h
        band(c, b.content_left, top, b.content_width, spec["so_what"], name="So what")
        limit = top - float(b["layout.gutter"])
    blocks = [summary_block(c, blk, k, ctx) for k, blk in enumerate(spec.get("blocks", []))]
    if not 2 <= len(blocks) <= 4:
        c.warn(f"summary has {len(blocks)} blocks; use 2–4 (one per section) and split the rest")
    end = y
    for (x, w), blk in zip(columns(c, max(1, len(blocks))), blocks):
        c.line(x, y, x + w, y, color="line", width=0.75)
        yy = y + 10
        lh = b["type.label"] * 1.5
        c.text(x, yy, w, lh, blk["number"], size="label", font="mono", color="accent",
               name=f"Summary {blk['number']}")
        yy += lh + 4
        if blk["heading"]:
            h = c.text_height(blk["heading"], "lead", w)
            c.text(x, yy, w, h, blk["heading"], size="lead", color=c.ink)
            yy += h + 6
        if blk["thesis"]:
            h = c.text_height(blk["thesis"], "body", w)
            c.text(x, yy, w, h, blk["thesis"], size="body", color=c.body_color, bold_color=c.ink)
            yy += h + 10
        if blk["points"]:
            yy = draw_bullets(c, x, yy, w, blk["points"], size="body")
        end = max(end, yy)
    check_bottom(c, end, limit)
