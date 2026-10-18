# Analytical methods for proposals, diagnostics, and decisions

Use this reference when an audience needs to understand an issue, compare
explanations or options, decide a direction, or organize execution: proposals,
diagnostics, strategy material, executive and board decisions, working
sessions, and similar analytical decks.

**Learn the purpose and conditions of a method, then adapt it to the task.**
A method is a solution to a communication problem, not a mandatory template or
a fixed slide position. A simple fact, a short update, or a direct explanation
may need none of these methods.

Preserve the active brand while applying them. Node treatment, connectors,
emphasis, and composition may change when that clarifies a relationship; the
colors, fonts, chrome, and structural slides come from `brand/brand.yaml` and
`brand/guidelines.md`.

## Read only what the task needs

| Need | Reference |
|---|---|
| Decide whether a method fits; plan the narrative | This file |
| Construct a particular analytical page | [analytical-patterns.md](analytical-patterns.md) |
| Design what a diagram means and how it looks | [decision-diagrams.md](decision-diagrams.md) |
| Set margins, gaps, insets, text alignment, shape proportions | [layout-craft.md](layout-craft.md) |
| Brand tokens and organization-specific rules | [`../brand/brand.yaml`](../brand/brand.yaml), [`../brand/guidelines.md`](../brand/guidelines.md) |

## 1. Select by communication need

Before choosing a visual, complete this reasoning:

1. **Audience question:** what must the reader understand or decide on this page?
2. **Available evidence:** what do we know, and what is still a hypothesis?
3. **Relationship:** is the important structure comparison, decomposition,
   sequence, dependency, prioritization, hierarchy, change, or accountability?
4. **Useful method:** which representation makes that relationship easiest to
   read? A paragraph or a plain table is a valid answer.
5. **Fit:** can it stay accurate and legible on this slide? If not, change the
   representation, separate overview from detail, or move detail to an appendix.

| Reader's question | Candidate method | Choose something simpler when |
|---|---|---|
| Why does this issue matter now? | Evidence plus implication; paired exhibits | A single verified fact establishes the point |
| What explains the gap? | Driver tree plus evidence or tests | The cause is already established and needs no decomposition |
| How was this recommendation derived? | Inputs, criteria, synthesis, output | There is no analytical selection or dependency to explain |
| Which option fits our constraints? | Common-criteria comparison | There is no real choice to evaluate |
| What should come first? | Ranked list or priority matrix linked to actions | Two independent, defensible axes are unavailable |
| How do initiatives serve the objective? | Strategy hierarchy and shared enablers | The objective has only one direct action |
| What changes as capability develops? | Maturity model with explicit entry criteria | The difference is only a delivery date; use a timeline |
| Who acts, and when? | Responsibility table, governance map, or roadmap | A single owner and next step answer the question |
| How will the output be used? | Annotated deliverable example | An example would duplicate an already clear specification |

These are candidates. Do not add an issue tree, quadrant, or roadmap just to
make material look more "analytical".

## 2. Build a story that fits the situation

Proposals, diagnostics, strategy deliverables, executive reports, and workshops
serve different readers. Use the sequence whose claims and evidence
requirements match the reader.

### Proposal: make the proposed work understandable

Possible sequence:

`Client situation -> decision or gap -> working hypotheses -> investigation
and criteria -> expected deliverables -> execution and relevant credentials`

Show the client's need before presenting capabilities. Explain how an activity
produces an output and how that output helps the client decide. Label
hypotheses, proposed work, and example deliverables as such. An analysis method
is not evidence that its eventual conclusion is already true.

A request-to-response table helps with a complex brief or RFP. For a short
proposal, a clear opening and scoped deliverables may be enough.

### Diagnostic or strategy material: make the decision defensible

Possible sequence:

`Recommendation -> supporting observations -> criteria and gaps -> tested
drivers -> options and tradeoffs -> chosen actions -> owners, measures, review`

Use only the stages the decision needs. An executive who already knows the
context may need the recommendation, evidence, tradeoff, and ask immediately.
A working session may instead open with the question and examine alternatives.
Neither sequence is a compulsory slide list.

### Useful moves within either story

- **Overview -> focused analysis -> synthesis.** Keep issue IDs and terminology
  stable so the reader can locate each deep dive.
- **Observation -> interpretation -> response.** State the consequence of a
  finding; support the recommendation with a stated criterion.
- **Candidate pool -> selection rule -> selected items.** Make exclusions and
  priorities understandable instead of showing only the final shortlist.
- **Method -> output -> use.** A proposed analysis becomes concrete when the
  reader sees what the output contains and who will use it.
- **Plan -> observed result -> next adjustment.** Report outcomes with their
  baseline and period; do not present activities as proven impact.

Keep a repeated analytical frame when the reader compares related cases, and
change only the focus or evidence within it. Deliberate continuity helps;
decorative variation makes comparison harder.

## 3. Give each page a clear reasoning structure

Map the reasoning onto the standard slide hierarchy:

