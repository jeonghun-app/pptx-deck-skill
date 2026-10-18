#!/usr/bin/env python3
"""Search the brand icon library (brand.yaml `icons.path`).

    python scripts/find_icon.py database [storage ...] [--brand brand/brand.yaml]

Prints matching icon names (usable as `icon:` in deck.yaml) and paths. Every
word must appear in the file path. Use only icons your organization licenses.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import load_brand  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("words", nargs="+")
    ap.add_argument("--brand")
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()
    brand = load_brand(args.brand)
    root = brand.path("icons.path")
    if not root or not root.exists():
        print("no icon library configured: set icons.path in brand.yaml to a folder of PNG/SVG icons")
        return 1
    formats = {f".{f.lower()}" for f in brand.get("icons.formats", ["png", "svg"])}
    words = [w.lower() for w in args.words]
    hits = [p for p in root.rglob("*") if p.suffix.lower() in formats
            and all(w in str(p.relative_to(root)).lower() for w in words)]
    hits.sort(key=lambda p: (len(p.name), str(p)))
    for p in hits[: args.limit]:
        print(f"{p.stem:40} {p.relative_to(root)}")
    if not hits:
        print("no match; try a shorter or more general word")
    elif len(hits) > args.limit:
        print(f"... {len(hits) - args.limit} more (use --limit)")
    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main())
