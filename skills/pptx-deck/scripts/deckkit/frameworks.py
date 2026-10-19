"""Framework layouts and the symbol cells used by assessment tables.

``matrix`` places options on two declared criteria, ``shift`` pairs a current
and a target state per dimension. The symbol helpers (Harvey balls, check
marks, status dots, tiers) are native shapes so they stay editable and render
the same in PowerPoint and LibreOffice; ``Canvas.table`` and the ``table``
layout call them for ``{s: ...}`` cells.
"""
from __future__ import annotations

from lxml import etree
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn
from pptx.util import Pt

from . import measure
from .canvas import Canvas
from .layouts import check_bottom, draw_bullets, grid_span, headline, layout, source_line

# -- copy defaults -------------------------------------------------------------
# Brand `copy.*` tokens override these; the language comes from `meta.language`.
COPY = {
    "en": {
        "placement_tag": "Qualitative placement",
        "current_label": "Now",
        "symbols": {
            "harvey": {0: "None", 1: "Low", 2: "Partial", 3: "High", 4: "Full", "na": "Not assessed"},
            "check": {"yes": "Met", "partial": "Partly met", "no": "Not met", "na": "Not assessed"},
            "rag": {"g": "On track", "a": "At risk", "r": "Off track", "na": "Not assessed"},
            "tier": {1: "Tier 1 (strongest)", 2: "Tier 2", 3: "Tier 3", "na": "Not assessed"},
        },
    },
    "ko": {
        "placement_tag": "정성적 배치",
        "current_label": "현재",
        "symbols": {
            "harvey": {0: "없음", 1: "낮음", 2: "부분", 3: "높음", 4: "완전", "na": "미평가"},
            "check": {"yes": "충족", "partial": "부분 충족", "no": "미충족", "na": "미평가"},
            "rag": {"g": "정상", "a": "주의", "r": "위험", "na": "미평가"},
            "tier": {1: "1등급(최상)", 2: "2등급", 3: "3등급", "na": "미평가"},
        },
    },
}

# Accepted values per family, in legend order. YAML reads bare yes/no as booleans.
SYMBOLS = {
    "harvey": [0, 1, 2, 3, 4],
    "check": ["yes", "partial", "no"],
    "rag": ["g", "a", "r"],
    "tier": [1, 2, 3],
}
_ALIASES = {
    "check": {True: "yes", False: "no", "y": "yes", "n": "no"},
    "rag": {"green": "g", "amber": "a", "red": "r"},
}


def language(c) -> str:
    return "ko" if str(getattr(c, "language", "en")).lower().startswith("ko") else "en"


def copy_text(c: Canvas, key: str) -> str:
    """Brand `copy.<key>` when set, else the built-in text for the deck language."""
    return c.brand.get(f"copy.{key}") or COPY[language(c)][key]


def is_symbol_cell(cell) -> bool:
    return isinstance(cell, dict) and "s" in cell


def normalize_symbol(family: str, raw):
    """Canonical value for ``raw`` in ``family`` ('na' for not assessed), or None if invalid."""
    if family not in SYMBOLS:
        return None
    if isinstance(raw, str):
        raw = raw.strip().lower()
        if raw in ("na", "n/a", "-"):
            return "na"
        if raw.isdigit():
            raw = int(raw)
    raw = _ALIASES.get(family, {}).get(raw, raw)
    if isinstance(raw, bool):  # True == 1 would otherwise pass as a number
        return None
    return raw if raw in SYMBOLS[family] else None


def symbol_labels(c: Canvas, family: str, override=None) -> dict:
    """Legend words for a family: built-in < brand `copy.symbol_labels` < the slide's ``legend``."""
    labels = dict(COPY[language(c)]["symbols"][family])
    for extra in ((c.brand.get("copy.symbol_labels") or {}).get(family), override):
        for key, text in (extra or {}).items():
            value = normalize_symbol(family, key)
            if value is not None:
                labels[value] = str(text)
    return labels


# -- symbol glyphs -------------------------------------------------------------

