#!/usr/bin/env python3
"""Read-only design-craft lint for a PPTX deck (reader-facing quality, not layout contracts).

CLI: deck-craft-lint.py deck.pptx [--brand brand.yaml] [--output lint.json]
                         [--md lint.md] [--mode present|read]

Each finding has a rule id, severity (fail/warn/info), slide number and evidence.
Sizes and positions are in points, normalized to the reference canvas width
(brand `canvas.width`, default 960 pt) so a deck on a different slide size is
judged by the same proportions.

With --brand, thresholds come from the brand profile: `type.min` (and optional
`type.table_min`) for minimum text size, `layout.body_bottom` / `canvas.height`
for the body end, `colors.*` as the allowed palette, `fonts.*` as the allowed
typefaces. Without it (or when PyYAML is not installed) neutral defaults are used
and the palette/font checks are skipped.

Exit codes: 0 = no fail findings, 1 = at least one fail finding, 2 = input error.
Limits: inherited font sizes/colors (placeholders, theme colors) are reported as
unresolved, not guessed. Background is the shape's own solid fill, else white.
A lint result is evidence for review, not a design approval.
"""
import argparse, colorsys, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    from pptx.util import Emu
except ImportError:
    print("python-pptx is required", file=sys.stderr); sys.exit(2)

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
# Explicit authoring instructions / sentinels are defects in a delivered deck; generic tokens need review.
TEMPLATE_FAIL = re.compile(r"(기술하세요|작성하세요|입력하세요|기입하세요|내용을\s*입력|텍스트를 입력|Lorem ipsum|Click to (add|edit)|__[A-Z_]+__|\{\{.*?\}\})", re.I)
TEMPLATE_WARN = re.compile(r"(\bTBD\b|\bTODO\b|OOO|ＯＯＯ|\bX{2,}\b)")
NUM_RE = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*(?:%|배|x|X)?")
MULT_X = re.compile(r"\d\s?[xX×](?![a-zA-Z])")
MULT_BAE = re.compile(r"\d\s?배")
SOURCE_RE = re.compile(r"^\s*(※\s*)?(Source|Sources|출처|자료|資料)\s*[:：]?", re.I)
HEX_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")

# Neutral defaults (points on a 960-pt-wide canvas) used when no brand profile is given.
DEFAULTS = {
    "ref_width_pt": 960.0,
    "min_pt": 9.75,         # smallest text anywhere
    "table_min_pt": 9.0,    # dense table headers may go one step lower
    "readable_pt": 10.5,    # body text below this is flagged for review (warn)
    "body_bottom_ratio": 466 / 540,
    "palette": None,        # set of allowed hex colors, or None to skip
    "status_colors": set(), # semantic colors that do not count as editorial accents
    "fonts": None,          # set of allowed typefaces (lowercase), or None to skip
    "source": "defaults",
}


def is_title(shape):
    """Title placeholder, or a shape the generator named 'Title'."""
    try:
        if shape.is_placeholder and "TITLE" in str(shape.placeholder_format.type):
            return True
    except Exception:
        pass
    return shape.name == "Title"


def merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def tint(hex6, amount):
    r, g, b = (int(hex6[i:i + 2], 16) for i in (0, 2, 4))
    mix = lambda c: round(c + (255 - c) * amount)
    return f"{mix(r):02X}{mix(g):02X}{mix(b):02X}"


