# Analytical page construction patterns

Pick a pattern only once you know which question the reader brings to the page
(see [analytical-methods.md](analytical-methods.md)). Each entry is a starting
recipe you adapt to the content; none of them is a mandatory layout, and the
order below is not a slide sequence.

When the hard part is telling decomposition from causality, wiring join
conditions, or choosing between categorical and measured priority diagrams, read
[decision-diagrams.md](decision-diagrams.md). For page and object geometry (the
outer shape, its inset content area, and the visible text are aligned
separately), read [layout-craft.md](layout-craft.md).

Layout names are `deck.yaml` `layout:` values. `custom` means a Python slide
built from `scripts/deckkit` primitives and brand tokens.

## Pattern index

Patterns are grouped by what the page has to do for the reader.

| Group | Slug | The reader wants to... | Typical layouts |
|---|---|---|---|
| Explain | `evidence-consequence` | see a finding and what follows from it | `two_column`, `chart`, `custom` |
| Explain | `driver-tree` | break a problem into parts worth testing | `diagram`, `custom` |
| Explain | `flow-synthesis` | trace several inputs into one result | `diagram` |
| Decide | `criteria-comparison` | weigh options on identical criteria | `table` (with `symbols`), `two_column`, `cards` |
| Decide | `priority-action` | turn an assessment into responses | `matrix`, `table` |
| Decide | `recommendation` | judge one proposed action, or a short list of them | `cards` (numbered, open), `table`, `two_column` |
| Decide | `impact-bridge` | link operating changes to a measured outcome | `diagram`, `custom` (waterfall) |
| Plan | `goal-hierarchy` | trace initiatives up to goals and down to enablers | `custom`, `diagram` |
| Plan | `maturity-ladder` | see where a capability is and where it should go | `table`, `process`, `custom` |
| Plan | `change-shift` | see what changes, dimension by dimension | `shift` |
| Plan | `workstream-plan` | see who works on what, in which phase or week | `process` (with `rows`), `table`, `timeline`, `custom` |
| Plan | `roles-and-authority` | know who decides, who delivers, who escalates | `diagram`, `table` |
| Report | `drill-down` | move from a headline number to its explanation | `chart` sequence, `custom` |
| Report | `annotated-deliverable` | know exactly what a deliverable contains and how to produce it | `custom`, `image` with callouts |

---

## Explain

### `evidence-consequence`

**Fits:** one observation needs interpreting, or two separate observations
together justify a single conclusion.

**Construction:** let the main exhibit take about two thirds of the twelve-column
grid and the interpretation the remaining third. When two exhibits carry equal
weight, split the width evenly and put one shared takeaway underneath. Treat the
ratios as defaults to adjust, not rules. Everything sits between
`layout.body_top` and `layout.body_bottom`, columns are separated by
`layout.gutter`, and each exhibit keeps its own source line directly beneath it.

**Reading cues:** a single accent mark points at the data that matters, and one
or two sentences say why it matters. Draw an arrow between panels only if it
stands for a real inference or relation; never use one to occupy space.

**Pick another pattern if:** a single fact already makes the point, the two
panels show the same data twice, or the interpretation panel squeezes the
exhibit until it is unreadable. Show one exhibit, or split overview and detail
across two pages.

### `driver-tree`

**Fits:** the reader needs to see what a problem is made of, or which possible
drivers are worth investigating.

**Construction:** state the root question, then split it on one classification
basis per level, with no overlaps and no gaps. Give every leaf a short ID that
will not change. Next to the tree, line up the evidence, the test question, or
the next step for each branch that matters. When a later page zooms into one
branch, keep the path back to the root visible and highlight only the active
branch. Decomposition uses plain lines without arrowheads.

**Reading cues:** vertical or horizontal nesting means "is part of". An arrow
means "is believed to influence" and carries a label saying so. If the tree is a
formula (revenue = volume x price), print the operators and keep units on every
node.

