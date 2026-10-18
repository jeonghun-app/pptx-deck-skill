# Layout craft: turning meaning into surfaces, lines, and text

This reference is about **building the chosen meaning out of actual shapes,
lines, and text**. Use it with [analytical-methods.md](analytical-methods.md)
for story and argument and [decision-diagrams.md](decision-diagrams.md) for what
relationships mean.

The numbers below are **starting values and worked calculations** for the
default brand profile (960 x 540 pt canvas). They are not universal PowerPoint
norms. The deck's brand profile (`brand/brand.yaml`), `brand/guidelines.md`, the
presentation setting, and an explicit company template take precedence.

## 1. Draw the page structure first, then make shapes

Describe the page as `claim -> order in which the evidence is read -> the
difference needed for the judgment`. Headline, analysis, and interpretation must
not repeat the same sentence three times.

Do not start by duplicating boxes on a blank slide. Decide three things first:

1. **Alignment lines:** body left edge, column boundaries, shared rows, the start
   line of headline and body.
2. **Relationship areas:** criteria and options, inputs and outputs, overview and
   detail.
3. **Focus:** the difference or path the reader must find on this page.

Placing similar shapes is not the same as making items comparable on the same
basis. For comparison fix the rows first, for sequence the direction, for
containment the boundary. A simple explanation may need only an aligned headline
and body, no shapes.

An optional lead line and an exhibit label (one line above the exhibit carrying
metric, unit, and period) each need a height budget within the body band.

## 2. Compute margins, gaps, and insets separately

| Level | What it controls | What to check |
|---|---|---|
| Page margin | Distance from content to canvas edge | Same start and end lines on pages of the same kind (`layout.margin_left`, `layout.margin_right`, `layout.body_bottom`) |
| Region gap | Distance between distinct evidence, columns, phases | Independent regions separate, yet the main exhibit keeps reading room (`layout.gutter`) |
| Element gap | Distance between label, icon, description, rows | Constant rhythm between elements of the same role |
| Shape inset | Distance from border to content | Actual content area left after text, icon, and header |
| Optical clearance | Distance from actual glyphs and strokes to surroundings | Long last lines, descenders, icon outlines, checked in the render |

Do not cover a shortfall at one level by blindly adding space at another. If text
inside a shape feels cramped, widening the gap outside the shape does not fix it.
Whitespace is not leftover area; it is the spacing that expresses relationships
between pieces of information.

With the default profile the horizontal body runs from x = 64 to x = 896 pt, a
width of 832 pt. Calculate column widths before placing; do not duplicate and
eyeball.

```text
n equal columns: column width = (available width - (n-1) x gap) / n
3 columns, gap 18 pt: (832 - 36) / 3 = 265.33 pt
comparison table:      criterion 136 + option 348 + option 348 = 832 pt
```

The 136 pt criterion column is a design value for this example; change it for
description length, units, and the comparison structure. Making the criterion
column as wide as the option columns is not the default. When you widen the
horizontal space, do not scale insets and type with it.

When moving a layout to a different aspect ratio, never scale x and y by
different factors. Take the relationships and alignment lines and recompose them
on the new canvas. If you show an entire picture as a reference image, keep its
aspect ratio and leave the remaining space empty.

For two equal-weight content blocks of different heights, also check vertical
balance **per block**. A short row list aligned only to the top of a tall panel
can look like it floats. If rows are not directly compared across the two, try
aligning the list's visual center with the panel, while keeping row spacing,
column start lines, and divider-to-text distance. Do not apply this where row
correspondence is the point, as in a table.

Treat a picture and its caption as one unit. If the picture is narrower than its
column, decide how picture and actual caption balance within the column. Do not
mistake an invisible full-column caption box for the picture's visual width.
After moving, confirm the caption's text box is still inside the column and
slide bounds.

## 3. Distinguish border alignment from glyph alignment

Think of three rectangles for every shape:

```text
outer rectangle:  the shape's x, y, width, height
text body:        outer rectangle minus left/right/top/bottom insets
actual glyph area: the rendered area after paragraphs, font, wrapping, icons, bullets
```

This is the default model for a rectangular text frame. Circles, diamonds, and
custom shapes can have their own text rectangles, so "outer minus insets" does
not certify their content area. For those shapes, consider placing the content
in a separate rectangular text box.

Two shapes with the same left edge but different insets start their text on
different lines. Two text boxes with the same center can look off-center because
of spaces, different fonts, or different line counts. Choose first whether you
are aligning borders, content, or baselines.

**Paragraph alignment, text-box alignment, and content-block placement** are
separate decisions. If a short step name and its description each sit in a box
fitted to their content, you can center both boxes on the node center: the
paragraphs stay left-aligned, yet name and description share one visual axis.
Alternatively, one wide text area with centered paragraphs achieves the same
intent. Check the existing object's width, insets, and inheritance, and build
one way consistently.

