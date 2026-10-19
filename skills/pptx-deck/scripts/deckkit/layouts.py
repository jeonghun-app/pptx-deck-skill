"""Slide layouts.

Each layout receives a ``Canvas``, the slide spec (a dict from deck.yaml) and
the build context. Content layouts draw the shared chrome (eyebrow, headline,
accent rule) and then place their body between ``layout.body_top`` and
``layout.body_bottom``. Layouts never invent values: every size, color and
position comes from the brand profile.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from . import exhibits, measure
from .canvas import Canvas

LAYOUTS = {}


def layout(name, structural=False):
    def register(fn):
        fn.structural = structural
        LAYOUTS[name] = fn
        return fn
    return register


# -- shared geometry ---------------------------------------------------------

def columns(c: Canvas, n: int, x=None, w=None, gap=None):
    x = c.brand.content_left if x is None else x
    w = c.brand.content_width if w is None else w
    gap = float(c.brand["layout.gutter"]) if gap is None else gap
    cw = (w - gap * (n - 1)) / n
    return [(x + i * (cw + gap), cw) for i in range(n)]


def grid_span(c: Canvas, start: int, span: int = 1):
    """(x, w) of ``span`` columns starting at column ``start`` (0-based) on the brand grid
    (``layout.columns`` columns separated by ``layout.gutter``). For custom renderers."""
    n = int(c.brand.get("layout.columns", 12))
    gap = float(c.brand["layout.gutter"])
    cw = (c.brand.content_width - gap * (n - 1)) / n
    return c.brand.content_left + start * (cw + gap), span * cw + (span - 1) * gap


def eyebrow_text(c: Canvas, text: str) -> str:
    return str(text).upper() if c.brand.get("type.eyebrow_uppercase") else str(text)


def reading_width(c: Canvas, size, width: float) -> float:
    """Width for reading text at ``size``: at most ``type.max_measure`` characters per line.

    Lines much longer than that make the eye lose its place on the way back to the
    next line, so wider space stays empty (or goes to the exhibit) instead.
    """
    chars = c.brand.get("type.max_measure")
    return min(width, measure.measure_width(c.size(size), float(chars))) if chars else width


def headline(c: Canvas, spec: dict, ctx) -> float:
    """Eyebrow (or section tracker) + headline + accent rule + lead. Returns the body start y.

    The band reserves ``layout.title_lines`` headline lines (two in ``meta.mode: read``),
    so the body starts at the same y on every content slide of the deck.
    """
    from . import story  # story builds on this module, so it is imported late
    b = c.brand
    x, w = b.content_left, b.content_width
    eyebrow_w = story.tracker(c, spec, ctx)
    eyebrow = story.eyebrow(c, spec, ctx)
    if eyebrow and eyebrow_w > 0:
        text = eyebrow_text(c, eyebrow)
        c.text(x, b["layout.eyebrow_y"], eyebrow_w, b["type.label"] * 1.4, text, size="label",
               font="mono", color="accent", name="Eyebrow")
    title = spec.get("title")
    if title:
        if ctx.title_placeholder(c, title):
            pass
        else:
            c.text(x, b["layout.title_y"], w, b["layout.title_h"], title, size="title",
                   font="heading", color=c.ink, bold=bool(b.get("type.heading_bold")),
                   spacing=b.get("type.heading_line_spacing"), anchor="top", name="Title",
                   check_fit=False)
        lines = measure.count_lines(title, b["type.title"], w, "heading")
        allowed = int(b.get("layout.title_lines") or 1)
        if lines > allowed:
            limit = "one line" if allowed == 1 else f"at most {allowed} lines"
            c.warn(f"headline wraps to {lines} lines; content headlines are {limit} — shorten it")
    if b.get("layout.rule_y") is not None and title and not spec.get("no_rule"):
        c.box(x, b["layout.rule_y"], b["layout.rule_w"], b["layout.rule_h"], fill="accent",
              radius=0, name="Rule")
    y = float(b["layout.body_top"])
    lead = spec.get("lead")
    if lead and spec.get("lead_style") == "band":  # the answer under a question headline
        y += story.band(c, x, y, w, lead, name="Lead band") + float(b["layout.gutter"])
    elif lead:
        lw = reading_width(c, "lead", w)
        h = c.text_height(lead, "lead", lw)
        c.text(x, y, lw, h, lead, size="lead", color=c.body_color, name="Lead")
        y += h + float(b["layout.gutter"])
    return y


def source_line(c: Canvas, spec: dict) -> float:
    """Draw the exhibit footer at the bottom of the body. Returns its top.

    ``source`` is a string (one line) or an object with ``notes``, ``question``,
    ``base``, ``n``, ``as_of``, ``rounding`` and ``text``. The block grows upward,
    so the body limit shrinks while the headline stays where it is.
    """
    b = c.brand
    bottom = float(b["layout.body_bottom"])
    src = spec.get("source")
    language = getattr(c, "language", "en")
    extra = exhibits.auto_notes(spec, b, language)
    if not src and not extra:
        return bottom
    if isinstance(src, dict) or extra:
        paras = exhibits.footer_paragraphs(src, b, language, extra)
        h = max(c.size("caption") * 1.5, c.text_height(paras, "caption", b.content_width))
        top = bottom - h
        c.text(b.content_left, top, b.content_width, h, paras, size="caption", color="muted",
               anchor="bottom", name="Source")
        return top - float(b["layout.gutter"]) / 2
    h = c.size("caption") * 1.5
    top = bottom - h
    c.text(b.content_left, top, b.content_width, h, exhibits.source_text(b, language, src),
           size="caption", color="muted", anchor="bottom", name="Source")
    return top - float(b["layout.gutter"]) / 2


def commentary_column(c: Canvas, spec: dict, y: float, limit: float):
    """Draw the side commentary of an exhibit and return the (x, w) left for it.

    ``commentary: {text | bullets, side: right | left, width: 3 | 4}`` takes that
    many grid columns; ``takeaway: "..."`` is the same as right, 4 columns. Text
    follows the width rule: ``type.lead`` at 4 columns, ``type.body`` at 3.
    """
    b = c.brand
    note = spec.get("commentary")
    if note is None and spec.get("takeaway"):
        note = {"text": spec["takeaway"]}
    if not note:
        return b.content_left, b.content_width
    if isinstance(note, str):
        note = {"text": note}
    n = int(b.get("layout.columns", 12))
    span = int(note.get("width", 4))
    if note.get("side", "right") == "left":
        (tx, tw), (x, w) = grid_span(c, 0, span), grid_span(c, span, n - span)
    else:
        (x, w), (tx, tw) = grid_span(c, 0, n - span), grid_span(c, n - span, span)
    size = "lead" if span >= 4 else "body"
    inner = tw - 12
    end = y
    if note.get("text"):
        th = c.text_height(note["text"], size, inner)
        c.text(tx + 12, y, inner, th, note["text"], size=size, color=c.ink, bold_color="accent",
               name="Commentary")
        end = y + th
    if note.get("bullets"):
        start = end + (c.size(size) * 0.6 if end > y else 0)
        end = draw_bullets(c, tx + 12, start, inner, note["bullets"], size=size)
    c.box(tx, y, 2, end - y, fill="accent", radius=0, name="Commentary rule")
    check_bottom(c, end, limit)
    return x, w


def check_bottom(c: Canvas, y_end: float, limit: float):
    if y_end > limit + 0.5:
        c.warn(f"content ends at {y_end:.0f}pt, below the body limit {limit:.0f}pt — split the slide "
               "or shorten the copy (do not shrink the type)", "ERROR")


def bullet_items(items):
    if isinstance(items, (str, int, float)):  # a single item written without a list
        items = [items]
    out = []
    for item in items or []:
        if isinstance(item, dict):
            out.append((str(item.get("text", "")), [str(s) for s in item.get("sub", [])]))
        else:
            out.append((str(item), []))
    return out


def draw_bullets(c: Canvas, x, y, w, items, size="lead", gap=None) -> float:
    gap = c.size(size) * 0.6 if gap is None else gap
    w = reading_width(c, size, w)  # narrow columns are unaffected; wide lists keep the measure
    paras = []
    for text, subs in bullet_items(items):
        paras.append({"text": text, "size": size, "bullet": "•", "color": c.body_color,
                      "bold_color": c.ink, "space_before": gap})
        paras += [{"text": sub, "size": "body", "bullet": "–", "color": "muted",
                   "left": c.size(size) * 1.1, "space_before": 2.0} for sub in subs]
    if not paras:
        return y
    # one box: the application flows the lines, so gaps stay even however lines break
    _, h = c.paragraphs(x, y, w, paras, name="Bullets")
    return y + h


def title_block(c: Canvas, x, y, w, h, text, *, size, spacing=None, bold=None, bold_color=None,
                name="Title"):
    """A large title whose last line sits on the line y + h.

    The box is bottom-anchored with headroom above, so a title that renders longer
    than estimated grows upward into free space instead of down into the text below.
    """
    bold = bool(c.brand.get("type.heading_bold")) if bold is None else bold
    return c.text(x, y - h * 0.6, w, h * 1.6, text, size=size, font="heading", color=c.ink,
                  bold=bold, spacing=spacing, bold_color=bold_color, anchor="bottom", name=name)


# -- structural slides -------------------------------------------------------

@layout("cover", structural=True)
def cover(c: Canvas, spec, ctx):
    b = c.brand
    x, w = b.content_left, b.content_width * 0.82
    title = spec.get("title", "")
    if ctx.title_placeholder(c, title, subtitle=spec.get("subtitle")):
        return
    th = c.text_height(title, "hero", w, b.get("type.heading_line_spacing"), font="heading")
    y = b.height * 0.42 - th / 2
    if spec.get("eyebrow"):
        c.text(x, y - b["type.label"] * 2.4, w, b["type.label"] * 1.4, eyebrow_text(c, spec["eyebrow"]),
               size="label", font="mono", color="on_dark_body" if c.dark else "accent")
    title_block(c, x, y, w, th, title, size="hero", spacing=b.get("type.heading_line_spacing"))
    y += th + b["layout.gutter"]
    if spec.get("subtitle"):
        sw = reading_width(c, "lead", w)
        sh = c.text_height(spec["subtitle"], "lead", sw)
        c.text(x, y, sw, sh, spec["subtitle"], size="lead", color=c.body_color, name="Subtitle")
    meta = " · ".join(str(v) for v in (spec.get("presenter"), spec.get("role"), spec.get("date")) if v)
    if meta:
        c.text(x, b.height - 96, w, b["type.body"] * 1.6, meta, size="body", color=c.muted,
               name="Presenter")
    ctx.cover_logo(c)


@layout("section", structural=True)
def section(c: Canvas, spec, ctx):
    b = c.brand
    x, w = b.content_left, b.content_width * 0.8
    title = spec.get("title", "")
    if ctx.title_placeholder(c, title, subtitle=spec.get("subtitle")):
        return
    th = c.text_height(title, "section", w, b.get("type.heading_line_spacing"), font="heading")
    y = b.height * 0.45 - th / 2
    if spec.get("number") is not None:
        c.text(x, y - b["type.section"] * 1.7, w, b["type.section"] * 1.5, f"{spec['number']:0>2}"
               if str(spec["number"]).isdigit() else str(spec["number"]), size="section",
               font="mono", color="accent", name="Number")
    title_block(c, x, y, w, th, title, size="section", spacing=b.get("type.heading_line_spacing"))
    if spec.get("subtitle"):  # the chapter's thesis; the summary layout can repeat it
        sy = y + th + b["layout.gutter"]
        sw = reading_width(c, "lead", w)
        c.text(x, sy, sw, c.text_height(spec["subtitle"], "lead", sw), spec["subtitle"],
               size="lead", color=c.body_color)


@layout("closing", structural=True)
def closing(c: Canvas, spec, ctx):
    b = c.brand
    x, w = b.content_left, b.content_width
    title = spec.get("title") or b.get("copy.closing_title", "Thank you")
    if ctx.title_placeholder(c, title, subtitle=spec.get("subtitle")):
        return
    th = c.text_height(title, "hero", w, font="heading")
    y = b.height * 0.42 - th / 2
    title_block(c, x, y, w, th, title, size="hero")
    y += th + b["layout.gutter"]
    for key, size in (("subtitle", "lead"), ("contact", "body")):
        if spec.get(key):
            kw = reading_width(c, size, w)
            h = c.text_height(spec[key], size, kw)
            c.text(x, y, kw, h, spec[key], size=size, color=c.body_color if key == "subtitle" else c.muted)
            y += h + b["layout.gutter"] / 2
    ctx.cover_logo(c)


@layout("statement", structural=True)
def statement(c: Canvas, spec, ctx):
    b = c.brand
    x, w = b.content_left, b.content_width * 0.86
    text = spec.get("text") or spec.get("title", "")
    th = c.text_height(text, "statement", w, b.get("type.heading_line_spacing"), font="heading")
    support = spec.get("support")
    sw = reading_width(c, "lead", w)
    sh = c.text_height(support, "lead", sw) if support else 0
    y = (b.height - th - sh - b["layout.gutter"]) / 2
    if spec.get("eyebrow"):
        c.text(x, y - b["type.label"] * 2.6, w, b["type.label"] * 1.4, eyebrow_text(c, spec["eyebrow"]),
               size="label", font="mono", color="accent")
    title_block(c, x, y, w, th, text, size="statement", spacing=b.get("type.heading_line_spacing"),
                bold_color="accent", name="Statement")
    if support:
        c.text(x, y + th + b["layout.gutter"], sw, sh, support, size="lead", color=c.body_color)


@layout("quote", structural=True)
def quote(c: Canvas, spec, ctx):
    b = c.brand
    x, w = b.content_left + 36, b.content_width * 0.8
    raw = str(spec.get("text", "")).strip("“”\"")
    text = f"“{raw}”"
    th = c.text_height(text, "statement", w, b.get("type.heading_line_spacing"), font="heading")
    y = (b.height - th) / 2 - 20
    c.box(b.content_left, y + 4, 3, th - 8, fill="accent", radius=0)
    title_block(c, x, y, w, th, text, size="statement", spacing=b.get("type.heading_line_spacing"),
                bold=False, name="Quote")
    who = " · ".join(str(v) for v in (spec.get("attribution"), spec.get("role")) if v)
    if who:
        c.text(x, y + th + b["layout.gutter"], w, b["type.body"] * 1.6, who, size="body", color=c.muted)


# -- content slides ----------------------------------------------------------

@layout("agenda")
def agenda(c: Canvas, spec, ctx):
    b = c.brand
    spec = {"eyebrow": b.get("copy.agenda_eyebrow", "AGENDA"), **spec}
    y = headline(c, spec, ctx)
    items = spec.get("items", [])
    current = spec.get("current")
    limit = float(b["layout.body_bottom"])
    row = min(44.0, (limit - y) / max(1, len(items)))
    x, w = b.content_left, b.content_width * 0.7
    for i, item in enumerate(items):
        active = current is not None and i == current
        color = c.ink if (current is None or active) else "muted"
        c.text(x, y, 40, row, f"{i + 1:02}", size="lead", font="mono",
               color="accent" if active or current is None else "muted", anchor="middle")
        c.text(x + 48, y, w - 48, row, str(item), size="lead", color=color, anchor="middle")
        c.line(x, y + row, x + w, y + row, color="line", width=0.5)
        y += row
    check_bottom(c, y, limit)


@layout("bullets")
def bullets(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    items = spec.get("bullets", [])
    if len(items) > 5:
        c.warn(f"{len(items)} bullets; keep 3–5 per slide and split the rest evenly")
    end = draw_bullets(c, b.content_left, y, b.content_width * 0.9, items)
    check_bottom(c, end, limit)


def _column_block(c: Canvas, x, y, w, block, limit):
    if isinstance(block, str):
        block = {"body": block}
    if block.get("heading"):
        h = c.text_height(block["heading"], "lead", w)
        c.text(x, y, w, h, block["heading"], size="lead", color=c.ink,
               bold=True)
        y += h + 8
    if block.get("body"):
        h = c.text_height(block["body"], "body", w)
        c.text(x, y, w, h, block["body"], size="body", color=c.body_color, bold_color=c.ink)
        y += h + 8
    if block.get("bullets"):
        y = draw_bullets(c, x, y, w, block["bullets"], size="body") + 8
    return y - 8


@layout("two_column")
def two_column(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    relation = spec.get("relation")
    gap = float(b["layout.gutter"]) * (3 if relation else 2)
    (lx, lw), (rx, rw) = columns(c, 2, gap=gap)
    end = max(_column_block(c, lx, y, lw, spec.get("left", {}), limit),
              _column_block(c, rx, y, rw, spec.get("right", {}), limit))
    if relation:  # the symbol states how the two panels relate
        mid = lx + lw + gap / 2
        c.text(mid - gap / 2, y, gap, (end - y), str(relation), size="lead", color="accent",
               align="center", anchor="middle", check_fit=False)
    else:
        c.line(lx + lw + gap / 2, y, lx + lw + gap / 2, end, color="line", width=0.5)
    check_bottom(c, end, limit)


@layout("cards")
def cards(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    items = spec.get("cards", [])
    n = len(items)
    is_open = spec.get("style", "filled") == "open"
    if n > (5 if is_open else 4):
        c.warn(f"{n} cards in one row; use at most {5 if is_open else 4}"
               f"{'' if is_open else ' (5 with style: open)'} or a table")
    cols = columns(c, max(1, n))
    highlight = spec.get("highlight")
    numbered = bool(spec.get("numbered"))
    pad = 14.0
    inset = 0.0 if is_open else pad  # open columns align their text with the column edge
    icon = 22.0
    num_pt = c.size("statement")
    num_h = num_pt * 1.2 + 8
    heights = []
    for (x, w), item in zip(cols, items):
        iw = w - 2 * inset
        hh = pad + (0 if is_open else pad)
        if numbered:
            hh += num_h
        if item.get("icon"):
            hh += icon + 10
        if item.get("heading"):
            hh += c.text_height(item["heading"], "lead", iw) + 6
        if item.get("body"):
            hh += c.text_height(item["body"], "body", iw)
        if item.get("bullets"):
            for t, _ in bullet_items(item["bullets"]):
                hh += c.text_height(t, "body", iw - c.size("body") * 1.1) + c.size("body") * 0.5
        heights.append(hh)
    card_h = max(heights or [0])
    for i, ((x, w), item) in enumerate(zip(cols, items)):
        active = highlight == i
        if is_open:  # no fill: a hairline over each column, the accent one marks the highlight
            if active:
                c.box(x, y - 1, w, 2, fill="accent", radius=0, name=f"Card {i + 1}")
            else:
                c.line(x, y, x + w, y, color="line", width=0.75, name=f"Card {i + 1}")
        else:
            c.box(x, y, w, card_h, fill="surface_alt" if not active else c.brand.tint("accent", 0.92),
                  line="accent" if active else None, line_width=1.0, name=f"Card {i + 1}")
        cx, cw = x + inset, w - 2 * inset
        cy = y + pad
        if numbered:
            c.text(cx, cy, cw, num_pt * 1.15, f"{i + 1:02}", size="statement", font="heading",
                   color="accent", check_fit=False, name=f"Card {i + 1} number")
            cy += num_h
        if item.get("icon"):
            path = ctx.icon(item["icon"], c)
            if path:
                c.image(path, cx, cy, icon, icon)
            cy += icon + 10
        if item.get("heading"):
            h = c.text_height(item["heading"], "lead", cw)
            c.text(cx, cy, cw, h, item["heading"], size="lead", color=c.ink)
            cy += h + 6
        if item.get("body"):
            h = c.text_height(item["body"], "body", cw)
            c.text(cx, cy, cw, h, item["body"], size="body", color=c.body_color,
                   bold_color=c.ink)
            cy += h
        if item.get("bullets"):
            draw_bullets(c, cx, cy, cw, item["bullets"], size="body")
    check_bottom(c, y + card_h, limit)


@layout("stats")
def stats(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    items = spec.get("stats", [])
    if not spec.get("source"):
        c.warn("stats slide without a source line")
    highlight = spec.get("highlight")
    if len(items) > 4:
        check_bottom(c, _stat_grid(c, items, highlight, y), limit)
        return
    value_size = b["type.statement"]
    end = y
    for i, ((x, w), item) in enumerate(zip(columns(c, max(1, len(items))), items)):
        color = "accent" if (highlight is None or highlight == i) else c.ink
        vh = value_size * 1.3
        c.text(x, y, w, vh, str(item.get("value", "")), size=value_size, font="heading",
               color=color, name=f"Stat {i + 1}", check_fit=False)
        if measure.text_width(str(item.get("value", "")), value_size) > w:
            c.warn(f"stat value '{item.get('value')}' is wider than its column")
        yy = y + vh + 4
        c.line(x, yy, x + w, yy, color="line", width=0.75)
        yy += 10
        if item.get("label"):
            h = c.text_height(item["label"], "lead", w)
            c.text(x, yy, w, h, item["label"], size="lead", color=c.ink)
            yy += h + 4
        if item.get("detail"):
            h = c.text_height(item["detail"], "body", w)
            c.text(x, yy, w, h, item["detail"], size="body", color=c.muted)
            yy += h
        end = max(end, yy)
    check_bottom(c, end, limit)


def _stat_grid(c: Canvas, items, highlight, y) -> float:
    """5-9 stats as a 3-column grid (3x2, 3x3) separated by hairlines, no boxes.

    Values are about three times the label size so the eye scans the numbers first."""
    b = c.brand
    if len(items) > 9:
        c.warn(f"{len(items)} stats; keep at most 9 or move the rest to a table")
    value_pt = c.size("statement" if len(items) <= 6 else "section")
    cols = columns(c, 3)
    gutter = float(b["layout.gutter"])
    pad = 12.0
    vh = value_pt * 1.25
    rows = [items[i:i + 3] for i in range(0, len(items), 3)]
    heights = []
    for row in rows:
        need = 0.0
        for (x, w), item in zip(cols, row):
            hh = vh + 4
            if item.get("label"):
                hh += c.text_height(item["label"], "body", w) + 2
            if item.get("detail"):
                hh += c.text_height(item["detail"], "body", w)
            need = max(need, hh)
        heights.append(need + 2 * pad)
    top = y
    for r, (row, h) in enumerate(zip(rows, heights)):
        if r:
            c.line(b.content_left, top, b.content_right, top, color="line", width=0.75)
        for j, ((x, w), item) in enumerate(zip(cols, row)):
            i = r * 3 + j
            yy = top + (pad if r else 0)
            value = str(item.get("value", ""))
            color = "accent" if (highlight is None or highlight == i) else c.ink
            c.text(x, yy, w, vh, value, size=value_pt, font="heading", color=color,
                   name=f"Stat {i + 1}", check_fit=False)
            if measure.text_width(value, value_pt) > w:
                c.warn(f"stat value '{value}' is wider than its column")
            yy += vh + 4
            if item.get("label"):
                lh = c.text_height(item["label"], "body", w)
                c.text(x, yy, w, lh, item["label"], size="body", color=c.ink)
                yy += lh + 2
            if item.get("detail"):
                dh = c.text_height(item["detail"], "body", w)
                c.text(x, yy, w, dh, item["detail"], size="body", color=c.muted)
        top += h - (0 if r else pad)
    end = top - pad
    for (x, w) in cols[1:]:  # vertical hairlines in the gutters
        c.line(x - gutter / 2, y, x - gutter / 2, end, color="line", width=0.75)
    return end


@layout("table")
def table(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    rows = spec.get("rows", [])
    cols = spec.get("columns", [])
    if len(rows) > 7 or len(cols) > 7:
        c.warn(f"table is {len(rows)}x{len(cols)}; keep within 7 rows and 7 columns or split it")
    x, w = commentary_column(c, spec, y, limit)
    y += 4 if spec.get("highlight_col") is not None else 0
    family = spec.get("symbols")
    labels = None
    if family:
        from .frameworks import SYMBOLS, symbol_labels
        if family not in SYMBOLS:
            c.warn(f"unknown symbols '{family}' (use {', '.join(SYMBOLS)})", "ERROR")
            family = None
        else:
            legend = spec.get("legend", "auto")
            labels = symbol_labels(c, family, legend if isinstance(legend, dict) else None)
    elif any(isinstance(cell, dict) for row in rows for cell in row):
        c.warn("table has {s: ...} cells but no 'symbols' family (harvey, check, rag, tier)", "ERROR")
    _, h = c.table(x, y, w, cols, rows, widths=spec.get("widths"),
                   numeric_cols=tuple(spec.get("numeric_cols", ())),
                   highlight_col=spec.get("highlight_col"), total_row=bool(spec.get("total_row")),
                   size="body", name="Table", symbols=family, symbol_labels=labels)
    y += h
    if family and spec.get("legend", "auto") is not False:  # symbols are read through the legend
        from .frameworks import normalize_symbol, symbol_legend
        used = {normalize_symbol(family, cell.get("s")) for row in rows for cell in row
                if isinstance(cell, dict) and "s" in cell}
        y += 8
        y += symbol_legend(c, x, y, w, family, labels, used)
    check_bottom(c, y, limit)


@layout("chart")
def chart(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    ch = spec.get("chart", {})
    x, w = commentary_column(c, spec, y, limit)
    if exhibits.panels_of(ch):
        chart_panels(c, x, y, w, limit - y, ch)
        return
    if ch.get("unit"):
        c.text(x, y, w, b["type.caption"] * 1.5, ch["unit"], size="caption", color="muted")
        y += b["type.caption"] * 1.8
    draw_chart(c, x, y, w, limit - y, ch, name="Chart")


def draw_chart(c: Canvas, x, y, w, h, ch: dict, name="Chart", **shared):
    """One native chart from a chart spec (also used for each panel)."""
    if ch.get("type") == "waterfall":
        return c.waterfall(x, y, w, h, ch, number_format=ch.get("number_format"), name=name, **shared)
    return c.chart(x, y, w, h, ch.get("type", "column"), ch.get("categories", []),
                   ch.get("series", []), highlight=ch.get("highlight"),
                   number_format=ch.get("number_format"), labels=ch.get("labels"),
                   legend=ch.get("legend"), name=name, highlight_series=ch.get("highlight_series"),
                   series_kind=ch.get("series_kind"), end_labels=ch.get("end_labels"),
                   estimates=ch.get("estimates"), annotations=ch.get("annotations"),
                   vmin=ch.get("min"), vmax=ch.get("max"), **shared)


def chart_panels(c: Canvas, x, y, w, h, ch: dict):
    """2-4 charts in one row: a shared header line (bold metric over its unit),
    one plot rectangle and baseline for all, and one value range when the panels
    share a unit (``shared_scale`` overrides). At most one key, drawn once."""
    b = c.brand
    panels = ch["panels"]
    if not 2 <= len(panels) <= 4:
        c.warn(f"{len(panels)} chart panels; use 2–4 in one row")
    cols = columns(c, max(1, len(panels)), x=x, w=w)
    head = 0.0
    for (px, pw), p in zip(cols, panels):
        hh = c.text_height(p.get("title", ""), "body", pw) if p.get("title") else 0
        hh += c.text_height(p["unit"], "caption", pw) if p.get("unit") else 0
        head = max(head, hh)
    for (px, pw), p in zip(cols, panels):
        yy = y
        if p.get("title"):
            th = c.text_height(p["title"], "body", pw)
            c.text(px, yy, pw, th, p["title"], size="body", color=c.ink, bold=True, name="Panel title")
            yy += th
        if p.get("unit"):
            c.text(px, yy, pw, c.text_height(p["unit"], "caption", pw), p["unit"], size="caption",
                   color="muted", name="Panel unit")
    top = y + head + (float(b["layout.gutter"]) / 2 if head else 0)
    multi = [p for p in panels if len(p.get("series", [])) > 1 and p.get("type") != "waterfall"]
    key = bool(multi) and not all(p.get("type") == "line" for p in multi)
    if key:  # one shared key instead of a legend per panel
        top = _panel_key(c, x, top, w, multi[0])
    units = {str(p.get("unit")) for p in panels}
    shared = ch.get("shared_scale", len(units) == 1)
    if shared and len({_orientation(p) for p in panels}) > 1:
        shared = False
    height = y + h - top
    specs = [dict(p, legend=False) for p in panels]
    # A shared scale needs one plot rectangle for all panels; different units need
    # only the shared baseline, so then just the top and bottom padding are merged.
    plans = [_plan(c, pw, height, p, None) for (_, pw), p in zip(cols, specs)]
    ranges = [(pl.lo, pl.hi, pl.step) for pl in plans]
    if shared:
        lo, hi, step = exhibits.axis_range(min(r[0] for r in ranges), max(r[1] for r in ranges))
        ranges = [(lo, hi, step)] * len(panels)
    pads = [[0.0] * 4 for _ in panels]
    for _ in range(2):  # lanes depend on the padding and the padding on the lanes: two passes settle
        plans = [_plan(c, pw, height, p, pad, r) for (_, pw), p, pad, r in zip(cols, specs, pads, ranges)]
        merged = [max(pl.pads[k] for pl in plans) for k in range(4)]
        pads = [merged if shared else [pl.pads[0], merged[1], pl.pads[2], merged[3]] for pl in plans]
    for i, ((px, pw), p) in enumerate(zip(cols, specs)):
        draw_chart(c, px, top, pw, height, p, name=f"Chart panel {i + 1}", value_range=ranges[i],
                   min_pads=pads[i])


def _orientation(p):
    return "h" if p.get("type") in exhibits.HORIZONTAL else "v"


def _plan(c: Canvas, w, h, p, pads, value_range=None):
    """The plot plan a panel would get on its own, for merging across panels."""
    kind = p.get("type", "column")
    fmt = p.get("number_format")
    if kind == "waterfall":
        cats, _, series = exhibits.waterfall_series(p)
        return exhibits.plan_chart(c, kind, w, h, cats, series, labels=True, number_format=fmt,
                                   value_range=value_range, min_pads=pads)
    series = p.get("series", [])
    labels, end = exhibits.label_modes(kind, len(series), p.get("labels"), p.get("end_labels"))
    texts = [t for _, _, t in exhibits.end_texts(series, labels, fmt)] if end else []
    return exhibits.plan_chart(c, kind, w, h, p.get("categories", []), series, labels=labels,
                               number_format=fmt, end_texts=texts, annotations=p.get("annotations") or [],
                               vmin=p.get("min"), vmax=p.get("max"), value_range=value_range,
                               min_pads=pads)


def _panel_key(c: Canvas, x, y, w, p) -> float:
    """Swatch + name for each series, in one row; returns the y below it."""
    colors = exhibits.series_colors(c.brand, p.get("type", "column"), len(p["series"]),
                                    p.get("series_kind"), p.get("highlight_series"))
    cap = c.size("caption")
    xx = x
    for s, color in zip(p["series"], colors):
        c.box(xx, y + cap * 0.35, cap * 0.8, cap * 0.8, fill=color, radius=0, name="Key swatch")
        tw = measure.text_width(str(s["name"]), cap) + 6
        c.text(xx + cap * 1.2, y, tw, cap * 1.5, str(s["name"]), size="caption", color=c.muted,
               wrap=False, check_fit=False, name="Key")
        xx += cap * 1.2 + tw + float(c.brand["layout.gutter"])
    return y + cap * 1.5 + float(c.brand["layout.gutter"]) / 2


@layout("process")
def process(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    steps = [s if isinstance(s, dict) else {"title": str(s)} for s in spec.get("steps", [])]
    current = spec.get("current")
    rows = spec.get("rows") or []
    x0, w0 = b.content_left, b.content_width
    if rows:  # the attribute labels take a left column; steps align over the cells
        _, label_w = grid_span(c, 0, 2)
        x0 += label_w + float(b["layout.gutter"])
        w0 -= label_w + float(b["layout.gutter"])
    if spec.get("style", "rail") == "chevron":
        if len(steps) > 6:
            c.warn(f"{len(steps)} chevrons; keep at most 6 or group the steps")
        end, cols, bands = _chevrons(c, steps, current, x0, w0, y)
    else:
        end, cols = _rail(c, steps, current, x0, w0, y)
        bands = [(x - 6, w + 12) for x, w in cols]
    if rows:
        end = _step_rows(c, rows, cols, bands, current, end + float(b["layout.gutter"]))
    check_bottom(c, end, limit)


def _rail(c: Canvas, steps, current, x0, w0, y):
    """Default style: accent rule over each step, numbered, arrows between the rules."""
    b = c.brand
    gap = float(b["layout.gutter"]) * 2
    cols = columns(c, max(1, len(steps)), x=x0, w=w0, gap=gap)
    end = y
    for i, ((x, w), step) in enumerate(zip(cols, steps)):
        active = current is None or current == i
        c.box(x, y, w, 3, fill="accent" if active else "line", radius=0)
        yy = y + 14
        number = f"{i + 1:02}" + (f"  ·  {step['period']}" if step.get("period") else "")
        c.text(x, yy, w, b["type.label"] * 1.5, number, size="label", font="mono",
               color="accent" if active else "muted")
        yy += b["type.label"] * 1.5 + 6
        h = c.text_height(step.get("title", ""), "lead", w)
        c.text(x, yy, w, h, step.get("title", ""), size="lead", color=c.ink if active else "muted")
        yy += h + 6
        if step.get("body"):
            bh = c.text_height(step["body"], "body", w)
            c.text(x, yy, w, bh, step["body"], size="body", color=c.body_color if active else "muted")
            yy += bh
        if i < len(steps) - 1:
            ax = x + w + gap * 0.25
            c.line(ax, y + 1.5, ax + gap * 0.5, y + 1.5, color="muted", width=1.0, arrow="end")
        end = max(end, yy)
    return end, cols


def _chevrons(c: Canvas, steps, current, x0, w0, y):
    """Chevron header: one native chevron per step (the first a pentagon), period above.

    Returns the bottom and the (x, w) text column under each chevron, so rows align."""
    from .frameworks import copy_text
    b = c.brand
    n = max(1, len(steps))
    h = c.size("body") * 2.6
    depth, gap = h * 0.32, 3.0
    cw = (w0 - (depth - gap)) / n
    label_h = b["type.label"] * 1.6
    has_top = current is not None or any(s.get("period") for s in steps)
    top = y + (label_h + 4 if has_top else 0)
    now = copy_text(c, "current_label")
    cols, bands, end = [], [], top + h
    for i, step in enumerate(steps):
        active = current == i
        sx = x0 + i * cw
        left = depth + 6 if i else 10.0
        shp = c.box(sx, top, cw + depth - gap, h, shape="chevron" if i else "pentagon", radius=0,
                    fill="accent" if active else "surface_alt", name=f"Chevron {i + 1}")
        shp.adjustments[0] = depth / h
        tx, tw = sx + left, cw - left - 4
        title = str(step.get("title", ""))
        if measure.text_width(title, c.size("body")) > tw:
            c.warn(f"chevron title '{title}' wraps; use one or two words")
        c.text(tx, top, tw, h, title, size="body", bold=True, anchor="middle", check_fit=False,
               color="on_accent" if active else (c.ink if current is None else c.muted),
               name=f"Chevron {i + 1} title")
        mark = " · ".join(str(v) for v in (step.get("period"), now if active else None) if v)
        if mark:
            c.text(tx, y, tw, label_h, mark, size="label", font="mono",
                   color="accent" if active else c.muted, name=f"Period {i + 1}")
        col_w = cw + depth - 12 - left
        yy = top + h
        if step.get("body"):
            bh = c.text_height(step["body"], "body", col_w)
            c.text(tx, yy + 10, col_w, bh, step["body"], size="body",
                   color=c.body_color if current is None or active else c.muted)
            yy += 10 + bh
        cols.append((tx, col_w))
        bands.append((sx, cw - gap))
        end = max(end, yy)
    return end, cols, bands


def _step_rows(c: Canvas, rows, cols, bands, current, y):
    """Phase x attribute grid: a label column, then one cell under each step. Hairlines only.

    ``bands`` are the (x, w) extents of each step's shape; the current one is tinted."""
    b = c.brand
    lx, lw = grid_span(c, 0, 2)
    pad = 8.0
    heights = []
    for row in rows:
        cells = list(row.get("cells", []))
        need = c.text_height(str(row.get("label", "")), "body", lw)
        for (x, w), cell in zip(cols, cells):
            need = max(need, c.text_height(str(cell), "body", w))
        heights.append(need + 2 * pad)
    if isinstance(current, int) and 0 <= current < len(bands):  # tint the current column first
        x, w = bands[current]
        c.box(x, y, w, sum(heights), fill=b.tint("accent", 0.93), radius=0, name="Current column")
    for row, h in zip(rows, heights):
        c.line(lx, y, b.content_right, y, color="line", width=0.5)
        c.text(lx, y + pad, lw, h - 2 * pad, str(row.get("label", "")), size="body", bold=True,
               color=c.ink, check_fit=False, name="Row label")
        for (x, w), cell in zip(cols, row.get("cells", [])):
            c.text(x, y + pad, w, h - 2 * pad, str(cell), size="body", color=c.body_color,
                   bold_color=c.ink, check_fit=False)
        y += h
    c.line(lx, y, b.content_right, y, color="line", width=0.5)
    return y