def _shape(c: Canvas, kind, x, y, w, h, *, fill=None, line=None, line_width=0.75, name=None):
    shp = c._plain(c.slide.shapes.add_shape(kind, Pt(x), Pt(y), Pt(w), Pt(h)))
    if name:
        shp.name = name
    if fill:
        shp.fill.solid()
        shp.fill.fore_color.rgb = c.brand.rgb(fill)
    else:
        shp.fill.background()
    if line:
        shp.line.color.rgb = c.brand.rgb(line)
        shp.line.width = Pt(line_width)
    else:
        shp.line.fill.background()
    return shp


def _set_angles(shp, start: float, end: float):
    """Pie angles in degrees, clockwise from 3 o'clock (DrawingML units are 1/60000 degree)."""
    av = shp._element.spPr.find(qn("a:prstGeom")).find(qn("a:avLst"))
    for gd in list(av):
        av.remove(gd)
    for name, deg in (("adj1", start), ("adj2", end)):
        gd = etree.SubElement(av, qn("a:gd"))
        gd.set("name", name)
        gd.set("fmla", f"val {int(round(deg % 360 * 60000))}")


def draw_symbol(c: Canvas, family: str, value, cx: float, cy: float, d: float, name=None):
    """Draw one symbol centred on (cx, cy) with diameter ``d``. ``value`` is canonical."""
    x, y = cx - d / 2, cy - d / 2
    tag = name or f"Symbol {family} {value}"
    if value == "na":  # a dash, never an empty shape that reads as zero
        c.line(cx - d * 0.3, cy, cx + d * 0.3, cy, color="muted", width=1.5, name=tag)
        return
    if family == "harvey":
        if value == 4:
            _shape(c, MSO_SHAPE.OVAL, x, y, d, d, fill=c.ink, name=tag)
            return
        if value:
            wedge = _shape(c, MSO_SHAPE.PIE, x, y, d, d, fill=c.ink, name=f"{tag} fill")
            _set_angles(wedge, 270, 270 + 90 * value)  # quarters from 12 o'clock, clockwise
        _shape(c, MSO_SHAPE.OVAL, x, y, d, d, line=c.ink, line_width=1.0, name=tag)
    elif family == "check":
        if value == "yes":
            pts = [(0.14, 0.52), (0.40, 0.78), (0.88, 0.24)]
            c.path([(x + px * d, y + py * d) for px, py in pts], color="positive", width=2.0,
                   arrow=None, name=tag)
        elif value == "no":
            for a, b_ in (((0.2, 0.2), (0.8, 0.8)), ((0.8, 0.2), (0.2, 0.8))):
                c.line(x + a[0] * d, y + a[1] * d, x + b_[0] * d, y + b_[1] * d, color="negative",
                       width=2.0, name=tag)
        else:  # partial: half-filled circle, a shape distinct from both marks
            s = d * 0.86
            wedge = _shape(c, MSO_SHAPE.PIE, cx - s / 2, cy - s / 2, s, s, fill="warning",
                           name=f"{tag} fill")
            _set_angles(wedge, 90, 270)
            _shape(c, MSO_SHAPE.OVAL, cx - s / 2, cy - s / 2, s, s, line="warning", line_width=1.25,
                   name=tag)
    elif family == "rag":
        s = d * 0.78
        color = {"g": "positive", "a": "warning", "r": "negative"}[value]
        _shape(c, MSO_SHAPE.OVAL, cx - s / 2, cy - s / 2, s, s, fill=color, name=tag)
    elif family == "tier":  # full, half, empty square: the order survives greyscale and print
        s = d * 0.8
        if value == 2:
            _shape(c, MSO_SHAPE.RECTANGLE, cx - s / 2, cy, s, s / 2, fill="accent", name=f"{tag} fill")
        _shape(c, MSO_SHAPE.RECTANGLE, cx - s / 2, cy - s / 2, s, s, fill="accent" if value == 1 else None,
               line="muted" if value == 3 else "accent", line_width=1.0, name=tag)


def symbol_size(c: Canvas, size="body") -> float:
    """Symbol diameter for cells set in ``size``: a little above the text size, at least 14 pt."""
    return max(14.0, c.size(size) * 1.1)


def legend_items(family: str, used) -> list:
    values = list(SYMBOLS[family])
    return values + (["na"] if "na" in used else [])


