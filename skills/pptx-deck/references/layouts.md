# Layout catalog — choose by content shape

Pick the layout from what the content *is*, not from catalog order. Decide the
representation first with [visuals.md](visuals.md). Every layout takes the
common keys in [deck-format.md](deck-format.md) (`title`, `eyebrow`, `lead`,
`source`, `notes`, `dark`, ...).

| Content shape | Layout |
|---|---|
| Deck opening | `cover` |
| Chapter change | `section` |
| Map of the talk (8+ content slides or 3+ chapters) | `agenda` |
| The whole argument on one page: each chapter's conclusion and the ask | `summary` |
| One sentence the audience must remember | `statement` |
| 3–5 parallel points, read in full | `bullets` |
| Two things compared or connected (before/after, problem/answer) | `two_column` |
| 2–4 parallel items with a short explanation each (5 as open columns) | `cards` |
| Numbered recommendations or takeaways | `cards` with `style: open`, `numbered: true` |
| 1–4 representative numbers; 5–9 key facts as a grid | `stats` |
| Values the reader looks up | `table` |
| Options rated on criteria (Harvey balls, checks, status, tiers) | `table` with `symbols` |
| Options placed on two criteria | `matrix` |
| Current state → target state, per dimension | `shift` |
| Differences between numbers | `chart` |
| Ordered stages, optionally a current one; phases × attributes | `process` |
| Events on dates | `timeline` |
| Components, boundaries and connections | `diagram` |
| A real quote with an attribution | `quote` |
| Screenshot, photo or exported figure | `image` |
| Short code or configuration | `code` |
| Anything else (Gantt, custom chart) | `custom` |
| Last slide | `closing` |

## The fixed frame of a content slide

All content layouts share one frame from `brand.yaml`, so headlines never jump
as slides advance:

| Element | Position (tokens) |
|---|---|
| Eyebrow | `layout.eyebrow_y`, `type.label`, mono font, `colors.accent` — or the section tracker (below) |
| Headline | `layout.title_y`, height `layout.title_h`, `type.title`, `layout.title_lines` lines (one; two in `meta.mode: read`) |
| Accent rule | `layout.rule_y` (null hides it), `layout.rule_w` × `layout.rule_h` |
| Lead | from `layout.body_top`, `type.lead`, at most `type.max_measure` characters wide; `lead_style: band` for a tinted band |
| Body | from `layout.body_top` (after the optional `lead`) to `layout.body_bottom` |
| Source line | bottom of the body band, `type.caption`, `colors.muted` |
| Next steps band | optional, at the very bottom of the body band; the body ends above it |
| Footer | `layout.footer_y`: footer text, page number, logo |

Content that ends above `body_bottom` leaves its spare space **at the bottom**;
do not stretch boxes or center the body vertically to fill it. Content that
would pass `body_bottom` is an ERROR: split the slide.

Text size follows the **width it sits in**, not the element's name: full-width
reading text uses `type.lead`; text in narrow columns (cards, table cells,
columns of 3–4) uses `type.body`. Never give the same kind of element two sizes
in one deck.

**Reading measure.** A line of reading text holds at most `type.max_measure`
average Latin characters (default 75; a CJK character counts about two, so a
Korean line holds roughly 40). The lead, bullets, section and cover subtitles and
statement support text are drawn `min(available width, measure)` wide, aligned
left; the space to their right stays empty. Long lines make the eye lose its
place on the way back to the next line. Narrow columns are already within the
measure and do not change. `type.max_measure: null` turns the cap off.

### Delivery mode: present or read

`meta.mode` is set once per deck.

- `present` (default): the deck is shown and spoken. Headlines hold one line,
  roughly 8–14 words.
- `read`: the deck is sent ahead or left behind and read at the reader's pace.
  The title band reserves **two** headline lines on every content slide: the
  rule and the body start move down by one headline line (`type.title` × 1.2 ×
  `type.heading_line_spacing`, about 30 pt by default). The shift applies to the
  whole deck, so the body starts at the same y whether a headline uses one line
  or two. Headlines stay one sentence of at most about 25 words; the lint warns
  past two lines or 25 words. Three lines means the slide carries two messages.

