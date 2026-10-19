#!/usr/bin/env python3
"""Check a deck spec before building it.

    python scripts/lint_deck.py deck.yaml [--brand brand/brand.yaml] [--json]

ERROR blocks the build (fix it first). WARN needs a decision. The checks are
the narrative contract (audience / objective / desired action), headline
form, density limits, evidence, emoji, assets and deck structure. They do not
replace looking at the rendered slides.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import load_brand, LAYOUTS  # noqa: E402
from deckkit import exhibits, measure  # noqa: E402
from deckkit.canvas import CHARTS  # noqa: E402

EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F2FF️]")
STRUCTURAL = {"cover", "section", "closing", "statement", "quote", "agenda"}
TODO = re.compile(r"\bTODO\b|\bTBD\b|\?\?\?|lorem ipsum", re.I)
TEXT_KEYS = ("title", "subtitle", "eyebrow", "lead", "text", "support", "caption", "takeaway",
             "notes", "source")


def walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_strings(v)


def lint_footer(add, i, s, brand, language, width):
    """Survey numbers need their sample size; a footer is a few lines at most."""
    src = s.get("source")
    if s.get("survey") and s.get("layout") in ("chart", "stats") and \
            not (isinstance(src, dict) and src.get("n") is not None):
        add("WARN", i, "survey figures without a sample size; add source.n (per segment when segments are compared)")
    paras = exhibits.footer_paragraphs(src, brand, language, exhibits.auto_notes(s, brand, language))
    lines = sum(measure.count_lines(p, brand["type.caption"], width) for p in paras)
    if lines > 3:
        add("WARN", i, f"exhibit footer runs to {lines} lines; keep it to 3 and move detail to the notes")


def lint_chart(add, i, ch, where=""):
    kind = ch.get("type", "column")
    if kind not in CHARTS:
        add("ERROR", i, f"{where}unsupported chart type '{kind}' (available: {', '.join(CHARTS)})")
        return
    if kind == "waterfall":
        if not ch.get("steps"):
            add("ERROR", i, f"{where}waterfall without steps")
        elif any(not isinstance(st.get("value"), (int, float)) for st in ch["steps"]):
            add("ERROR", i, f"{where}every waterfall step needs a numeric value")
        elif exhibits.waterfall_low(ch) < 0:
            add("ERROR", i, f"{where}waterfall running total goes below zero; rebase the start or split the bridge")
        cats = exhibits.waterfall_categories(ch)
    else:
        cats = ch.get("categories", [])
    series = ch.get("series", [])
    n = len(cats)
    for ser in series:
        if len(ser.get("values", [])) != n:
            add("ERROR", i, f"{where}series '{ser.get('name')}' has {len(ser.get('values', []))} values for {n} categories")
    if kind in ("pie", "doughnut") and n > 5:
        add("WARN", i, f"{where}part-to-whole chart with more than 5 parts; use a bar chart")
    marked = exhibits.as_list(ch.get("highlight"))
    if marked and len(series) > 1:
        add("WARN", i, f"{where}highlight marks categories of a single series; use highlight_series")
    for ref in marked:
        if exhibits.category_index(cats, ref) is None:
            add("ERROR", i, f"{where}highlight '{ref}' is not a category")
    for ref in exhibits.as_list(ch.get("highlight_series")):
        if not isinstance(ref, int) or not 0 <= ref < len(series):
            add("ERROR", i, f"{where}highlight_series {ref!r} is not a series index")
    if ch.get("series_kind") not in (None, "ordered", "nominal"):
        add("ERROR", i, f"{where}series_kind must be ordered or nominal")
    if kind == "line" and len(series) > 6 and ch.get("highlight_series") is None:
        add("WARN", i, f"{where}{len(series)} lines with no highlight; highlight one series or use panels")
    est = ch.get("estimates")
    if est and kind not in exhibits.ANNOTATED:
        add("ERROR", i, f"{where}estimates work on column, bar and line charts, not '{kind}'")
    elif est and exhibits.category_index(cats, est.get("from")) is None:
        add("ERROR", i, f"{where}estimates.from '{est.get('from')}' is not a category")
    notes = ch.get("annotations") or []
    if notes and kind not in exhibits.ANNOTATED:
        add("ERROR", i, f"{where}annotations work on column, bar and line charts, not '{kind}'")
        return
    for a in notes:
        k = a.get("kind")
        if k not in ("ref_line", "band", "callout", "delta"):
            add("ERROR", i, f"{where}unknown annotation kind '{k}' (ref_line, band, callout, delta)")
            continue
        refs = {"band": ("from", "to"), "callout": ("at",), "delta": ("from", "to")}.get(k, ())
        for key in refs:
            if exhibits.category_index(cats, a.get(key)) is None:
                add("ERROR", i, f"{where}{k} {key} '{a.get(key)}' is not a category")
        if k == "ref_line" and exhibits.ref_value(a, series) is None:
            add("ERROR", i, f"{where}ref_line value must be a number or 'mean'")
        if k == "delta":
            if a.get("fmt", "abs") not in ("pp", "pct", "x", "abs"):
                add("ERROR", i, f"{where}delta fmt must be pp, pct, x or abs")
            if a.get("fmt") == "pct" and exhibits.is_percent(ch.get("number_format")):
                add("WARN", i, f"{where}a difference between shares reads in percentage points; use fmt: pp")
    points = sum(a.get("kind") in exhibits.POINT_KINDS for a in notes)
    if points > 3:
        add("WARN", i, f"{where}{points} callouts and deltas; keep the 1–3 the headline needs")
    if points and n > 8:
        add("WARN", i, f"{where}callouts on a chart with {n} categories get lost; cut categories or drop them")


def lint_commentary(add, i, s, name):
    if name not in ("chart", "table", "image", "diagram"):
        add("WARN", i, f"commentary has no effect on '{name}' slides (chart, table, image, diagram)")
    if s.get("commentary") and s.get("takeaway"):
        add("WARN", i, "both commentary and takeaway; takeaway is ignored — keep one")
    note = s.get("commentary")
    if isinstance(note, dict):
        if not (note.get("text") or note.get("bullets")):
            add("ERROR", i, "commentary needs text or bullets")
        if note.get("side", "right") not in ("right", "left"):
            add("ERROR", i, "commentary side must be right or left")
        if note.get("width", 4) not in (3, 4):
            add("ERROR", i, "commentary width is 3 or 4 grid columns")


def lint(deck_path: Path, brand_path=None):
    spec = yaml.safe_load(deck_path.read_text(encoding="utf-8")) or {}
    meta = spec.get("meta", {}) or {}
    if brand_path is None and meta.get("brand"):
        brand_path = deck_path.parent / meta["brand"]
    brand = load_brand(brand_path)
    out = []

    def add(level, slide, msg):
        out.append({"level": level, "slide": slide, "message": msg})

    for key in ("audience", "objective", "desired_action"):
        if not str(meta.get(key, "")).strip():
            add("ERROR", 0, f"meta.{key} is empty — the narrative contract must be written before building")

    slides = spec.get("slides") or []
    if not slides:
        add("ERROR", 0, "deck has no slides")
        return out
    width = brand.content_width
    language = str(meta.get("language") or brand.get("copy.default_language", "en"))
    run = 1
    for i, s in enumerate(slides, start=1):
        name = s.get("layout", "bullets")
        if name not in LAYOUTS:
            add("ERROR", i, f"unknown layout '{name}' (available: {', '.join(sorted(LAYOUTS))})")
            continue
        for text in walk_strings(s):
            if EMOJI.search(text):
                add("ERROR", i, f"emoji in text: '{text[:40]}' — use words or a brand icon")
            if TODO.search(text):
                add("WARN", i, f"open placeholder: '{text[:60]}'")
        if not str(s.get("notes", "")).strip():
            add("WARN", i, "no speaker notes")
        title = s.get("title", "")
        if name not in STRUCTURAL and name != "custom" and not s.get("full_bleed"):
            if not title:
                add("ERROR", i, "content slide without a headline")
            else:
                if measure.count_lines(title, brand["type.title"], width) > 1:
                    add("WARN", i, "headline wraps past one line — shorten it rather than shrinking the type")
                if len(title.split()) <= 3 and not re.search(r"[가-힣]{2,}(다|요|니다)$", title):
                    add("WARN", i, f"headline '{title}' reads like a topic label; state the conclusion")
        if name == "bullets" and len(s.get("bullets", [])) > 5:
            add("WARN", i, f"{len(s['bullets'])} bullets; split evenly across two slides")
        if name == "table":
            rows, cols = len(s.get("rows", [])), len(s.get("columns", []))
            if rows > 7 or cols > 7:
                add("WARN", i, f"table {rows}x{cols} exceeds 7x7; split or move detail to an appendix")
            for r, row in enumerate(s.get("rows", []), start=1):
                if len(row) != cols:
                    add("ERROR", i, f"table row {r} has {len(row)} cells, header has {cols}")
        src = s.get("source")
        if name in ("stats", "chart") and not (src.get("text") if isinstance(src, dict) else src):
            add("WARN", i, "numbers without a source line")
        lint_footer(add, i, s, brand, language, width)
        if name == "chart":
            ch = s.get("chart", {}) or {}
            panels = ch.get("panels") or []
            if panels and not 2 <= len(panels) <= 4:
                add("WARN", i, f"{len(panels)} chart panels; use 2–4 in one row, or split the slide")
            for k, p in enumerate(panels or [ch], start=1):
                lint_chart(add, i, p, f"panel {k}: " if panels else "")
            seen = {}
            for p in panels:  # one key serves all panels only if a series keeps its color
                names = tuple(str(ser.get("name")) for ser in p.get("series", []))
                colors = exhibits.series_colors(brand, p.get("type", "column"), len(names),
                                                p.get("series_kind"), p.get("highlight_series"))
                if len(names) > 1 and seen.setdefault(names, colors) != colors:
                    add("WARN", i, "panels draw the same series in different colors; give them the same "
                                   "series_kind and highlight_series")
        if "commentary" in s or "takeaway" in s:
            lint_commentary(add, i, s, name)
        if name == "cards" and len(s.get("cards", [])) > 4:
            add("WARN", i, "more than 4 cards in one row")
        if name == "image":
            p = deck_path.parent / str(s.get("image", ""))
            if not p.exists():
                add("ERROR", i, f"image not found: {s.get('image')}")
            if not s.get("alt"):
                add("WARN", i, "image without alt text")
        if name == "custom":
            p = deck_path.parent / str(s.get("python", ""))
            if not p.exists():
                add("ERROR", i, f"custom renderer not found: {s.get('python')}")
        if name == "diagram":
            ids = {n_.get("id") for n_ in s.get("nodes", [])}
            for e in s.get("edges", []):
                for end in ("from", "to"):
                    if e.get(end) not in ids:
                        add("ERROR", i, f"edge references unknown node '{e.get(end)}'")
        prev = slides[i - 2].get("layout") if i > 1 else None
        run = run + 1 if name == prev and name not in STRUCTURAL else 1
        if run == 3:
            add("WARN", i, f"third '{name}' slide in a row; vary the form unless it is a deliberate series")

    if len(slides) >= 4:
        if slides[0].get("layout") != "cover":
            add("WARN", 1, "multi-slide deck does not start with a cover")
        if slides[-1].get("layout") != "closing":
            add("WARN", len(slides), "multi-slide deck does not end with a closing slide")
    content = [s for s in slides if s.get("layout") not in STRUCTURAL]
    sections = [s for s in slides if s.get("layout") == "section"]
    if len(content) >= 8 and not any(s.get("layout") == "agenda" for s in slides):
        add("WARN", 0, "8+ content slides and no agenda")
    if len(sections) == 1:
        add("WARN", 0, "a single section divider does not divide anything; use two or more, or none")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck")
    ap.add_argument("--brand")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    findings = lint(Path(args.deck), args.brand)
    if args.json:
        print(json.dumps(findings, indent=2, ensure_ascii=False))
    else:
        for f in findings:
            where = f"slide {f['slide']}" if f["slide"] else "deck"
            print(f"{f['level']:5} {where}: {f['message']}")
        errors = sum(f["level"] == "ERROR" for f in findings)
        print(f"{errors} error(s), {len(findings) - errors} warning(s)")
    return 1 if any(f["level"] == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
