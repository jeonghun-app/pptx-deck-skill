# pptx-deck-skill

[한국어](README.ko.md) · **Version 0.2.0** · [Changelog](CHANGELOG.md) · [Releases](https://github.com/jeonghun-app/pptx-deck-skill/releases)

Agent skills that turn a presentation story into a **native, editable
PowerPoint file in your organization's own design**. The model plans the story;
your brand profile decides every color, font, position and slide pattern.

- **`pptx-deck`** — PLAN → BUILD → QA. A plan file (`deck.yaml`) with audience,
  objective and final copy is built into PPTX with python-pptx, rendered to a
  contact sheet and checked.
- **`pptx-layout-audit`** — deck-wide review of alignment, spacing, connectors,
  minimum sizes, contrast and editability for any PPTX.

![Sample deck, neutral default brand](docs/images/sample-neutral-contact.png)

See [Examples](#examples) for the slides at full size and the PPTX files.

## What's new in 0.2

- **Exhibits that carry their own point.** Structured footers (notes, question,
  base, n, date, source), highlights in one accent with grey context, line end
  labels, `waterfall`, estimate styling, annotations computed from the data
  (reference lines, bands, callouts, deltas), a `commentary` column beside any
  exhibit, and `panels` of small multiples.
- **Framework layouts.** `matrix` (2×2 / 3×3), symbol tables (Harvey balls,
  check marks, status), `shift` (from → to), chevron `process` with aligned rows,
  numbered open `cards`, and `stats` grids of up to nine values.
- **Reading structure.** An executive `summary` built from the section
  conclusions, a section tracker, a reading mode with two-line headlines,
  answer bands for question headlines, and `next_steps` bands.
- **Measured, not guessed.** Text is measured with the fonts the deck renders
  in, so wrap and overflow warnings match the slides.
- **Korean conventions.** Noun-phrase headlines, `%p`, unit and source labels.

Upgrading from 0.1: existing deck specs and brand files build without
changes. A few defaults changed visibly (line end labels, a reading-width cap,
accent tints for several series on the default palette); each has an opt-out
listed in the [changelog](CHANGELOG.md).

## Why

Generated slides usually look generated: arbitrary colors, bold everything,
cards for every idea, text that overflows. This skill separates the two jobs:

- **Story and craft** live in the skill: conclusion headlines, one message per
  slide, choosing table vs chart vs diagram, density limits, connector
  semantics, writing rules, QA.
- **Design** lives in *your* files: `brand/brand.yaml` (tokens and optional
  company template) and `brand/guidelines.md` (voice, vocabulary, approved
  patterns, exceptions). Swap them and the same deck rebuilds in another brand.

Output is native PowerPoint: real text boxes, native tables and charts with
embedded data, diagrams as shapes with glued connectors, speaker notes on every
slide.

## Examples

All decks below are built by the generator from the specs in
[`skills/pptx-deck/examples/decks/`](skills/pptx-deck/examples/decks) — no hand
editing. Download a PPTX and open it in PowerPoint, Keynote or Google Slides to
check that every element is editable. GitHub cannot preview PPTX, so the images
below are LibreOffice renders of the same files.

### 1. Proposal deck — neutral default brand

[⬇ sample-neutral.pptx](docs/examples/sample-neutral.pptx) · spec:
[`sample.deck.yaml`](skills/pptx-deck/examples/decks/sample.deck.yaml) · 19 slides

| | |
|---|---|
| ![cover](docs/images/slides/sample-neutral-01.png) | ![summary](docs/images/slides/sample-neutral-03.png) |
| `cover` | `summary` — one block per section, the ask in the bar |
| ![stats](docs/images/slides/sample-neutral-05.png) | ![chart](docs/images/slides/sample-neutral-06.png) |
| `stats` — numbers with a source line | `chart` — native chart, one highlighted bar, takeaway beside it |
| ![diagram](docs/images/slides/sample-neutral-10.png) | ![table](docs/images/slides/sample-neutral-11.png) |
| `diagram` — native shapes, glued connectors, a boundary | `table` — recommended column highlighted |
| ![image](docs/images/slides/sample-neutral-15.png) | ![cards](docs/images/slides/sample-neutral-16.png) |
| `image` — screenshot with caption and alt text | `cards` — one highlighted |

<details>
<summary>All 19 slides</summary>

![contact sheet](docs/images/sample-neutral-contact.png)

</details>

### 2. The same deck with another brand profile

[⬇ sample-warm-editorial.pptx](docs/examples/sample-warm-editorial.pptx) · brand:
[`warm-editorial/brand.yaml`](skills/pptx-deck/examples/brands/warm-editorial/brand.yaml)
(about 40 lines: colors, a serif heading font, rounded panels, no headline rule,
a footer label). The spec is unchanged.

| | |
|---|---|
| ![cover](docs/images/slides/sample-warm-editorial-01.png) | ![diagram](docs/images/slides/sample-warm-editorial-10.png) |
| ![table](docs/images/slides/sample-warm-editorial-11.png) | ![closing](docs/images/slides/sample-warm-editorial-19.png) |

<details>
<summary>All 19 slides</summary>

![contact sheet](docs/images/sample-warm-editorial-contact.png)

</details>

### 3. Korean deck with a custom slide

[⬇ ko-sample.pptx](docs/examples/ko-sample.pptx) · spec:
[`ko-sample.deck.yaml`](skills/pptx-deck/examples/decks/ko-sample.deck.yaml) · the
Gantt is a `custom` slide written with deckkit primitives
([`custom/gantt.py`](skills/pptx-deck/examples/decks/custom/gantt.py)).

| | |
|---|---|
| ![cover](docs/images/slides/ko-sample-01.png) | ![stats](docs/images/slides/ko-sample-02.png) |
| ![cards](docs/images/slides/ko-sample-03.png) | ![gantt](docs/images/slides/ko-sample-04.png) |

### 4. Exhibits — charts that carry their own point

[⬇ exhibits.pptx](docs/examples/exhibits.pptx) · spec:
[`exhibits.deck.yaml`](skills/pptx-deck/examples/decks/exhibits.deck.yaml)

| | |
|---|---|
| ![footer](docs/images/slides/exhibits-05.png) | ![end labels](docs/images/slides/exhibits-10.png) |
| Structured footer: notes, then question · base · n · date, then source | Line end labels, a reference line, estimates dashed and marked |
| ![waterfall](docs/images/slides/exhibits-11.png) | ![deltas](docs/images/slides/exhibits-12.png) |
| `waterfall` with a commentary column | Deltas computed from the data, never typed |
| ![panels](docs/images/slides/exhibits-14.png) | ![commentary](docs/images/slides/exhibits-18.png) |
| `panels` — small multiples on one scale and baseline | `commentary` beside a diagram |

### 5. Frameworks — decisions on one page

[⬇ frameworks.pptx](docs/examples/frameworks.pptx) · spec:
[`frameworks.deck.yaml`](skills/pptx-deck/examples/decks/frameworks.deck.yaml)

| | |
|---|---|
| ![matrix](docs/images/slides/frameworks-05.png) | ![symbols](docs/images/slides/frameworks-09.png) |
| `matrix` — named quadrants, poles on both axes, placement basis tagged | Symbol table — Harvey balls with a legend and a distinct n/a |
| ![shift](docs/images/slides/frameworks-13.png) | ![chevron](docs/images/slides/frameworks-15.png) |
| `shift` — from → to, one dimension per row | `process` chevrons with aligned rows and a "now" marker |
| ![open cards](docs/images/slides/frameworks-18.png) | ![stats grid](docs/images/slides/frameworks-21.png) |
| Numbered open columns for recommendations | `stats` grid of up to nine values |

### 6. Story — a reading deck

[⬇ story.pptx](docs/examples/story.pptx) · spec:
[`story.deck.yaml`](skills/pptx-deck/examples/decks/story.deck.yaml) · `meta.mode: read`
(two-line headlines in a fixed band) with a dot tracker

| | |
|---|---|
| ![summary](docs/images/slides/story-02.png) | ![tracker](docs/images/slides/story-05.png) |
| Executive summary built from the section conclusions | Section tracker, `eyebrow: auto`, a capped reading measure |
| ![band](docs/images/slides/story-06.png) | ![next steps](docs/images/slides/story-09.png) |
| A question headline with its answer in a band | A `next_steps` band that closes the argument |

Rebuild the examples after changing layouts or brands: `./build-examples.sh`.

## Install

Requirements: Python 3.11+, and for visual QA LibreOffice (`soffice`) and
Poppler (`pdftoppm`).

**As a Claude Code plugin**

```
/plugin marketplace add jeonghun-app/pptx-deck-skill
/plugin install pptx-deck@pptx-deck-skill
```

then install the Python dependencies: `pip install -r requirements.txt`.

**As plain skills** (Claude Code or any agent that reads `SKILL.md` folders)

```
git clone https://github.com/jeonghun-app/pptx-deck-skill
cd pptx-deck-skill && ./install.sh      # links skills into ~/.claude/skills and installs deps
```

## Make it yours

1. **From a company template** (recommended)

   ```
   cd skills/pptx-deck
   python scripts/extract_brand.py ~/company-template.pptx -o brand/brand.yaml --report brand/extract-report.md
   ```

   The template is copied into `brand/assets/` and its layouts are mapped to
   cover / section / content / closing / blank. Decks are then built on its masters, so
   backgrounds, logos and title styles come from the template. Review the report
   — the script cannot know which theme color is your accent.

2. **From scratch** — edit `skills/pptx-deck/brand/brand.yaml`. A partial file
   is fine; missing keys inherit the neutral defaults
   (see `examples/brands/warm-editorial/brand.yaml`).

   If your brand fonts are not installed where you build, point
   `fonts.<role>.file` at the font files so text is measured exactly. A brand
   with its own `colors.series` keeps that chart palette.

3. **Write the rules that are not numbers** in `brand/guidelines.md`: voice,
   banned words, required slides, approved patterns, diagram conventions.

4. **Check it**: build the samples with your brand and look at the contact sheet.

   ```
   python scripts/build_deck.py examples/decks/sample.deck.yaml -o out/sample.pptx
   python scripts/render_deck.py out/sample.pptx      # out/sample.render/contact.png
   ```

Precedence: explicit request > company template and `brand.yaml` >
`guidelines.md` > the skill's defaults.

## Use

Ask your agent for a deck ("make a 10-slide proposal for …"). The skill will:

1. ask for source material and what it cannot infer (audience, objective,
   desired action, length);
2. write `<name>.deck.yaml` and stop for your approval;
3. build, lint, render and look at every slide, fix, and report what it checked.

Run the steps yourself:

```
cd skills/pptx-deck
python scripts/lint_deck.py my.deck.yaml
python scripts/build_deck.py my.deck.yaml -o out/my.pptx
python scripts/render_deck.py out/my.pptx
python ../pptx-layout-audit/scripts/deck-craft-lint.py out/my.pptx --brand brand/brand.yaml
```

Deck-wide options in `meta`: `mode: read` for a pre-read deck (two-line
headlines in a fixed band), `tracker: tabs | dots` for a section tracker, and
`language: ko` for Korean wording. See
[`references/deck-format.md`](skills/pptx-deck/references/deck-format.md).

Layouts: `cover`, `section`, `agenda`, `summary`, `statement`, `bullets`,
`two_column`, `cards`, `stats`, `table`, `chart` (incl. `waterfall` and
`panels`), `matrix`, `shift`, `process`, `timeline`, `diagram`, `quote`,
`image`, `code`, `closing`, and `custom` (your own Python renderer using the
brand-bound drawing primitives). See
[`references/layouts.md`](skills/pptx-deck/references/layouts.md).

## Repository layout

```
skills/
  pptx-deck/
    SKILL.md              workflow the agent follows
    brand/                YOUR design: brand.yaml, guidelines.md, assets/
    references/           craft: story, writing, visuals, diagrams, data, QA
    scripts/              build_deck, render_deck, lint_deck, extract_brand, find_icon, deckkit/
    examples/             sample decks and an example brand
  pptx-layout-audit/
    SKILL.md, references/, scripts/ (inspect-layout, deck-craft-lint)
docs/                     example PPTX files and their rendered previews (./build-examples.sh)
```

## Tests

```
pip install -r requirements.txt
python -m pytest skills/pptx-deck/scripts/tests
python -B skills/pptx-layout-audit/scripts/test_inspect_layout.py
python -B skills/pptx-layout-audit/scripts/test_deck_craft_lint.py
```

## Notes

- Visual QA renders with LibreOffice, which approximates PowerPoint. Install
  your brand fonts on the render machine and open final files in the
  application your audience uses.
- Use only logos, fonts, icons and images your organization is licensed to
  use. This repository ships none.

## License

MIT
