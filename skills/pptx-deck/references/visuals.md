# Visual strategy — table, chart, diagram, architecture, image

This file decides **what to express content with**: the nature of the content →
the means of expression. The slide `layout:` values are the generator's frames;
[patterns.md](patterns.md) covers constructions the layouts do not name.

Why a separate decision step: without explicit criteria, everything converges on
cards and paragraphs. When older decks are converted without one, architecture
slides come out with no diagram and chart slides with no chart — and QA still
passes, because alignment and contrast are fine. Only tables tend to survive as
tables.

---

## 1. Questions to ask first

Ask in this order and stop at the first match.

| Question | If yes |
|---|---|
| Does it need a connected arrangement with boundaries, branching, or merging? | **`layout: diagram`** (native nodes, edges, groups) |
| Is a classification, comparison, or mapping read along shared rows and columns? | **`layout: table`**, or an aligned grid in `custom` |
| A one-directional flow of 3–4 nodes? | `layout: process` |
| A fixed sequence of stages with a current position? | Stage rail ([patterns.md](patterns.md) §4) |
| Progress or plan on a time axis? | `layout: timeline` (one track) / Gantt ([patterns.md](patterns.md) §1, several workstreams) |
| Is the **difference** between numbers the point? | **`layout: chart`** (bars, columns), a progress meter, or a before → after delta |
| Does the reader look up **values** (row × column)? | **`layout: table`** |
| One to three headline numbers to imprint? | `layout: stats` (light) / dark stat row ([patterns.md](patterns.md) §3) |
| Must a real screen or device be shown? | **`layout: image`** |
| Descriptions of parallel items? | `layout: cards`; when each item is a list, open columns ([patterns.md](patterns.md) §7) |

**Never show the same data two ways at once.** A table of the same values beside
a chart makes both unreadable. Use the chart and write the values on the bars.

Complementary exhibits may share a slide when they support one governing message
and stay readable — a driver table can explain a chart without repeating its
values. Choose this only when the relationship is useful
([composition.md](composition.md) §1). When modernizing a diagram's form, keep
its relationship grammar and verify at the actual display size. Never turn a
decomposition into causal arrows, or a qualitative classification into
coordinates with no basis.

---

## 2. Tables — when the reader looks up values

### Use / don't use

- **Use** when columns hold values of different kinds (stage, priority, status,
  date, note) and readers look for the row they care about.
- **Don't use** for a single numeric column — that is a chart. A two-column
  "item : value" list is a bar chart or bullets, not a table.

### Limits (split beyond them)

| | Default | Dense |
|---|---|---|
| Text size | `type.body` | `type.caption` |
| **Max body rows per slide** | 5 | **7** |
| Max columns | 6 | 7 |

The limits come from the body band (`layout.body_top` to `layout.body_bottom`)
with clearance above the footer. A dense table of 8 rows whose first column wraps
to two lines, plus a legend, overruns `layout.body_bottom` — so 8 rows do not fit.
Content that touches the footer band is the usual cause of slides that "look
cramped at the bottom".

Beyond 7 rows, **split into two slides and repeat the header row.** Never go
below `type.caption` in tables and never below `type.min` anywhere. A sub-lead
costs roughly one row of height — with one, the dense limit is 6 rows. If the
headline already states the conclusion, drop the sub-lead.

### Rules

- Numeric columns are right-aligned with tabular (equal-width) figures; otherwise
  digits do not line up and cannot be compared.
- The first column is the key. For name + category, use two lines in one cell:
  the name, then the category smaller in `colors.muted`.
- Status is a dot **plus a label**. A dot alone carries no information for
  color-blind readers.
- If status or color carries meaning, put a **legend under the table — always**.
- When the table needs a reading, put it in a `commentary` column beside the
  table, not in a sub-lead above it: the rows keep their height.
- One highlighted row only. Three highlighted rows are not emphasis.
- State the reference date in a caption ("As of 2026-07").
- Table style (header fill, rules, zebra) is a brand choice; the default is
  hairline rules in `colors.line` and no zebra. Override in `brand/guidelines.md`.

---

## 3. Charts — when the reader should see a difference

### Principle: the author controls the scale

Native charts are editable, but their automatic axes can start above zero and
exaggerate differences. Set the value axis explicitly: **bars and columns start
at zero.** Always **write the values as numbers** too — the bar is a supporting
encoding; the written number is the truth.

### Choosing a type

| Data | Use | Items |
|---|---|---|
| Long item names (service, team, account names) | Horizontal bar chart | 4–8 |
| A time order (months, quarters) | Column chart | 4–8 |
| One share or progress value | Progress meter (`stats` or `custom`) | 1–3 |
| Before → after (savings, improvement) | Delta: two values, an arrow, the change | 1–2 |
| Multiple series or a longer time series | A line chart, aligned small multiples, or a measured custom chart — only when that relationship matters | Governed by legibility |