def load_brand(path):
    """Read thresholds from a brand.yaml. Missing PyYAML falls back to defaults with a note."""
    cfg = dict(DEFAULTS, status_colors=set())
    notes = []
    if not path:
        return cfg, notes
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"brand profile not found: {path}")
    try:
        import yaml
    except ImportError:
        notes.append("PyYAML not installed: --brand ignored, neutral defaults used")
        print("warning: PyYAML not installed; using neutral defaults instead of the brand profile", file=sys.stderr)
        return cfg, notes
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    # A partial profile inherits the pptx-deck defaults, exactly as the builder does.
    default = Path(__file__).resolve().parents[2] / "pptx-deck" / "brand" / "brand.yaml"
    if default.is_file() and default.resolve() != p.resolve():
        data = merge(yaml.safe_load(default.read_text(encoding="utf-8")) or {}, data)
        notes.append("brand profile merged with the pptx-deck defaults")
    canvas, typ, lay = data.get("canvas") or {}, data.get("type") or {}, data.get("layout") or {}
    if canvas.get("width"):
        cfg["ref_width_pt"] = float(canvas["width"])
    if typ.get("min") is not None:
        cfg["min_pt"] = float(typ["min"])
        cfg["table_min_pt"] = float(typ.get("table_min", typ["min"]))
        cfg["readable_pt"] = float(typ.get("readable_min", typ["min"]))
    if lay.get("body_bottom") and canvas.get("height"):
        cfg["body_bottom_ratio"] = float(lay["body_bottom"]) / float(canvas["height"])
    palette = set()

    def collect(v):
        if isinstance(v, (list, tuple)):
            for x in v:
                collect(x)
        elif v is not None and HEX_RE.match(str(v)):
            palette.add(str(v).lstrip("#").upper())
    for v in (data.get("colors") or {}).values():
        collect(v)
    if palette:
        palette |= {"FFFFFF", "000000"}
        # light tints the generator derives for highlighted cells, cards and muted bars
        cols_ = data.get("colors") or {}
        for key, amounts in (("accent", (0.9, 0.92, 0.93)), ("muted", (0.45,))):
            if cols_.get(key) and HEX_RE.match(str(cols_[key])):
                palette |= {tint(str(cols_[key]).lstrip("#").upper(), a) for a in amounts}
        cfg["palette"] = palette
    cols = data.get("colors") or {}
    cfg["status_colors"] = {str(cols[k]).lstrip("#").upper() for k in ("positive", "warning", "negative") if cols.get(k)}
    fonts = set()
    for role in (data.get("fonts") or {}).values():
        if isinstance(role, dict):
            fonts |= {str(f).lower() for f in role.values() if f}
        elif role:
            fonts.add(str(role).lower())
    if fonts:
        cfg["fonts"] = fonts
    cfg["source"] = str(p)
    return cfg, notes


def lum(rgb):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def hex2rgb(h):
    h = str(h).lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def solid_rgb(fill):
    try:
        if fill.type == 1 and fill.fore_color.type is not None:  # MSO_FILL.SOLID
            return hex2rgb(fill.fore_color.rgb)
    except Exception:
        pass
    return None


