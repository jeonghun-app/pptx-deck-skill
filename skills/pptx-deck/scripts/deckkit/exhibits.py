"""Exhibit helpers: structured footers, series colors, fixed plot geometry,
direct labels and annotations for native charts.

``Canvas.chart`` and the ``chart`` layout use these. The plot rectangle of a
chart is normally chosen by the application that renders it, so nothing can be
drawn at a data position. When a chart needs that (annotations, line end
labels, waterfall labels, panels on a shared baseline), the plot area is
written as a manual inner layout and the value axis is pinned, which makes
``Plot.pos`` exact in PowerPoint and LibreOffice alike.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from . import measure
from .brand import contrast

HORIZONTAL = ("bar", "stacked_bar")
ANNOTATED = ("column", "bar", "line", "stacked_column", "stacked_bar")
POINT_KINDS = ("callout", "delta")
MINUS = "−"

# Footer and annotation wording per deck language. ``copy.exhibit_labels`` in
# the brand overrides any of these keys.
WORDS = {
    "en": {"question": "Q: {}", "base": "Base: {}", "n": "n = {}", "as_of": "As of {}",
           "rounding": "Figures may not add up to the totals shown because of rounding.",
           "estimate_from": "Values from {} on are estimates.", "estimate_suffix": "{} = estimate.",
           "estimate_series": "{} (estimate)", "pp": "pp", "x": "x"},
    "ko": {"question": "질문: {}", "base": "대상: {}", "n": "n = {}", "as_of": "{} 기준",
           "rounding": "반올림으로 합계가 맞지 않을 수 있습니다.",
           "estimate_from": "{}부터는 추정치입니다.", "estimate_suffix": "{}: 추정치.",
           "estimate_series": "{} (추정)", "pp": "%p", "x": "배"},
}


def words(brand, language: str = "en") -> dict:
    base = dict(WORDS.get(language, WORDS["en"]))
    base.update({k: v for k, v in (brand.get("copy.exhibit_labels") or {}).items() if v})
    return base


# -- footer ------------------------------------------------------------------

def source_text(brand, language: str, src) -> str:
    """The source line with its label ("Source: ..."), unless it already has one."""
    label = brand.get("copy.source_label") or ("출처" if language == "ko" else "Source")
    text = str(src)
    if text.lower().startswith((label.lower(), "source", "note", "출처", "자료", "주:")):
        return text
    return f"{label}: {text}"


def format_n(n) -> str:
    if isinstance(n, dict):  # per-segment sample sizes warn about small cells
        return ", ".join(f"{_int(v)} ({k})" for k, v in n.items())
    return _int(n)


def _int(v) -> str:
    return f"{v:,}" if isinstance(v, int) else str(v)


def footer_paragraphs(src, brand, language: str = "en", extra=()) -> list:
    """Footer block, top to bottom: notes, then question/base/n/date, then source.

    ``src`` is a string (one source line) or a dict with ``notes``, ``question``,
    ``base``, ``n``, ``as_of``, ``rounding`` and ``text``. ``extra`` holds notes the
    chart adds itself (estimates); they follow the numbered notes.
    """
    if not isinstance(src, dict):
        src = {"text": src} if src else {}
    w = words(brand, language)
    notes = [f"{i}) {n}" for i, n in enumerate(as_list(src.get("notes")), start=1)]
    notes += [str(e) for e in extra]
    if src.get("rounding"):
        notes.append(w["rounding"])
    out = []
    if notes:
        out.append("  ".join(notes))
    meta = []
    if src.get("question"):
        meta.append(w["question"].format(src["question"]))
    if src.get("base"):
        meta.append(w["base"].format(src["base"]))
    if src.get("n") is not None:
        meta.append(w["n"].format(format_n(src["n"])))
    if src.get("as_of"):
        meta.append(w["as_of"].format(src["as_of"]))
    if meta:
        out.append(" · ".join(meta))
    if src.get("text"):
        out.append(source_text(brand, language, src["text"]))
    return out


def chart_specs(spec: dict) -> list:
    """The chart spec of a slide, or each of its panels."""
    ch = spec.get("chart") or {}
    return list(ch.get("panels") or []) or ([ch] if ch else [])


def auto_notes(spec: dict, brand, language: str = "en") -> list:
    """Notes the slide's charts add to the footer: one per distinct estimate rule."""
    w = words(brand, language)
    out = []
    for ch in chart_specs(spec):
        est = ch.get("estimates")
        if not est or ch.get("type", "column") not in ANNOTATED:  # bars and lines only
            continue
        if est.get("note"):
            note = str(est["note"])
        elif est.get("suffix"):
            note = w["estimate_suffix"].format(est["suffix"])
        else:
            cats = ch.get("categories", [])
            i = category_index(cats, est.get("from"))
            note = w["estimate_from"].format(cats[i] if i is not None else est.get("from"))
        if note not in out:
            out.append(note)
    return out


