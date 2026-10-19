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
from deckkit import measure, story  # noqa: E402
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
    lines_allowed = story.title_lines(brand, meta)
    read = story.mode(meta) == "read"
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
                lines = measure.count_lines(title, brand["type.title"], width)
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
    if len(content) >= 10 and not any(s.get("layout") == "summary" for _, s in content):
        add("WARN", 0, f"{len(content)} content slides and no summary; add a summary slide that "
                       "states each section's conclusion")


def _norm(text) -> str:
    return re.sub(r"[^\w]+", " ", str(text)).strip().lower()


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
