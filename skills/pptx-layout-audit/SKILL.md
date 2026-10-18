---
name: pptx-layout-audit
description: Audit and correct slide layout in a PowerPoint deck — text alignment, spacing, insets, nested shapes, connector routing, design craft (minimum size, contrast, accent budget, density) and native editability. Use for a requested deck-wide layout review or a concrete layout defect; works on any PPTX, with brand-aware checks when a brand profile is supplied.
---

# PPTX Layout Audit

Review the deck against its actual rendered output. Preserve its story, evidence,
active template and editable content. A layout review does not authorize
publishing, sending or deploying anything.

## Choose the review scope

- Complete review: [orchestration procedure](references/layout-review.sop.md).
- Text, table cells and alignment: [typography](references/typography.sop.md).
- Connectors, nodes and nested boundaries: [diagrams](references/diagrams.sop.md).
- PPTX structure, application output and editability:
  [native output](references/native-output.sop.md).

A small defect may need only one role. A full review needs slide coverage, not a
fixed number of reviewers. Delegate roles to subagents only when the user (or
applicable instructions) authorizes delegation; otherwise run the same roles
sequentially and say so in the report.

## Shared decisions

1. Establish the semantic role before choosing alignment. Long explanations and
   comparable labels usually share a left edge; short symmetric node labels may
   be centered; comparable magnitudes share a right or decimal edge.
   Identifiers, dates and phone numbers are not magnitudes merely because they
   contain digits. Record deliberate exceptions.
   Compare paragraph alignment, the text box within its owner, and the whole
   block within its column separately. A left-aligned short text box can be
   centered on its node without changing its paragraph properties.
2. Measure the **content box**, not just the outer shape. Account for border,
   text inset, icon column, scope heading, line spacing and rendered glyph
   bounds. Inches, points and EMU are different units.
   See [measurement and finding contracts](references/contracts.md).
3. Correct the source (deck.yaml or the deckkit build script), then rebuild.
   Do not hand-patch the generated PPTX or a preview image while the source stays
   wrong. Shorten needless copy or redistribute space before reducing readable type.
4. Distinguish a drawing's meaning from its appearance: edge direction, node
   ownership, return paths and verified/pending states survive visual cleanup.
5. Structural checks, text extraction and visual inspection prove different
   things. Save evidence for each. A LibreOffice render is evidence for
   LibreOffice, not a PowerPoint test; label which application you used.

## Evidence and tools

Run shell commands for local inspection and rebuilding, view rendered PNGs one
at a time, and delegate to subagents only when the user authorizes it.
Paths below are relative to this skill's directory.

Render for visual review (LibreOffice → per-slide PNG + contact sheet):

```sh
python ../pptx-deck/scripts/render_deck.py deck.pptx
```

Read-only structural inventory and explicit contracts:

```sh
python scripts/inspect-layout.py deck.pptx --output audit/layout.json \
  [--contracts audit/contracts.json]
python -B scripts/test_inspect_layout.py        # regression suite
```

`--contracts` verifies declared alignment, gap, text-alignment, padding and
directed-edge constraints. The script reports unsupported transformations
instead of silently certifying them. It does not judge optical alignment, glyph
fit, intended diagram semantics or overall aesthetics.

Without contracts the result is an inventory with status `inspected`, not a
layout approval. Exit codes: `0` inventory done / all declared checks passed,
`1` demonstrated structural or contract failure, `2` input or I/O error, `3`
unverified checks without a demonstrated failure. Read the JSON before
describing the outcome. Contracts select top-level native IDs; the recursive
group inventory does not certify nested text geometry, merged cells, inherited
formatting or node-drag behavior.

Reader-facing design lint (read-only):

```sh
python scripts/deck-craft-lint.py deck.pptx --md audit/craft.md \
  [--brand ../pptx-deck/brand/brand.yaml] [--mode read]
python -B scripts/test_deck_craft_lint.py       # regression suite
```

It reports off-canvas objects, leftover template wording, minimum text size,
small-text contrast, light text on fills, chromatic families per slide, density,
footer clearance, unit and source-notation mixing, distorted circles, headline
numbers missing from the slide and typed chart labels that disagree with data.
With `--brand` it reads `type.min`, `layout.body_bottom`, `colors.*` and
`fonts.*` from the brand profile and also flags off-palette colors and
off-brand fonts; without PyYAML it falls back to neutral defaults and records
that limitation. Exit `1` means at least one `fail` finding. Inherited sizes and
theme colors are not judged.

For building rather than reviewing, use the `pptx-deck` skill
(`python ../pptx-deck/scripts/build_deck.py deck.yaml -o out/deck.pptx`) and its
references. Plan section dividers at real topic transitions and keep the closing
slide as the last physical page, within the requested slide count, unless the
user or the company template requires otherwise. Check that sequence in the deck
spec, the native slide order and the rendered output; the inspector cannot
approve the narrative or decide whether a divider is appropriate.

Review at most four previews per recorded checkpoint, one image at a time, each
no larger than 1280×800 px and about 200 KB. Record slide coverage and artifact
hashes. Repeat a reviewed batch after a relevant change or unresolved finding.

## Completion

Deliver the requested native PPTX. The review record names the final artifact
hash, each role's coverage, resolved findings, accepted exceptions and
unverified environments. An automated PASS is not a claim of perfect design.
Disclose material font substitution or untested application behavior.