A brand whose band already reserves two lines sets `layout.title_lines: 2` and
gives `title_h`, `rule_y` and `body_top` for two lines; read mode then adds
nothing.

### Section tracker and `eyebrow: auto`

`chrome.tracker` in the brand (or `meta.tracker` in the deck) shows the reader's
position on content slides that sit inside a section. It is built from the
`section` slides; a section's `short:` key gives its tracker label (default:
its title).

| Value | Drawn |
|---|---|
| `none` (default) | Nothing |
| `tabs` | One tab per section across the eyebrow band (`type.label`, mono): the current section in `colors.accent` with a 2 pt underline, the others in `colors.muted` over a hairline. **Tabs replace the eyebrow** on those slides: the current tab already names the chapter, and a second label in the same band would compete with it. Up to 6 sections; more fall back to dots |
| `dots` | One small circle per section at the right end of the eyebrow band, the current one filled in the accent. The eyebrow stays on the left and is shortened so it never runs under the dots |

Use a tracker for long or read decks (3+ sections, about 15+ slides); in a short
presented deck the agenda and section slides are enough. It is never drawn on
cover, section, closing, statement and quote slides, on the agenda, or on slides
before the first section. Keep `short:` labels to one or two words; the builder
warns when a tab label does not fit its tab.

`eyebrow: auto` writes the enclosing section's number and short label
(`01 · DIAGNOSIS`). With `dots` or no tracker it is the simplest way to keep
eyebrows consistent; under `tabs` it is not drawn.

### Bands any content slide can take

**`lead_style: band`** draws the `lead` as a full-width tinted band
(`colors.surface_alt`, accent rule on the left) directly under the headline,
with its text at the reading measure. Use it under a **question headline**: the
band is the answer, so the page still leads with its conclusion. Never leave
the answer to the body.

**`next_steps`** adds a numbered row at the bottom of the body: what the reader
should do with the page.

```yaml
next_steps:
  label: What this means      # default copy.next_steps_label, else "What this means" / "시사점"
  items:                      # 2–4 short phrases, verb first
    - Name one owner per new account
    - Replace the setup inbox with a checklist
```

Its height is reserved before the layout draws, so the body (and its source
line) ends above the band; content that no longer fits is an overflow ERROR.
Use it on the pages that close an argument — the lint warns when more than one
content slide in four carries it. For a chapter-end page of 2–4 actions, use
`cards` instead ([composition.md](composition.md) §1).

## Structural layouts

### `cover`
`title`, `subtitle`, `eyebrow`, `presenter`, `role`, `date`. Background from
`backgrounds.cover`; logo from `chrome.logo` (`path_on_dark` on dark covers).
In template mode the title/subtitle placeholders of `template.layouts.cover`
are filled instead.

### `section`
`number` (shown as `01`, `02` ...), `title`, `subtitle`, `short`. Short title
(2–6 words); it orients. `subtitle` is one sentence stating what the section
will show (its thesis); the `summary` layout repeats it. `short` is the one- or
two-word label for the tracker and `eyebrow: auto` (default: the title). Skip
the thesis only on reference sections (appendix, method).

### `closing`
`title` (default `copy.closing_title`), `subtitle`, `contact`. Conclusions and
requests belong on the slides before it. Add contact details only when they are
confirmed.

### `statement`
`text` (or `title`), `support`, `eyebrow`. `**bold**` renders in the accent.
Use once or twice per deck, for the sentence the audience must keep.

### `quote`
`text`, `attribution`, `role`. Only real quotes with permission to use them.

## Content layouts

### `agenda`
`items` (list of strings), `current` (0-based index to highlight while the
others recede). Eyebrow defaults to `copy.agenda_eyebrow`.

### `bullets`
`bullets`: strings, or `{text, sub: [..]}` for one level of detail. 3–5 items;
split evenly beyond that. Lead each bullet with its point; bold only the phrase
that carries it. The list is at most the reading measure wide
(`type.max_measure` at `type.lead`, about 600 pt by default) and starts at the
left margin; the space to its right stays empty.

