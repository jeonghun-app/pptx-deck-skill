#!/usr/bin/env python3
"""Check a deck spec before building it.

    python scripts/lint_deck.py deck.yaml [--brand brand/brand.yaml] [--json]

ERROR blocks the build (fix it first). WARN needs a decision. INFO is a
suggestion that some organizations decide differently. The checks are the
narrative contract (audience / objective / desired action), headline form,
density limits, evidence, emoji, assets, deck structure and reading structure
(mode, summary, tracker, Korean notation). They do not replace looking at the
rendered slides.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import load_brand, LAYOUTS  # noqa: E402
from deckkit import exhibits, measure, story  # noqa: E402
from deckkit.canvas import CHARTS  # noqa: E402
from deckkit.frameworks import SYMBOLS, is_symbol_cell, normalize_symbol  # noqa: E402

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
    if name not in ("chart", "table", "image", "diagram", "matrix"):
        add("WARN", i, f"commentary has no effect on '{name}' slides (chart, table, image, diagram, matrix)")
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
    measure.set_fonts(brand)
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
    lines_allowed = story.title_lines(brand, meta)
    read = story.mode(meta) == "read"
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
                lines = measure.count_lines(title, brand["type.title"], width, "heading")
                if lines > lines_allowed:
                    limit = "one line" if lines_allowed == 1 else f"{lines_allowed} lines"
                    add("WARN", i, f"headline wraps past {limit} — shorten it rather than shrinking the type")
                if read and len(title.split()) > READ_WORDS:
                    add("WARN", i, f"headline has {len(title.split())} words; reading-mode headlines stay "
                                   f"within about {READ_WORDS} — if it needs more, the slide has two messages")
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
        lint_frameworks(s, name, lambda level, msg, i=i: add(level, i, msg))
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
    lint_story(slides, meta, brand, add)
    return out


READ_WORDS = 25
HANGUL = re.compile("[가-힣]")
PCT_POINT = re.compile(r"%p(?![a-zA-Z])")
PCT_POINT_WORD = re.compile(r"%\s?포인트|퍼센트\s?포인트")
SOURCE_PREFIX = re.compile(r"^\s*(자료|출처|source)\s*[:：]", re.I)


def polite_ending(text: str) -> bool:
    """True for a formal polite ending (~습니다, ~합니다, ~입니다), not for 아니다."""
    t = text.strip().rstrip(".")
    if len(t) < 3 or not t.endswith("니다") or not HANGUL.match(t[-3]):
        return False
    return (ord(t[-3]) - 0xAC00) % 28 == 17  # final consonant ㅂ: 습, 합, 입, 됩 ...


def source_text(src) -> str:
    """Source text of a slide: a string, or the ``text`` of a source object."""
    return str(src.get("text", "")) if isinstance(src, dict) else str(src or "")


def lint_story(slides, meta, brand, add):
    """Reading structure: mode, tracker, summary, bands, measure and Korean notation."""
    m = story.mode(meta)
    if m not in story.MODES:
        add("ERROR", 0, f"meta.mode '{m}' is not one of {', '.join(story.MODES)}")
    sections = story.sections(slides)
    tracker = story.tracker_style(brand, meta)
    if tracker not in story.TRACKERS:
        add("ERROR", 0, f"tracker '{tracker}' is not one of {', '.join(story.TRACKERS)}")
    elif tracker != "none" and len(sections) < 2:
        add("WARN", 0, f"tracker '{tracker}' needs two or more section slides; none is drawn")
        tracker = "none"
    elif tracker == "tabs" and len(sections) > story.MAX_TABS:
        add("WARN", 0, f"{len(sections)} sections are too many tabs; the tracker falls back to dots")
        tracker = "dots"
    content = [(i, s) for i, s in enumerate(slides, start=1) if s.get("layout", "bullets") not in STRUCTURAL]
    measure_chars = brand.get("type.max_measure")
    body = float(brand["type.body"])
    language = str(meta.get("language") or brand.get("copy.default_language", "en"))
    default_label = brand.get("copy.source_label") or ("출처" if language == "ko" else "Source")
    prefixes = {}
    seen_section = False
    with_steps = 0
    for i, s in enumerate(slides, start=1):
        name = s.get("layout", "bullets")
        if name not in LAYOUTS:
            continue  # reported above
        seen_section = seen_section or name == "section"
        if s.get("eyebrow") == "auto":
            if tracker == "tabs" and seen_section:
                add("INFO", i, "eyebrow: auto is not drawn under tracker tabs; the current tab names the section")
            elif not seen_section:
                add("WARN", i, "eyebrow: auto before the first section slide; no eyebrow is drawn")
        if s.get("lead_style") not in (None, "band"):
            add("ERROR", i, f"lead_style '{s.get('lead_style')}' is not supported (use band)")
        elif s.get("lead_style") == "band" and not s.get("lead"):
            add("WARN", i, "lead_style: band without a lead; write the answer as the lead")
        if s.get("next_steps"):
            with_steps += 1
            ns = s["next_steps"]
            items = ns if isinstance(ns, list) else (ns or {}).get("items", [])
            if not 2 <= len(items) <= 4:
                add("WARN", i, f"next_steps has {len(items)} items; keep 2–4")
            if LAYOUTS[name].structural or s.get("full_bleed"):
                add("WARN", i, f"next_steps is ignored on a '{name}' slide without the content frame")
        if name == "summary":
            blocks = s.get("blocks", [])
            if not 2 <= len(blocks) <= 4:
                add("WARN", i, f"summary has {len(blocks)} blocks; use 2–4 (one per section) and split the rest")
            for k, blk in enumerate(blocks, start=1):
                if not isinstance(blk, dict) or blk.get("section") is None:
                    continue
                n = int(blk["section"])
                if not 1 <= n <= len(sections):
                    add("ERROR", i, f"summary block {k} refers to section {n}; the deck has {len(sections)}")
                    continue
                sec = sections[n - 1]
                heading = blk.get("heading")
                if heading and _norm(heading) not in (_norm(sec["title"]), _norm(sec["short"])):
                    add("WARN", i, f"summary block {k} heading '{heading}' differs from section {n} "
                                   f"'{sec['title']}'; repeat the section's wording so readers can find it")
        if measure_chars and name in ("image", "diagram", "code") and s.get("caption"):
            cap = str(s["caption"])
            cpl = measure.chars_per_line(body, brand.content_width)
            if cpl > float(measure_chars) and measure.count_lines(cap, body, brand.content_width) > 1:
                add("WARN", i, f"caption runs over several lines of ~{cpl:.0f} characters across the full "
                               "width; keep it to one line or move the detail into the notes")
        title = str(s.get("title", ""))
        if name not in STRUCTURAL and polite_ending(title):
            add("INFO", i, f"Korean headline ends in ~습니다/~합니다: '{title[:30]}'; headlines default to a "
                           "noun-phrase conclusion or ~다, and ~합니다 is for leads and notes")
        if s.get("source"):
            match = SOURCE_PREFIX.match(source_text(s["source"]))
            label = match.group(1) if match else default_label
            prefixes.setdefault(label.lower(), i)
    texts = [t for s in slides for t in walk_strings(s)]
    if any(PCT_POINT.search(t) for t in texts) and any(PCT_POINT_WORD.search(t) for t in texts):
        add("WARN", 0, "both '%p' and '%포인트' are used for percentage points; pick one (default %p)")
    if len(prefixes) > 1:
        add("WARN", 0, f"source lines use more than one prefix ({', '.join(prefixes)}); "
                       "use one per deck (copy.source_label)")
    if content and with_steps / len(content) > 0.25:
        add("WARN", 0, f"next_steps on {with_steps} of {len(content)} content slides; keep it for the "
                       "pages that close an argument (at most one in four)")
    # a summary restates section conclusions, so it is expected only in a sectioned story
    if len(content) >= 10 and len(sections) >= 2 and not any(s.get("layout") == "summary" for _, s in content):
        add("WARN", 0, f"{len(content)} content slides and no summary; add a summary slide that "
                       "states each section's conclusion")


def _norm(text) -> str:
    return re.sub(r"[^\w]+", " ", str(text)).strip().lower()


def _words(text) -> int:
    return len(measure.strip_markup(str(text)).split())


def lint_frameworks(s, name, add):
    """Checks for matrix, shift, symbol tables, process, cards and stats."""
    if name == "matrix":
        size = s.get("size", 2)
        if size not in (2, 3):
            add("ERROR", f"matrix size {size}; use 2 (2x2) or 3 (3x3)")
            size = 2
        measured = s.get("basis", "qualitative") == "measured"
        if s.get("basis", "qualitative") not in ("qualitative", "measured"):
            add("ERROR", f"matrix basis '{s.get('basis')}'; use qualitative or measured")
        if measured and not s.get("source"):
            add("ERROR", "measured matrix without a source; say where the scores come from")
        for key in ("x", "y"):
            axis = s.get(key) or {}
            if not (axis.get("label") and axis.get("low") and axis.get("high")):
                add("WARN", f"matrix {key} axis needs a label and both poles (low, high)")
            if measured and float(axis.get("max", 1)) <= float(axis.get("min", 0)):
                add("ERROR", f"matrix {key} axis max must be greater than min")
            raw = (s.get("thresholds") or {}).get(key)
            if raw is not None:
                count = len(raw) if isinstance(raw, list) else 1
                if not measured:
                    add("WARN", "matrix thresholds need basis: measured; qualitative cells are equal")
                elif count != size - 1:
                    add("ERROR", f"matrix {key} threshold needs {size - 1} value(s) for a {size}x{size} matrix")
        quadrants = s.get("quadrants") or []
        if len(quadrants) != size * size:
            add("ERROR", f"matrix has {len(quadrants)} quadrants; a {size}x{size} matrix needs {size * size}")
        for n, q in enumerate(quadrants):
            if not (q.get("name") if isinstance(q, dict) else q):
                add("ERROR", f"matrix cell {n} has no name; name every cell")
        lit = sum(1 for q in quadrants if isinstance(q, dict) and q.get("highlight"))
        if lit > 1 and not s.get("highlight_set"):
            add("ERROR", f"{lit} highlighted matrix cells; highlight one (or set highlight_set: true)")
        items = s.get("items") or []
        if len(items) > 20:
            add("WARN", f"{len(items)} matrix items; keep 20 or fewer, or split the matrix")
        per_cell = {}
        for item in items:
            label = item.get("label", item.get("id", ""))
            has_xy = item.get("x") is not None or item.get("y") is not None
            if measured:
                if item.get("x") is None or item.get("y") is None:
                    add("ERROR", f"matrix item '{label}' needs x and y with basis: measured")
            else:
                if has_xy:
                    add("WARN", f"matrix item '{label}' has x/y but the basis is qualitative; "
                        "place it by cell or measure it")
                cell = item.get("cell")
                if not isinstance(cell, int) or not 0 <= cell < size * size:
                    add("ERROR", f"matrix item '{label}' needs a cell from 0 to {size * size - 1}")
                else:
                    per_cell[cell] = per_cell.get(cell, 0) + 1
        for cell, count in per_cell.items():
            if count > 6:
                add("WARN", f"{count} items in matrix cell {cell}; keep 6 or fewer per cell")
    elif name == "shift":
        rows = s.get("rows") or []
        if len(rows) > 6:
            add("WARN", f"{len(rows)} shift rows; keep 3-6")
        for n, row in enumerate(rows, start=1):
            if not str(row.get("to", "")).strip():
                add("ERROR", f"shift row {n} has no 'to' state")
            if not str(row.get("dimension", "")).strip():
                add("WARN", f"shift row {n} has no dimension label")
            a, b = (len(measure.strip_markup(str(row.get(k, "")))) for k in ("from", "to"))
            if min(a, b) and max(a, b) > 2 * min(a, b) and max(a, b) > 20:
                add("WARN", f"shift row {n}: from and to differ in length by more than 2x; "
                    "write both states in the same grammar")
    elif name == "table" and (s.get("symbols") or any(
            isinstance(cell, dict) for row in s.get("rows", []) for cell in row)):
        lint_symbols(s, add)
    elif name == "process":
        steps = s.get("steps") or []
        chevron = s.get("style", "rail") == "chevron"
        if s.get("style", "rail") not in ("rail", "chevron"):
            add("ERROR", f"process style '{s.get('style')}'; use rail or chevron")
        if len(steps) > (6 if chevron else 5):
            add("WARN", f"{len(steps)} process steps; keep at most {6 if chevron else 5}"
                f"{'' if chevron else ' (6 with style: chevron)'}")
        current = s.get("current")
        if current is not None and not (isinstance(current, int) and 0 <= current < len(steps)):
            add("ERROR", f"process current {current} is not a step index (0 to {len(steps) - 1})")
        for row in s.get("rows") or []:
            if len(row.get("cells", [])) != len(steps):
                add("WARN", f"process row '{row.get('label', '')}' has {len(row.get('cells', []))} "
                    f"cells for {len(steps)} steps")
    elif name == "cards":
        cards = s.get("cards") or []
        is_open = s.get("style", "filled") == "open"
        if s.get("style", "filled") not in ("filled", "open"):
            add("ERROR", f"cards style '{s.get('style')}'; use filled or open")
        if len(cards) > (5 if is_open else 4):
            add("WARN", f"more than {5 if is_open else 4} cards in one row"
                f"{'' if is_open else ' (5 with style: open)'}")
        counts = [_words(card.get("heading", "")) for card in cards if card.get("heading")]
        if s.get("numbered") and counts and max(counts) > 2 * min(counts):
            add("WARN", "numbered card headings differ in length by more than 2x; "
                "write them in the same grammar (verb + object)")
    elif name == "stats" and len(s.get("stats") or []) > 9:
        add("WARN", f"{len(s['stats'])} stats; keep at most 9 (a 3x3 grid)")


def lint_symbols(s, add):
    """Symbol tables: one family, every assessed cell filled (na, never blank), a legend."""
    family = s.get("symbols")
    if not family:
        add("ERROR", "table has {s: ...} cells but no 'symbols' family (harvey, check, rag, tier)")
        return
    if family not in SYMBOLS:
        add("ERROR", f"unknown symbols '{family}' (use {', '.join(SYMBOLS)})")
        return
    rows = s.get("rows") or []
    sym_cols = {c for row in rows for c, cell in enumerate(row) if is_symbol_cell(cell)}
    for r, row in enumerate(rows, start=1):
        for c, cell in enumerate(row):
            if c not in sym_cols:
                continue
            if not is_symbol_cell(cell):
                if cell in (None, ""):
                    add("ERROR", f"table row {r}, column {c + 1} is empty; write a symbol or {{s: na}}")
                else:
                    add("WARN", f"table row {r}, column {c + 1} mixes text into a symbol column")
                continue
            if normalize_symbol(family, cell.get("s")) is None:
                add("ERROR", f"table row {r}, column {c + 1}: '{cell.get('s')}' is not a {family} value "
                    f"({', '.join(str(v) for v in SYMBOLS[family])}, na)")
            if family == "rag" and not str(cell.get("label", "")).strip():
                add("WARN", f"table row {r}, column {c + 1}: status without a label; "
                    "say what the status means here")
    if s.get("legend", "auto") is False:
        add("WARN", "symbol table without a legend; readers need it to decode the symbols")


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
        infos = sum(f["level"] == "INFO" for f in findings)
        print(f"{errors} error(s), {len(findings) - errors - infos} warning(s)"
              + (f", {infos} info" if infos else ""))
    return 1 if any(f["level"] == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
