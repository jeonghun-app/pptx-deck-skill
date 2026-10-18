# QA — mandatory for every deck

A deck that has not been looked at is not finished. QA has four steps; each
proves something different, and none replaces another.

## 1. Content QA — against the plan

- Read the headlines alone, top to bottom: do they tell the story and reach
  `meta.objective`? Does the last content slide ask for `meta.desired_action`?
- Every number has a source line; every quote and customer name is approved for
  use; nothing was invented to fill a slot.
- No `TODO:` left (or each remaining one is reported to the user).
- Speaker notes exist on every slide and read as speech.
- Brand guidelines: vocabulary, required slides, confidentiality label.

## 2. Spec QA

```
python scripts/lint_deck.py <name>.deck.yaml [--brand brand/brand.yaml]
```

ERROR must be 0. Read every WARN and either fix it or say why it stands
(rules: [deck-format.md](deck-format.md)).

## 3. Build QA

```
python scripts/build_deck.py <name>.deck.yaml -o out/<name>.pptx
```

The builder estimates text size against each box and reports wrapped
headlines, possible overflow, content below `layout.body_bottom`, missing
icons, images and notes (also in `out/<name>.build.json`). The estimate is
deliberately cautious but it is not a renderer: a clean build still needs step 4.

For a structural and design-craft review of the PPTX itself:

```
python ../pptx-layout-audit/scripts/deck-craft-lint.py out/<name>.pptx --brand brand/brand.yaml --md audit/craft.md
python ../pptx-layout-audit/scripts/inspect-layout.py out/<name>.pptx --output audit/layout.json
```

The first reports minimum size, contrast, off-brand colors and fonts, density,
footer clearance and mismatched numbers; the second inventories geometry and
verifies explicit alignment contracts.

## 4. Visual QA — look at it

```
python scripts/render_deck.py out/<name>.pptx      # out/<name>.render/slide-NN.png + contact.png
```

Open `contact.png` first for rhythm across the deck, then each slide at full
size. Look for:

- clipped, overflowing or overlapping text; text touching a box edge
- a single word alone on a headline's last line (rewrite the sentence)
- content in the footer band; a body pushed to one side
- uneven gaps between siblings; misaligned edges that should share a line
- connectors crossing labels or nodes; arrowheads on the wrong end
- low contrast (small muted text, text on images)
- more than one focal point; more than one accent on a slide
- the same layout repeated without reason; a slide much denser than its neighbors
- placeholders, `TODO:`, sample text left behind
- in template mode: template placeholders left empty or duplicated, titles that
  wrap in the template's title size

LibreOffice renders approximately: missing fonts are substituted and line
breaks can differ. Install the brand fonts on the render machine. When
PowerPoint is available, open the final file there too, and say in the report
which application you checked.

## Repeat

Fix the source (`deck.yaml`, the custom renderer or the brand), rebuild,
re-render, look again — until clean. Never patch the generated PPTX by hand
and leave the source behind.

## Report

Say what you checked, what you fixed, what remains (accepted warnings and why),
and what you could not verify (application, fonts, data you did not have).
