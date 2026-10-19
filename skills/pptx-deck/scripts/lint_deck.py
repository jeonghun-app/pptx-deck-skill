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
from deckkit import measure  # noqa: E402
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
        if name in ("stats", "chart") and not s.get("source"):
            add("WARN", i, "numbers without a source line")
        if name == "chart":
            ch = s.get("chart", {})
            if ch.get("type", "column") not in CHARTS:
                add("ERROR", i, f"unsupported chart type '{ch.get('type')}' (available: {', '.join(CHARTS)})")
            n = len(ch.get("categories", []))
            for ser in ch.get("series", []):
                if len(ser.get("values", [])) != n:
                    add("ERROR", i, f"series '{ser.get('name')}' has {len(ser.get('values', []))} values for {n} categories")
            if ch.get("type") in ("pie", "doughnut") and n > 5:
                add("WARN", i, "part-to-whole chart with more than 5 parts; use a bar chart")
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
    return out


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
        print(f"{errors} error(s), {len(findings) - errors} warning(s)")
    return 1 if any(f["level"] == "ERROR" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
