# Diagram, arrow and containment review

Checks what edges, nodes and nested scopes mean and how they are drawn. Work from
the source relationship model and the final rendered slide together.

## When to use

- An arrow points the wrong way, misses its node, or runs through text.
- A boundary is too tight, too loose, or collides with an external route.
- As the diagram role inside a full [layout review](layout-review.sop.md).

## Inputs

| Input | Needed | Notes |
|---|---|---|
| Artifact path | yes | Absolute presentation path, plus any declarative source (the `diagram` layout's nodes, edges and groups in `deck.yaml`) |
| Report path | yes | Absolute path the coordinator assigned to this role |
| Slides | no | Defaults to every slide with a diagram or nested shapes |
| Preview directory | no | Bounded previews rendered by `render_deck.py` or PowerPoint |

If the artifact or report path is missing, ask for both in one question.

## Procedure

1. **Rebuild the meaning first.** Map which node owns what, which way requests
   and responses travel, where branches split, and what each line style means.
   - For every edge, write down its source, its target, and why it points that
     way.
   - Separate real containment from shapes that are merely close together or
     decorative.
   - Keep verified/pending distinctions and disclosure labels intact.
   - If the meaning is ambiguous, flag it before proposing any geometric
     simplification.
2. **Inspect routes and owner geometry.**
   - Compare source and target ports with the outer node boundary and the
     attachment that was intended.
   - Check arrowhead placement, endpoints that overshoot, and accidental
     reversals.
   - Check crossings, shared branch segments, and that the line style stays the
     same through every bend.
   - Find lines that pass through unrelated nodes, text, or scope headings.
   - Reserve a heading band in each scope, and check the clearance above the
     first child and below the last.
   - After resizing a scope, recheck neighbouring route corridors: better inner
     padding can push the border into an external arrow.
   - Judge node fit with the icon rail, title, detail text and inner insets all
     included.
   - Compare sibling widths, spacing and optical balance, without imposing a
     fixed node count.
   - View at most four previews per checkpoint.
3. **Write the corrections.** For each finding, give the specific source change
   and what must be rechecked after it.

## Report

Write findings to the assigned report path using [contracts.md](contracts.md).
Give stable node and edge IDs and measured endpoint coordinates. Say whether a
line is a glued native connector or an independent line segment that will not
follow its nodes. Every routing recommendation keeps the edge's meaning.

## Pitfalls

- Never replace the slide with a single image; that removes the native
  editability the deck requires.
- A right-to-left configuration edge can be correct while the main request flow
  runs left to right.
- A dashed pending edge stays dashed in the native output, including the short
  vertical pieces at its elbow.
- An arrow that points backward only in the PPTX: inspect line flips, head/tail
  metadata and group transforms.
- A label touching a boundary: check its real glyph width and the owner's
  padding instead of nudging the label in the preview by hand.
