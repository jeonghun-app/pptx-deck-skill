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
| 2–4 parallel items with a short explanation each | `cards` |
| 1–4 representative numbers | `stats` |
| Values the reader looks up | `table` |
| Differences between numbers | `chart` |
| Ordered stages, optionally a current one | `process` |
| Events on dates | `timeline` |
| Components, boundaries and connections | `diagram` |
| A real quote with an attribution | `quote` |
| Screenshot, photo or exported figure | `image` |
| Short code or configuration | `code` |
| Anything else (Gantt, matrix, custom chart) | `custom` |
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
the one card that matters most (tinted with an accent outline). All cards share
the height of the tallest; keep their copy similar in length.

### `stats`
`stats`: `{value, label, detail}`; 1–4. `highlight`: index of the value in the
accent (default: all in the accent). Always give `source`. Values must be short
enough for their column — the builder warns when they are not.

### `table`
`columns` (header labels), `rows` (lists of cells). A cell is a string or
`[keyword, detail]` (keyword over a muted detail line; the keyword is bold except in the
first column, which holds row labels). `widths` (relative
column widths), `numeric_cols` (right-aligned column indexes), `highlight_col`
(recommended column: tinted with an accent cap — say *why* in the headline,
never by color alone), `total_row: true` (last row emphasized). ≤ 7 × 7.

### `chart`
`chart`: `type` (`column`, `bar`, `stacked_column`, `stacked_bar`, `line`,
`waterfall`, `doughnut`, `pie`), `categories`, `series: [{name, values}]`,
`unit` (the line above the chart: metric, scope, period, unit), `number_format`
(e.g. `'0%'`, `'#,##0'`), `labels` (direct data labels; default true, which
also hides the value axis), `legend`, `min` / `max` (value axis bounds).

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
`steps`: strings or `{title, body}`; 3–5. `current`: index of the active step;
the others recede.

### `timeline`
`events`: `{date, title, body}`; 3–6. `current`: index of "now".

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