**Pick another pattern if:** the branches overlap and you cannot explain why,
the cause is already settled, or the tree is too deep to read at slide size. A
table handles flat categories; deep trees split into an overview page and a
selected-branch page.

### `flow-synthesis`

**Fits:** the audience must see how several inputs feed a recommendation, or how
parallel streams of work merge into one output.

**Construction:** list inputs, processing steps, decisions, and outputs before
drawing anything, and write down each real source-to-target relation. Then lay
the parallel inputs out as lanes that meet at a synthesis node, followed by any
downstream branches, using `diagram` nodes, edges, and groups. Phase labels help
orientation; wrapping every node in a phase box does not.

**Reading cues:** an arrow carries data or a dependency, and a merge means the
receiving step actually consumes every incoming input. Decision points are
`kind: decision` nodes with their criterion stated and each outgoing edge
labeled. A group outline marks a genuine boundary of scope.

**Pick another pattern if:** the content is only a straight run of steps; use
`process` or `timeline`. The reverse also holds: do not flatten a process that
truly branches into a numbered list.

---

## Decide

### `criteria-comparison`

**Fits:** the reader is choosing between options, contrasting current and target
states, or checking how fully a proposal answers a request.

**Construction:** fix the criteria first and fill the same rows for every
option, in a `table` or in aligned open columns. Include scope, supporting
evidence, and the condition under which each option wins. If the comparison runs
over several pages, keep the column order and headers identical and group the
criteria into sensible blocks.

**Reading cues:** shared rows signal that values are comparable. Use one
treatment, applied once, to mark the recommended option or the deciding
difference. Ordinal ratings read fastest as symbols (`table` with `symbols:
harvey | check | rag | tier`): one family per table, the legend under it, `na`
for "not assessed" (never a blank that reads as zero), and a verdict column
when there is a result. A requirement-to-answer map links each requirement ID to the output
and page that answers it; it is a traceability table, not an agenda decoration.

**Pick another pattern if:** one numeric measure decides the matter; a bar or
dot `chart` says it faster. Never give the favoured option a friendlier set of
criteria.

### `priority-action`

**Fits:** two independent criteria separate the possible responses, or the
reader needs to see how an assessment changes what happens next.

**Construction:** before placing any item, write down what each axis measures,
which way it increases, what it is based on, and where the thresholds are.
`layout: matrix` draws the frame: name both poles of each axis, give every
cell a one- or two-word name, and highlight only the cell the headline
recommends. Declare the basis: `qualitative` lists items inside their cells and
tags the exhibit "Qualitative placement"; `measured` plots values on scales,
prints the thresholds and requires a source. Item
IDs stay the same in the matrix and in the action table beside or after it, and
the table names the response, the owner, and the next review date where
relevant. A qualitative quadrant holds categories; exact coordinates are only
allowed when measured values back them.

**Reading cues:** an item's position is the assessment. A shaded zone stands for
a stated selection rule. Bubble size encodes magnitude only when a real number
sits behind it.

**Pick another pattern if:** there are no scores, the two axes measure the same
thing, or a made-up threshold would decide the outcome. A ranked list, an
explicit criteria table, or plain categories are more honest. Do not invent
precise positions to fill a quadrant.

### `recommendation`

**Fits:** the reader must judge one course of action, or act on a short list
of them.

**Construction:** for one action, lay out three aligned columns: the situation
(two to four facts), the proposal (the one highlighted column), and the
expected effects (each a short "+" item). For several actions, use numbered open
columns (`cards` with `style: open, numbered: true`): 3–5 items, each a 2–6 word
imperative heading over 2–4 lines of body, all in the same grammar. When each
action pairs with a problem, use a `table` row per problem with fixed columns:
problem, response, mechanism, benefit.

**Reading cues:** the numeral is a handle for discussion ("point 3") and for
later pages that pick one item up; parallel headings let the reader compare
without reading every body. Put the reason and the payoff on the same page as
the action, so it can be judged and not only read.

**Pick another pattern if:** the items have a real order or dependencies (use
`process`), one item dominates (a `statement` with support), or the findings are
still exploratory.

