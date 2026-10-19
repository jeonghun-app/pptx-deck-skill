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
and when a deck of 10+ content slides has no summary. Points are noun phrases or
short sentences, 2–3 per block.

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
`doughnut`, `pie`), `categories`, `series: [{name, values}]`, `highlight`
(category index with one series: that bar in the accent, others muted),
`unit` (axis label shown above the chart), `number_format` (e.g. `'0%'`,
`'#,##0'`), `labels` (direct data labels; default true, which also hides the
value axis), `legend`. `takeaway`: the reading of the chart, placed beside it.
Rules in [data-viz.md](data-viz.md).

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