### `summary`
The executive summary: the whole argument on one page, built from the section
conclusions. A reader who stops here has the argument; a reader who jumps to a
section recognises the same wording there.

```yaml
- layout: summary
  title: Onboarding is slow because accounts wait between teams   # the deck's conclusion
  blocks:                       # 2–4, in deck order, one per section
    - section: 1                # heading = 1st section slide's title, thesis = its subtitle
      points: ["Eleven days from contract to first use; about two are work"]
    - heading: What we change first   # or a block without a section reference
      thesis: One owner per account removes the handoffs.
      points: [...]
  so_what: Approve a six-week trial in one region   # full-width band at the bottom
```

`section: n` refers to the n-th `section` slide of the deck (1-based) and shows
that section's number. Blocks are columns on the grid with a hairline on top,
heading at `type.lead`, thesis and points at `type.body`. `so_what` is a
`colors.surface_alt` band with an accent rule; its height comes out of the body.
The lint warns when a block heading differs from the section title it refers to,
and when a deck with 10+ content slides and two or more sections has no summary. Points are noun phrases or
short sentences, 2–3 per block.

### `two_column`
`left`, `right`: each `{heading, body}` or `{heading, bullets}`.
`relation`: a symbol drawn between the columns that states how they relate —
`"→"` (leads to), `"vs"` (contrast), `"="`, `"+"`. Without it a thin divider is
drawn. Decide the relationship before drawing two panels
([reader-craft.md](reader-craft.md)).

### `cards`
`cards`: `{heading, body | bullets, icon}`; 2–4 per row. `highlight`: index of
the one card that matters most. All cards share the height of the tallest; keep
their copy similar in length.

- `style: filled` (default): panels on `colors.surface_alt`; the highlight is
  tinted with an accent outline.
- `style: open`: no fills. A hairline (`colors.line`) runs over each column and
  the text starts at the column edge; the highlight gets an accent rule instead.
  Up to 5 per row, because without panels five short columns still read.
- `numbered: true`: a large numeral (`01`, `02` … at `type.statement`, accent)
  above each heading. The number gives the reader a handle ("point 3") for
  discussion and for later slides that pick up one item.

Numbered open cards suit recommendations, takeaways and chapter-end
implications: 3–5 items, each heading verb + object in the same grammar, 2–4
lines of body. Do not use them for steps with a real order (`process`) or when
one item dominates (`statement`). Lint: WARN above 4 cards (5 with
`style: open`); WARN when numbered headings differ in length by more than 2×.

### `stats`
`stats`: `{value, label, detail}`; 1–9. `highlight`: index of the value in the
accent (default: all in the accent). Always give `source`. Values must be short
enough for their column — the builder warns when they are not.

- 1–4 values: one row; label at `type.lead` under a rule.
- 5–9 values: a three-column grid (5–6 → 3 × 2, 7–9 → 3 × 3) separated by
  hairlines, no boxes. Values at `type.statement` (`type.section` for 7–9),
  about three times the `type.body` label, so the eye scans the numbers first
  and the labels qualify them. Use the grid for fact sheets and "at a glance"
  pages; when one number is the message use 1–3 values or `statement`.

Lint: WARN above 9 values.

### `table`
`columns` (header labels), `rows` (lists of cells). A cell is a string or
`[keyword, detail]` (keyword over a muted detail line; the keyword is bold except in the
first column, which holds row labels). `widths` (relative
column widths), `numeric_cols` (right-aligned column indexes), `highlight_col`
(recommended column: tinted with an accent cap — say *why* in the headline,
never by color alone), `total_row: true` (last row emphasized). ≤ 7 × 7.

**Symbol cells.** For options rated against criteria, set `symbols` to one
family per table and write rated cells as `{s: value}`:

| `symbols` | Values | Drawn as |
|---|---|---|
| `harvey` | `0`–`4` (quarters filled) | Outline circle in `colors.ink` with a filled wedge from 12 o'clock |
| `check` | `yes`, `partial`, `no` | Check (`colors.positive`), half-filled circle (`colors.warning`), cross (`colors.negative`) |
| `rag` | `g`, `a`, `r` | Dot in `positive` / `warning` / `negative` with a word beside it |
| `tier` | `1`–`3` (1 = strongest) | Full, half and empty accent squares |

Every family also takes `na` (not assessed), drawn as a grey dash so it is never
read as zero. `{s: value, label: text}` puts a word after the symbol; status
(`rag`) cells always show one — the cell's `label`, else the legend word — so
the status never depends on color alone. Symbols are native shapes centred in
their cells (left of the label when there is one); a column of label-free symbols
gets a centred header. A legend line is drawn under the table: every value of
the family, plus `na` when used. `legend: {value: text}` renames entries for this
table (brand default: `copy.symbol_labels`); `legend: false` hides it.

```yaml
- layout: table
  symbols: harvey
  columns: [Option, Cost, Speed, Risk, Verdict]
  rows:
    - [Build, {s: 1}, {s: 4}, {s: 2}, Not preferred]
    - [Buy,   {s: 3}, {s: 3}, {s: na}, [Preferred, pending risk review]]
```

Use symbols when the pattern across a grid matters more than exact values;
when exact numbers matter, show the numbers or a chart. Keep a final verdict
column when there is a result. Lint: ERROR for `{s: …}` cells without
`symbols`, unknown values, and blank cells in a symbol column (write `na`);
WARN for `rag` cells without a label, text mixed into a symbol column, and
`legend: false`.

### `chart`
`chart`: `type` (`column`, `bar`, `stacked_column`, `stacked_bar`, `line`,
`waterfall`, `doughnut`, `pie`), `categories`, `series: [{name, values}]`,
`unit` (the line above the chart: metric, scope, period, unit), `number_format`
(e.g. `'0%'`, `'#,##0'`), `labels` (direct data labels, which also hide the value axis; default true,
except on line charts with end labels), `legend`, `min` / `max` (value axis
bounds; bars always start at zero, lines span their data unless it nearly
reaches zero). Categories in `highlight`, `estimates` and annotations are an
index (`3`) or a name in quotes (`"2024"`).

| Key | Effect |
|---|---|
| `highlight` | One series: category index, name, or a list of them, in `colors.accent`; the rest grey |
| `highlight_series` | Several series: index or list in `colors.accent`; the others in a grey ramp |
| `series_kind` | `ordered` (accent ramp, dark to light; default for stacks and multi-series column, bar and line) or `nominal` (`colors.series`) |
| `end_labels` | Line charts: series name and last value at each line's end, no legend. Default on with up to 6 series |
| `estimates` | `{from: category, suffix: e, note: ...}`: lines dashed and bars lighter from that category on; the footer explains it |
| `annotations` | `ref_line`, `band`, `callout`, `delta` on column, bar and line charts (below) |
| `panels` | 2–4 charts in one row (below) |

`waterfall` takes `steps: [{label, value}]` instead of categories and series,
plus optional `start: {label, value}` and `total: "End label"`. Rises use
`colors.positive`, falls `colors.negative`, start and end `colors.ink`; every
bar is labeled. The running total must stay at or above zero.

```yaml
annotations:
  - { kind: ref_line, value: 40, label: "Target {value}" }   # value: a number or mean
  - { kind: band, from: "2026", to: "2027", label: Forecast } # shaded category span
  - { kind: callout, at: "2025", text: "Launch" }             # pill with a leader to the point
  - { kind: delta, from: "2024", to: "2026", fmt: pp }        # pp | pct | x | abs, computed
```

Categories are referenced by name, or by index when no category has that name.
`{value}` in a label is replaced by the computed value in the chart's number
format; a delta's text is always computed from the plotted values. Callouts
and deltas sit in lanes above the plot (right of horizontal bars) so they never
cover data; keep to the 1–3 the headline needs.