### `impact-bridge`

**Fits:** the audience needs a line from a measurable result back to the
operating changes behind it, or a reconciliation of contributions to a total.

**Construction:** split the outcome into contributors that do not overlap, then
attach the drivers someone can act on. A tree shows decomposition, a
relationship graph shows dependency, and a waterfall shows additive changes that
sum to the total, nothing else. Keep the baseline, unit, period, calculation
method, assumptions, and dependencies on the page.

**Reading cues:** an action linked to an outcome is a hypothesis until evidence
says otherwise. Formula edges show their operators. Waterfall bars are signed
changes drawn on one scale.

**Pick another pattern if:** the effects overlap, the mechanism has not been
tested, or the contributions do not add up. Show the qualitative mechanism with
a validation plan, or present scenarios separately, rather than a false total.

---

## Plan

### `goal-hierarchy`

**Fits:** the reader needs to trace each initiative up to a strategic direction
and see which capabilities several initiatives depend on.

**Construction:** the goal sits at the top, directions below it, initiatives
under the direction they serve, and shared enablers in a band along the bottom.
A simple hierarchy works as an aligned grid; switch to `diagram` edges once
relationships branch or cross. Attach a KPI only to the initiative or result it
actually measures.

**Reading cues:** stacking expresses alignment. A shared enabler band spans only
the directions it really supports. A pitched-roof "house" outline is optional and
rarely beats a clear goal band.

**Pick another pattern if:** the content is three themes with a sentence each;
`cards` or open columns are enough. Do not fake dependencies or equal weight to
complete a symmetric shape.

### `maturity-ladder`

**Fits:** capability builds up in stages and each stage has criteria you can
observe.

