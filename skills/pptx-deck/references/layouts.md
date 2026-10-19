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
| Eyebrow | `layout.eyebrow_y`, `type.label`, mono font, `colors.accent` |
| Headline | `layout.title_y`, height `layout.title_h`, `type.title`, one line |
| Accent rule | `layout.rule_y` (null hides it), `layout.rule_w` × `layout.rule_h` |
| Body | from `layout.body_top` (after the optional `lead`) to `layout.body_bottom` |
| Source line | bottom of the body band, `type.caption`, `colors.muted` |
| Footer | `layout.footer_y`: footer text, page number, logo |

Content that ends above `body_bottom` leaves its spare space **at the bottom**;
do not stretch boxes or center the body vertically to fill it. Content that
would pass `body_bottom` is an ERROR: split the slide.

Text size follows the **width it sits in**, not the element's name: full-width
reading text uses `type.lead`; text in narrow columns (cards, table cells,
columns of 3–4) uses `type.body`. Never give the same kind of element two sizes
in one deck.

## Structural layouts

### `cover`
`title`, `subtitle`, `eyebrow`, `presenter`, `role`, `date`. Background from
`backgrounds.cover`; logo from `chrome.logo` (`path_on_dark` on dark covers).
In template mode the title/subtitle placeholders of `template.layouts.cover`
are filled instead.

### `section`
`number` (shown as `01`, `02` ...), `title`, `subtitle`. Short title; it
orients, it does not argue.

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
that carries it.

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
`doughnut`, `pie`), `categories`, `series: [{name, values}]`, `highlight`
(category index with one series: that bar in the accent, others muted),
`unit` (axis label shown above the chart), `number_format` (e.g. `'0%'`,
`'#,##0'`), `labels` (direct data labels; default true, which also hides the
value axis), `legend`. `takeaway`: the reading of the chart, placed beside it.
Rules in [data-viz.md](data-viz.md).

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
    - { title: Foundation, period: 2026 }
    - { title: Scale,      period: 2027-28 }
    - { title: Maturity,   period: 2029+ }
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
  x: { label: Ease of adoption, low: Hard, high: Easy }
  y: { label: Strategic value,  low: Low,  high: High }
  size: 2                  # 2 or 3 cells per axis
  basis: qualitative       # qualitative (default) | measured
  quadrants:               # row-major from the top-left (high y, low x); a name each
    - { name: Plan carefully, body: High value, needs process change }
    - { name: Start here, highlight: true }
    - { name: Avoid }
    - { name: Quick fixes }
  items:
    - { id: A, label: Claims triage, cell: 1 }     # qualitative: by cell index
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
    - { dimension: Planning, from: "**Annual** plan per unit", to: "**Quarterly** shared roadmap" }
    - { dimension: Teams, from: Siloed teams, to: Cross-functional teams, highlight: true }
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
