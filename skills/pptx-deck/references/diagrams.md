# Relationship diagrams: design, build, refine

Design the relationship and its scope first, then build the diagram from an
editable source. Automatic placement saves coordinate work; it does not make the
diagram correct, aligned, or readable. Check it at real slide size.

A technically correct graph and a slide that presents well are two separate
reviews. Do not call a diagram finished because the layout ran or because every
label is above `type.min`.

For system and architecture diagrams (zones, components, data stores, external
actors), also read [architecture-diagrams.md](architecture-diagrams.md).
For numeric relationships, use a chart instead: [data-viz.md](data-viz.md).

## 1. Pick the representation from the relationship

| Relationship | Default representation | Why |
|---|---|---|
| Branching, merging, nested boundaries | `diagram` layout (nodes on a grid, groups, edges) | Native shapes and connectors stay editable and aligned |
| Small flow built on repeated rows/columns | `diagram` layout | The grid fixes alignment and type hierarchy |
| Short linear sequence, no branches | `process` layout | Simpler than a graph |
| Activities and events on a time axis | `timeline` layout | Dates and durations share one axis |
| Same-criteria comparison, mapping, target hierarchy | `table` layout | Row/column alignment *is* the relationship |
| Request/response over time between participants | `diagram` with one column per participant and one row per message, or `custom` | Keep each participant's lane and the message order |
| Unusual geometry (radial, overlapping regions, freeform) | `custom` with deckkit primitives | Full control, still native |
| Very large or deeply nested graph | External layout engine to PNG, placed with `image` | Last resort; loses editability |

Do not list hand-computed coordinates for every box and line of a complex graph.
Do not turn a comparison table or schedule into graph nodes either: that destroys
the meaning carried by alignment. A generated bitmap is not a substitute for an
editable, verifiable relationship diagram.

## 2. Implementation options

### Option 1 (default): the native `diagram` layout