def chroma_family(rgb):
    h, l, s = colorsys.rgb_to_hls(*(v / 255 for v in rgb))
    if s < 0.28 or l < 0.12 or l > 0.93:
        return None  # neutral / near-white / near-black
    return int(((h * 360) + 15) // 30) % 12


class Xf:
    """Affine mapping from a group's child space to slide space (per axis scale + offset)."""
    def __init__(self, sx=1.0, sy=1.0, ox=0.0, oy=0.0):
        self.sx, self.sy, self.ox, self.oy = sx, sy, ox, oy

    def apply(self, x, y, w, h):
        return self.ox + x * self.sx, self.oy + y * self.sy, w * self.sx, h * self.sy

    def child(self, grp):
        xfrm = grp._element.grpSpPr.find(NS_A + "xfrm")
        if xfrm is None:
            return self
        off, ext = xfrm.find(NS_A + "off"), xfrm.find(NS_A + "ext")
        choff, chext = xfrm.find(NS_A + "chOff"), xfrm.find(NS_A + "chExt")
        if None in (off, ext, choff, chext):
            return self
        cx, cy = int(chext.get("cx")) or 1, int(chext.get("cy")) or 1
        gsx, gsy = int(ext.get("cx")) / cx, int(ext.get("cy")) / cy
        # child -> group parent space: off + (c - chOff) * g ; then parent -> slide via self
        ox = int(off.get("x")) - int(choff.get("x")) * gsx
        oy = int(off.get("y")) - int(choff.get("y")) * gsy
        return Xf(self.sx * gsx, self.sy * gsy, self.ox + ox * self.sx, self.oy + oy * self.sy)


def leaves(shapes, xf):
    for s in shapes:
        if s.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from leaves(s.shapes, xf.child(s))
        else:
            if s.left is None or s.width is None:
                yield s, None
            else:
                yield s, xf.apply(s.left, s.top, s.width, s.height)


def run_size_pt(run, para):
    if run.font.size is not None:
        return run.font.size.pt
    ppr = para._p.find(NS_A + "pPr")
    if ppr is not None:
        d = ppr.find(NS_A + "defRPr")
        if d is not None and d.get("sz"):
            return int(d.get("sz")) / 100
    return None


def run_fonts(run):
    """Explicit typefaces on a run: latin (python-pptx font.name) plus east-asian."""
    names = []
    if run.font.name:
        names.append(run.font.name)
    rpr = run._r.find(NS_A + "rPr")
    if rpr is not None:
        ea = rpr.find(NS_A + "ea")
        if ea is not None and ea.get("typeface") and not ea.get("typeface").startswith("+"):
            names.append(ea.get("typeface"))
    return names


def rgb_hex(rgb):
    return "%02X%02X%02X" % rgb


def run_rgb(run):
    try:
        if run.font.color is not None and run.font.color.type is not None:
            return hex2rgb(run.font.color.rgb)
    except Exception:
        pass
    return None


def text_frames(shape):
    if shape.has_text_frame:
        yield shape.text_frame, solid_rgb(shape.fill) if hasattr(shape, "fill") else None, False
    if getattr(shape, "has_table", False) and shape.has_table:
        for row in shape.table.rows:
            for cell in row.cells:
                bg = None
                try:
                    bg = solid_rgb(cell.fill)
                except Exception:
                    pass
                yield cell.text_frame, bg, True


def chart_findings(shape, add, sn):
    chart = shape.chart
    vals = []
    try:
        for plot in chart.plots:
            for ser in plot.series:
                vals += [v for v in ser.values if v is not None]
    except Exception:
        pass
    x = chart._chartSpace
    # Typed numeric label overrides must equal the plotted value at the displayed precision.
    for ser in x.iter(NS_C + "ser"):
        pts = {int(pt.get("idx")): float(pt.findtext(NS_C + "v")) for pt in ser.iterfind(f"{NS_C}val//{NS_C}pt")
               if pt.findtext(NS_C + "v") not in (None, "")}
        for dl in ser.iterfind(f"{NS_C}dLbls/{NS_C}dLbl"):
            t = "".join(e.text or "" for e in dl.iter(NS_A + "t"))
            m = re.search(r"-?\d+(?:[.,]\d+)?", t)
            if not m:
                continue
            idx = int(dl.find(NS_C + "idx").get("val"))
            typed = float(m.group(0).replace(",", "."))
            dec = len(m.group(0).split(".")[1]) if "." in m.group(0) else 0
            v = pts.get(idx)
            if v is None:
                add("chart-typed-label", "warn", sn, f"typed label '{t}' at point {idx} has no cached value to compare")
            elif abs(round(v, dec) - typed) > 0.5 * 10 ** -dec and abs(round(v * 100, dec) - typed) > 0.5 * 10 ** -dec:
                add("chart-typed-label", "fail", sn, f"typed label '{t}' at point {idx} differs from plotted value {v:g}")
            else:
                add("chart-typed-label", "info", sn, f"typed label '{t}' at point {idx} matches value {v:g}; prefer generated labels")
    if chart.has_legend:
        add("chart-legend", "info", sn, "native chart has a legend; prefer direct labels")
    if x.findall(".//" + NS_C + "majorGridlines"):
        add("chart-gridlines", "info", sn, "native chart has major gridlines")
    return vals


def lint(path, mode, cfg=None, notes=()):
    cfg = cfg or dict(DEFAULTS)
    prs = Presentation(path)
    W, H = prs.slide_width, prs.slide_height
    k = cfg["ref_width_pt"] / Emu(W).pt  # normalized pt per actual pt
    findings = []
    add = lambda rule, sev, sn, ev: findings.append({"rule": rule, "severity": sev, "slide": sn, "evidence": ev})
    deck_text, left_edges, per_slide = [], {}, []
    char_cap = 180 if mode == "present" else 400
    tol = 1.5 * 12700 / k  # 1.5 pt on the normalized canvas, in EMU
    body_limit = cfg["body_bottom_ratio"] * H  # body end before the footer band
    palette, status, allowed_fonts = cfg["palette"], cfg["status_colors"], cfg["fonts"]
    rotated = 0

    for sn, slide in enumerate(prs.slides, 1):
        families, chars, texts, chart_vals = Counter(), 0, [], []
        biggest = (0, "")
        # a solid slide background (Format Background) replaces the assumed white page
        slide_bg = None
        if slide._element.cSld.bg is not None:
            slide_bg = solid_rgb(slide.background.fill)
        text_lefts, body_bottoms, has_footer = [], [], False
        for shp, box in leaves(slide.shapes, Xf()):
            if box is None:
                continue
            x, y, w, h = box
            xfrm = shp._element.find(".//" + NS_A + "xfrm")
            is_rot = xfrm is not None and (xfrm.get("rot") not in (None, "0") or xfrm.get("flipH") == "1" or xfrm.get("flipV") == "1")
            rotated += bool(is_rot)
            # off-canvas (1.5 pt tolerance); pictures larger than the slide are treated as intended bleed
            if x < -tol or y < -tol or x + w > W + tol or y + h > H + tol:
                has_text = shp.has_text_frame and shp.text_frame.text.strip()
                if shp.shape_type == MSO_SHAPE_TYPE.PICTURE and not has_text:
                    add("off-canvas", "info", sn, f"picture '{shp.name}' bleeds past the slide edge (intended crop?)")
                    continue
                add("off-canvas", "fail" if has_text else "warn", sn,
                    f"'{shp.name}' extends outside the slide ({Emu(int(x)).pt:.0f},{Emu(int(y)).pt:.0f},{Emu(int(w)).pt:.0f}x{Emu(int(h)).pt:.0f}pt)"
                    + (f" text='{shp.text_frame.text.strip()[:40]}'" if has_text else ""))
                continue  # off-canvas objects are not part of the visible page
            # circles distorted by group scaling
            try:
                if shp.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE and "OVAL" in str(shp.auto_shape_type) and not is_rot:
                    r = w / h if h else 1
                    d_pt = max(w, h) * k / 12700
                    if 0.9 < r < 1.1 and abs(w - h) * k / 12700 > max(0.375, 0.01 * d_pt):
                        add("distorted-circle", "warn", sn, f"'{shp.name}' near-circle with w/h={r:.3f}")
            except Exception:
                pass
            # colors
            for rgb in filter(None, [solid_rgb(shp.fill) if hasattr(shp, "fill") else None]):
                f = chroma_family(rgb)
                if f is not None and rgb_hex(rgb) not in status:
                    families[f] += 1
                if palette is not None and rgb_hex(rgb) not in palette and shp.shape_type != MSO_SHAPE_TYPE.PICTURE:
                    add("off-brand-color", "warn" if f is not None else "info", sn,
                        f"fill #{rgb_hex(rgb)} on '{shp.name}' is not in the brand palette")
            if getattr(shp, "has_chart", False) and shp.has_chart:
                chart_vals += chart_findings(shp, add, sn)
            for tf, bg, in_table in text_frames(shp):
                t = tf.text.strip()
                if not t:
                    continue
                texts.append(t)
                if not in_table:
                    text_lefts.append((y, x))
                if y >= H * 0.92:
                    has_footer = True
                elif y < body_limit:
                    body_bottoms.append((y + h, t[:30]))
                if TEMPLATE_FAIL.search(t):
                    add("template-text", "fail", sn, f"authoring instruction or sentinel: '{t[:60]}'")
                elif TEMPLATE_WARN.search(t):
                    add("template-text", "warn", sn, f"placeholder-like token, check intent: '{t[:60]}'")
                for para in tf.paragraphs:
                    for run in para.runs:
                        rt = run.text.strip()
                        if not rt:
                            continue
                        sz = run_size_pt(run, para)
                        col = run_rgb(run)
                        if col is not None:
                            f = chroma_family(col)
                            if f is not None and rgb_hex(col) not in status:
                                families[f] += 1
                            if palette is not None and rgb_hex(col) not in palette:
                                add("off-brand-color", "warn" if f is not None else "info", sn,
                                    f"text color #{rgb_hex(col)} is not in the brand palette '{rt[:30]}'")
                        if allowed_fonts is not None:
                            for fn in run_fonts(run):
                                if fn.lower() not in allowed_fonts:
                                    add("off-brand-font", "warn", sn, f"font '{fn}' is not a brand font '{rt[:30]}'")
                        if sz is None:
                            continue
                        npt = sz * k  # size normalized to the reference canvas
                        if is_title(shp):  # a named or placeholder title outranks size
                            biggest = (float("inf"), tf.text.strip())
                        elif y < H * 0.25 and npt > biggest[0] and len(re.sub(r"[\d\s.]", "", tf.text)) >= 4:
                            biggest = (npt, tf.text.strip())
                        mono = "mono" in (run.font.name or "").lower()
                        floor = cfg["table_min_pt"] if in_table else cfg["min_pt"]
                        if npt < floor - 0.05:
                            add("min-size", "fail", sn, f"{npt:.2f}pt text below the {floor:g}pt minimum '{rt[:30]}'" + (" (table)" if in_table else ""))
                        elif npt < cfg["readable_pt"] - 0.05 and not mono and not in_table and y < H * 0.92:  # footer chrome may sit at the minimum
                            add("min-size", "warn", sn, f"{npt:.2f}pt readable text below {cfg['readable_pt']:g}pt '{rt[:30]}'")
                        if col is not None:
                            back = bg or slide_bg or (255, 255, 255)
                            c = contrast(col, back)
                            # WCAG: large text = >=18pt, or >=14pt bold (python-pptx bold flag)
                            large = npt >= 18 or (npt >= 14 and bool(run.font.bold))
                            need = 3.0 if large else 4.5
                            if lum(col) > 0.8 and bg is not None and c < need:
                                add("light-text-on-fill", "fail" if c < 3 else "warn", sn, f"light text on fill contrast {c:.2f}:1 (needs {need}) '{rt[:30]}'")
                            elif lum(col) > 0.8 and bg is None and slide_bg is None:
                                pass  # light text over another shape: background unknown, not judged
                            elif c < need:
                                add("small-text-contrast", "warn", sn, f"{npt:.2f}pt text contrast {c:.2f}:1 (needs {need}) '{rt[:30]}'")
                chars += len(re.sub(r"\s", "", t))
        # per-slide judgments
        fam_n = len(families)
        if fam_n > 2:
            add("color-families", "warn", sn, f"{fam_n} chromatic hue families in fills/text; check the editorial focus (logos, icons and status colors may be exceptions)")
        body_chars = chars - len(re.sub(r"\s", "", biggest[1]))
        if body_chars > char_cap:
            add("density", "info", sn, f"{body_chars} body characters (signal > {char_cap} for {mode} mode); check questions, encodings and local crowding")
        if has_footer:
            over = [(b, t) for b, t in body_bottoms if b > body_limit + tol]
            if over:
                b, t = max(over)
                add("footer-clearance", "warn", sn, f"body text ends at {b * k / 12700:.0f}pt, past the {body_limit * k / 12700:.0f}pt body end: '{t}'")
        if biggest[1]:
            raw = [n for n in NUM_RE.findall(biggest[1]) if not re.fullmatch(r"(19|20)\d\d|\d|0\d", n)]
            pool = " ".join(t for t in texts if t != biggest[1]) + " " + " ".join(f"{v:g}" for v in chart_vals)
            missing = sorted({n for n in raw if n.rstrip("%배xX") not in pool})
            if missing:
                add("headline-number", "warn", sn, f"headline numbers not found elsewhere on the slide: {missing}")
        if text_lefts:
            body = [x for (yy, x) in text_lefts if H * 0.18 < yy < H * 0.92]
            if body:
                left_edges[sn] = round(min(body) * k / 12700, 1)
        deck_text += texts
        per_slide.append({"slide": sn, "chars": chars, "color_families": fam_n})

    # deck-level judgments
    joined = "\n".join(deck_text)
    if MULT_X.search(joined) and MULT_BAE.search(joined):
        add("multiplier-notation", "warn", 0, "both 'Nx' and 'N배' multiplier notations are used")
    prefixes = Counter()
    for t in deck_text:
        for line in t.splitlines():
            m = SOURCE_RE.match(line)
            if m:
                prefixes[m.group(0).strip().rstrip(":：").strip()] += 1
    if len(prefixes) > 1:
        add("source-format", "warn", 0, f"mixed source prefixes: {dict(prefixes)}")
    if left_edges:
        mode_x, cnt = Counter(left_edges.values()).most_common(1)[0]
        off = {s: x for s, x in left_edges.items() if abs(x - mode_x) > 1.5}
        if off and len(off) <= len(left_edges) // 2:
            add("left-edge", "info", 0, f"body left edge mode x={mode_x}pt; slides off by >1.5pt: {off}")

    # aggregate repeated run-level findings per slide so the report stays reviewable
    grouped = defaultdict(list)
    for f in findings:
        grouped[(f["slide"], f["rule"], f["severity"])].append(f["evidence"])
    findings = [{"slide": s, "rule": r, "severity": v, "count": len(evs),
                 "evidence": evs[0] if len(evs) == 1 else f"{len(evs)}× e.g. " + " ; ".join(evs[:3])}
                for (s, r, v), evs in grouped.items()]
    findings.sort(key=lambda f: (f["slide"], {"fail": 0, "warn": 1, "info": 2}[f["severity"]], f["rule"]))
    sev = Counter()
    for f in findings:
        sev[f["severity"]] += f["count"]
    return {
        "schema_version": 1, "artifact": str(path), "mode": mode,
        "slide_count": len(prs.slides), "normalization_factor": round(k, 4),
        "thresholds": {"source": cfg["source"], "reference_width_pt": cfg["ref_width_pt"],
                       "min_pt": cfg["min_pt"], "table_min_pt": cfg["table_min_pt"],
                       "readable_pt": cfg["readable_pt"], "body_bottom_pt": round(body_limit * k / 12700, 1),
                       "palette_checked": palette is not None, "fonts_checked": allowed_fonts is not None},
        "summary": {"fail": sev["fail"], "warn": sev["warn"], "info": sev["info"],
                    "by_rule": {k2: sum(f["count"] for f in findings if f["rule"] == k2) for k2 in sorted({f["rule"] for f in findings})}},
        "slides": per_slide, "findings": findings,
        "limitations": ["inherited sizes/theme colors unresolved", "background assumed white unless the shape or the slide background has a solid fill",
                        f"rotated/flipped shapes are measured by their unrotated box ({rotated} found)",
                        "visual judgment (optical alignment, emphasis, narrative) is outside this lint"] + list(notes),
    }


def to_md(r):
    out = [f"# deck-craft-lint — {Path(r['artifact']).name}", "",
           f"mode `{r['mode']}` · slides {r['slide_count']} · fail {r['summary']['fail']} · warn {r['summary']['warn']} · info {r['summary']['info']}", "",
           "| rule | count |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in sorted(r["summary"]["by_rule"].items())]
    out += ["", "| slide | severity | rule | evidence |", "|---|---|---|---|"]
    out += [f"| {f['slide'] or 'deck'} | {f['severity']} | {f['rule']} | {f['evidence'].replace('|', '/')} |" for f in r["findings"]]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pptx")
    ap.add_argument("--output", default="-")
    ap.add_argument("--md")
    ap.add_argument("--mode", choices=["present", "read"], default="present")
    ap.add_argument("--brand", help="brand.yaml with allowed colors, fonts and minimum sizes")
    a = ap.parse_args()
    try:
        cfg, notes = load_brand(a.brand)
        r = lint(a.pptx, a.mode, cfg, notes)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr); sys.exit(2)
    js = json.dumps(r, ensure_ascii=False, indent=1)
    if a.output == "-":
        print(js)
    else:
        Path(a.output).write_text(js, encoding="utf-8")
    if a.md:
        Path(a.md).write_text(to_md(r), encoding="utf-8")
    sys.exit(1 if r["summary"]["fail"] else 0)


if __name__ == "__main__":
    main()