def symbol_legend(c: Canvas, x: float, y: float, w: float, family: str, labels: dict, used) -> float:
    """One legend line (wrapping when needed) under an assessment table. Returns its height."""
    pt = c.size("caption")
    d = max(c.size("min"), pt * 1.05)
    line_h = pt * 1.5
    gap = float(c.brand["layout.gutter"])
    cx, cy = x, y
    for value in legend_items(family, used):
        text = labels.get(value, str(value))
        tw = measure.text_width(text, pt) + 4
        item_w = d + 5 + tw
        if cx > x and cx + item_w > x + w:
            cx, cy = x, cy + line_h
        draw_symbol(c, family, value, cx + d / 2, cy + line_h / 2, d, name=f"Legend {family} {value}")
        c.text(cx + d + 5, cy, tw, line_h, text, size="caption", color="muted", anchor="middle",
               wrap=False, check_fit=False, name=f"Legend text {value}")
        cx += item_w + gap
    return cy + line_h - y


# -- side column -------------------------------------------------------------

def side_column(c: Canvas, spec: dict, y: float, limit: float):
    """Optional reading column (``takeaway`` or ``commentary``). Returns (x, w) left for the exhibit.

    ``takeaway: text`` is the right column at 4 of 12 grid columns, as on charts.
    ``commentary: {text | bullets, side: right|left, width: 3|4}`` sets side and width.
    """
    b = c.brand
    note = spec.get("commentary")
    if isinstance(note, str):
        note = {"text": note}
    if not note and spec.get("takeaway"):
        note = {"text": spec["takeaway"]}
    if not note:
        return b.content_left, b.content_width
    n = int(b.get("layout.columns", 12))
    span = 3 if int(note.get("width", 4)) == 3 else 4
    gutter = float(b["layout.gutter"])
    if note.get("side") == "left":
        px, pw = grid_span(c, 0, span)
        ex, ew = grid_span(c, span, n - span)
    else:
        ex, ew = grid_span(c, 0, n - span)
        px, pw = grid_span(c, n - span, span)
    end = y
    if note.get("text"):
        th = c.text_height(note["text"], "lead", pw - 12)
        c.box(px, y, 2, th, fill="accent", radius=0, name="Commentary rule")
        c.text(px + 12, y, pw - 12, th, note["text"], size="lead", color=c.ink, bold_color="accent",
               name="Commentary")
        end = y + th
    if note.get("bullets"):
        top = end + (gutter if note.get("text") else 0)
        end = draw_bullets(c, px, top, pw, note["bullets"], size="body")
    check_bottom(c, end, limit)
    return ex, ew


# -- matrix ------------------------------------------------------------------

def _fmt(value, unit="") -> str:
    return f"{float(value):g}{unit}"


def _fraction(axis: dict, value) -> float:
    """Position of ``value`` on a measured axis as a 0-1 fraction (unclamped)."""
    lo, hi = float(axis.get("min", 0)), float(axis.get("max", 1))
    return (float(value) - lo) / ((hi - lo) or 1.0)  # lint reports max <= min


def _axis_labels(c: Canvas, axis: dict, measured: bool):
    low, high = str(axis.get("low", "")), str(axis.get("high", ""))
    if measured:  # print the scale ends so positions can be read as values
        unit = str(axis.get("unit", ""))
        lo, hi = _fmt(axis.get("min", 0), unit), _fmt(axis.get("max", 1), unit)
        low = f"{low} · {lo}" if low else lo
        high = f"{high} · {hi}" if high else hi
    return low, str(axis.get("label", "")), high


def _axis_text(c: Canvas, x, y, length, band, texts, vertical: bool, name: str):
    """Pole, title, pole along one axis. Vertical axes read bottom to top (rotated)."""
    pt = c.size("caption")
    low, title, high = texts
    widths = [measure.text_width(t, pt) * 1.1 + 8 if t else 0 for t in (low, title, high)]
    if widths[0] + widths[1] + widths[2] + 12 > length:
        c.warn(f"{name} labels do not fit along the axis; shorten the title or pole labels")
    spans = [(0, widths[0], low, "left", c.muted, False),
             ((length - widths[1]) / 2, widths[1], title, "center", c.ink, True),
             (length - widths[2], widths[2], high, "right", c.muted, False)]
    for off, w, text, align, color, bold in spans:
        if not text:
            continue
        if vertical:  # unrotated box centred where the rotated text must sit
            cx, cy = x + band / 2, y + length - off - w / 2
            box = c.text(cx - w / 2, cy - band / 2, w, band, text, size="caption", color=color,
                         bold=bold, align="center", anchor="middle", check_fit=False, wrap=False,
                         name=f"{name} {align}")
            box.rotation = 270
        else:
            c.text(x + off, y, w, band, text, size="caption", color=color, bold=bold, align=align,
                   anchor="middle", check_fit=False, wrap=False, name=f"{name} {align}")