# -- numbers -----------------------------------------------------------------

_CORE = re.compile(r"[#0][#0,]*(\.[#0]+)?")


def is_percent(number_format) -> bool:
    return "%" in re.sub(r'"[^"]*"', "", str(number_format or ""))


def decimals(number_format) -> int:
    m = _CORE.search(str(number_format or "").split(";")[0])
    return len(m.group(1)) - 1 if m and m.group(1) else 0


def format_number(value, number_format=None) -> str:
    """Render a value the way a chart data label with this Excel format shows it.

    Covers the formats decks use: thousands separators, fixed decimals, percent,
    quoted or literal prefixes and suffixes, and trailing-comma scaling.
    """
    if value is None:
        return ""
    v = float(value)
    fmt = str(number_format or "General")
    section = fmt.split(";")[0]
    m = _CORE.search(section)
    if fmt == "General" or not m:
        return str(int(v)) if v.is_integer() else f"{v:.2f}".rstrip("0").rstrip(".")
    integer = m.group(0).split(".")[0]
    v /= 1000 ** (len(integer) - len(integer.rstrip(",")))  # "#,##0," shows thousands
    if is_percent(section):
        v *= 100
    places = decimals(section)
    body = f"{abs(v):,.{places}f}" if "," in integer.rstrip(",") else f"{abs(v):.{places}f}"
    clean = lambda s: re.sub(r'\\(.)', r"\1", re.sub(r'"([^"]*)"', r"\1", re.sub(r"[_*].", "", s)))
    sign = MINUS if v < 0 and round(abs(v), places) else ""
    return f"{sign}{clean(section[:m.start()])}{body}{clean(section[m.end():])}"


def signed(value, number_format=None) -> str:
    text = format_number(abs(value), number_format)
    return (MINUS if value < 0 else "+") + text


def nice_step(span: float, ticks: int = 5) -> float:
    raw = span / max(1, ticks)
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag + 1e-12:
            return m * mag
    return 10 * mag


def axis_range(lo: float, hi: float):
    """Nice (min, max, major unit) that contains lo..hi."""
    if hi <= lo:
        hi = lo + (abs(lo) or 1)
    step = nice_step(hi - lo)
    snap = lambda v: round(v, 10)  # 3 * 0.2 is 0.6000000000000001 in binary floating point
    return snap(math.floor(lo / step + 1e-9) * step), snap(math.ceil(hi / step - 1e-9) * step), step


def category_index(categories, ref):
    """A category given by name, or by index when no category has that name."""
    if ref is None:
        return None
    names = [str(cat) for cat in categories]
    if str(ref) in names:
        return names.index(str(ref))
    if isinstance(ref, int) and -len(names) <= ref < len(names):
        return ref % len(names)
    return None


def estimate_start(categories, estimates):
    """Index of the first estimated category, or None."""
    return category_index(categories, (estimates or {}).get("from")) if estimates else None


def as_list(value):
    if value is None:
        return []
    return list(value) if isinstance(value, (list, tuple)) else [value]


# -- colors ------------------------------------------------------------------

def readable(brand, color: str, background: str = "surface", fallback: str = "muted") -> str:
    """The series color for a text label when it reads at 4.5:1, else ``fallback``.
    Light ramp and grey context colors are fills, not text colors."""
    if contrast(brand.hex(color), brand.hex(background)) >= 4.5:
        return brand.hex(color)
    return brand.hex(fallback)


def default_series_kind(brand, kind: str, n_series: int) -> str:
    if brand.get("colors.series_mode", "ramp") != "ramp":
        return "nominal"
    if kind.startswith("stacked") or (kind in ("column", "bar", "line") and n_series > 1):
        return "ordered"
    return "nominal"