@layout("timeline")
def timeline(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    events = spec.get("events", [])
    current = spec.get("current")
    cols = columns(c, max(1, len(events)))
    date_h = b["type.label"] * 1.6
    axis = y + date_h + 10
    c.line(b.content_left, axis, b.content_right, axis, color="line", width=1.0)
    end = axis
    for i, ((x, w), ev) in enumerate(zip(cols, events)):
        active = current is None or current == i
        c.text(x, y, w, date_h, str(ev.get("date", "")), size="label", font="mono",
               color="accent" if active else "muted")
        c.box(x, axis - 4, 8, 8, shape="oval", fill="accent" if active else "chrome")
        yy = axis + 16
        h = c.text_height(ev.get("title", ""), "lead", w)
        c.text(x, yy, w, h, ev.get("title", ""), size="lead", color=c.ink)
        yy += h + 4
        if ev.get("body"):
            bh = c.text_height(ev["body"], "body", w)
            c.text(x, yy, w, bh, ev["body"], size="body", color=c.body_color)
            yy += bh
        end = max(end, yy)
    check_bottom(c, end, limit)


@layout("diagram")
def diagram(c: Canvas, spec, ctx):
    """Native diagram on a grid: nodes in cells, labeled groups, glued connectors."""
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    caption = spec.get("caption")
    if caption:
        ch = c.text_height(caption, "body", b.content_width)
        c.text(b.content_left, limit - ch, b.content_width, ch, caption, size="body", color=c.muted)
        limit -= ch + b["layout.gutter"]
    x0, w0 = commentary_column(c, spec, y, limit)
    grid = spec.get("grid", {})
    nodes = spec.get("nodes", [])
    n_cols = int(grid.get("cols") or max((n.get("col", 0) + n.get("colspan", 1) for n in nodes), default=1))
    n_rows = int(grid.get("rows") or max((n.get("row", 0) + n.get("rowspan", 1) for n in nodes), default=1))
    node_h_max = float(grid.get("node_height", 58))
    # rows never grow beyond what a node and its labels need; spare space stays below
    cell_w = w0 / n_cols
    cell_h = min((limit - y) / n_rows, node_h_max + 84)
    # horizontal gap between nodes = 2 * pad_x; wide enough for an edge label
    pad_x = max(float(b["layout.gutter"]) * 0.9, cell_w * float(grid.get("gap", 0.18)))

    def cell_rect(col, row, colspan=1, rowspan=1):
        return x0 + col * cell_w, y + row * cell_h, colspan * cell_w, rowspan * cell_h

    by_id = {n["id"]: n for n in nodes}
    for g in spec.get("groups", []):
        if g.get("nodes"):  # boundary around member nodes
            members = [by_id[m] for m in g["nodes"] if m in by_id]
            c0 = min(m.get("col", 0) for m in members)
            r0 = min(m.get("row", 0) for m in members)
            c1 = max(m.get("col", 0) + m.get("colspan", 1) for m in members)
            r1 = max(m.get("row", 0) + m.get("rowspan", 1) for m in members)
            g = {**g, "col": c0, "row": r0, "colspan": c1 - c0, "rowspan": r1 - r0}
        gx, gy, gw, gh = cell_rect(g["col"], g["row"], g.get("colspan", 1), g.get("rowspan", 1))
        inset = 4.0
        c.box(gx + inset, gy + inset, gw - 2 * inset, gh - 2 * inset, line="chrome",
              dash=g.get("style") == "dashed", line_width=0.75,
              fill="surface_alt" if g.get("fill") else None, name=f"Group {g.get('label', '')}")
        c.text(gx + inset + 8, gy + inset + 5, gw - 2 * inset - 16, b["type.label"] * 1.5,
               str(g.get("label", "")), size="label", font="mono", color="muted")

    shapes = {}
    for n in nodes:
        cx, cy, cw, chh = cell_rect(n.get("col", 0), n.get("row", 0), n.get("colspan", 1), n.get("rowspan", 1))
        nh = min(node_h_max, chh - 2 * max(22.0, pad_x)) if n.get("rowspan", 1) == 1 else chh - 2 * 22
        nw = cw - 2 * pad_x
        nx, ny = cx + pad_x, cy + (chh - nh) / 2
        kind = n.get("kind", "default")
        style = {
            "default": dict(fill="surface", line="muted", line_width=0.75),
            "accent": dict(fill=c.brand.tint("accent", 0.9), line="accent", line_width=1.25),
            "muted": dict(fill="surface_alt", line=None),
            "external": dict(fill="surface", line="muted", dash=True),
            "store": dict(fill="surface", line="muted", shape="can", radius=0),
            "decision": dict(fill="surface", line="muted", shape="diamond", radius=0),
        }.get(kind if kind != "default" else n.get("shape", "default"), {})
        label = str(n.get("label", n.get("id", "")))
        sub = n.get("sub")
        shp = c.box(nx, ny, nw, nh, name=f"Node {n['id']}", **style)
        tf = shp.text_frame
        tf.clear()
        icon_path = ctx.icon(n["icon"], c) if n.get("icon") else None
        text_x = nx + (30 if icon_path else 0)
        text = label + (f"\n{sub}" if sub else "")
        size = "body"
        need = c.text_height(text, size, nw - 16 - (30 if icon_path else 0))
        if need > nh:
            c.warn(f"node '{n['id']}' label does not fit ({need:.0f}pt > {nh:.0f}pt); shorten it or widen the grid")
        c.text(text_x + 8, ny, nw - 16 - (30 if icon_path else 0), nh,
               [label] + ([str(sub)] if sub else []), size=size, color=c.ink,
               align="left" if icon_path else "center", anchor="middle", check_fit=False,
               name=f"Label {n['id']}")
        if icon_path:
            c.image(icon_path, nx + 8, ny + (nh - 24) / 2, 24, 24)
        shapes[n["id"]] = (shp, n)

    for e in spec.get("edges", []):
        if e["from"] not in shapes or e["to"] not in shapes:
            c.warn(f"edge {e['from']} -> {e['to']} references a missing node", "ERROR")
            continue
        (a, na), (bb, nb) = shapes[e["from"]], shapes[e["to"]]
        dc = nb.get("col", 0) - na.get("col", 0)
        dr = nb.get("row", 0) - na.get("row", 0)
        if abs(dc) >= abs(dr) and dc != 0:
            sides = ("right", "left") if dc > 0 else ("left", "right")
        else:
            sides = ("bottom", "top") if dr > 0 else ("top", "bottom")
        sides = (e.get("from_side", sides[0]), e.get("to_side", sides[1]))
        kind = e.get("kind", "flow")
        color = "accent" if e.get("highlight") else "muted"
        lw = 1.5 if e.get("highlight") else 1.0
        if sides[0] == sides[1]:  # U-route around the nodes, e.g. a return path underneath
            out = 26.0 if sides[0] in ("bottom", "right") else -26.0
            def port(shape, side):
                L, T, W, H = (v / 12700 for v in (shape.left, shape.top, shape.width, shape.height))
                return {"top": (L + W / 2, T), "bottom": (L + W / 2, T + H),
                        "left": (L, T + H / 2), "right": (L + W, T + H / 2)}[side]
            (ax, ay), (bx2, by2) = port(a, sides[0]), port(bb, sides[1])
            if sides[0] in ("top", "bottom"):
                edge_y = (max(ay, by2) if out > 0 else min(ay, by2)) + out
                pts = [(ax, ay), (ax, edge_y), (bx2, edge_y), (bx2, by2)]
                mid = ((ax + bx2) / 2, edge_y)
            else:
                edge_x = (max(ax, bx2) if out > 0 else min(ax, bx2)) + out
                pts = [(ax, ay), (edge_x, ay), (edge_x, by2), (bx2, by2)]
                mid = (edge_x, (ay + by2) / 2)
            c.path(pts, color=color, width=lw, dash=kind == "return",
                   arrow=None if kind == "decomposition" else "end", name=f"Edge {e['from']}-{e['to']}")
            if e.get("label"):
                lw_ = min(cell_w * 1.5, measure.text_width(e["label"], c.size("caption")) + 10)
                lh = c.size("caption") * 1.5
                c.text(mid[0] - lw_ / 2, mid[1] + (2 if out > 0 else -lh - 2), lw_, lh, str(e["label"]),
                       size="caption", color="muted", align="center", anchor="middle", inset=1,
                       check_fit=False, name="Edge label", fill="dark" if c.dark else "surface")
            continue
        conn = c.connect(a, bb, a_side=sides[0], b_side=sides[1], elbow=(dc != 0 and dr != 0) or e.get("elbow", False),
                         color=color, width=lw, dash=kind == "return",
                         arrow=None if kind == "decomposition" else "end",
                         name=f"Edge {e['from']}-{e['to']}")
        if e.get("label"):
            bx = (conn.begin_x + conn.end_x) / 2 / 12700
            by = (conn.begin_y + conn.end_y) / 2 / 12700
            lw = min(cell_w * 0.9, measure.text_width(e["label"], c.size("caption")) + 10)
            lh = c.size("caption") * 1.5
            c.text(bx - lw / 2, by - lh - 2 if dr == 0 else by - lh / 2, lw, lh, str(e["label"]),
                   size="caption", color="muted", align="center", anchor="middle", inset=1,
                   check_fit=False, name="Edge label", fill="dark" if c.dark else "surface")


@layout("image")
def image(c: Canvas, spec, ctx):
    b = c.brand
    path = ctx.asset(spec.get("image", ""))
    if spec.get("full_bleed"):
        c.image(path, 0, 0, b.width, b.height, fit="cover", alt=spec.get("alt", ""))
        return
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    caption = spec.get("caption")
    if caption:
        ch = c.text_height(caption, "body", b.content_width)
        c.text(b.content_left, limit - ch, b.content_width, ch, caption, size="body", color=c.muted)
        limit -= ch + 8
    if not spec.get("alt"):
        c.warn("image without alt text")
    x, w = commentary_column(c, spec, y, limit)
    c.image(path, x, y, w, limit - y, fit=spec.get("fit", "contain"),
            alt=spec.get("alt", ""), name="Image")


@layout("code")
def code(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    text = str(spec.get("code", "")).rstrip("\n")
    lines = text.split("\n")
    size = c.size("body")
    h = min(limit - y, len(lines) * size * 1.2 * 1.15 + 28)
    c.box(b.content_left, y, b.content_width, h, fill="surface_alt", name="Code panel")
    c.text(b.content_left + 14, y + 14, b.content_width - 28, h - 28, lines, size="body",
           font="mono", color=c.ink, spacing=1.15, wrap=False, check_fit=False, name="Code")
    caption = spec.get("caption")
    if caption:
        ch = c.text_height(caption, "body", b.content_width)
        c.text(b.content_left, y + h + 8, b.content_width, ch, caption, size="body", color=c.muted,
               name="Caption")
        check_bottom(c, y + h + 8 + ch, limit)
    if len(lines) * size * 1.2 * 1.15 + 28 > limit - y:
        c.warn(f"code block has {len(lines)} lines and overflows; show the essential lines only", "ERROR")


@layout("custom")
def custom(c: Canvas, spec, ctx):
    """Delegates to ``render(canvas, spec, ctx, body_top)`` in a Python file."""
    path = ctx.asset(spec["python"])
    module_spec = importlib.util.spec_from_file_location(f"custom_{Path(path).stem}", path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    top = headline(c, spec, ctx) if spec.get("title") else float(c.brand["layout.body_top"])
    module.render(c, spec, ctx, top)