def _bounds(spec_axis: dict, threshold, size: int, measured: bool) -> list:
    """Cell boundaries along an axis as 0-1 fractions (thresholds split measured axes)."""
    if measured and threshold is not None:
        values = threshold if isinstance(threshold, list) else [threshold]
        inner = sorted(min(1.0, max(0.0, _fraction(spec_axis, v))) for v in values)
        if len(inner) == size - 1:
            return [0.0] + inner + [1.0]
    return [i / size for i in range(size + 1)]


@layout("matrix")
def matrix(c: Canvas, spec, ctx):
    """2x2 or 3x3 matrix: named poles, named cells, items by cell or by measured x/y."""
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    mx, mw = side_column(c, spec, y, limit)
    size = 3 if int(spec.get("size", 2)) == 3 else 2
    measured = spec.get("basis", "qualitative") == "measured"
    ax, ay = spec.get("x", {}) or {}, spec.get("y", {}) or {}
    thresholds = spec.get("thresholds", {}) or {}
    quadrants = list(spec.get("quadrants", []))
    items = list(spec.get("items", []))
    gutter = float(b["layout.gutter"])
    band = c.size("caption") * 1.6
    label_pt = c.size("label")

    tag = spec.get("tag", None if measured else copy_text(c, "placement_tag"))
    top = y
    if tag:
        tw = measure.text_width(str(tag), label_pt) + 14
        th = label_pt * 1.9
        c.box(mx + mw - tw, y, tw, th, line="muted", line_width=0.75, radius=0, text=str(tag),
              text_size="label", text_color="muted", inset=2, name="Tag")
        top = y + th + gutter / 2

    gx, gy = mx + band + 6, top
    gw = mx + mw - gx
    gh = limit - gy - band - 6
    xb = _bounds(ax, thresholds.get("x"), size, measured)
    yb = _bounds(ay, thresholds.get("y"), size, measured)
    gap = 0.0 if measured else gutter / 6
    pad = 10.0
    body_pt = c.size("body")

    # cells, row-major from the top-left; row 0 is the high end of y
    rects = []
    for r in range(size):
        for col in range(size):
            x0 = gx + xb[col] * gw + (gap / 2 if col else 0)
            x1 = gx + xb[col + 1] * gw - (gap / 2 if col < size - 1 else 0)
            y0 = gy + (1 - yb[size - r]) * gh + (gap / 2 if r else 0)
            y1 = gy + (1 - yb[size - r - 1]) * gh - (gap / 2 if r < size - 1 else 0)
            rects.append((x0, y0, x1 - x0, y1 - y0))
    for i, (x0, y0, w0, h0) in enumerate(rects):
        q = quadrants[i] if i < len(quadrants) else {}
        q = q if isinstance(q, dict) else {"name": str(q)}
        active = bool(q.get("highlight"))
        c.box(x0, y0, w0, h0, fill=b.tint("accent", 0.9) if active else "surface_alt",
              line="accent" if active else None, line_width=1.0, radius=0, name=f"Cell {i + 1}")
        cy = y0 + pad
        iw = w0 - 2 * pad
        if q.get("name"):
            nh = c.text_height(q["name"], "body", iw)
            c.text(x0 + pad, cy, iw, nh, q["name"], size="body", bold=True,
                   color="accent" if active else c.ink, name=f"Cell {i + 1} name")
            cy += nh + 2
        if q.get("body"):
            bh = c.text_height(q["body"], "body", iw)
            if measure.count_lines(q["body"], body_pt, iw) > 3:
                c.warn(f"matrix cell '{q.get('name', i + 1)}' description runs past 3 lines; shorten it")
            c.text(x0 + pad, cy, iw, bh, q["body"], size="body", color=c.body_color,
                   name=f"Cell {i + 1} body")
            cy += bh + 4
        if not measured:  # qualitative: list the items, positions inside a cell carry no meaning
            for item in (it for it in items if it.get("cell") == i):
                ident = str(item.get("id", "")).strip()
                text = f"**{ident}**  {item.get('label', '')}" if ident else str(item.get("label", ""))
                ih = c.text_height(text, "body", iw - body_pt * 1.1)
                c.text(x0 + pad, cy, iw, ih, text, size="body", bullet="•", color=c.body_color,
                       bold_color="accent" if active else c.ink, name=f"Item {ident or item.get('label', '')}")
                cy += ih + 2
        if cy - 2 > y0 + h0 - pad / 2:
            c.warn(f"matrix cell '{q.get('name', i + 1)}' content does not fit; move items or shorten text",
                   "ERROR")

    # axes: arrows on the outer edges, labels in the bands outside them
    c.line(gx, gy + gh + 4, gx + gw, gy + gh + 4, color="muted", width=1.0, arrow="end", name="X axis")
    c.line(gx - 4, gy + gh, gx - 4, gy, color="muted", width=1.0, arrow="end", name="Y axis")
    _axis_text(c, gx, gy + gh + 6, gw, band, _axis_labels(c, ax, measured), False, "X axis")
    _axis_text(c, mx, gy, gh, band, _axis_labels(c, ay, measured), True, "Y axis")

    if measured:
        _thresholds(c, ax, ay, thresholds, gx, gy, gw, gh)
        _plot_items(c, items, quadrants, rects, ax, ay, gx, gy, gw, gh)