def series_colors(brand, kind: str, n: int, series_kind=None, highlight_series=None) -> list:
    """One fill/line color per series.

    ``highlight_series`` puts the focus series in the accent and the others in a
    grey ramp; ``ordered`` series get a ramp of accent tints from dark to light;
    ``nominal`` series take ``colors.series`` in order.
    """
    focus = set(as_list(highlight_series))
    if focus:
        lo, hi = (float(v) for v in brand.get("chart.context_tints", [0.45, 0.75]))
        others = [i for i in range(n) if i not in focus]
        out = []
        for i in range(n):
            if i in focus:
                out.append(brand.hex("accent"))
            else:
                k = others.index(i)
                t = lo if len(others) == 1 else lo + (hi - lo) * k / (len(others) - 1)
                out.append(brand.tint("muted", t))
        return out
    if (series_kind or default_series_kind(brand, kind, n)) == "ordered":
        light = float(brand.get("chart.ramp_light", 0.7))
        return [brand.tint("accent", 0 if n == 1 else light * i / (n - 1)) for i in range(n)]
    return [brand.series(i) for i in range(n)]


# -- waterfall ---------------------------------------------------------------

def waterfall_categories(ch: dict) -> list:
    cats = [ch["start"]["label"]] if ch.get("start") else []
    cats += [s.get("label", "") for s in ch.get("steps", [])]
    if ch.get("total"):
        cats.append(ch["total"])
    return cats


def waterfall_rows(ch: dict):
    """Bars of a waterfall as (category, base, length, role, signed value).

    Roles: ``total`` (start and end, from zero), ``rise`` and ``fall`` (floating
    on the running total). ``end = start + sum(steps)`` by construction.
    """
    rows = []
    run = 0.0
    if ch.get("start"):
        run = float(ch["start"]["value"])
        rows.append((ch["start"]["label"], 0.0, run, "total", run))
    for step in ch.get("steps", []):
        v = float(step["value"])
        base = run if v >= 0 else run + v
        rows.append((step.get("label", ""), base, abs(v), "rise" if v >= 0 else "fall", v))
        run += v
    if ch.get("total"):
        rows.append((ch["total"], 0.0, run, "total", run))
    return rows


def waterfall_series(ch: dict):
    """Categories, bar rows and the four stacked series of a waterfall (base first)."""
    rows = waterfall_rows(ch)
    series = [{"name": "Base", "values": [r[1] for r in rows]}]
    for role, label in (("total", "Total"), ("rise", "Increase"), ("fall", "Decrease")):
        series.append({"name": label, "values": [r[2] if r[3] == role else None for r in rows]})
    return [r[0] for r in rows], rows, series


def waterfall_low(ch: dict) -> float:
    """Lowest running total; below zero a stacked bridge cannot be drawn."""
    return min([0.0] + [base for _, base, _, _, _ in waterfall_rows(ch)])


# -- direct labels -------------------------------------------------------------

def label_modes(kind: str, n_series: int, labels=None, end_labels=None):
    """(point labels, end labels). Line charts with up to 6 series get end labels
    by default; point labels are then off unless asked for."""
    end = (kind == "line" and n_series <= 6) if end_labels is None else bool(end_labels) and kind == "line"
    return ((not end) if labels is None else bool(labels)), end


def end_texts(series, labels: bool, number_format=None) -> list:
    """(series index, last value, text) for each line's end label. The value is
    left out when point labels already show it."""
    out = []
    for i, s in enumerate(series):
        last = next((v for v in reversed(s["values"]) if v is not None), None)
        if last is None:
            continue
        text = str(s["name"]) if labels else f"{s['name']}  **{format_number(last, number_format)}**"
        out.append((i, last, text))
    return out


# -- geometry ----------------------------------------------------------------

@dataclass
class Plot:
    """Inner plot rectangle on the slide (pt) and the pinned value range."""
    x: float
    y: float
    w: float
    h: float
    lo: float
    hi: float
    n: int
    horizontal: bool = False

    def pos(self, value: float) -> float:
        """Slide coordinate of a value: x for horizontal bars, else y."""
        t = (float(value) - self.lo) / ((self.hi - self.lo) or 1)
        return self.x + t * self.w if self.horizontal else self.y + self.h - t * self.h

    def slot(self, i: int):
        """(start, end) of category ``i`` along the category axis."""
        size = (self.h if self.horizontal else self.w) / max(1, self.n)
        start = (self.y if self.horizontal else self.x) + i * size
        return start, start + size

    def center(self, i: int) -> float:
        a, b = self.slot(i)
        return (a + b) / 2


