# Changelog

## 0.2.0 — 2026-10-19

Construction craft for analytical and decision decks: exhibits that carry
their own point, framework layouts, and a reading structure for long decks.

### Added
- **Exhibits**
  - Structured exhibit footer: `source` may be an object with numbered notes,
    survey question, base, n (per segment), data date, rounding caveat and source.
  - Highlighting by category list (`highlight`) and by series (`highlight_series`),
    always in `colors.accent`, with context in grey.
  - Ordered series as a ramp of the accent (`series_kind`, brand `colors.series_mode`).
  - Line end labels instead of legends; labels nudged apart when they collide.
  - `waterfall` chart type (rises, falls, start and end totals).
  - Estimate styling (`estimates`): dashed lines, lighter bars, labelled and noted.
  - Chart annotations computed from the data: reference line, band, callout, delta
    (`pp`, `pct`, `x`, `abs`).
  - `commentary` column beside a chart, table, image, diagram or matrix.
  - `chart.panels`: two to four charts on one header line and one baseline.
- **Frameworks**
  - `matrix` layout (2×2 / 3×3) with named cells, axis poles, qualitative or
    measured placement and thresholds.
  - Symbol cells in `table` (`harvey`, `check`, `rag`, `tier`) with an automatic
    legend and a distinct "not assessed" mark.
  - `shift` layout (from → to rows).
  - `process`: chevron style, periods, aligned attribute rows, a "now" marker.
  - `cards`: open style and numbering, up to five open columns.
  - `stats`: up to nine values in a grid.
- **Story**
  - `summary` layout: an executive summary built from the section conclusions,
    with a so-what bar.
  - Section tracker (`chrome.tracker`: `tabs` or `dots`) and `eyebrow: auto`.
  - Reading mode (`meta.mode: read`): two-line headlines in a fixed band.
  - `lead_style: band` for question headlines; `next_steps` band on content slides.
  - Reading-measure cap (`type.max_measure`) for full-width text.
  - Korean conventions: noun-phrase or 〜다 headlines, `%p`, unit and source labels.
- Text is measured with the fonts the deck renders in (brand `fonts.<role>.file`,
  or the font fontconfig matches), so overflow and wrap warnings match the render.
- Lint rules for every new feature, and new example decks:
  `exhibits.deck.yaml`, `frameworks.deck.yaml`, `story.deck.yaml`.

### Changed
- Bullet lists are one text box with paragraphs, so gaps stay even however the
  lines break.
- Cover, section, closing, statement and quote titles sit on a fixed baseline
  and grow upward if they run longer than estimated.
- The "no summary" warning applies only to decks with two or more sections.
- The English sample deck opens with a summary slide; Korean sample headlines
  use the noun-phrase form.
- Example brand `warm-editorial`: darker accent for readable eyebrows.

### Fixed
- A sub-bullet in the sample deck was split at a comma; the deck format
  reference now explains quoting text with commas in `[ ... ]` lists.

## 0.1.0 — 2026-10-19

Initial release: `pptx-deck` (PLAN → BUILD → QA with a brand profile and
optional company template) and `pptx-layout-audit`.