A symmetric composition for short steps or a hub can coexist on one page with a
shared left line for long descriptions and icon-plus-text rows. Do not turn the
centering of a few labels into a page-wide center-alignment rule.

| Content role | Default alignment | Check before making an exception |
|---|---|---|
| Multi-line description or condition | Left, top | Could it become a short one-line label? |
| Short symmetric step or verdict label | Center horizontally and vertically allowed | Does reading order stay the same when line counts differ? |
| Icon + name + description | Fixed icon column + left-aligned text column | Text not centered across the whole shape |
| Description cells in a comparison table | Left, same start line per row | Comparison basis holds as sentence length varies |
| Compared amounts, quantities, ratios | Right or decimal-aligned | Units, digits, and precision match |
| Numbers, dates, identifiers | Left or center by role | Not right-aligned just because they are digits |
| Boundary name | Fixed header position inside the boundary | Inner nodes do not overlap the header area |

Never position content with spaces, repeated tabs, or empty paragraphs. Build
icon, text, and badge as one role unit and place that unit. A bullet's text start
cannot be computed from shape insets alone; include paragraph indent and hanging
indent and check where the first glyph actually starts. Compute table cells from
cell margins and merged areas; do not add a shape's default inset again. Do not
mechanically multiply text insets by a group's scale factor: distinguish the
outer transform, the actual inset units, and the glyph render.

Apply optical correction only after shared coordinates, fonts, and insets match.
If you corrected for an icon's transparent area or a typeface's shape, record
why. Never nudge same-type nodes one by one to fix different problems.

## 4. Design line count and area before reducing font size

Body text and diagram labels play different roles. Keep the brand type scale
(`type.lead` full-width, `type.body` narrow columns and labels, `type.caption`
sources, nothing below `type.min`). Do not adopt small document-style type as a
presentation target.

When building a shape, estimate the line counts of name, description, and
condition first:

```text
required height = top inset + title line height x title lines
                + title/description gap + body line height x body lines
                + bottom inset
line height     = font size x type.line_spacing (type.heading_line_spacing for headings)
```

This is a height budget. It does not fully predict glyphs or PowerPoint's
paragraph layout, so verify in the render. Test the representative node with the
longest realistic text before duplicating it. If one node in a row grows, review
the whole row's height, column width, or a detail split.

- Distinguish headline-to-first-paragraph spacing, paragraph spacing, and line
  spacing inside a shape.
- Do not apply both line spacing and space-after so that one item floats.
- Check short last lines, lines holding only a parenthesis, and an isolated
  product name or unit on its own line.
- Break headlines manually only at meaning boundaries; recheck after changing
  width or font.
- Emphasize key nouns or conditions selectively; never bold a whole sentence.
- Auto-shrink proves the text fits, not that the layout reads well. Do not rely
  on it.

The longer the sentence, the more a ragged centered start line costs. Keep
descriptions on a clean left line and reserve centering for short symmetric
labels.

## 5. Design repeated shapes as small components

First test one representative shape with the shortest and the longest text. Then
duplicate it for the same role. Never redraw each shape "about the same".

A unit is usually `surface/border + icon column + name + optional description`.
All text can live in one shape, or, when different alignments are needed,
separate native text boxes can be grouped as one role unit.

| Shape decision | Starting point | Change when |
|---|---|---|
| Fill | Open area or quiet fill (`colors.surface_alt`) | Showing an actual selected state or an important result |
| Outline | Thin, consistent line (`colors.line`) | A real system or responsibility boundary has its own defined grammar in `brand/guidelines.md` |
| Corners | Same treatment for the same role (`layout.radius`) | Brand boundary rules say otherwise |
| Aspect ratio | The size content and relationship need | Never stretch a box just to fill the frame |
| Emphasis | Focus on one path, row, or key difference (`colors.accent`) | Warnings and status also get text or symbols |
| Depth order | background -> boundary -> connector -> node -> label/annotation | Verify against the meaning of actual crossings and overlaps |

Stacking a large dark fill, heavy border, bold text, accent color, and shadow on
one object makes form louder than content. Pick the emphasis channel you need and
remove the rest. Do not enlarge every node to make the page look less empty.

Be wary of scaling a whole group so that text, lines, and icons grow with it.
When a component's frame changes, re-place name, description, icon, and spacing
by role. Check that nodes with different line counts keep the same internal
alignment rule.

## 6. Connect lines after placing nodes

Reserve the main-flow rows and columns, the shared positions for branches and
joins, and the outside space for return paths first. When line direction carries
meaning, check the connection sites and what each end is attached to. Make sure a
line is not attached to a text box next to the visible box instead of the box
itself.

- Distinguish classification lines from directional delivery lines.
- Use a shared branch column and join column so the same relationship reads in
  the same rhythm.