@dataclass
class Plan:
    """Value range and padding of a chart's plot area, decided before drawing.

    ``pads`` are left, top, right, bottom inside the chart frame. Between the
    plot and the lanes sit the data labels (``label_room``) and, above vertical
    charts, the band labels (``band_room``).
    """
    lo: float
    hi: float
    step: float
    pads: list
    label_room: float = 0.0
    band_room: float = 0.0
    lanes: list = field(default_factory=list)
    lane_size: float = 0.0

    def plot(self, x, y, w, h, n: int, horizontal: bool) -> Plot:
        left, top, right, bottom = self.pads
        return Plot(x + left, y + top, w - left - right, h - top - bottom, self.lo, self.hi, n, horizontal)


def stack_totals(series, n: int) -> list:
    return [sum(float(s["values"][i] or 0) for s in series if i < len(s["values"])) for i in range(n)]


def point_value(kind: str, series, si: int, ci: int) -> float:
    if kind.startswith("stacked"):
        return stack_totals(series, ci + 1)[ci]
    v = series[si]["values"][ci]
    return float(v) if v is not None else 0.0


def ref_value(a: dict, series):
    """A reference line's value: a number, or ``mean`` of one series' data."""
    value = a.get("value")
    if isinstance(value, (int, float)):
        return float(value)
    si = int(a.get("series", 0))
    if str(value).lower() in ("mean", "average") and 0 <= si < len(series):
        values = [float(v) for v in series[si]["values"] if v is not None]
        return sum(values) / len(values) if values else None
    return None


def ref_label(a: dict, series, number_format) -> str:
    text = str(a.get("label") or "{value}")
    return text.replace("{value}", format_number(ref_value(a, series), number_format))


def data_extent(kind: str, series, annotations=()):
    """(lo, hi) of what the plot must show: data, stack tops, reference lines.
    Bars always include zero; a line includes zero unless it goes negative."""
    n = max((len(s["values"]) for s in series), default=0)
    if kind.startswith("stacked") or kind == "waterfall":
        vals = stack_totals(series, n)
    else:
        vals = [float(v) for s in series for v in s["values"] if v is not None]
    vals += [v for v in (ref_value(a, series) for a in annotations or [] if a.get("kind") == "ref_line")
             if v is not None]
    lo, hi = (min(vals), max(vals)) if vals else (0.0, 1.0)
    return min(lo, 0.0), max(hi, 0.0)


def bar_center(plot: Plot, kind: str, ci: int, si: int, n_series: int, gap: float) -> float:
    """Center of one bar along the category axis (clustered bars sit side by side)."""
    if kind == "line" or kind.startswith("stacked") or n_series == 1:
        return plot.center(ci)
    a, b = plot.slot(ci)
    bw = (b - a) / (n_series + gap / 100)
    return a + gap / 100 * bw / 2 + (si + 0.5) * bw


def pill_size(c, text: str):
    pt = c.size("caption")
    return measure.text_width(measure.strip_markup(text), pt) + 14, pt * 1.44 + 6


def label_width(c, value, number_format) -> float:
    return measure.text_width(format_number(value, number_format), c.size("caption")) + 6


