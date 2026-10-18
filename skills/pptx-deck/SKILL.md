---
name: pptx-deck
description: >-
  Plan, build and QA native, editable PowerPoint decks (PPTX) in your
  organization's own design. PLAN (deck.yaml with audience, objective and
  final copy) → BUILD (python-pptx generator driven by a brand profile and an
  optional company template) → QA (spec lint, rendered contact sheet, layout
  audit). Use for any request to create, rewrite or restyle a presentation,
  slide deck, PPT or PPTX, or to capture a company template as a reusable brand.
---

# pptx-deck

Turn a presentation story into a native PowerPoint file that looks like it came
from your organization: every color, font, position and slide pattern comes
from the **brand profile**, not from the model's taste. Text stays editable,
charts are native charts, diagrams are native shapes with glued connectors.

Paths below are relative to this skill's directory. Run scripts with a Python
that has `python-pptx`, `PyYAML` and `Pillow` (`pip install -r requirements.txt`
at the repository root). Rendering needs LibreOffice and Poppler.

## The brand profile comes first

| File | Holds |
|---|---|
| `brand/brand.yaml` | Measurable design: canvas, fonts, type scale, colors, grid, headline band, footer, logo, backgrounds, icon library, optional company template |
| `brand/guidelines.md` | Everything that is not a number: voice, vocabulary, required slides, approved patterns, diagram conventions, exceptions, rules learned from revisions |
| `brand/assets/` | Logo, template `.pptx`, background images, icons the organization licenses |

**Precedence:** explicit request in the conversation > the company template and
`brand.yaml` > `brand/guidelines.md` > the defaults in `references/`.

At the start of every deck task, read `brand/brand.yaml` and
`brand/guidelines.md`. If the user supplies a different brand file, pass it
with `--brand`.

### Capturing a company design

When the user provides a company template or a representative deck:

```
python scripts/extract_brand.py company-template.pptx -o brand/brand.yaml --report brand/extract-report.md
```

This copies the template into `brand/assets/`, maps its layouts to the slide
roles (cover, section, content, closing, blank), and drafts colors, fonts,
title band and body area from the theme and placeholders. Then:

1. Show the report and confirm the guesses the script cannot know: which theme
   color is the accent, which layout is the content layout, whether headlines
   fit one line at the master's title size.
2. Study the organization's best decks for the rules that are not numbers and
   write them into `brand/guidelines.md` — method in
   [references/reference-design-study.md](references/reference-design-study.md).
3. Build the sample deck with the new brand and review the contact sheet
   before using it for real work.

Without a template the skill draws its own chrome (background, headline band,
footer, logo) from `brand.yaml`; with a template the masters supply backgrounds,
logos and placeholders, and the skill fills them.

## What to read when

| Reference | When |
|---|---|
| [deck-format.md](references/deck-format.md) | Before writing the plan — the `deck.yaml` schema |
| [layouts.md](references/layouts.md) | Choosing a layout by content shape; every key per layout |
| [brand-profile.md](references/brand-profile.md) | Editing `brand.yaml`; what each token controls; template mode |
| [composition.md](references/composition.md) | Structuring the story: conclusion first, headlines as the storyline, one focus, density limits |
| [writing.md](references/writing.md) | Writing any slide text; Korean-language deck conventions |
| [reader-craft.md](references/reader-craft.md) | Reading layers, panel relationships, spotlight and (1/N) sequences, emphasis budget |
| [visuals.md](references/visuals.md) | Deciding between table, chart, diagram and image before filling slots |
| [data-viz.md](references/data-viz.md) | Any numeric comparison; native chart rules |
| [diagrams.md](references/diagrams.md) | Relationships, flows and boundaries with the `diagram` layout |
| [architecture-diagrams.md](references/architecture-diagrams.md) | System and architecture diagrams |
| [decision-diagrams.md](references/decision-diagrams.md) | Diagrams that support a decision: trees, convergence, criteria → choice |
| [analytical-methods.md](references/analytical-methods.md) | Proposals, diagnostics, strategy and executive decision decks |
| [analytical-patterns.md](references/analytical-patterns.md) | Construction recipes for analytical pages |
| [layout-craft.md](references/layout-craft.md) | Margins vs gaps vs insets, alignment, proportions, structural slides |
| [patterns.md](references/patterns.md) | Gantt, status dashboard, stage rail, co-branding, migrating old decks |
| [native-construction.md](references/native-construction.md) | Custom slides in python-pptx: units, text frames, groups, connectors, tables |
| [images.md](references/images.md) | Screenshots, photos, images from an existing PPTX |
| [revision-learning.md](references/revision-learning.md) | Learning from a deck a person edited |
| [qa.md](references/qa.md) | The full QA procedure |
| `../pptx-layout-audit/SKILL.md` | Deck-wide alignment, spacing, connector and editability review |

---

## Phase 1 — PLAN

A thin plan produces a thin deck. Spend the time here.

### 1a. Collect the evidence first

Before inventing anything, ask for what already exists:

> "Is there material this presentation should be based on — notes, an existing
> deck (.pptx), documents, links, screenshots, data? Share paths or links and I
> will read them and build the plan from them."

Actually read what you receive. From an existing PPTX, extract text, notes and
images with python-pptx ([images.md](references/images.md)). Mine exact numbers
with their sources, real quotes with their speakers, product names, diagrams
worth redrawing. Prefer the user's own wording over marketing copy. When sources
contradict each other, ask — do not silently pick one.

### 1b. Ask what cannot be inferred

Ask in one batch:

- Audience and seniority (executives / practitioners / mixed)
- **Objective**: what changes for the audience, and what they should do afterwards
- Event, date, presenter name and role (they go on the cover verbatim)
- Language (proper nouns keep their original spelling)
- Target length (slide count or speaking time)
- Missing numbers, screenshots or logos: request them, or leave `TODO:` —
  **never fabricate**
- Choices with two good answers (table vs chart, one dense slide vs two) —
  present them with a recommendation

### 1c. Structure the story

- Plan the cover, section dividers and closing together with the body. In a
  multi-slide deck, put dividers at real chapter changes and end with the
  closing slide; all of them count toward the requested length.
- Agenda only for 8+ content slides or 3+ chapters.
- **Headlines state the conclusion.** "Architecture overview" ✗ →
  "Requests pass through only three layers" ✓. Topic labels belong only on
  agenda and section slides.
- Read [composition.md](references/composition.md); for proposals, diagnostics
  and strategy, also [analytical-methods.md](references/analytical-methods.md).

### 1d. Choose layouts by content shape

[layouts.md](references/layouts.md) maps content shape → layout. Do not pick in
catalog order. **Decide the representation first** with
[visuals.md](references/visuals.md):

- the *difference* between numbers is the point → `chart`
- readers look *values* up → `table` (≤ 7 rows × 7 columns)
- boundaries, branches, multi-step connections → `diagram`
- a few representative numbers → `stats` with a source
- defined stages with a current position → `process`; dates → `timeline`
- nothing fits → `custom` with deckkit primitives, using brand tokens only

Without this step everything collapses into cards and paragraphs. If the
original was a diagram and no layout fits yet, leave an explicit `TODO:` —
never quietly turn it into text.

Variation rules: no layout three times in a row without a reason (a deliberate
parallel series is fine); every slide has one meaningful visual structure or a
deliberate text composition; no decorative icons or shapes that explain nothing;
one message per slide, carried by the headline.

### 1e. Write the plan file

Write `<name>.deck.yaml` following [deck-format.md](references/deck-format.md).
`meta.audience`, `meta.objective` and `meta.desired_action` are mandatory — the
linter blocks the build without them. Every slot holds final copy (not a
draft), every number has a source, every slide has speaker `notes` the presenter
can say aloud.

**Self-check before showing it:** read only the headlines top to bottom. They
must tell the story and reach the objective on their own. Cut or rethink any
slide that does not serve the objective.

```
python scripts/lint_deck.py <name>.deck.yaml
```

### 1f. Get approval (stop here)

Show the file path and a one-line summary per slide (number · layout ·
headline). List open `TODO:` items and every decision you made on the user's
behalf. **Wait for approval or edits** — unless the user said to go ahead.

When the user edits the `.deck.yaml` and asks to rebuild, build **what the file
says**, not what the conversation said.

---

## Phase 2 — BUILD

```
python scripts/build_deck.py <name>.deck.yaml -o out/<name>.pptx [--brand brand/brand.yaml]
```

The builder places every element from brand tokens and writes
`out/<name>.build.json` with warnings: wrapped headlines, text that may
overflow its box, content below `layout.body_bottom`, missing notes, assets or
icons. Treat every `ERROR` as a build failure.

When something does not fit, **split the slide — do not shrink the type**.
Split evenly (4 bullets → 2 + 2, not 3 + 1), keep a subheading with its
content, keep comparison columns and split the rows.

Custom slides (`layout: custom`) are Python files with
`render(canvas, spec, ctx, top)`; use the canvas primitives (`text`, `box`,
`line`, `connect`, `image`, `table`, `chart`) and brand tokens only — see
`examples/decks/custom/gantt.py` and
[native-construction.md](references/native-construction.md).

Never:
- literal colors, fonts or sizes outside the brand profile
- text below `type.min`
- bold headlines unless the brand sets `type.heading_bold: true`
- emoji — use words, or icons from the brand icon library
  (`python scripts/find_icon.py <keyword>`)
- moving the headline band per slide; it is fixed by `layout.*`
- hand-editing the generated PPTX and leaving `deck.yaml` behind

---

## Phase 3 — QA (mandatory)

Follow [qa.md](references/qa.md). In short:

```
python scripts/lint_deck.py <name>.deck.yaml                     # spec: ERROR 0
python scripts/build_deck.py <name>.deck.yaml -o out/<name>.pptx  # build warnings: ERROR 0
python scripts/render_deck.py out/<name>.pptx                    # PNGs + contact.png
python ../pptx-layout-audit/scripts/deck-craft-lint.py out/<name>.pptx --brand brand/brand.yaml
```

**Look at the contact sheet and at each slide.** Scripts passing does not make
a deck presentable. Check: clipped or overflowing text, a lone word on a
headline's last line, overlapping elements, content in the footer band,
uneven sibling gaps, low contrast, leftover `TODO:`, a slide crowded on one
side, unexplained layout repetition.

Fix → rebuild → re-render → look again, until clean. Then report what you
checked, what you fixed, and what you could not verify (for example,
PowerPoint-specific rendering when only LibreOffice was available, or fonts
substituted on the render machine).

For a deck-wide alignment and editability review, use the
`pptx-layout-audit` skill.

---

## Editing an existing deck

- **Built with this skill:** edit `deck.yaml` (or the custom renderer) and
  rebuild. Keep the plan as the source of truth.
- **Any other PPTX:** read it with python-pptx, rebuild it as a `deck.yaml` in
  the brand (restyling), or make targeted edits with python-pptx while
  preserving its masters (small fixes). Say which approach you take.
- **A person edited a generated deck:** compare original and edited versions
  and record reusable rules in `brand/guidelines.md` —
  [revision-learning.md](references/revision-learning.md).