`panels: [chart spec, ...]` draws 2–4 native charts on one shared header line
(each panel's `title` in bold over its `unit` in caption size) and one
baseline. Panels with the same `unit` share one value range and one plot
rectangle; `shared_scale: false|true` overrides. One key is drawn for all
panels when bars or columns have several series; line panels label their ends.

`commentary: {text | bullets, side: right | left, width: 3 | 4}` puts the
reading in a column of that many grid columns beside the exhibit, behind an
accent rule; text is `type.lead` at 4 columns and `type.body` at 3. It works on
`chart`, `table`, `image` and `diagram`. `takeaway: "..."` is the same as
`commentary` on the right, 4 columns wide.

`source` is a string or a footer object with notes, question, base, `n` and
date; `survey: true` on the slide asks the lint for `n`.
Rules and examples in [data-viz.md](data-viz.md).

### `process`
`steps`: strings or `{title, body, period}`. `current`: index of the active
step; the others recede.

- `style: rail` (default): an accent rule over each step, `01`-style numbers,
  arrows between the rules; 3–5 steps. `period` is printed after the number.
- `style: chevron`: native chevrons (the first a pentagon) with the title
  inside on one line, the `period` above each chevron, up to 6 steps. The
  current chevron is filled in the accent and its period reads "… · Now"
  (`copy.current_label`), so the marker is text as well as color.
- `rows: [{label, cells: [..]}]`: a phase × attribute grid under the steps —
  objectives, outputs, owners, gates. Labels take a left column; one cell sits
  under each step, aligned with its title; hairlines only; the current column
  is tinted.

```yaml
- layout: process
  style: chevron
  current: 0
  steps:
    - { title: Prepare,  period: Q1 }
    - { title: Pilot,    period: Q2 }
    - { title: Roll out, period: Q3–Q4 }
  rows:
    - { label: Objective,  cells: [Data in place, Two use cases live, Run at scale] }
    - { label: Key output, cells: [Signed-off maps, Weekly measures, Operating model] }
```

Equal-width phases are conceptual, not durations: say so in the notes or use a
time-proportional Gantt (`custom`) when durations matter. Without committed
dates, label the plan illustrative. Lint: WARN above 5 rail or 6 chevron steps,
when a row's cell count differs from the step count; ERROR when `current` is
not a step index. The builder warns when a chevron title wraps — use one or two
words.

### `timeline`
`events`: `{date, title, body}`; 3–6. `current`: index of "now".

### `matrix`
A 2 × 2 or 3 × 3 matrix: two declared criteria, named cells, items placed in
them. Use it when two independent criteria separate the options; when the axes
are correlated or not defensible, a ranked list or a criteria table is more
honest.

```yaml
- layout: matrix
  x: { label: Effort to implement, low: High, high: Low }
  y: { label: Expected impact,     low: Low,  high: High }
  size: 2                  # 2 or 3 cells per axis
  basis: qualitative       # qualitative (default) | measured
  quadrants:               # row-major from the top-left (high y, low x); a name each
    - { name: Plan carefully, body: High value, needs process change }
    - { name: Start here, highlight: true }
    - { name: Avoid }
    - { name: Quick fixes }
  items:
    - { id: A, label: Report formatting, cell: 1 }     # qualitative: by cell index
  takeaway: One sentence, in the right column like a chart takeaway
```

- **Axes**: arrows along the left and bottom edges with the poles at the ends
  and the axis title in the middle (the y axis reads bottom to top). Name the
  poles in words; the builder warns when title and poles do not fit the axis.
- **Cells**: equal size, `colors.surface_alt`, the name bold at the top-left,
  an optional `body` of up to 3 lines. One cell may be `highlight: true`
  (accent tint and outline) — the one the headline recommends.
- **Qualitative** (`basis: qualitative`): items are listed inside their cell
  (`id` in bold, then the label), because a position inside a judged cell
  carries no meaning. The tag "Qualitative placement" (`copy.placement_tag`) is
  drawn above the top-right corner; `tag:` replaces the text, `tag: false`
  removes it.
- **Measured** (`basis: measured`): axes are scales — give `min`, `max` and an
  optional `unit` per axis (defaults 0–1); the poles print the scale ends.
  Items take `x` and `y` in axis units and are drawn as dots with direct labels
  (labels move to avoid each other; the builder warns when they cannot).
  `thresholds: {x: 60, y: 8}` (a list of two values each for 3 × 3) draws dashed
  lines at the stated values, prints the values, and splits the cells there.
  Items in the highlighted cell, or with `highlight: true`, are in the accent.
  `source` is required.
- **Side column**: `takeaway: text` (right, 4 of 12 grid columns) or
  `commentary: {text | bullets, side: right | left, width: 3 | 4}`.

Lint: ERROR for a measured matrix without `source`, a measured item without
`x`/`y`, a qualitative item without a valid `cell`, a missing cell name, the
wrong number of cells, more than one highlighted cell (unless
`highlight_set: true`); WARN for `x`/`y` on a qualitative matrix, more than 6
items in a cell or 20 in total, and an axis without a label or both poles.
Rules in [decision-diagrams.md](decision-diagrams.md).

### `shift`
From → to rows: one dimension per row, the current state, a chevron, the
target state. Use it for operating-model change, current vs target, old vs new
approach; not for two unrelated lists (`two_column`) and not before the target
is defined.

```yaml
- layout: shift
  headers: [Today, Target]          # or dated labels
  rows:                             # 3-6
    - { dimension: Status, from: "**Weekly** status emails", to: "**Live** dashboard" }
    - { dimension: Approvals, from: Approvals by email, to: Approvals in the tool, highlight: true }
```

The dimension sits on a `colors.surface_alt` tab (22 % of the width), the
current state in `colors.muted` (35 %), a chevron (6 %), the target state in
ink (37 %); hairlines between rows. `highlight: true` tints the dimension and
turns the chevron and the target's bold words to the accent. Write both states
in the same grammar and bold the word that changes. Lint: ERROR for a row
without `to`; WARN above 6 rows, for a row without a dimension, and when the
two states differ in length by more than 2×.

### `diagram`
Native shapes on a grid, connectors glued to the shapes so they follow edits.

```yaml
grid: { cols: 4, rows: 2, node_height: 58, gap: 0.18 }   # gap: share of a cell kept free on each side
groups:   # labeled boundaries, drawn first
  - { label: CI environment, col: 1, row: 0, colspan: 2, rowspan: 2, style: dashed, fill: false }
  - { label: Editorial team, nodes: [draft, review] }   # or: a boundary around member nodes
nodes:
  - { id: runner, label: Check runner, sub: isolated, col: 1, row: 0, kind: accent, icon: server }
edges:
  - { from: pr, to: runner, label: on push, kind: flow, highlight: true }
caption: One sentence that states what the diagram proves.
```

Node `kind`: `default`, `accent` (the one focus), `muted` (context),
`external` (dashed: outside your control), `store` (cylinder: data at rest),
`decision` (diamond: a test with two named outcomes).
Edge `kind`: `flow` (arrow, label what is passed), `decomposition` (no arrow),
`return` (dashed arrow). `highlight: true` draws one path in the accent.
`from_side` / `to_side` (`top`, `bottom`, `left`, `right`) override the
automatic sides; the same side on both ends (`bottom`/`bottom`) draws a loop
around the row, which suits return paths. Rows never grow taller than a node
and its labels need, so a one-row diagram leaves its spare space below. Rules in [diagrams.md](diagrams.md) and
[architecture-diagrams.md](architecture-diagrams.md).

### `image`
`image` (path relative to the deck file), `alt` (required), `caption`, `fit`
(`contain` default, `cover` to crop), `full_bleed: true` (whole slide, no
chrome). Rules in [images.md](images.md).

### `code`
`code` (literal block), `caption`. Show only the lines that matter; long code
is an ERROR.

### `custom`
`python`: path to a file defining `render(canvas, spec, ctx, top)`. The whole
slide spec is passed in, so add any keys the renderer needs. The headline frame
is drawn first when `title` is set; `top` is the y where the body starts.
Example: `examples/decks/custom/gantt.py`. Primitives and rules:
[native-construction.md](native-construction.md).