def plan_chart(c, kind: str, w: float, h: float, categories, series, *, labels: bool,
               number_format=None, legend: bool = False, end_texts=(), annotations=(),
               vmin=None, vmax=None, value_range=None, min_pads=None, gap: float = 60) -> Plan:
    """Choose the value range and the plot padding inside a ``w`` x ``h`` chart frame."""
    cap = c.size("caption")
    label_h = cap * 1.4
    annotations = annotations or []
    if value_range:
        lo, hi, step = value_range
    else:
        lo, hi = data_extent(kind, series, annotations)
        lo, hi, step = axis_range(float(vmin) if vmin is not None else lo,
                                  float(vmax) if vmax is not None else hi)
        lo = float(vmin) if vmin is not None else lo
        hi = float(vmax) if vmax is not None else hi
    count = int(round((hi - lo) / step)) if step else 1
    ticks = [lo + k * step for k in range(count + 1)]
    tick_w = max(measure.text_width(format_number(t, number_format), cap) for t in ticks) + 8
    refs = [a for a in annotations if a.get("kind") == "ref_line"]
    band_labels = any(a.get("kind") == "band" and a.get("label") for a in annotations)
    legend_h = cap * 1.8 if legend else 0.0
    plan = Plan(lo, hi, step, [0.0, 0.0, 0.0, 0.0])
    if kind in HORIZONTAL:
        plan.label_room = max((label_width(c, v, number_format) for s in series for v in s["values"]
                               if v is not None), default=0) if labels else 0.0
        left = min(max((measure.text_width(str(t), cap) for t in categories), default=0) + 10, w * 0.4)
        top = 4 + legend_h + (label_h if refs else 0)
        bottom = 4 if labels else cap * 1.2 + 8
        plan.pads = [left, top, 6 + plan.label_room, bottom]
    else:
        plan.label_room = label_h if labels else 0.0
        plan.band_room = label_h if band_labels else 0.0
        side = [measure.text_width(measure.strip_markup(t), cap) for t in end_texts]
        side += [measure.text_width(ref_label(a, series, number_format), cap) for a in refs]
        right = min(6 + (max(side) + 14 if side else 0), w * 0.35)
        left = 4 if labels else tick_w
        slot = (w - left - right) / max(1, len(categories))
        lines = max((measure.count_lines(str(t), cap, slot - 6) for t in categories), default=1)
        top = 4 + legend_h + plan.band_room + plan.label_room
        plan.pads = [left, top, right, lines * cap * 1.2 + 8]
    if min_pads:  # sides the lanes do not grow: they fix the data positions the lanes use
        for k in ((1, 3) if kind in HORIZONTAL else (0, 2)):
            plan.pads[k] = max(plan.pads[k], min_pads[k])
    points = [a for a in annotations if a.get("kind") in POINT_KINDS]
    if points and kind in ANNOTATED:
        _place_lanes(c, plan, kind, w, h, categories, series, points, number_format, gap)
    if min_pads:  # the lane side counts once: the forced pad already includes another panel's lanes
        plan.pads = [max(a, b) for a, b in zip(plan.pads, min_pads)]
    return plan


def _place_lanes(c, plan: Plan, kind, w, h, categories, series, points, number_format, gap):
    """Assign each callout and delta to a lane beside the plot so none collide.

    Vertical charts stack lanes above the plot, horizontal bars to its right.
    In its own lane an annotation needs room for its span (pill and bracket);
    its leaders run down through the lanes nearer the data and must not cross
    a pill there. Brackets that share an end may touch; that reads as intended.
    """
    horizontal = kind in HORIZONTAL
    plot = plan.plot(0, 0, w, h, len(categories), horizontal)
    units = words(c.brand, getattr(c, "language", "en"))
    placed, margin = [], 6.0
    lanes = [{"spans": [], "pills": [], "drops": []} for _ in range(len(points) + 1)]
    overlaps = lambda a, b: a[0] - margin < b[1] and b[0] < a[1] + margin
    # Callouts are pinned to their point, so they take the lanes nearest the data;
    # deltas follow, short spans first, and climb over them.
    reach = lambda a: abs((category_index(categories, a.get("to")) or 0)
                          - (category_index(categories, a.get("from")) or 0))
    for a in sorted(points, key=lambda a: (a["kind"] != "callout", reach(a))):
        si = int(a.get("series", 0))
        if a["kind"] == "callout":
            ci = category_index(categories, a.get("at"))
            if ci is None or si >= len(series):
                continue
            values = [point_value(kind, series, si, ci)]
            text = str(a.get("text", "")).replace("{value}", format_number(values[0], number_format))
            mids = [bar_center(plot, kind, ci, si, len(series), gap)]
        else:
            ci, cj = category_index(categories, a.get("from")), category_index(categories, a.get("to"))
            if ci is None or cj is None or si >= len(series):
                continue
            values = [point_value(kind, series, si, ci), point_value(kind, series, si, cj)]
            text = delta_text(values[0], values[1], a.get("fmt", "abs"), number_format, units,
                              a.get("decimals"))
            mids = [bar_center(plot, kind, k, si, len(series), gap) for k in (ci, cj)]
        pw, ph = pill_size(c, text)
        size = ph if horizontal else pw
        mid = sum(mids) / len(mids)
        pill = (mid - size / 2, mid + size / 2)
        span = (min(mids + [pill[0]]), max(mids + [pill[1]]))
        row = next((r for r in range(len(lanes) - 1)
                    if not any(overlaps(span, o) for o in lanes[r]["spans"])
                    and not any(pill[0] < d < pill[1] for d in lanes[r]["drops"])
                    and not any(p_[0] < d < p_[1] for rr in range(r) for p_ in lanes[rr]["pills"]
                                for d in mids)), len(lanes) - 1)
        if row == len(lanes) - 1:
            c.warn(f"annotation '{text}' crosses another one; drop or move one of them")
        lanes[row]["spans"].append(span)
        lanes[row]["pills"].append(pill)
        for rr in range(row):
            lanes[rr]["drops"].extend(mids)
        placed.append({"kind": a["kind"], "text": text, "values": values, "size": (pw, ph), "row": row,
                       "cats": [ci] if a["kind"] == "callout" else [ci, cj], "series": si,
                       "n_series": len(series), "gap": gap})
    if not placed:
        return
    rows = 1 + max(it["row"] for it in placed)
    if horizontal:
        plan.lane_size = max(it["size"][0] for it in placed) + 12
        plan.pads[2] += plan.lane_size * rows
    else:
        plan.lane_size = max(it["size"][1] for it in placed) + 10
        plan.pads[1] += plan.lane_size * rows
    plan.lanes = placed