**Do not stretch three columns across the full body width.** Each slot becomes
very wide and the columns get lost in it, rendering as thin threads. Columns read
best at about half the slot width, at most about 87 pt. Narrow the plot area:

| Items | Plot width |
|---|---|
| 3 | 420–480 pt |
| 4 | 540–600 pt |
| 5+ | Full body width |

A delta reads left to right: label "Now" and the value in neutral → an arrow →
label "After" and the value in accent → the change ("61% lower") as the focus.

### Rules

- Highlight only what the headline names in `colors.accent` (`highlight` for
  bars of one series, `highlight_series` for whole series); the rest grey. If
  every bar is accent, nothing is.
- Ordered series (stack segments, size bands) use a ramp of accent tints;
  categories with no order use `colors.series` in order. Do not invent extra
  colors ([data-viz.md](data-viz.md) §2).
- **No chart without a source.** Put the footer under every chart: notes, then
  question, base and n for survey figures, then the source.
- Put the comparison the headline makes on the chart (a reference line, a
  computed delta) instead of leaving the reader to subtract.
- Default: no pie or donut. One share → a meter; several → horizontal bars.
  An organization may allow them in `brand/guidelines.md`.

---

## 4. Diagrams and architecture — when the reader should see relationships

### Do not place boxes by hand

This is the most often broken rule. Hand-placed boxes ① drift out of alignment
from slide to slide, ② must all be moved when one item is added, and ③ leave
arrows that do not follow the nodes. Describe nodes, edges, and groups and let
`layout: diagram` place and route them.

**Any boundary, branch, or multiple layers → diagram.** Decision table:

| Structure | Means |
|---|---|
| A → B → C in one line, 3–4 nodes | `layout: process` |
| Fixed stages + current position | Stage rail ([patterns.md](patterns.md) §4) |
| ≤ 3 tiers, no boundaries, ≤ 6 nodes | `layout: cards`, one row per tier |
| **Boundaries or zones** (network, trust, site, organization) | **`layout: diagram` with groups** |
| **Branching, merging, bidirectional flows** | **`layout: diagram`** |
| **7 or more nodes** | **`layout: diagram`** |
| A sequence (messages exchanged over time) | Numbered steps on a diagram, or lifelines in `custom` |

Architecture content is vendor-neutral: boundaries and zones as groups,
services and components as nodes, data stores as their own node type, external
actors outside the outermost boundary. Use icons only from your organization's
icon set (`brand.yaml` `icons.path`), found with
`python scripts/find_icon.py <keyword>`.

### When migrating — never silently turn a diagram into paragraphs

If the source had a diagram and you have no equivalent yet, **leave a visible
placeholder** in the diagram area that says what must go there, for example:

> PLACEHOLDER — source diagram: load balancer → app cluster → (cache · relational
> DB), two sites. Elements to carry over: site boundary, 2 sites, 3 tiers,
> 2 data stores.

A card list passes QA and nobody revisits it; a placeholder is caught in review.
A deck with a placeholder left is not finished.

### Diagram size and comparison

- Give a complex relationship diagram the full usable body area.
- A current/target pair, or a diagram with a complementary evidence panel, fits
  only when comparison is the point and both stay readable. Keep the same scope,
  orientation, labels, and scale where the comparison needs them.
- Measure labels at the size they render on the slide. Keep normal body and label
  sizes where possible; no text may fall below `type.min`. If the composition
  cannot meet that, split into overview and detail.
- Add a short diagram note naming the relationship or change to look at — a
  `caption` under it, or a `commentary` column beside it when the note is the
  argument.

---

## 5. Images — when a real screen or device must be shown

- Screenshots are fitted (contain), never cropped — cropping defeats the purpose.
- Several screenshots sit in columns of one grid, not stacked as large boxes.
- Say what to look at in a `commentary` column (3 or 4 grid columns) beside the
  image; it reads before the eye wanders over the screenshot.
- Text over a photo needs a scrim (a dark translucent band) for contrast.
- Alt text is required and states **what is visible** ("The approval step in the
  order editor", not "editor screen").
- Do not embed long screen recordings in the distributed file. Mark the slot as
  "Live demo" and let the presenter play the video separately.

---

## 6. Self-check

After the deck is built, count:

1. Of the slides comparing numbers, **how many are tables** — should any be charts?
2. Of the slides explaining relationships, **how many are cards** — should any be diagrams?
3. Does **every chart have a source**?
4. Do tables respect the limits: 5 body rows by default, 7 dense, at most 7 columns?
5. Is any **placeholder** left? If so, the deck is not done.

For a migration, render the original and the new deck with
`python scripts/render_deck.py` and compare the contact sheets side by side.
