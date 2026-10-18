# Diagrams that support a decision

Judge a diagram by **which relationship it exposes and which judgment that
relationship makes possible**. Adding boxes and icons, or switching layout
technique, does not improve the logic by itself.

Use this after choosing the relationship to show in
[analytical-methods.md](analytical-methods.md). Pair it with
[analytical-patterns.md](analytical-patterns.md) for page recipes and
[layout-craft.md](layout-craft.md) for margins, insets, alignment, and
proportions. When the diagram shows a real system (boundaries and zones,
services and components, data stores, external actors), combine this decision
logic with your organization's icon set (brand.yaml `icons.path`) and the
architecture rules in `brand/guidelines.md`; neither replaces the other.

## 1. Write the relationship as a sentence before drawing

Record it in the slide's `notes` as needed. No extra required fields.

> Question: what must we check before declaring the workshop ready?
> Classify the check items by "can it run" and "can it be explained", and map
> each item to the evidence that verifies it.
> Lines mean classification. They do not mean failure causes or work order.
> Without a rehearsal record, an item is "unverified", never "done".

Then decide in this order:

1. Pick the conclusion the reader needs and the evidence that supports it.
2. For every node, decide **what kind of thing at what level** it is: activity,
   deliverable, condition, organization, metric.
3. Read every connection aloud: "A is classified into B", "A is input to B".
   If it does not form a sentence, it is not a relationship.
4. Check what position, color, area, and line additionally claim. Remove any
   meaning that has no basis.
5. If there is no relationship to show, use a table or prose. Never add
   decorative connectors.

## 2. Relationships that must not be swapped

| Relationship | What the reader must read | Representation and check |
|---|---|---|
| Decomposition / classification | What it consists of or splits into | Branches without arrowheads, brackets, indentation. If it sums, show operator, unit, and scope |
| Causality | Which change causes which change | Direction plus mechanism. Until verified, mark "hypothesis" with how it will be tested |
| Information / output flow | What passes to the next step | Label the arrow with the object passed or the verb |
| Sequence / precondition | What must be satisfied first | Step number, condition, completion criterion. Encode duration only on a real time axis |
| Contrast / correspondence | Which items are compared or matched | Same row, column, scale, ID. No automatic arrows between two columns |
| Containment / scope | What lies inside which responsibility or system | Name the boundary. Check that position does not falsely claim containment |
| Selection | Which result is chosen by which criterion | Show the condition and each branch outcome; treat "unverified" as its own outcome |
| Responsibility / consultation | Who performs, decides, reviews | Role names and relationship verbs. Do not load every meaning onto one org-chart line |

**A decomposition diagram does not prove causality.** A tree of non-arrowed
branches and a cause-search diagram can look alike while meaning different
things. **Alignment is also a relationship.** If placing a test question next to
its branch already conveys the link, do not add a connector.

## 3. Constructions that strengthen common relationships

### Decompose -> verify: do not let the leaves end in a question

The value of a decomposition is finding where to check, not the number of items.
Split the big question and map each leaf to a test question, evidence, and a
status. If the classification covers only part of the space, do not label it
"all". Do not assert an item as a cause without a causal test.

In numeric trees, distinguish sum, subtraction, multiplication, and ratio. Never
add overlapping branches, or merge ratios with different denominators into one
bar. If the mapped questions get long, continue on a detail page with the same IDs.

### Many inputs -> synthesis -> parallel outputs: show the join condition

This is not a list of steps: several pieces of evidence converge on one
analysis, then parallel work branches from the result and may merge again.
Preserve that structure when modernizing.

- Show inputs as evidence from different sources; write the analysis performed
  inside the synthesis node.
- Name branch outputs as concrete nouns, not just "improvement" or "enhancement".
- State whether a join needs **all** inputs or **one of** them.
- Separate work completion from approval. The number of incoming arrows does not
  determine completion.

If the full path is too long, split analysis and execution across two pages and
keep shared output IDs on both.

### Criteria -> selection -> action: finish the comparison with a decision

Compare on the same criteria, then state the choice under current conditions and
what would change it. Do not describe only the chosen option's strengths.

- Judge mandatory conditions first. A failed mandatory condition is not offset by
  points elsewhere.
- Never fill an unchecked cell with zero or "met".
- Without scores, write met / partial / unverified with the basis.
- A weighted total requires that you can explain scale, direction, weight basis,
  and sensitivity.

With only qualitative classification, use a categorical matrix. If dots are
plotted without an origin, a scale, and a scoring basis, do not reproduce their
positions as numbers. Attach the next action, owner, and exit condition to each
classification result.

### Objective -> execution -> shared foundation: separate hierarchy from support scope

The useful relationship is directions and initiatives aligned under an
objective, plus a foundation that supports several directions. A roof-and-pillar
shape is unnecessary; open horizontal levels and same-column alignment create
the correspondence.

Write the objective as an outcome, initiatives as actions, and checks as
evidence, so the three levels do not repeat the same sentence. Draw the shared
foundation as a band spanning the columns it supports and state its scope. If it
supports only some initiatives, do not draw it across every column.

### Phases, schedules, responsibilities: fix what the axis means

Equal-width phase columns do not mean equal durations. A month axis places
activity durations and events in time. Do not mix the two.

