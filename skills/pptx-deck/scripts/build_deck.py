#!/usr/bin/env python3
"""Build a native PPTX from a deck spec.

    python scripts/build_deck.py deck.yaml -o out/deck.pptx [--brand brand/brand.yaml]

Runs the spec lint first and stops on a lint ERROR (``--no-lint`` skips it).
Writes the PPTX and ``<out>.build.json`` with layout warnings (overflow,
wrapped headlines, missing notes or assets). Exit code 1 when any ERROR is found.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deckkit import build  # noqa: E402
from lint_deck import lint  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("deck", help="deck spec (YAML)")
    ap.add_argument("-o", "--output", help="output .pptx (default: out/<deck name>.pptx)")
    ap.add_argument("--brand", help="brand profile (default: meta.brand in the deck, else the skill's brand/brand.yaml)")
    ap.add_argument("--no-lint", action="store_true", help="skip the spec lint (not recommended)")
    args = ap.parse_args()
    deck = Path(args.deck)
    if not args.no_lint:
        errors = [f for f in lint(deck, args.brand) if f["level"] == "ERROR"]
        for f in errors:
            where = f"slide {f['slide']}" if f["slide"] else "deck"
            print(f"ERROR {where}: {f['message']}")
        if errors:
            print("spec lint failed; fix the deck spec (python scripts/lint_deck.py for all findings)")
            return 1
    out = Path(args.output) if args.output else deck.parent / "out" / (deck.stem.replace(".deck", "") + ".pptx")
    report = build(deck, out, args.brand)
    errors = [w for w in report["warnings"] if w["level"] == "ERROR"]
    print(f"built {report['output']} — {report['slides']} slides, brand: {report['brand']}")
    for w in report["warnings"]:
        where = f"slide {w['slide']}" if w["slide"] else "deck"
        print(f"  {w['level']:5} {where}: {w['message']}")
    if not report["warnings"]:
        print("  no layout warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