Nodes are placed on a grid by `col`/`row`; optional `groups` draw labeled
boundaries around nodes; `edges` connect node IDs with a semantic `kind` and an
optional `label`. The builder renders native, editable shapes plus elbow or
straight connectors attached to node ports; an edge whose two ends use the same
side (`from_side: bottom, to_side: bottom`) is drawn as a loop around the row.
Example (all keys: [layouts.md](layouts.md#diagram)):

```yaml
- layout: diagram
  title: Rejected drafts return to the author with a reason
  nodes:
    - { id: draft,   label: Draft,          col: 0, row: 0 }
    - { id: review,  label: Review,         col: 1, row: 0 }
    - { id: gate,    label: "Criteria met?", col: 2, row: 0, kind: decision }
    - { id: release, label: Release,        col: 3, row: 0 }
  groups:
    - { label: Editorial team, nodes: [draft, review] }
  edges:
    - { from: draft,  to: review,  kind: flow,     label: review copy }
    - { from: review, to: gate,    kind: flow }
    - { from: gate,   to: release, kind: flow,     label: all met }
    - { from: gate,   to: draft,   kind: return,   label: not met · revise,
        from_side: bottom, to_side: bottom, highlight: true }   # loops under the row
```

Build and inspect:

```text
python scripts/lint_deck.py deck.yaml
python scripts/build_deck.py deck.yaml -o out/deck.pptx
python scripts/render_deck.py out/deck.pptx
```

### Option 2: `custom` Python with deckkit primitives

Use when the geometry does not fit a grid. Compose `box`, `text`, `connect()`
(a native connector glued to two shapes), `path()` (an open polyline, for loops
and routed returns), `line`, and `image` from `scripts/deckkit` with brand
tokens only (no literal hex or font names). Keep the same rules below: ports, connector semantics, one
highlighted path, role-based type.

### Option 3 (last resort): external layout engine to image

Only for graphs too large or nested to place by hand (dozens of nodes, many
crossing containers). Lay out with D2 or Graphviz, export a **high-resolution
PNG** (at least 2x the placed size), and place it with the `image` layout.

- You accept loss of editability: text cannot be fixed in PowerPoint, and lint
  cannot measure the type inside the picture.
- Keep the source file (`.d2`, `.dot`) next to the deck and regenerate from it.
  Never hand-edit the exported picture.
- Set the engine's fonts and colors from brand tokens before export; an external
  file does not inherit the deck theme.
- Compute displayed text size (section 6) by hand, because the image is scaled.

Do not describe an image-with-source as equivalent to native editing.

## 3. Boundaries and grouping

A group can mean real containment (a zone, an owner, a runtime, a session) or a
logical category. **Name what the boundary means, in its label and its style.**

- Real containment: a named boundary. Confirm each member actually belongs.
- Items of the same kind: an open column heading, whitespace, or a hairline in
  `colors.line` is often enough; no box needed.
- Parallel outputs: show the join condition explicitly. Being in the same box
  does not create an order.
- Do not add a boundary only to fill the aspect ratio. Do not remove a needed
  boundary only to make layout easier.
- Do not wrap every group in the same dashed accent outline: boundary, emphasis,
  and uncertainty become indistinguishable. Give dashes one meaning per diagram
  and add a legend if it is not obvious.
- Default boundary: name plus a thin line, no fill. A light `colors.surface_alt`
  fill is acceptable for steps of a small process. Do not use large dark boxes
  just because a node is important; let position, alignment, a short name, or an
  icon carry importance first.
- Compare the gap from a boundary header to the first child with the space under
  the last child. Do not stretch a boundary to the frame and leave a large empty
  area inside it.
- Nested boundaries keep three separate allowances: the title band, space above
  the first child, space below the last child.

## 4. Connector grammar

| `kind` | Meaning | Drawing |
|---|---|---|
| `decomposition` | Part-of / breaks down into | Line, **no arrowhead** |
| `flow` | Something passes from A to B | Arrow; label names what is passed |
| `return` | Reply, rejection, feedback path | Arrow in the reverse direction; keep it distinct from the request |

- Name what flows ("review copy", "invoice"), not just that something flows.
- A decision is a **node** with `kind: decision` (drawn as a diamond), not an
  edge kind. Its outcomes are ordinary `flow` (or `return`) edges leaving the
  diamond, each labeled with its outcome; state the criterion on the slide.
- Label both outcomes of a decision.
- Do not merge request and response into one double-headed line.
- A dashed line meaning "hypothesis" carries the label "hypothesis" and the
  evidence still to be checked.
- Use sequence numbers only when the real order has been verified.
- Prefer straight and elbow connectors. A diagonal is acceptable when no clean
  orthogonal route exists; it is not banned.
- Return or configuration arrows that run against the main flow stay that way if
  that is what they mean. Simplifying the look must not drop direction,
  ownership, or conditions.

## 5. One highlighted path

Highlight at most one path (the one the headline is about) with `colors.accent`
and a slightly heavier line; everything else stays in `colors.muted` / `colors.line`.

- Node and edge emphasis must mean the same thing.
- Several options that form one decision set may be highlighted together; do not
  put different meanings on the same accent.
- Labels and branch outcomes must still read without color.

## 6. Fit to the real space

First measure the area the diagram actually gets: content width between
`layout.margin_left` and `layout.margin_right`, height from below the title (or
lead) to `layout.body_bottom`, minus any caption. Do not use a fixed aspect ratio
or node count as a pass condition. About 2:1 to 3:1 is a starting point for a
full-width diagram; correct relationships and legibility win.

For anything scaled (an image, or a group you resize):

```text
scale = min(placed width / source width, placed height / source height)
displayed size = source size × scale
```

### Role-based typography

Size text by role, not by available space. Starting ranges on the 960x540 canvas:

| Role | Start at | Check |
|---|---|---|
| Node / step name | `type.body` to about `type.body` + 2 pt | 1–2 lines; the path is seen before the words |
| Real boundary name | `type.caption` to `type.body` | Does not overpower the nodes inside |
| Role, condition, parameter | `type.caption` to `type.body` − 1 | Distinct from names; not mistaken for optional |
| Edge / owner label | `type.caption` | Close to its line; does not compete with other text |

`type.min` is the floor, not a target. Do not drop the whole diagram to the floor.
Also check the ceiling: a small graph blown up to fill the frame makes every label
near `type.title` size, which reads as crude. Do not enlarge a simple diagram to
fill empty space; leave the space or add a real caption. Full-width explanation,
tables, and code keep their own type rules.

### When the diagram gets too long or too flat

1. Move long sentences out of nodes into a caption or notes; keep any condition
   the decision depends on.
2. Keep the main flow on one row; stack parallel branches above and below it.
3. Try the other direction (left-to-right vs top-to-bottom).
4. Remove groups that represent no real relationship (keep the needed ones).
5. Split into an overview and a detail slide that reuse the same node IDs.

Never add nodes or fake dependencies to fill space.

## 7. Repeated relationships share rows, columns, and ports

- Customer A/B → validation → Role A/B: put each A on one row and each B on the
  other, at both ends.
- An icon sits beside its node name, with the same size and visual center
  everywhere. Do not stack icon above title above description when the text is short.
- Icon sizes: about 24 pt for components/services, 18–21 pt for roles and
  generic objects. Same meaning, same size.
- If a function name and a one-line description repeat, consider two columns of
  the same row instead of tall cards.
- Connectors attach to the node's defined left/right/top/bottom ports, never to
  the title text. Prefer short horizontal runs and a shared branching column.
- An endpoint on a port is not enough: check the arrival direction. A line that
  enters a top port must end pointing down.
- Put edge labels above or below the line, close to it. A long label must not
  make the line look broken, and must not overlap another line or node; move it
  or open a channel.
- A node with icon, title, and description has an outer rectangle and an inner
  text area; check the text area's insets separately from the shape's position.

## 8. Rebuilding a diagram from an existing PPTX

When the original is native shapes, extract the **connections, directions,
scopes, and selection state** along with the labels. A connector's `headEnd` /
`tailEnd` element can exist with type `none` or be omitted: that is not an
arrowhead. Confirm against the original's rendering. Do not claim a slide was
rebuilt when text was only laid over a low-resolution screenshot.

## 9. Preview checks

Run the build and render, then review the contact sheet and each changed slide:

```text
python scripts/build_deck.py deck.yaml -o out/deck.pptx
python scripts/render_deck.py out/deck.pptx
python ../pptx-layout-audit/scripts/inspect-layout.py out/deck.pptx --output audit/layout.json
python ../pptx-layout-audit/scripts/deck-craft-lint.py out/deck.pptx
```

1. Meaning: directions, boundaries, ownership, and conditions match the source
   or the previous version.
2. Every label fits its node; nothing overlaps; no line passes through another node.
3. Displayed text sizes follow the role hierarchy, within floor and ceiling.
4. Insets inside nodes and boundaries are even; header-to-first-child and
   last-child-to-bottom spaces are balanced.
5. Connectors leave and arrive at ports in the right direction; edge labels sit
   on their own line.
6. Exactly one highlighted path, readable without color.
7. The diagram ends above `layout.body_bottom`; the footer band is clear.
8. Open the PPTX once in PowerPoint and drag a node: glued connectors (drawn
   with `connect()`) should follow. Same-side loops are drawn with `path()` and
   do not follow; recheck them after moving nodes.

Passing automated checks is not proof of visual quality, reader comprehension,
or that the real system behaves as drawn. Report what was checked.