- Keep lines out of the actual glyph area, not just the text body.
- Place a line label near its segment, but not where it reads as another node's
  description.
- Route return lines outside the main flow, with their condition.
- Before resolving with long crossing diagonals, change node order, columns, or
  split to a detail page.

Attach a condition label to the segment it explains. Put a legend that explains
line types in a clearly defined place, such as a separate area above the
boundary. If it sits on the right, align the legend box's right edge with that
boundary or the body's right edge; moving a legend is not the same as
right-aligning its paragraphs. If you move a lower row of nodes, recheck its
connectors, descriptions, and source line to keep flow and spacing.

Connector coordinates and connector attachment are separate checks. That a
native line can be moved does not mean it follows its nodes when they move; use
real connectors (`deckkit` `connect()`) glued to shapes when it must. An open
polyline drawn with `path()` (loops, routed returns) is not glued and must be
rechecked by hand after nodes move.
Do not judge the actual path of curved, rotated, or custom connectors from their
outer rectangle.

## 7. Build tables as one system

When rows and columns map information, prefer a native table (`table` layout or
the `deckkit` table primitive) or one declarative grid. If you imitate a table
with separate text boxes and lines, badges and helper shapes must move with their
row when row height changes.

1. Decide the comparison criteria and each column's data type.
2. Allocate width to the long description column first.
3. Fix insets and alignment by role for header, body, and notes.
4. Verify actual height with the longest row.
5. Emphasize only totals or the decisive difference, sparingly.
6. Reserve space for the source line below the table and for the footer.

After increasing row height, check that independent badges outside cells did not
stay at the old position, and that the recommendation badge sits on the option
the text recommends. Visual emphasis is part of the decision, so include it in
the content review.

## 8. Review "looks good" as concrete questions

| Visible problem | Cause to check first | Fix |
|---|---|---|
| Clumsy and heavy | Large dark fills, duplicated emphasis, excess outlines | Keep only needed boundaries and emphasis; rebalance hierarchy |
| Everything big, no focus | Enlargement without roles, nodes filling empty space | Redesign text, icon, and frame sizes separately |
| Centered but looks crooked | Different insets, spaces, transparent areas, font | Check against the content area and actual glyphs |
| Feels untidy | Slightly different start lines, gaps, line counts, corners | Align one reference line per role |
| Unclear where to start | Equal contrast everywhere, arrows without relationships | Focus on the main flow and the difference that supports the headline |
| Dense and cramped | Headline, table, and footer space not budgeted separately | Restructure columns, wording, or overview/detail |
| Differs between render and PowerPoint | Font, line spacing, cell height, theme inheritance, group transforms | Check the final app render and the saved properties together |

This table is not a taste score. Geometry checks judge alignment, margins, and
gaps (`python ../pptx-layout-audit/scripts/inspect-layout.py out/deck.pptx --output audit/layout.json`,
`python ../pptx-layout-audit/scripts/deck-craft-lint.py out/deck.pptx`); the
rendered app output judges fonts, wrapping, and table growth
(`python scripts/render_deck.py out/deck.pptx`); visual review judges reading
order and visual weight. Record problems found and fixes made, and never claim
an environment was checked when it was not.

## 9. Design cover, dividers, and closing with the deck

A multi-slide deck includes section dividers at real chapter transitions and a
closing slide. Budget the dividers and the closing within the requested slide
count from the start.

| Role | Content | Composition |
|---|---|---|
| Cover (`cover`) | Topic, verified presenter and event information | Brand cover background (`backgrounds.cover`), wide title area at `type.hero` |
| Divider (`section`) | Short chapter name, optional number and one-line guide | More open than content slides; repeated title start line |
| Last content slide | Conclusion and next action derived from the evidence | Completes the judgment alongside its evidence |
| Closing (`closing`) | `copy.closing_title` (default "Thank you"), verified contact details only | Same background family (`backgrounds.closing`); check logo and text contrast |

Place dividers where the argument changes. Do not add formal dividers to a short
explanation without chapters, or repeat the same divider before every topic. The
conclusion-headline rule does not apply to cover, divider, or closing slides.

Use a Q&A slide only when there is actual Q&A time; it does not replace the
closing automatically. If there is an appendix, confirm the last real slide is
the closing. A single-slide request, an explicit company template, or another
user instruction takes precedence.

Match text and logo to the background: dark text and the standard logo on light
backgrounds, `colors.on_dark` text and `chrome.logo.path_on_dark` on dark ones.
Verify contrast in the render. Do not blow up text or boxes to create a sense of
transition; let whitespace do it.

### For Korean-language decks

- Optical clearance: check Korean final consonants (받침) and the last line of
  long wrapped text against borders, not just Latin descenders.
- The closing title may be `감사합니다` instead of "Thank you"; set
  `copy.closing_title` in `brand.yaml` rather than editing slides.
