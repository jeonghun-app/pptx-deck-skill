"""Drawing primitives bound to a brand.

All coordinates are points on the brand canvas. Colors are brand tokens
(``accent``, ``muted`` ...) or literal hex. Fonts are roles (``heading``,
``body``, ``mono``). Use these instead of raw python-pptx calls in custom
slides so every value stays inside the brand profile.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

from .brand import Brand
from . import measure

ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT,
         "justify": PP_ALIGN.JUSTIFY}
ANCHOR = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}
BOLD = re.compile(r"(\*\*.+?\*\*)")
SHAPES = {"rect": MSO_SHAPE.RECTANGLE, "round": MSO_SHAPE.ROUNDED_RECTANGLE,
          "oval": MSO_SHAPE.OVAL, "can": MSO_SHAPE.CAN, "chevron": MSO_SHAPE.CHEVRON,
          "pentagon": MSO_SHAPE.PENTAGON, "diamond": MSO_SHAPE.DIAMOND}
CHARTS = {
    "bar": XL_CHART_TYPE.BAR_CLUSTERED, "column": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "stacked_bar": XL_CHART_TYPE.BAR_STACKED, "stacked_column": XL_CHART_TYPE.COLUMN_STACKED,
    "line": XL_CHART_TYPE.LINE_MARKERS, "doughnut": XL_CHART_TYPE.DOUGHNUT,
    "pie": XL_CHART_TYPE.PIE,
}
# Removes PowerPoint's default table style so rules come only from the brand.
NO_STYLE_TABLE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"


@dataclass
class Warnings:
    items: list = field(default_factory=list)

    def add(self, slide: int, message: str, level: str = "WARN"):
        self.items.append({"slide": slide, "level": level, "message": message})


class Canvas:
    def __init__(self, slide, brand: Brand, number: int = 0, warnings: Warnings | None = None,
                 dark: bool = False):
        self.slide = slide
        self.brand = brand
        self.number = number
        self.warnings = warnings or Warnings()
        self.dark = dark

    # -- helpers ----------------------------------------------------------
    def warn(self, message: str, level: str = "WARN"):
        self.warnings.add(self.number, message, level)

    @property
    def ink(self) -> str:
        return "on_dark" if self.dark else "ink"

    @property
    def body_color(self) -> str:
        return "on_dark_body" if self.dark else "body"

    @property
    def muted(self) -> str:
        return "on_dark_body" if self.dark else "muted"

    def size(self, role_or_pt) -> float:
        if isinstance(role_or_pt, (int, float)):
            pt = float(role_or_pt)
        else:
            pt = float(self.brand[f"type.{role_or_pt}"])
        minimum = float(self.brand.get("type.min", 0))
        if pt < minimum:
            self.warn(f"text {pt}pt is below type.min {minimum}pt; raised to the minimum")
            pt = minimum
        return pt

    def _font(self, run, role: str, size: float, color: str, bold: bool, italic: bool = False):
        fonts = self.brand.get(f"fonts.{role}") or self.brand["fonts.body"]
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = self.brand.rgb(color)
        rpr = run._r.get_or_add_rPr()
        for tag, face in (("a:latin", fonts.get("latin")), ("a:ea", fonts.get("east_asian")),
                          ("a:cs", fonts.get("latin"))):
            if not face:
                continue
            el = rpr.find(qn(tag))
            if el is None:
                el = etree.SubElement(rpr, qn(tag))
            el.set("typeface", face)
        # schema order inside rPr: ln, fill, effect, ..., latin, ea, cs
        for tag in ("a:latin", "a:ea", "a:cs"):
            el = rpr.find(qn(tag))
            if el is not None:
                rpr.remove(el)
                rpr.append(el)

    @staticmethod
    def _plain(shape):
        """Drop the theme style reference so no inherited shadow or effect applies."""
        style = shape._element.find(qn("p:style"))
        if style is not None:
            shape._element.remove(style)
        return shape

    @staticmethod
    def _no_inset(tf, inset: float | tuple = 0):
        l, t, r, b = inset if isinstance(inset, tuple) else (inset,) * 4
        tf.margin_left, tf.margin_top, tf.margin_right, tf.margin_bottom = (Pt(l), Pt(t), Pt(r), Pt(b))

    # -- text ---------------------------------------------------------------
    def text(self, x, y, w, h, content, *, size="body", color=None, font="body", bold=False,
             italic=False, align="left", anchor="top", spacing=None, inset=0, wrap=True,
             bold_color=None, bullet=None, paragraph_gap=0.0, name=None, check_fit=True,
             fill=None):
        """Add a text box.

        ``content`` is a string (``\\n`` separates paragraphs, ``**x**`` is bold)
        or a list of strings (one paragraph each).
        ``bullet`` is a character such as "•" or "–" to prefix every paragraph
        with a hanging indent.
        """
        pt = self.size(size)
        color = color or self.body_color
        spacing = spacing or float(self.brand.get("type.line_spacing", 1.2))
        paras = content if isinstance(content, list) else str(content).split("\n")
        box = self.slide.shapes.add_textbox(Pt(x), Pt(y), Pt(w), Pt(h))
        if name:
            box.name = name
        if fill:  # e.g. masks the line behind an edge label
            box.fill.solid()
            box.fill.fore_color.rgb = self.brand.rgb(fill)
        tf = box.text_frame
        tf.word_wrap = wrap
        tf.auto_size = MSO_AUTO_SIZE.NONE  # boxes keep their planned size; QA catches overflow
        self._no_inset(tf, inset)
        tf.vertical_anchor = ANCHOR[anchor]
        for i, para in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = ALIGN[align]
            p.line_spacing = spacing
            if paragraph_gap and i > 0:
                p.space_before = Pt(paragraph_gap)
            if bullet:
                self._bullet(p, bullet, pt)
            for piece in BOLD.split(str(para)):
                if not piece:
                    continue
                strong = piece.startswith("**") and piece.endswith("**")
                run = p.add_run()
                run.text = piece[2:-2] if strong else piece
                self._font(run, font, pt, (bold_color or color) if strong else color,
                           bold or strong, italic)
        if check_fit:
            inner_w = w - (inset[0] + inset[2] if isinstance(inset, tuple) else 2 * inset)
            need = sum(measure.text_height(p, pt, inner_w - (pt if bullet else 0), spacing)
                       for p in paras) + paragraph_gap * (len(paras) - 1)
            if need > h + 0.5:
                label = measure.strip_markup(paras[0])[:40]
                self.warn(f"text may overflow its box ({need:.0f}pt needed, {h:.0f}pt available): '{label}'")
        return box

    def _bullet(self, p, char: str, pt: float):
        ppr = p._p.get_or_add_pPr()
        ppr.set("marL", str(int(Pt(pt * 1.1))))
        ppr.set("indent", str(-int(Pt(pt * 1.1))))
        for tag in ("a:buNone", "a:buChar", "a:buClr"):
            for el in ppr.findall(qn(tag)):
                ppr.remove(el)
        clr = etree.SubElement(ppr, qn("a:buClr"))
        etree.SubElement(clr, qn("a:srgbClr")).set("val", self.brand.hex("accent"))
        etree.SubElement(ppr, qn("a:buChar")).set("char", char)

    def text_height(self, content, size, width, spacing=None) -> float:
        spacing = spacing or float(self.brand.get("type.line_spacing", 1.2))
        paras = content if isinstance(content, list) else str(content).split("\n")
        return sum(measure.text_height(p, self.size(size), width, spacing) for p in paras)

    # -- shapes -------------------------------------------------------------
    def box(self, x, y, w, h, *, fill=None, line=None, line_width=0.75, dash=False,
            shape="rect", radius=None, name=None, text=None, text_size="body",
            text_color=None, align="center", anchor="middle", inset=6, bold=False):
        radius = self.brand.get("layout.radius", 0) if radius is None else radius
        kind = SHAPES["round"] if (shape == "rect" and radius) else SHAPES[shape]
        shp = self.slide.shapes.add_shape(kind, Pt(x), Pt(y), Pt(w), Pt(h))
        if name:
            shp.name = name
        if kind == MSO_SHAPE.ROUNDED_RECTANGLE:
            shp.adjustments[0] = min(0.5, radius / max(1.0, min(w, h)))
        self._plain(shp)
        if fill:
            shp.fill.solid()
            shp.fill.fore_color.rgb = self.brand.rgb(fill)
        else:
            shp.fill.background()
        if line:
            shp.line.color.rgb = self.brand.rgb(line)
            shp.line.width = Pt(line_width)
            if dash:
                self._dash(shp.line._get_or_add_ln())
        else:
            shp.line.fill.background()
        tf = shp.text_frame
        tf.word_wrap = True
        self._no_inset(tf, inset)
        tf.vertical_anchor = ANCHOR[anchor]
        if text is not None:
            pt = self.size(text_size)
            for i, para in enumerate(str(text).split("\n")):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.alignment = ALIGN[align]
                p.line_spacing = float(self.brand.get("type.heading_line_spacing", 1.05))
                run = p.add_run()
                run.text = para
                self._font(run, "body", pt, text_color or self.ink, bold)
        return shp

    @staticmethod
    def _dash(ln):
        for el in ln.findall(qn("a:prstDash")):
            ln.remove(el)
        dash = etree.SubElement(ln, qn("a:prstDash"))
        dash.set("val", "dash")
        # prstDash must precede round/bevel/miter, headEnd, tailEnd
        for tag in ("a:round", "a:bevel", "a:miter", "a:headEnd", "a:tailEnd"):
            for el in ln.findall(qn(tag)):
                ln.remove(el)
                ln.append(el)

    @staticmethod
    def _arrow(ln, end: str = "tail", kind: str = "triangle"):
        tag = qn(f"a:{end}End")
        for el in ln.findall(tag):
            ln.remove(el)
        el = etree.SubElement(ln, tag)
        el.set("type", kind)
        el.set("w", "med")
        el.set("len", "med")
        if end == "head":  # headEnd must precede tailEnd
            tail = ln.find(qn("a:tailEnd"))
            if tail is not None:
                ln.remove(tail)
                ln.append(tail)

    def line(self, x1, y1, x2, y2, *, color="line", width=0.75, dash=False, arrow=None,
             name=None):
        """Straight line. ``arrow``: None | 'end' | 'both'."""
        conn = self._plain(self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Pt(x1), Pt(y1), Pt(x2), Pt(y2)))
        if name:
            conn.name = name
        conn.line.color.rgb = self.brand.rgb(color)
        conn.line.width = Pt(width)
        ln = conn.line._get_or_add_ln()
        if dash:
            self._dash(ln)
        if arrow in ("end", "both"):
            self._arrow(ln, "tail")
        if arrow == "both":
            self._arrow(ln, "head")
        return conn

    def connect(self, a, b, *, a_side="right", b_side="left", elbow=True, color="muted",
                width=1.0, dash=False, arrow="end", name=None):
        """Glued connector between two shapes; it follows them when edited."""
        sites = {"top": 0, "left": 1, "bottom": 2, "right": 3}
        kind = MSO_CONNECTOR.ELBOW if elbow else MSO_CONNECTOR.STRAIGHT
        conn = self._plain(self.slide.shapes.add_connector(kind, 0, 0, 0, 0))
        conn.begin_connect(a, sites[a_side])
        conn.end_connect(b, sites[b_side])
        if name:
            conn.name = name
        conn.line.color.rgb = self.brand.rgb(color)
        conn.line.width = Pt(width)
        ln = conn.line._get_or_add_ln()
        if dash:
            self._dash(ln)
        if arrow in ("end", "both"):
            self._arrow(ln, "tail")
        if arrow == "both":
            self._arrow(ln, "head")
        return conn

    def path(self, points, *, color="muted", width=1.0, dash=False, arrow="end", name=None):
        """Open polyline through ``points`` [(x, y), ...] — for routes a straight or
        elbow connector cannot draw (e.g. a return path that loops under its nodes).
        Not glued: re-check it after moving the nodes it connects."""
        (x0, y0), rest = points[0], points[1:]
        fb = self.slide.shapes.build_freeform(Pt(x0), Pt(y0), scale=1.0)
        fb.add_line_segments([(Pt(x), Pt(y)) for x, y in rest], close=False)
        shp = self._plain(fb.convert_to_shape())
        if name:
            shp.name = name
        shp.fill.background()
        shp.line.color.rgb = self.brand.rgb(color)
        shp.line.width = Pt(width)
        ln = shp.line._get_or_add_ln()
        if dash:
            self._dash(ln)
        if arrow in ("end", "both"):
            self._arrow(ln, "tail")
        if arrow == "both":
            self._arrow(ln, "head")
        return shp

    # -- images -------------------------------------------------------------
    def image(self, path, x, y, w, h, *, fit="contain", name=None, alt=""):
        path = Path(path)
        if not path.exists():
            self.warn(f"image not found: {path}", "ERROR")
            return self.box(x, y, w, h, line="chrome", dash=True, text=f"missing: {path.name}",
                            text_size="caption", text_color="muted")
        if path.suffix.lower() == ".svg":
            png = svg_to_png(path)
            if png is None:
                self.warn(f"cannot place SVG without a converter (install cairosvg or rsvg-convert): {path.name}", "ERROR")
                return None
            path = png
        from PIL import Image
        with Image.open(path) as im:
            iw, ih = im.size
        scale = (min if fit == "contain" else max)(w / iw, h / ih)
        pw, ph = iw * scale, ih * scale
        px, py = x + (w - pw) / 2, y + (h - ph) / 2
        pic = self.slide.shapes.add_picture(str(path), Pt(px), Pt(py), Pt(pw), Pt(ph))
        if fit == "cover":  # crop to the frame instead of overflowing it
            cx = max(0.0, (pw - w) / pw / 2)
            cy = max(0.0, (ph - h) / ph / 2)
            pic.crop_left = pic.crop_right = cx
            pic.crop_top = pic.crop_bottom = cy
            pic.left, pic.top, pic.width, pic.height = Pt(x), Pt(y), Pt(w), Pt(h)
        if name:
            pic.name = name
        if alt:
            pic._element.nvPicPr.cNvPr.set("descr", alt)
        return pic

    # -- table --------------------------------------------------------------
    def table(self, x, y, w, columns, rows, *, widths=None, numeric_cols=(), highlight_col=None,
              total_row=False, size="body", row_h=None, name=None):
        """Quiet native table: thin horizontal rules, no vertical lines.

        A cell may be a string or ``[keyword, detail]`` (bold keyword over a
        muted detail line).
        """
        n_cols = len(columns)
        widths = widths or [1] * n_cols
        total = float(sum(widths))
        col_w = [w * v / total for v in widths]
        pt = self.size(size)
        detail_pt = self.size("caption")
        pad = 5.0
        heights = [pt * 1.8 + 2 * pad]
        for row in rows:
            hmax = 0.0
            for cell, cw in zip(row, col_w):
                head, detail = (cell + [""])[:2] if isinstance(cell, list) else (cell, "")
                hh = self.text_height(str(head), pt, cw - 2 * pad)
                if detail:
                    hh += self.text_height(str(detail), detail_pt, cw - 2 * pad)
                hmax = max(hmax, hh)
            heights.append(max(row_h or 0, hmax + 2 * pad))
        gf = self.slide.shapes.add_table(len(rows) + 1, n_cols, Pt(x), Pt(y), Pt(w), Pt(sum(heights)))
        if name:
            gf.name = name
        tbl = gf.table
        tbl_pr = tbl._tbl.tblPr
        tbl_pr.set("firstRow", "1")
        tbl_pr.set("bandRow", "0")
        style = tbl_pr.find(qn("a:tableStyleId"))
        if style is None:
            style = etree.SubElement(tbl_pr, qn("a:tableStyleId"))
        style.text = NO_STYLE_TABLE
        for i, cw in enumerate(col_w):
            tbl.columns[i].width = Pt(cw)
        for r, hh in enumerate(heights):
            tbl.rows[r].height = Pt(hh)
        tint = self.brand.tint("accent", 0.93)
        last = len(rows)
        for r in range(last + 1):
            for c in range(n_cols):
                cell = tbl.cell(r, c)
                cell.margin_left = cell.margin_right = Pt(pad)
                cell.margin_top = cell.margin_bottom = Pt(pad)
                cell.vertical_anchor = MSO_ANCHOR.BOTTOM if r == 0 else MSO_ANCHOR.TOP
                highlighted = highlight_col is not None and c == highlight_col
                if highlighted and r > 0:
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = self.brand.rgb(tint)
                else:
                    cell.fill.background()
                value = columns[c] if r == 0 else rows[r - 1][c] if c < len(rows[r - 1]) else ""
                head, detail = (value + [""])[:2] if isinstance(value, list) else (value, "")
                tf = cell.text_frame
                tf.word_wrap = True
                p = tf.paragraphs[0]
                p.alignment = PP_ALIGN.RIGHT if c in numeric_cols else PP_ALIGN.LEFT
                run = p.add_run()
                run.text = str(head)
                if r == 0:
                    self._font(run, "body", self.size("caption"),
                               "accent" if highlighted else "muted", highlighted)
                else:
                    strong = bool(detail) and c > 0 or (total_row and r == last)
                    self._font(run, "body", pt, "ink", strong)
                if detail and r > 0:
                    p2 = tf.add_paragraph()
                    p2.alignment = p.alignment
                    run2 = p2.add_run()
                    run2.text = str(detail)
                    self._font(run2, "body", detail_pt, "muted", False)
                # borders: header bottom, row separators, table end
                bottom = ("line", 1.0) if r in (0, last) else ("line", 0.5)
                top = ("muted", 1.0) if total_row and r == last else None
                self._cell_borders(cell, top=top, bottom=bottom)
        if highlight_col is not None:  # accent cap above the recommended column
            cx = x + sum(col_w[:highlight_col])
            self.box(cx, y - 2, col_w[highlight_col], 2, fill="accent")
        return gf, sum(heights)

    def _cell_borders(self, cell, top=None, bottom=None):
        tc_pr = cell._tc.get_or_add_tcPr()
        for side in ("lnL", "lnR", "lnT", "lnB"):
            for el in tc_pr.findall(qn(f"a:{side}")):
                tc_pr.remove(el)
        spec = {"lnL": None, "lnR": None, "lnT": top, "lnB": bottom}
        # border elements must come first inside tcPr, in L, R, T, B order
        for index, side in enumerate(("lnL", "lnR", "lnT", "lnB")):
            ln = etree.Element(qn(f"a:{side}"))
            value = spec[side]
            if value:
                color, width = value
                ln.set("w", str(int(Pt(width))))
                fill = etree.SubElement(ln, qn("a:solidFill"))
                etree.SubElement(fill, qn("a:srgbClr")).set("val", self.brand.hex(color))
            else:
                ln.set("w", "0")
                etree.SubElement(ln, qn("a:noFill"))
            tc_pr.insert(index, ln)

    # -- chart --------------------------------------------------------------
    def chart(self, x, y, w, h, kind, categories, series, *, highlight=None, number_format=None,
              labels=True, legend=None, gap=60, name=None):
        """Native chart styled from the brand.

        ``series`` is ``[{"name": str, "values": [...]}, ...]``. With one series,
        ``highlight`` is a category index drawn in the accent while the others
        stay muted. With several series, colors follow ``colors.series``.
        """
        data = CategoryChartData()
        data.categories = categories
        for s in series:
            data.add_series(s["name"], s["values"])
        frame = self.slide.shapes.add_chart(CHARTS[kind], Pt(x), Pt(y), Pt(w), Pt(h), data)
        if name:
            frame.name = name
        chart = frame.chart
        chart.has_title = False  # the slide headline carries the message
        chart.font.size = Pt(self.size("caption"))
        chart.font.color.rgb = self.brand.rgb(self.muted)
        fonts = self.brand["fonts.body"]
        chart.font.name = fonts.get("latin")
        single = len(series) == 1
        if legend is None:
            legend = not single
        chart.has_legend = bool(legend)
        if legend:
            chart.legend.position = XL_LEGEND_POSITION.TOP
            chart.legend.include_in_layout = False
            chart.legend.font.size = Pt(self.size("caption"))
        plot = chart.plots[0]
        if kind in ("bar", "column", "stacked_bar", "stacked_column"):
            plot.gap_width = gap
            if kind.startswith("stacked"):
                plot.overlap = 100
        if kind not in ("pie", "doughnut"):
            va = chart.value_axis
            va.has_major_gridlines = True
            va.major_gridlines.format.line.color.rgb = self.brand.rgb("line")
            va.major_gridlines.format.line.width = Pt(0.5)
            va.format.line.fill.background()
            va.tick_labels.font.size = Pt(self.size("caption"))
            if kind in ("bar", "column", "stacked_bar", "stacked_column"):
                va.minimum_scale = 0  # bars encode length; they always start at zero
            if labels:
                va.visible = False
                va.has_major_gridlines = False
            ca = chart.category_axis
            ca.format.line.color.rgb = self.brand.rgb("line")
            ca.tick_labels.font.size = Pt(self.size("caption"))
            ca.tick_labels.font.color.rgb = self.brand.rgb(self.body_color)
            if kind in ("bar", "stacked_bar"):
                ca.reverse_order = True  # first category on top, as read
        muted = self.brand.tint(self.brand.hex("muted"), 0.45)
        for i, s in enumerate(plot.series):
            fmt = s.format
            color = self.brand.series(i)
            if kind == "line":
                fmt.line.color.rgb = self.brand.rgb(color)
                fmt.line.width = Pt(2.25 if i == 0 else 1.5)
                s.smooth = False
                continue
            fmt.fill.solid()
            fmt.fill.fore_color.rgb = self.brand.rgb(color if not (single and highlight is not None) else muted)
            if kind in ("pie", "doughnut"):
                for j in range(len(categories)):
                    pt_ = s.points[j]
                    pt_.format.fill.solid()
                    pt_.format.fill.fore_color.rgb = self.brand.rgb(
                        self.brand.series(j) if highlight is None else ("accent" if j == highlight else muted))
            elif single and highlight is not None:
                pt_ = s.points[highlight]
                pt_.format.fill.solid()
                pt_.format.fill.fore_color.rgb = self.brand.rgb("accent")
        if labels:
            plot.has_data_labels = True
            dl = plot.data_labels
            dl.font.size = Pt(self.size("caption"))
            dl.font.color.rgb = self.brand.rgb(self.ink)
            if number_format:
                dl.number_format = number_format
                dl.number_format_is_linked = False
            if kind in ("bar", "column"):
                dl.position = XL_LABEL_POSITION.OUTSIDE_END
            elif kind == "line":
                dl.position = XL_LABEL_POSITION.ABOVE
        return frame


def svg_to_png(path: Path) -> Path | None:
    out = Path(tempfile.mkdtemp(prefix="deckkit-")) / (path.stem + ".png")
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=str(path), write_to=str(out), output_width=512)
        return out
    except Exception:
        pass
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-w", "512", "-o", str(out), str(path)], check=False)
        if out.exists():
            return out
    return None