- If order matters, use a phase x workstream table. Do not widen a phase just
  because it takes longer.
- If schedule matters, use bars proportional to a real time axis: events are
  points, durations are bars.
- If responsibility matters, map performing and approving roles and outputs to
  each work row.
- Maturity is not a staircase reached automatically over time. Write per-stage
  evidence and entry criteria.

Without dates, mark relative weeks as **illustrative plan**, or use an undated
phase diagram. Never use a staffing or maturity picture as evidence of an actual
schedule. If you subtract fixed padding from both ends of each bar, a two-week
bar is no longer twice a one-week bar: map durations to the full axis unit and
put breathing room above and below the row instead. Decorative spacing must not
distort data proportions.

### Feedback -> revise -> re-verify: put conditions on the return path

Forward delivery and feedback flow in different directions. Merging request and
response into one double-headed arrow hides what comes back.

Show what is reviewed, the acceptance criterion, who revises on failure, where
re-verification happens, and the output after passing. Route the return path
outside the main flow and label it, e.g. "not met -> revised draft". Drawing a
loop does not prove continuous improvement happens.

### Overview -> focus -> detail: keep context and identifiers

When tracing one part inside an overall analytic frame, keep item IDs, order,
comparison axes, and units across the detail pages. Unselected parts can remain
as quiet context instead of disappearing. Turn the detail panel into the
selected item's evidence, verification, and status.

The main argument must be visible without animation or clicks, and printed or
PDF output must keep every needed state (use separate slides, not build effects).

## 4. Modern visual rules

Keep the brand's colors, type, and icon set; change the diagram's surface.
Reduce heavy boxes and decorative arrows so that **relationship, reading order,
and decision point** show first.

| Element | Default treatment | When it should differ |
|---|---|---|
| Classification / explanatory node | Open label or low-contrast fill (`colors.surface_alt`), generous line spacing | Strengthen the border only for activities, deliverables, or items that need to stand out as objects |
| Activity / deliverable | Short verb / concrete noun, thin outline (`colors.line`), restrained corners (`layout.radius`) | Show decision conditions as a separate question and branch outcomes |
| Shared classification | Column headers, whitespace, alignment, faint dividers | Real system or responsibility scope gets a named boundary |
| Connector | Neutral color (`colors.muted`), one consistent weight, arrowheads only where needed | Selected path in `colors.accent` plus a label |
| Dashed line | One meaning defined in the legend | Never use dashes for hypothesis, asynchronous, boundary, and secondary all in one diagram |
| Emphasis | The one path or selection set the current judgment needs | Risk and status also use text or symbols; never color alone |
| Output / conclusion | Concise result or verdict connected to the preceding items | Do not copy earlier content into a big box at the end of the page |

Do not stack bold, fill, border, and shadow on the same element. Choose
straight, elbow, or curved connectors for legibility, not taste. When lines
cross, reconsider hierarchy, reading direction, or a separate detail page before
decorating the lines.

The `diagram` layout's grid placement suits diagrams where **alignment itself is
the relationship**: comparison, correspondence, time axes. Explicit nodes, edges,
and groups suit branching, convergence, and nested boundaries. Do not hand-list
coordinates for a complex graph when the grid can place it, and never let the
tool decide the kind of relationship for you.

## 5. Verify at slide size

Text in an inserted picture is not the size the reader sees. If a diagram or
chart is inserted as an image:

```text
display scale     = min(frame width / image width, frame height / image height)
displayed size pt = source font size x display scale
```

Prefer native shapes, which avoid the problem. Either way, diagram labels should
reach `type.body`, full-width reading text `type.lead`; `type.min` is a floor no
text may go below, not a design target. Check labels on connectors between
nested nodes too.

Aspect ratio and node count do not decide pass/fail. Measure whether text and
flow read in the actual space. If it does not fit, fix in this order:

1. Remove duplicate wording and unnecessary decoration.
2. Change column/row arrangement, main-flow direction, or grouping while keeping
   the relationship.
3. Split into overview and detail, linked by IDs.
4. Rebuild and render again: check text, line crossings, labels, the content end
   at `layout.body_bottom`, and the clear band above `layout.footer_y`.

```bash
python scripts/build_deck.py deck.yaml -o out/deck.pptx
python scripts/render_deck.py out/deck.pptx
python ../pptx-layout-audit/scripts/deck-craft-lint.py out/deck.pptx
```

For spotlight or stepwise sequences, check every slide in the sequence, not just
the first. Passing automated checks does not replace a review of meaning and
appearance.

## 6. Final questions that read the diagram's logic

- Can the headline's judgment actually be found in the diagram?
- Can you explain the relationship each line and spatial placement claims in one
  sentence?
- Does it imply any direction, precision, containment, total, or completion
  status without evidence?
- Do IDs, names, and counts match across the candidate list, diagram, and detail
  panel?
- Are join conditions and failure paths of parallel work shown as far as needed?
- After a selection, are the action, owner, and evidence to check present?
- Can relationship and status still be read with the accent color removed?
- Have you kept "the layout looks better" separate from "readers understand it
  better"?

This is not a blanket scorecard. Apply only the questions that match the
relationship the diagram claims, and record defects found and fixes made in the
QA notes.
