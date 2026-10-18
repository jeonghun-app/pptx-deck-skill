# Typography and alignment review

Checks text alignment, table cells, baseline rhythm and inner spacing on the
assigned slides. The reviewer returns evidence and proposed corrections; the
coordinator edits the source, unless this role was explicitly given its own
non-overlapping edit scope.

## When to use

- Text looks misaligned, clipped, oddly wrapped, or unevenly spaced.
- Table headers and columns do not line up with their content.
- As the typography role inside a full [layout review](layout-review.sop.md).

## Inputs

| Input | Needed | Notes |
|---|---|---|
| Artifact path | yes | Absolute presentation path, plus source or geometry files if available |
| Report path | yes | Absolute path the coordinator assigned to this role |
| Slides | no | Slide numbers to review; defaults to all |
| Preview directory | no | Bounded previews rendered by `render_deck.py` or PowerPoint |

If the artifact or report path is missing, ask for both in one question.

## Procedure

1. **Assign an alignment role to every text object.** Classify headings,
   paragraphs, node labels, evidence captions, tables and footers.
   - Alignment follows the reading role and whether values are compared; no
     single deck-wide setting is correct.
   - Running text is left-aligned. Center only short, symmetric labels.
     Right-align magnitudes that are compared down a column.
   - Numeric identifiers (phone numbers, IDs, codes) are not magnitudes.
   - Compare each object with its actual owner shape and its siblings.
2. **Inspect stored and rendered text.** Measure insets, baselines, wrapping and
   rhythm.
   - Check horizontal and vertical alignment as two separate questions.
   - Include icon columns, bullets, border widths and nested padding in the
     measurement.
   - Compare each table header with its column's body alignment and data type.
   - Look at the rendered glyphs for clipping, unintended wraps, widows and
     collisions. Successful text extraction does not mean the text fits; clipped
     glyphs still extract.
   - Keep deliberate optical alignment where mathematical centering looks wrong.
   - View at most four previews per recorded checkpoint.
   - Note whether each property is explicit, inherited, a default, or
     unresolved.
   - Ordinary-shape insets and table-cell margins are different properties;
     account for merged-cell width.
   - Do not apply group scaling to text insets unless you have confirmed the
     target renderer behaves that way.
   - Keep content width and height signed. A zero or negative stored width is a
     structural risk, not proof of visible clipping.
   - Record paragraph text start, hanging-bullet position and continuation-line
     start as three separate values.
   - Before copying a component across the deck, try it with a realistic long
     label.
3. **Write the findings.** Use the format in [contracts.md](contracts.md).

## Report

Write only to the assigned report path. Each finding names the slide and object
ID, the measurement unit, the evidence, and the impact on the audience. Mark
intentional exceptions and unverified cases separately from defects. Suggest
reflowing, adding padding, or resizing the owner before suggesting smaller type.

## Pitfalls

- A phone number is one identifier. Its digits do not make it a right-aligned
  number.
- A centered node label is judged inside the content area left after the icon
  rail, not inside the node's full outer rectangle.
- Spec and PPTX disagree: compare content-box insets and unit conversions
  (pt vs EMU) first.
- Fonts look different: check what the target application actually substituted
  before changing line breaks, and record the environment where you saw it.