def delta_text(a: float, b: float, fmt: str, number_format, units=None, places=None) -> str:
    """The difference between two plotted values, computed from the data.

    ``pp``: percentage points (values that are shares); ``pct``: relative change;
    ``x``: multiple; ``abs``: difference in the chart's own number format.
    ``units`` is the wording from ``words()`` (``pp`` and ``x``).
    """
    w = units or WORDS["en"]
    if fmt == "pp":
        d = (b - a) * (100 if is_percent(number_format) else 1)
        places = decimals(number_format) if places is None else int(places)
        return f"{MINUS if round(d, places) < 0 else '+'}{abs(d):.{places}f}{w['pp']}"
    if fmt in ("pct", "x") and not a:
        return "n/a"
    if fmt == "pct":
        d = (b / a - 1) * 100
        places = 0 if places is None else int(places)
        return f"{MINUS if round(d, places) < 0 else '+'}{abs(d):.{places}f}%"
    if fmt == "x":
        return f"{b / a:.{1 if places is None else int(places)}f}{w['x']}"
    return signed(b - a, number_format)


# -- drawing around a chart ----------------------------------------------------

def draw_bands(c, plot: Plot, plan: Plan, categories, annotations):
    """Shaded category spans, drawn before the chart so they sit behind the data."""
    cap = c.size("caption")
    for a in annotations or []:
        if a.get("kind") != "band":
            continue
        i, j = category_index(categories, a.get("from")), category_index(categories, a.get("to"))
        if i is None or j is None:
            continue
        start, end = plot.slot(min(i, j))[0], plot.slot(max(i, j))[1]
        if plot.horizontal:
            c.box(plot.x, start, plot.w, end - start, fill="surface_alt", radius=0, name="Band")
        else:
            c.box(start, plot.y, end - start, plot.h, fill="surface_alt", radius=0, name="Band")
        if not a.get("label"):
            continue
        if plot.horizontal:
            c.text(plot.x + 4, start + 2, plot.w - 8, cap * 1.5, str(a["label"]), size="caption",
                   color=c.muted, align="right", check_fit=False, name="Band label")
        else:
            top = plot.y - plan.label_room - cap * 1.5
            c.text(start, top, end - start, cap * 1.4, str(a["label"]), size="caption", color=c.muted,
                   align="center", anchor="bottom", check_fit=False, name="Band label")


