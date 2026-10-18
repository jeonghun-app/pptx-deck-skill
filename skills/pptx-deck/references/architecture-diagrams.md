# System and architecture diagrams

A grammar for showing systems: zones and boundaries, components and services,
data stores, external actors, and the calls between them. It sits between two
other layers:

| Layer | Decides | Read |
|---|---|---|
| Logic | Is this decomposition, cause, flow, choice, or ownership? | [diagrams.md](diagrams.md) |
| Diagram grammar | How scope, components, connections, and numbers are told apart | this file |
| Slide design | Type, spacing, emphasis, density at slide size | brand profile and SKILL.md |

Keep the logic and improve the surface. Adding icons does not make an
architecture correct, and putting things in the same box does not put them in
the same network, account, or trust zone.

Build with the native `diagram` layout (nodes, groups, edges) or `custom`
deckkit code; see [diagrams.md](diagrams.md) for options, sizing, ports, and
preview checks.

## 1. Decide scope first, then place elements

Order: background (light or dark) → boundary structure → components → connections
→ step numbers, if any.

- **A rectangular boundary means real containment**: a trust zone, network
  segment, deployment environment, tenant, region, or ownership/responsibility
  area. Write which one in the label. Keep it visually distinct from decorative panels.
- Do not put a managed or third-party service inside your own network boundary
  because it looks tidier. Draw it where it actually runs and connect to it.
- Different boundary kinds (organization, environment, network, zone) do not
  substitute for each other. Nest them as they are really nested.
- An administrative scope (who manages accounts or policies) is not a hop on the
  request path. Connect the real caller to the real target.
- Do not let a boundary imply an absolute guarantee ("fully isolated", "no
  impact"). State what the separation actually covers.
- An example architecture from a template is a design example. Its components,
  addresses, and call patterns are not evidence for the current system.

## 2. Groups show their kind; the inside stays light

- Default group: **group icon (optional) + name + thin outline, no fill.** Use
  about 1–1.25 pt outlines in `colors.line` or a darker neutral.
- Leave enough room that badge, title, outline, and inner nodes never touch. A
  minimum nesting gap is a floor, not the target spacing.
- Boundary-kind colors are a **category code**, separate from the editorial
  accent. Do not recolor a boundary to emphasize it, and do not explain a
  highlighted path and a boundary category with the same legend. The name and
  line style must read without color.
- If your organization defines boundary colors and dash styles per kind (for
  example: network solid, zone dashed, external generic), record them in
  `brand/guidelines.md` and apply them consistently. Without such rules, use one
  neutral outline for all real boundaries and distinguish kinds by label and
  dash: solid for containment, dashed for a logical zone.
- Not every logical cluster needs a styled group. If no boundary kind fits, use
  a neutral named group or no box at all.

## 3. Icons identify; labels explain

| What you are showing | Use |
|---|---|
| A product, service, or platform component | Its icon from your organization's icon set |
| An individual resource (a queue, a bucket, a role) | The resource icon, if the set has one |
| A scope (network, environment, tenant) | The group badge and boundary |
| Users, documents, generic applications | Generic icons from the same set |
| A policy decision, completed state, or activity | A short label, a step, or a decision shape, not a component icon |

- Icons come from brand `icons.path`. Find keys with
  `python scripts/find_icon.py <keyword>`. Use only icons your organization is
  allowed to use.
- Never crop, rotate, mirror, recolor, distort, or redraw an icon, and never
  substitute a similar-looking icon for a different component. If no icon
  exists, use a text label or a generic icon.
- Within one diagram, the same kind and role use the same icon size; scale
  proportionally only.
- Icon-only nodes carry an explicit empty label or a visible name, never an
  internal key.

## 4. Labels sit apart from icons and stay readable

- Component names: at most two lines, never broken mid-word.
- Do not leave a vendor or product-family prefix alone on the first line; keep it
  with the next word.
- Introduce the full name before using an abbreviation, and do not let two
  abbreviations collide.
- Separate the component name from its role description. Long explanations go
  below the diagram or into speaker notes.
- An icon can sit inside a boundary while its label overflows it. Check the label
  bounds too; wrap the name or give the boundary more inner room.
- Sizes follow the role table in [diagrams.md](diagrams.md#role-based-typography):
  names around `type.body`, roles and conditions at `type.caption`, boundary names
  between them. `type.min` is a floor. Do not copy tiny footer sizes from
  print-style diagram templates onto slides.

## 5. Connections are thin, open, and traceable

- Thin lines (about 1–1.5 pt) with **open (line) arrowheads**. Prefer straight
  and elbow routes; a diagonal is acceptable when nothing cleaner works.
- Flow: arrow plus what is passed or done.
- Classification: line without arrowhead, or just alignment.
- Comparison: if shared rows/columns already show the relationship, add no line.
- Request and response: do not hide both in one double-headed line; draw the
  paths the reader needs.
- A dashed *boundary* style (for a zone) must not be read as an asynchronous or
  unconfirmed *connection*. If dashed connectors mean something, label it or add
  a legend.
- Show external vs internal scope, branches, and the return path. Do not copy an
  old example's stack as a current recommendation.

## 6. Numbered steps match the explanation

- One numbering style per diagram: small circles, same size, same font, in
  `colors.ink` with `colors.on_dark` digits on light slides (inverse on dark).
  Do not color each number by component category.
- Place numbers in reading order, next to the connection or node they describe,
  and repeat the same numbers in the explanation list or notes.
- Use numbers only for a real sequence or for references from the text. Do not
  mix option labels (A/B) with step numbers (1/2), and do not number parallel
  work as if it were sequential.

## 7. Light and dark backgrounds without inverting artwork

- Keep the deck's theme. On a dark slide (`colors.dark`), adapt only **text,
  neutral lines, the outermost boundary, and step numbers** for contrast
  (`colors.on_dark`, `colors.on_dark_body`).
- Do not invert or recolor icon artwork or category colors to white. If an icon
  is unreadable on dark, use the icon set's dark variant or a light slide.
- Do not apply on-dark treatment to light cover art.
- Print or certification-style formats (portrait pages, fixed large type, heavy
  lines) are a separate context; do not declare a general technical deck to be one.

## 8. Checks after building

Check that the diagram **reads with the same meaning**, not that it matches some
template's colors.

1. Do each boundary's name, style, and icon match real containment?
2. Are flow, classification, and comparison lines not swapped?
3. Where it matters, are component, resource, scope, and generic object distinct?
4. Do the numbers match the explanation, and are parallel paths not shown as a sequence?
5. Do badges, headers, nodes, and edge labels stay clear of each other and inside boundaries?
6. Is the displayed type hierarchy (names, roles, boundary names, edge labels)
   intact at slide size?
7. Are template examples, proposed design, confirmed facts, and unconfirmed items
   kept apart (in the slide or notes)?

Run the build, render, and layout checks listed in
[diagrams.md](diagrams.md#9-preview-checks).
