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