def draw_ref_lines(c, plot: Plot, series, annotations, number_format) -> list:
    """Dashed reference lines. Returns the labels that go on the right edge of a
    vertical chart, as items for ``side_labels``."""
    pending = []
    cap = c.size("caption")
    for a in annotations or []:
        if a.get("kind") != "ref_line" or ref_value(a, series) is None:
            continue
        text = ref_label(a, series, number_format)
        p = plot.pos(ref_value(a, series))
        if plot.horizontal:
            c.line(p, plot.y, p, plot.y + plot.h, color=c.muted, width=1.0, dash=True, name="Reference line")
            tw = measure.text_width(text, cap) + 8
            c.text(p - tw / 2, plot.y - cap * 1.5 - 2, tw, cap * 1.5, text, size="caption",
                   color=c.muted, align="center", anchor="bottom", check_fit=False, name="Reference label")
        else:
            c.line(plot.x, p, plot.x + plot.w, p, color=c.muted, width=1.0, dash=True, name="Reference line")
            pending.append({"y": p, "text": text, "color": c.muted, "name": "Reference label"})
    return pending


def side_labels(c, plot: Plot, items: list, frame_top: float, frame_bottom: float) -> list:
    """Labels right of the plot at their data y, nudged apart so none overlap."""
    if not items:
        return []
    cap = c.size("caption")
    h = cap * 1.44
    items = sorted(items, key=lambda it: it["y"])
    ys = [it["y"] - h / 2 for it in items]
    ys[0] = max(ys[0], frame_top)
    for i in range(1, len(ys)):  # push down past the label above
        ys[i] = max(ys[i], ys[i - 1] + h)
    if ys[-1] > frame_bottom - h:  # then back up from the bottom edge
        ys[-1] = frame_bottom - h
        for i in range(len(ys) - 2, -1, -1):
            ys[i] = min(ys[i], ys[i + 1] - h)
    if ys[0] < frame_top - 0.5:
        c.warn("chart end labels do not fit beside the plot; use fewer series or panels")
    x = plot.x + plot.w + 8
    for it, yy in zip(items, ys):
        width = measure.text_width(measure.strip_markup(it["text"]), cap) + 6
        c.text(x, yy, width, h, it["text"], size="caption", color=it["color"], bold_color=it["color"],
               anchor="middle", wrap=False, check_fit=False, name=it["name"])
        it["box"] = (x, yy, width, h)
    return items


def draw_lanes(c, plot: Plot, plan: Plan, kind: str, number_format, labels: bool):
    """Callout pills and delta brackets in their lanes, with leaders to the data."""
    surface = "dark" if c.dark else "surface"
    for it in plan.lanes:
        pw, ph = it["size"]
        delta = it["kind"] == "delta"
        it["mids"] = [bar_center(plot, kind, ci, it["series"], it["n_series"], it["gap"]) for ci in it["cats"]]
        it["mid"] = sum(it["mids"]) / len(it["mids"])
        if plot.horizontal:
            left = plot.x + plot.w + plan.label_room + it["row"] * plan.lane_size + 6
            ends = [plot.pos(max(v, 0)) + (label_width(c, v, number_format) if labels else 0) + 2
                    for v in it["values"]]
            if delta:
                cx = left + (plan.lane_size - 12) / 2
                (ya, yb) = it["mids"]
                c.path([(ends[0], ya), (cx, ya), (cx, yb), (ends[1], yb)], color=c.muted, width=0.75,
                       arrow="end", name="Delta bracket")
                px, py = cx - pw / 2, it["mid"] - ph / 2
            else:
                px, py = left, it["mid"] - ph / 2
                c.line(ends[0], it["mid"], px, it["mid"], color=c.muted, width=0.75, name="Callout leader")
        else:
            row_bottom = plot.y - plan.label_room - plan.band_room - it["row"] * plan.lane_size
            py = row_bottom - plan.lane_size / 2 - ph / 2
            px = it["mid"] - pw / 2
            tops = [(plot.pos(v) if kind == "line" else plot.pos(max(v, 0))) - plan.label_room - 2
                    for v in it["values"]]
            if delta:
                (xa, xb), yy = it["mids"], py + ph / 2
                c.path([(xa, tops[0]), (xa, yy), (xb, yy), (xb, tops[1])], color=c.muted, width=0.75,
                       arrow="end", name="Delta bracket")
            else:
                c.line(it["mid"], py + ph, it["mid"], tops[0], color=c.muted, width=0.75,
                       name="Callout leader")
        c.box(px, py, pw, ph, fill=surface, line="accent", line_width=0.75, shape="round",
              radius=ph / 2, text=it["text"], text_size="caption", text_color="accent" if delta else c.ink,
              bold=delta, inset=2, name="Delta" if delta else "Callout")
