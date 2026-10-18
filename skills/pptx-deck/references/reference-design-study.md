# Studying your organization's template and best decks

Use this when setting up the skill for an organization: turning its official
template and its best existing decks into `brand/brand.yaml` (the numbers) and
`brand/guidelines.md` (the rules that are not numbers). It is not needed for an
everyday one-slide edit.

Extracting text or copying a cover look is not a design study. Each result must
carry **evidence, conditions of use, how to build it, and how to check it**.

When a user has edited a deck you delivered and sent it back, analyse the
before/after difference with [revision-learning.md](revision-learning.md)
instead. Finding common patterns across good decks and interpreting one user's
specific edits are different tasks.

## 0. Rights first

- Study only material your organization owns or is licensed to use: its own
  template, its own published or internal decks, material the user explicitly
  provides for this purpose.
- Never copy third-party content (text, images, diagrams, data, layouts traced
  from someone else's deck) into the skill, and never record identifying details
  of third-party material — file names, authors, clients, page numbers — in
  `brand/`, the references or examples.
- Even for your own decks, keep customer names, figures, employee data and
  commercial claims out of the brand files. Record the *rule*, not the instance.

## 1. Fix the scope

- List the source files with SHA-256, real slide count, slide order and canvas
  size (`sldSz`). Same name ≠ same bytes; many near-identical copies form one
  family — group them so one family does not dominate the observations.
- For PPTX, trace the layouts, masters and theme actually used. For PDF, note
  that only the rendering is available (no stored properties).
- Count separately what you inventoried structurally and what you inspected
  visually. Reading the XML of 300 slides is not reviewing the design of 300
  slides.
- A value that appears often is a *candidate*, not automatically a good rule.

## 2. Draft the measurable part automatically

```sh
python scripts/extract_brand.py template.pptx          # drafts brand.yaml values
python ../pptx-layout-audit/scripts/inspect-layout.py best-deck.pptx --output audit/layout.json
python ../pptx-layout-audit/scripts/deck-craft-lint.py best-deck.pptx --md audit/craft.md
```

`extract_brand.py` proposes canvas, theme colors, fonts, layout names and
placeholder positions from the template. `inspect-layout.py` gives measured
geometry, insets and type sizes of real slides. Treat both as drafts: confirm
each value against the rendered slides (`python scripts/render_deck.py`) and
resolve inherited values before writing them as tokens.

## 3. Choose the analysis perspectives you need

Not every study needs all of them. With several reviewers (subagents, when the
user authorizes delegation), split by perspective:

| Perspective | What to read | What to record | Lands in |
|---|---|---|---|
| Page grid | outer margins, body band, columns, repeated baselines | coordinates, ratios, exceptions | `layout.*` |
| Text content area | shape insets, anchor, paragraph/icon areas | outer vs content vs glyph alignment | guidelines |
| Typography | sizes, fonts, line spacing, CJK line breaks | role hierarchy, density | `type.*`, `fonts.*` |
| Color | fills, text colors, accents, status colors | palette, accent budget, contrast | `colors.*` |
| Shape construction | shape kinds, groups, parts, z-order | reusable build order | guidelines |
| Connectors and layout | ports, lines, branch/merge/return, labels | meaning-preserving layout | guidelines |
| Tables | column split, row height, cell alignment, emphasis | house table style | guidelines |
| Charts | scale, labels, units, annotation | encoding rules, evidence hierarchy | `colors.series`, guidelines |
| Story flow | headline sequence, overview → detail → synthesis, appendix | narrative pattern | guidelines |
| Emphasis | value, area, color, line, repetition vs exception | what to keep, what to remove | guidelines |
| Native build & QA | real application, inheritance, edit behavior | reproducible steps, limits of automation | guidelines |
| Chrome | footer text, logo, page numbers, cover/closing | structural slide rules | `chrome.*`, `backgrounds.*`, `copy.*` |

Give each reviewer a distinct file/slide range, question and report path. Do not
have two reviewers analyse the same source from the same perspective. Only one
reviewer controls the presentation application; others read the shared renders
and the source structure. One person merges the reports into the brand files.

## 4. Turn an observation into a conditional rule

Minimum record per rule (kept in your private study notes, not in the skill):

```text
Source:        file id / SHA-256 / real slide / object id
Observation:   what is placed how, with which properties and relationships
Measurement:   original unit, converted pt; explicit / inherited / computed / unknown
Visual check:  image, application + version, what was inspected
Why it helps:  which reading, comparison or judgment it makes easier
Applies when:  content and purpose where it is used
Counter-case:  where the same look would be wrong
Our build:     how to reproduce it with brand tokens / deckkit / a layout
Check:         stored property, render, meaning or editing behavior
```

What goes into `brand/guidelines.md` is only the last five lines, rewritten as
a plain rule with its reason. Example:

```markdown
### Comparison tables
- Put the recommended option in the rightmost column with an accent cap; the
  reader scans left to right and ends on the recommendation.
- Not for neutral inventories with no recommendation — highlight nothing there.
- Build: deckkit `table(..., highlight_col=...)`; check the cap renders above the header.
```

- A condition, completion criterion or style you added that the source did not
  show is **your improvement** — label it so.
- Do not record an unresolved inherited value as a confirmed token.
- Stored shape bounds alone do not prove where glyphs or curves actually sit.
- A value seen in one deck, or one export glitch, is not a permanent rule.

## 5. Tie visual review to evidence

- Keep the original untouched; open a copy and compare hashes before/after.
- If you extract selected slides, map original slide numbers to the excerpt.
- Keep original layouts, masters and assets; never stretch a preview.
- If you unhide hidden slides to study them, record that.
- Record application and version, possible font substitution, PDF conversion.
- Review one image at a time, at most 1280×800 px / ~200 KB; write findings and
  open questions down at least every four slides.

A shared render does not mean every reviewer looked at that slide. Distinguish
rendered, actually viewed, and structure-only slides. Clipping caused by your
conversion is not the original author's mistake.

## 6. Fold the result into the brand

- Numbers → `brand/brand.yaml` (canvas, fonts, type scale, colors, layout grid,
  chrome, backgrounds, copy, icons, template layout mapping).
- Rules with conditions → `brand/guidelines.md`, grouped by topic (voice and
  terminology, approved slide patterns, table/chart/diagram house style,
  required disclaimers, structural slides).
- General craft that is not organization-specific stays in these references;
  do not duplicate it into guidelines.
- Keep source lists and detailed analyses in your private study notes, outside
  the skill. Examples in guidelines are newly written and marked illustrative.

When guidelines grow, remove duplicates, conflicts and dead links in the same
pass. Keep the differences between presented and read decks, and between native
objects and embedded images.

Finish by building a small comparison, diagram and table with the new profile
(`python scripts/build_deck.py deck.yaml -o out/deck.pptx`), render it, and run
`python scripts/lint_deck.py deck.yaml` and the craft lint with
`--brand brand/brand.yaml`. Separate automated checks from aesthetic judgment.
Measure the study by the quality of reusable decisions and checks it produced,
not by reviewer count or document length.
