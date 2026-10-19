#!/usr/bin/env bash
# Rebuild the example decks and README previews in docs/ from the sample specs.
# Needs the Python deps, LibreOffice and Poppler. Run after changing layouts or brands.
set -euo pipefail
root="$(cd "$(dirname "$0")" && pwd)"
py="${PYTHON:-python3}"
skill="$root/skills/pptx-deck"
out="$root/docs/examples"; img="$root/docs/images"; tmp="$(mktemp -d)"
mkdir -p "$out" "$img/slides"
"$py" "$skill/scripts/build_deck.py" "$skill/examples/decks/sample.deck.yaml" -o "$out/sample-neutral.pptx"
"$py" "$skill/scripts/build_deck.py" "$skill/examples/decks/sample.deck.yaml" \
  --brand "$skill/examples/brands/warm-editorial/brand.yaml" -o "$out/sample-warm-editorial.pptx"
"$py" "$skill/scripts/build_deck.py" "$skill/examples/decks/ko-sample.deck.yaml" -o "$out/ko-sample.pptx"
for feature in exhibits frameworks story; do
  "$py" "$skill/scripts/build_deck.py" "$skill/examples/decks/$feature.deck.yaml" -o "$out/$feature.pptx"
done
rm -f "$out"/*.build.json
for deck in sample-neutral sample-warm-editorial ko-sample exhibits frameworks story; do
  "$py" "$skill/scripts/render_deck.py" "$out/$deck.pptx" --out "$tmp/$deck" --dpi 100
done
"$py" - "$tmp" "$img" <<'PY'
import sys
from PIL import Image
tmp, img = sys.argv[1], sys.argv[2]
pick = {"sample-neutral": [1, 3, 5, 6, 10, 11, 15, 16], "sample-warm-editorial": [1, 10, 11, 19],
        "ko-sample": [1, 2, 3, 4], "exhibits": [5, 10, 11, 12, 14, 18],
        "frameworks": [5, 9, 13, 15, 18, 21], "story": [2, 5, 6, 9]}
for deck, nums in pick.items():
    for n in nums:
        im = Image.open(f"{tmp}/{deck}/slide-{n:02d}.png").convert("RGB")
        im.thumbnail((1200, 1200))
        im.save(f"{img}/slides/{deck}-{n:02d}.png", optimize=True)
    sheet = Image.open(f"{tmp}/{deck}/contact.png").convert("RGB")
    sheet.thumbnail((1600, 1600))
    sheet.save(f"{img}/{deck}-contact.png", optimize=True)
PY
rm -rf "$tmp"
echo "examples rebuilt in docs/"