def _thresholds(c: Canvas, ax, ay, thresholds, gx, gy, gw, gh):
    """Dashed lines at the stated threshold values, each printed beside its line."""
    pt = c.size("caption")
    lh = pt * 1.5
    for key, axis in (("x", ax), ("y", ay)):
        raw = thresholds.get(key)
        if raw is None:
            continue
        unit = str(axis.get("unit", ""))
        for v in (raw if isinstance(raw, list) else [raw]):
            f = min(1.0, max(0.0, _fraction(axis, v)))
            text = _fmt(v, unit)
            tw = measure.text_width(text, pt) + 6
            if key == "x":
                px = gx + f * gw
                c.line(px, gy, px, gy + gh, color="muted", width=0.75, dash=True, name="Threshold x")
                c.text(px + 3, gy + gh - lh - 2, tw, lh, text, size="caption", color="muted",
                       check_fit=False, name="Threshold x value")
            else:
                py = gy + (1 - f) * gh
                c.line(gx, py, gx + gw, py, color="muted", width=0.75, dash=True, name="Threshold y")
                c.text(gx + gw - tw - 3, py - lh - 1, tw, lh, text, size="caption", color="muted",
                       align="right", check_fit=False, name="Threshold y value")


def _plot_items(c: Canvas, items, quadrants, rects, ax, ay, gx, gy, gw, gh):
    """Measured items: dots at their values with direct labels; labels move off each other."""
    pt = c.size("caption")
    lh = pt * 1.4
    dot = 7.0
    placed = []

    def free(r):
        return all(r[0] + r[2] <= p[0] or p[0] + p[2] <= r[0] or r[1] + r[3] <= p[1] or p[1] + p[3] <= r[1]
                   for p in placed)

    highlighted = {i for i, q in enumerate(quadrants) if isinstance(q, dict) and q.get("highlight")}
    for item in items:
        if item.get("x") is None or item.get("y") is None:
            c.warn(f"matrix item '{item.get('label', '')}' needs x and y with basis: measured", "ERROR")
            continue
        fx, fy = _fraction(ax, item["x"]), _fraction(ay, item["y"])
        if not (0 <= fx <= 1 and 0 <= fy <= 1):
            c.warn(f"matrix item '{item.get('label', '')}' lies outside the axis range; it is drawn at the edge")
        fx, fy = min(1.0, max(0.0, fx)), min(1.0, max(0.0, fy))
        px, py = gx + fx * gw, gy + (1 - fy) * gh
        inside = next((i for i, (x0, y0, w0, h0) in enumerate(rects)
                       if x0 <= px <= x0 + w0 and y0 <= py <= y0 + h0), None)
        color = "accent" if item.get("highlight") or inside in highlighted else c.ink
        c.box(px - dot / 2, py - dot / 2, dot, dot, shape="oval", fill=color, radius=0,
              name=f"Dot {item.get('id', item.get('label', ''))}")
        ident = str(item.get("id", "")).strip()
        text = f"{ident} {item.get('label', '')}".strip()
        tw = measure.text_width(text, pt) + 4
        right = px + dot / 2 + 3 + tw <= gx + gw
        lx = px + dot / 2 + 3 if right else px - dot / 2 - 3 - tw
        rect = None
        for dy in (0, -lh, lh, -2 * lh, 2 * lh):
            cand = (lx, py - lh / 2 + dy, tw, lh)
            if free(cand) and gy <= cand[1] and cand[1] + lh <= gy + gh:
                rect = cand
                break
        if rect is None:
            rect = (lx, py - lh / 2, tw, lh)
            c.warn(f"matrix label '{text}' overlaps another label; spread the items or shorten labels")
        placed.append(rect)
        c.text(rect[0], rect[1], rect[2], rect[3], text, size="caption", color=color,
               align="left" if right else "right", anchor="middle", check_fit=False,
               name=f"Dot label {ident or text}")


