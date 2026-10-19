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
Visible defaults that differ from 0.1.0, each with its opt-out:
- Line charts label each line at its end (series name and last value) instead
  of every point, and drop the legend. Opt out with `end_labels: false`
  (or `labels: true` for point labels).
- Full-width reading text (leads, bullets, subtitles) is capped at about 75
  characters per line (`type.max_measure`); narrow columns are unchanged.
  Opt out with `type.max_measure: null`.
- Several series on one chart get tints of the accent when the brand keeps the
  default palette. A brand with its own `colors.series` keeps its palette, as
  before; set `colors.series_mode: ramp` or `palette` to choose explicitly.
- Line chart axes span the data (bars still start at zero), so narrow-range
  trends stay readable. Set `min:` / `max:` to fix the axis.

Other changes:
- Bullet lists are one text box with paragraphs, so gaps stay even however the
  lines break.
- Cover, section, closing, statement and quote titles sit on a fixed baseline
  and grow upward if they run longer than estimated.
- The "no summary" warning applies only to decks with two or more sections.
- The English sample deck opens with a summary slide; Korean sample headlines
  use the noun-phrase form.
- Example brand `warm-editorial`: darker accent for readable eyebrows.

### Fixed
- Numeric category references (`highlight: 3`) always mean the index, as in
  0.1.0; write `"3"` to pick a category named 3.
- Malformed chart, waterfall, estimate, next-steps and summary keys are
  reported by the linter instead of stopping the build with a traceback.
- Tracker tabs and other monospace text are measured in the monospace face,
  including faces inside font collections.
- Language codes such as `ko-KR` select the Korean wording everywhere.
- Matrix commentary follows the same column rules as charts and tables.
- A sub-bullet in the sample deck was split at a comma; the deck format
  reference now explains quoting text with commas in `[ ... ]` lists.

## 0.1.0 — 2026-10-19

Initial release: `pptx-deck` (PLAN → BUILD → QA with a brand profile and
optional company template) and `pptx-layout-audit`.
