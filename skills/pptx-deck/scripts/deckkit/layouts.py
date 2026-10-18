"""Slide layouts.

Each layout receives a ``Canvas``, the slide spec (a dict from deck.yaml) and
the build context. Content layouts draw the shared chrome (eyebrow, one-line
headline, accent rule) and then place their body between ``layout.body_top``
and ``layout.body_bottom``. Layouts never invent values: every size, color and
position comes from the brand profile.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from . import measure
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


def headline(c: Canvas, spec: dict, ctx) -> float:
    """Eyebrow + one-line headline + accent rule. Returns the body start y."""
    b = c.brand
    x, w = b.content_left, b.content_width
    eyebrow = spec.get("eyebrow")
    if eyebrow:
        text = eyebrow_text(c, eyebrow)
        c.text(x, b["layout.eyebrow_y"], w, b["type.label"] * 1.4, text, size="label",
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
        lines = measure.count_lines(title, b["type.title"], w)
        if lines > 1:
            c.warn(f"headline wraps to {lines} lines; content headlines are one line — shorten it")
    if b.get("layout.rule_y") is not None and title and not spec.get("no_rule"):
        c.box(x, b["layout.rule_y"], b["layout.rule_w"], b["layout.rule_h"], fill="accent",
              radius=0, name="Rule")
    y = float(b["layout.body_top"])
    lead = spec.get("lead")
    if lead:
        h = c.text_height(lead, "lead", w)
        c.text(x, y, w, h, lead, size="lead", color=c.body_color, name="Lead")
        y += h + float(b["layout.gutter"])
    return y


def source_line(c: Canvas, spec: dict) -> float:
    """Draw the source / footnote line at the bottom of the body. Returns its top."""
    b = c.brand
    bottom = float(b["layout.body_bottom"])
    src = spec.get("source")
    if not src:
        return bottom
    h = c.size("caption") * 1.5
    top = bottom - h
    label = b.get("copy.source_label") or ("출처" if getattr(c, "language", "en") == "ko" else "Source")
    text = src if str(src).lower().startswith((label.lower(), "source", "note", "출처", "주:")) else f"{label}: {src}"
    c.text(b.content_left, top, b.content_width, h, text, size="caption", color="muted",
           anchor="bottom", name="Source")
    return top - float(b["layout.gutter"]) / 2


def check_bottom(c: Canvas, y_end: float, limit: float):
    if y_end > limit + 0.5:
        c.warn(f"content ends at {y_end:.0f}pt, below the body limit {limit:.0f}pt — split the slide "
               "or shorten the copy (do not shrink the type)", "ERROR")


def bullet_items(items):
    out = []
    for item in items or []:
        if isinstance(item, dict):
            out.append((str(item.get("text", "")), [str(s) for s in item.get("sub", [])]))
        else:
            out.append((str(item), []))
    return out


def draw_bullets(c: Canvas, x, y, w, items, size="lead", gap=None) -> float:
    gap = c.size(size) * 0.6 if gap is None else gap
    for text, subs in bullet_items(items):
        h = c.text_height(text, size, w - c.size(size) * 1.1)
        c.text(x, y, w, h, text, size=size, bullet="•", color=c.body_color, bold_color=c.ink)
        y += h
        for sub in subs:
            sh = c.text_height(sub, "body", w - c.size(size) * 2.2)
            c.text(x + c.size(size) * 1.1, y + 2, w - c.size(size) * 1.1, sh, sub, size="body",
                   bullet="–", color="muted")
            y += sh + 2
        y += gap
    return y - gap


# -- structural slides -------------------------------------------------------

@layout("cover", structural=True)
def cover(c: Canvas, spec, ctx):
    b = c.brand
    x, w = b.content_left, b.content_width * 0.82
    title = spec.get("title", "")
    if ctx.title_placeholder(c, title, subtitle=spec.get("subtitle")):
        return
    th = c.text_height(title, "hero", w, b.get("type.heading_line_spacing"))
    y = b.height * 0.42 - th / 2
    if spec.get("eyebrow"):
        c.text(x, y - b["type.label"] * 2.4, w, b["type.label"] * 1.4, eyebrow_text(c, spec["eyebrow"]),
               size="label", font="mono", color="on_dark_body" if c.dark else "accent")
    c.text(x, y, w, th, title, size="hero", font="heading", color=c.ink,
           bold=bool(b.get("type.heading_bold")), spacing=b.get("type.heading_line_spacing"),
           name="Title")
    y += th + b["layout.gutter"]
    if spec.get("subtitle"):
        sh = c.text_height(spec["subtitle"], "lead", w)
        c.text(x, y, w, sh, spec["subtitle"], size="lead", color=c.body_color, name="Subtitle")
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
    th = c.text_height(title, "section", w, b.get("type.heading_line_spacing"))
    y = b.height * 0.45 - th / 2
    if spec.get("number") is not None:
        c.text(x, y - b["type.section"] * 1.7, w, b["type.section"] * 1.5, f"{spec['number']:0>2}"
               if str(spec["number"]).isdigit() else str(spec["number"]), size="section",
               font="mono", color="accent", name="Number")
    c.text(x, y, w, th, title, size="section", font="heading", color=c.ink,
           bold=bool(b.get("type.heading_bold")), spacing=b.get("type.heading_line_spacing"),
           name="Title")
    if spec.get("subtitle"):
        sy = y + th + b["layout.gutter"]
        c.text(x, sy, w, c.text_height(spec["subtitle"], "lead", w), spec["subtitle"],
               size="lead", color=c.body_color)


@layout("closing", structural=True)
def closing(c: Canvas, spec, ctx):
    b = c.brand
    x, w = b.content_left, b.content_width
    title = spec.get("title") or b.get("copy.closing_title", "Thank you")
    if ctx.title_placeholder(c, title, subtitle=spec.get("subtitle")):
        return
    th = c.text_height(title, "hero", w)
    y = b.height * 0.42 - th / 2
    c.text(x, y, w, th, title, size="hero", font="heading", color=c.ink,
           bold=bool(b.get("type.heading_bold")), name="Title")
    y += th + b["layout.gutter"]
    for key, size in (("subtitle", "lead"), ("contact", "body")):
        if spec.get(key):
            h = c.text_height(spec[key], size, w)
            c.text(x, y, w, h, spec[key], size=size, color=c.body_color if key == "subtitle" else c.muted)
            y += h + b["layout.gutter"] / 2
    ctx.cover_logo(c)


@layout("statement", structural=True)
def statement(c: Canvas, spec, ctx):
    b = c.brand
    x, w = b.content_left, b.content_width * 0.86
    text = spec.get("text") or spec.get("title", "")
    th = c.text_height(text, "statement", w, b.get("type.heading_line_spacing"))
    support = spec.get("support")
    sh = c.text_height(support, "lead", w) if support else 0
    y = (b.height - th - sh - b["layout.gutter"]) / 2
    if spec.get("eyebrow"):
        c.text(x, y - b["type.label"] * 2.6, w, b["type.label"] * 1.4, eyebrow_text(c, spec["eyebrow"]),
               size="label", font="mono", color="accent")
    c.text(x, y, w, th, text, size="statement", font="heading", color=c.ink,
           bold=bool(b.get("type.heading_bold")), spacing=b.get("type.heading_line_spacing"),
           bold_color="accent", name="Statement")
    if support:
        c.text(x, y + th + b["layout.gutter"], w, sh, support, size="lead", color=c.body_color)


@layout("quote", structural=True)
def quote(c: Canvas, spec, ctx):
    b = c.brand
    x, w = b.content_left + 36, b.content_width * 0.8
    raw = str(spec.get("text", "")).strip("“”\"")
    text = f"“{raw}”"
    th = c.text_height(text, "statement", w, b.get("type.heading_line_spacing"))
    y = (b.height - th) / 2 - 20
    c.box(b.content_left, y + 4, 3, th - 8, fill="accent", radius=0)
    c.text(x, y, w, th, text, size="statement", font="heading", color=c.ink,
           spacing=b.get("type.heading_line_spacing"), name="Quote")
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
    if n > 4:
        c.warn(f"{n} cards in one row; use at most 4 or a table")
    cols = columns(c, max(1, n))
    highlight = spec.get("highlight")
    pad = 14.0
    icon = 22.0
    heights = []
    for (x, w), item in zip(cols, items):
        hh = pad * 2
        if item.get("icon"):
            hh += icon + 10
        if item.get("heading"):
            hh += c.text_height(item["heading"], "lead", w - 2 * pad) + 6
        if item.get("body"):
            hh += c.text_height(item["body"], "body", w - 2 * pad)
        if item.get("bullets"):
            for t, _ in bullet_items(item["bullets"]):
                hh += c.text_height(t, "body", w - 2 * pad - c.size("body") * 1.1) + c.size("body") * 0.5
        heights.append(hh)
    card_h = max(heights or [0])
    for i, ((x, w), item) in enumerate(zip(cols, items)):
        active = highlight == i
        c.box(x, y, w, card_h, fill="surface_alt" if not active else c.brand.tint("accent", 0.92),
              line="accent" if active else None, line_width=1.0, name=f"Card {i + 1}")
        cy = y + pad
        if item.get("icon"):
            path = ctx.icon(item["icon"], c)
            if path:
                c.image(path, x + pad, cy, icon, icon)
            cy += icon + 10
        if item.get("heading"):
            h = c.text_height(item["heading"], "lead", w - 2 * pad)
            c.text(x + pad, cy, w - 2 * pad, h, item["heading"], size="lead", color=c.ink)
            cy += h + 6
        if item.get("body"):
            h = c.text_height(item["body"], "body", w - 2 * pad)
            c.text(x + pad, cy, w - 2 * pad, h, item["body"], size="body", color=c.body_color,
                   bold_color=c.ink)
            cy += h
        if item.get("bullets"):
            draw_bullets(c, x + pad, cy, w - 2 * pad, item["bullets"], size="body")
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


@layout("table")
def table(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    rows = spec.get("rows", [])
    cols = spec.get("columns", [])
    if len(rows) > 7 or len(cols) > 7:
        c.warn(f"table is {len(rows)}x{len(cols)}; keep within 7 rows and 7 columns or split it")
    y += 4 if spec.get("highlight_col") is not None else 0
    _, h = c.table(b.content_left, y, b.content_width, cols, rows, widths=spec.get("widths"),
                   numeric_cols=tuple(spec.get("numeric_cols", ())),
                   highlight_col=spec.get("highlight_col"), total_row=bool(spec.get("total_row")),
                   size="body", name="Table")
    check_bottom(c, y + h, limit)


@layout("chart")
def chart(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    ch = spec.get("chart", {})
    takeaway = spec.get("takeaway")
    x, w = b.content_left, b.content_width
    if takeaway:  # chart on the left two thirds, the reading on the right
        cols = columns(c, 3)
        x, w = cols[0][0], cols[1][0] + cols[1][1] - cols[0][0]
        tx, tw = cols[2]
        th = c.text_height(takeaway, "lead", tw)
        c.box(tx, y, 2, th, fill="accent", radius=0)
        c.text(tx + 12, y, tw - 12, th, takeaway, size="lead", color=c.ink, bold_color="accent")
    if ch.get("unit"):
        c.text(x, y, w, b["type.caption"] * 1.5, ch["unit"], size="caption", color="muted")
        y += b["type.caption"] * 1.8
    c.chart(x, y, w, limit - y, ch.get("type", "column"), ch.get("categories", []),
            ch.get("series", []), highlight=ch.get("highlight"),
            number_format=ch.get("number_format"), labels=ch.get("labels", True),
            legend=ch.get("legend"), name="Chart")


@layout("process")
def process(c: Canvas, spec, ctx):
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    steps = spec.get("steps", [])
    current = spec.get("current")
    gap = float(b["layout.gutter"]) * 2
    cols = columns(c, max(1, len(steps)), gap=gap)
    end = y
    for i, ((x, w), step) in enumerate(zip(cols, steps)):
        step = step if isinstance(step, dict) else {"title": str(step)}
        active = current is None or current == i
        c.box(x, y, w, 3, fill="accent" if active else "line", radius=0)
        yy = y + 14
        c.text(x, yy, w, b["type.label"] * 1.5, f"{i + 1:02}", size="label", font="mono",
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
    check_bottom(c, end, limit)


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
    grid = spec.get("grid", {})
    nodes = spec.get("nodes", [])
    n_cols = int(grid.get("cols") or max((n.get("col", 0) + n.get("colspan", 1) for n in nodes), default=1))
    n_rows = int(grid.get("rows") or max((n.get("row", 0) + n.get("rowspan", 1) for n in nodes), default=1))
    x0, w0 = b.content_left, b.content_width
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
    c.image(path, b.content_left, y, b.content_width, limit - y, fit=spec.get("fit", "contain"),
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