# -- shift (from -> to) ------------------------------------------------------

@layout("shift")
def shift(c: Canvas, spec, ctx):
    """Aligned from -> to rows: one dimension per row, current state, chevron, target state."""
    b = c.brand
    y = headline(c, spec, ctx)
    limit = source_line(c, spec)
    rows = spec.get("rows", [])
    if len(rows) > 6:
        c.warn(f"{len(rows)} shift rows; keep 3-6 and split the rest")
    x, w = b.content_left, b.content_width
    gutter = float(b["layout.gutter"])
    dim_w = w * 0.22
    sep_w = w * 0.06
    from_w = w * 0.35 - gutter
    to_w = w - dim_w - sep_w - from_w - gutter
    from_x = x + dim_w + gutter
    sep_x = from_x + from_w
    to_x = sep_x + sep_w
    pad = 10.0
    headers = spec.get("headers") or []
    if headers:
        hh = c.size("label") * 1.6
        for i, (hx, hw) in enumerate(((from_x, from_w), (to_x, to_w))):
            if i < len(headers):
                c.text(hx, y, hw, hh, eyebrow_case(c, headers[i]), size="label", font="mono",
                       color="accent" if i == 1 else c.muted, name=f"Shift header {i + 1}")
        y += hh + 4
        c.line(x, y, x + w, y, color="line", width=1.0, name="Shift header rule")
        y += 4
    for i, row in enumerate(rows):
        dim, src, dst = (str(row.get(k, "")) for k in ("dimension", "from", "to"))
        active = bool(row.get("highlight"))
        need = max(c.text_height(dim, "body", dim_w - 2 * pad), c.text_height(src, "body", from_w),
                   c.text_height(dst, "body", to_w))
        h = need + 2 * pad
        c.box(x, y + 3, dim_w, h - 6, fill=b.tint("accent", 0.9) if active else "surface_alt",
              radius=0, name=f"Dimension {i + 1}")
        c.text(x + pad, y + 3, dim_w - 2 * pad, h - 6, dim, size="body", bold=True,
               color="accent" if active else c.ink, anchor="middle", check_fit=False,
               name=f"Dimension {i + 1} label")
        c.text(from_x, y, from_w, h, src, size="body", color=c.muted, bold_color=c.body_color,
               anchor="middle", check_fit=False, name=f"From {i + 1}")
        cw, ch = min(12.0, sep_w * 0.3), min(18.0, h * 0.5)
        chev = c.box(sep_x + (sep_w - cw) / 2, y + (h - ch) / 2, cw, ch, shape="chevron",
                     fill="accent" if active else "chrome", radius=0, name=f"Shift arrow {i + 1}")
        chev.adjustments[0] = 0.5
        c.text(to_x, y, to_w, h, dst, size="body", color=c.ink, bold_color="accent" if active else c.ink,
               anchor="middle", check_fit=False, name=f"To {i + 1}")
        y += h
        c.line(x, y, x + w, y, color="line", width=0.5, name=f"Shift rule {i + 1}")
    check_bottom(c, y, limit)


def eyebrow_case(c: Canvas, text) -> str:
    return str(text).upper() if c.brand.get("type.eyebrow_uppercase") else str(text)