**Construction:** define what qualifies a stage, carry earlier prerequisites
forward, and mark both the current and the target stage with the evidence for
each. A "today" marker is nearly always needed; `process` `current` draws it
(in chevron style the current step's period reads "· Now"). Stage columns or a readable step form both work; a compact
capability-by-stage `table` is often clearer than a crowded staircase.

**Reading cues:** height means more capability. Spacing between stages is
ordinal unless a real time axis is given. Each stage should say what it adds,
not just sound more ambitious than the last.

**Pick another pattern if:** the stages are really calendar periods, the
capabilities have no natural order, or nobody has assessed the current state.
Use a timeline, a comparison, or an assessment plan instead.

### `change-shift`

**Fits:** a transformation the reader should see as a set of concrete changes:
operating model, current vs target process, old vs new approach.

**Construction:** one row per dimension (`layout: shift`): a short dimension
label, the current state, a chevron, the target state. Write both states in the
same grammar ("Long planning cycles" → "Short planning cycles") and bold the
word that changes. Four to six rows; head the columns "Today" / "Target" or
with dates.

**Reading cues:** each row reads on its own and compares with the others,
because the pairing is done for the reader. Highlight only the row the headline
is about.

**Pick another pattern if:** the two sides are unrelated lists (`two_column`)
or the target is not defined yet.

### `workstream-plan`

**Fits:** several workstreams move through shared phases, or the reader needs
dates, milestones, and review rhythm.

**Construction:** for a method view, make workstreams the rows and phases the
columns; each cell names the main activity and what it produces. `process`
with `style: chevron` and `rows` draws this directly: the phases as a chevron
header with the period above each, then one row per attribute (objective,
output, owner, gate) aligned under the phases, the current phase tinted. Draw gates on
phase boundaries only where a real decision happens. For calendar views, use
`timeline` or a `custom` Gantt that computes bar positions from dates, labels
the milestones, and includes a legend. A crowded calendar splits by workstream
or by time horizon.

**Reading cues:** equal-width method columns mean conceptual phases, not equal
durations. In a Gantt, bar start and length are time. Keep three marks distinct:
bars for work, markers for point events, and a separate symbol for review or
decision milestones.

**Pick another pattern if:** the only question is what happens next; name the
owner and the done-condition directly. Never draw a roadmap with dates nobody
has committed to.

### `roles-and-authority`

**Fits:** it would otherwise be unclear who holds decision rights, who delivers,
or where issues escalate.

**Construction:** a compact `diagram` (hierarchy or interaction map) shows real
authority and relationships; an aligned `table` beside or after it lists
actions, outputs, cadence, and decision rights. Use the same role names in both
so the reader can cross-reference.

**Reading cues:** reporting, collaboration, and escalation each get their own
label or line style, with a legend whenever more than one edge meaning appears.
A line between two boxes does not, on its own, make anyone accountable.

**Pick another pattern if:** an action table already settles ownership. An org
chart by itself is not an operating model, and a big hub in the middle does not
prove that one team owns everything.

---

## Report

### `drill-down`

**Fits:** a headline result needs breaking down by contributor, entity, period,
or process step.

**Construction:** carry the selected item's ID, the metric definition, the
period, and the series identity from one view to the next. Put an overview chart
and its breakdown on one page if both stay legible; otherwise use consecutive
pages that share an orientation cue. Comparable charts share the same scale.
Numeric plots are native `chart` slides, not shapes drawn to look like charts.

Two sequences work well: repeat the same slide at identical coordinates and move
only the highlight, or follow a summary page with detail pages titled `(1/N)`,
`(2/N)`.

**Reading cues:** a focus outline or annotation marks what was selected, and the
following view explains it. Labels placed directly on the data save the reader a
trip to the legend.

**Pick another pattern if:** the second chart merely restyles the first, or
mismatched bases would suggest an explanation that is not real. Show one chart,
or state the limitation before offering a causal hypothesis.

### `annotated-deliverable`

**Fits:** the audience has to know precisely what a deliverable will contain,
what decision it supports, or how to produce one consistently.

**Construction:** state the deliverable's purpose, its required sections or
fields, and the acceptance criteria, then show a small, representative sample
next to them. Annotate the sample with callouts tied to specific parts, for
example: the question this section answers, the data it draws on, how a
reviewer will judge it, and what changes in the next version. For a template or
form, show each field with its owner, its allowed values, and an example entry.

**Reading cues:** every callout points at the exact field or line it describes.
Mark the sample clearly as illustrative, and leave placeholders visible where
real content is still missing. If the sample would shrink into an unreadable
miniature document, keep a cropped excerpt on the slide and move the full
template to an appendix.

**Pick another pattern if:** a short written specification already answers the
question. Never present invented sample text or figures as the audience's own
draft or real results.

---

## Shape and connector grammar

| Device | Meaning on the page | Check before keeping it |
|---|---|---|
| Rectangle or open block | One entity, activity, piece of evidence, or deliverable | Equal roles look equal; text fits at its normal size |
| Container or bracket | A shared scope, a group of sibling branches, or common support | The grouping is real and carries a label |
| Chevron or stage rail | An ordered progression | Nobody will read it as proportional duration |
| Diamond | A real decision with more than one outcome | The criterion and each outgoing choice can be read |
| Branch line | Part-of or analytical decomposition | Siblings share one basis; formulas show operators |
| Arrow | Direction of flow, dependency, or influence | Both ends and the direction mean something; uncertainty is stated |
| Dashed line or border | One declared secondary, proposed, or uncertain relation | Only one such meaning per diagram, explained in a legend |
| Number badge | A stable cross-reference or step order | The same IDs appear on the map, the chart, and the action list |
| Matrix axis | A declared criterion or measured variable | Direction, scale, and threshold are written down |
| Callout with leader | A specific observation, exception, or reading | Anchored to the actual item; nothing covers its text or line |

Keep a single reading direction, left to right or top to bottom. Labels stay
next to what they describe, and lines route around text rather than across it.
Strokes, fills, fonts, and emphasis come from brand tokens (`colors.line`,
`colors.muted`, `colors.accent`, `fonts.body`). Diagrams stay native and
editable; check the rendered slide (`python scripts/render_deck.py
out/deck.pptx`) at the size it will actually be shown.