- **Eyebrow:** chapter, issue ID, or analytical lens, when useful.
- **Headline:** the principal conclusion or recommendation, or an explicit
  investigation question when evidence is incomplete.
- **Body:** the evidence and relationships needed to understand that statement.
- **Implication:** the consequence, decision condition, or next action, if the
  headline and body do not already make it evident.
- **Source and notes:** scope, period, units, provenance, assumptions, and what
  is needed to reproduce the reasoning.

One message can need more than one exhibit: a trend plus a driver breakdown, or
an option comparison plus its selection condition. Use two or three coordinated
panels only when each contributes different evidence. Keep one visual focus,
aligned labels, and an explicit reading order. Do not repeat the same numbers in
a chart and an adjacent lookup table.

A small implication panel must not compress the main exhibit into unreadable
labels. If the page no longer fits, keep the comparison or causal relation
intact across an overview and a clearly linked detail page.

## 4. Preserve the active brand

The brand profile and the current deck decide appearance. Do not reset a deck
to a different look as part of applying these methods.

| Element | Rule |
|---|---|
| Canvas | Compose for the brand canvas (default 960 x 540 pt); keep `layout.margin_left` / `layout.margin_right` and end content at `layout.body_bottom` |
| Density | Reduce detail or split pages before shrinking text |
| Typography | Brand `fonts`; hierarchy from size first, then selective emphasis on key nouns or conditions |
| Readable copy | `type.lead` for full-width reading text, `type.body` for narrow columns, `type.caption` for sources; nothing below `type.min` |
| Palette | Brand `colors`; `colors.series` when distinct data series are needed |
| Focus | `colors.accent` on the relevant path, selected option, or exception; keep the surrounding structure restrained |
| Surfaces | Open columns, whitespace, `colors.surface_alt` panels, `colors.line` hairlines; a box should denote a meaningful unit or scope |
| Icons | Your organization's icon set (brand.yaml `icons.path`, search with `python scripts/find_icon.py <keyword>`) for real components and useful concepts; no decorative substitutes |
| Diagrams | Native, editable shapes and connectors (`diagram` layout or `custom` with `scripts/deckkit`); labels and connectors carry the reasoning |
| Continuity | Stable IDs, order, scales, and selected-state treatment across related pages |

Avoid heavy chapter fills, decorative shadows, three-dimensional shapes, clip-art
illustrations, and dense document-style page proportions unless the brand
guidelines call for them. Keep the brand's `cover`, `section`, and `closing`
layouts. Rewrite long lead sentences into the headline/body hierarchy.

## 5. Record the reasoning in the plan

When a page needs analytical structure, add brief authoring notes to that
slide's `notes` in `deck.yaml` (or to your planning document). These are notes,
not new required fields.

```text
Audience question:
Principal message:
Evidence and source:
Evidence status: observed / calculated / hypothesis / illustrative
Relationship to make visible:
Chosen method and why it fits:
Reading order and focus:
Decision or next action:
Assumptions / missing evidence:
```

For execution material, include owner, deliverable, completion condition,
measure, and timing. For comparative material, include criteria, scope, and the
reason for the recommendation. Capture only the fields the task uses.

Keep source facts separate from deductions. If two observations support a
hypothesis, do not draw a proven causal arrow between them. If a number is
calculated, keep the inputs and formula. If evidence is missing, keep an
explicit TODO; never borrow values from an example chart.

## 6. Apply the methods by analogy

| New task | What transfers | What must be decided afresh |
|---|---|---|
| Architecture proposal | Constraints -> options -> chosen structure -> validation | Actual requirements, components, boundaries, success criteria |
| Cost or operational review | Outcome -> contributors -> evidence -> prioritized action | Current measurements, calculation basis, dependencies, accountable owners |
| Adoption roadmap | Capability criteria -> current gap -> initiatives -> review cadence | The client's current state, prerequisites, capacity, dates |
| Executive progress review | Objective -> observed result -> issue -> next decision | Verified outcome, remaining uncertainty, the specific ask |
| A document with no matching pattern | Identify its underlying relationship and construct a fitting representation | Whether a graphic helps at all; do not force the closest-looking pattern |

These mappings are authoring options, not findings about any client.

## 7. Review usefulness as well as appearance

After building (`python scripts/build_deck.py deck.yaml -o out/deck.pptx`) and
rendering (`python scripts/render_deck.py out/deck.pptx`), check:

- Does the chosen method answer an actual reader question?
- Do the headlines, read in order, form an understandable argument?
- Does every exhibit support its page's governing message?
- Can the reader distinguish evidence, interpretation, and proposed action?
- Are comparison criteria, time periods, and numerical bases compatible?
- Do shapes, connectors, positions, and sizes mean what they visually imply?
- Are selected issues traceable to actions and, where relevant, owners and KPIs?
- Is the page useful without animation or a presenter explaining its layout?
- Does the rendered result still follow the brand and stay readable?

When you study a new example page for future use, record the problem it solves,
the relationship it exposes, the conditions for using it, and how it would map
onto this skill's layouts. Keep observations about the example separate from
your proposed improvements. Extend the method library only when it adds a
useful distinction.
