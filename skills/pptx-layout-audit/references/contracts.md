# Measurement and finding contracts

Shared formats for every review role: how findings are written down, how
coordinates are normalized, and which layout expectations `inspect-layout.py`
can check for you.

## When to use

- Any review role writing a report file.
- Declaring explicit alignment, gap, padding or edge expectations for
  `inspect-layout.py --contracts`.
- Testing this skill itself, where results must be tied to one snapshot of the
  skill.

## Inputs

**Revision identity.** Every finding refers to an artifact hash and stable
shape IDs or names. The coordinator gives each agent its own report path.
Findings travel as files; an agent's return message carries only coverage and
the issues that need action.

When the skill itself is under test, snapshot its instructions, references and
helper scripts before the first run and tie every result to that snapshot.
Finish editing the skill before validating the installed final version; results
from an earlier snapshot remain historical evidence only.

**Units.** Normalize coordinates before comparing them:

- 1 inch = 72 points = 914400 EMU.
- A 96-dpi pixel is 9525 EMU (0.75 pt); convert any px value first.
- Text-body insets (`lIns/rIns/tIns/bIns`) shrink the content box and are stored
  in EMU.
- Table cell margins (`marL/marR/marT/marB`) are EMU in OOXML; check the unit
  your authoring API expects (python-pptx takes a `Length`, i.e. EMU).
- Keep the intended geometry and the rendered glyph bounds as two separate
  records.

`inspect-layout.py` reports coordinates and text insets in points.

**Contract file (optional).** Contracts refer to **top-level native shape IDs**,
never to XML enumeration order, which is not stable:

```json
{
  "tolerance_pt": 0.75,
  "rules": [
    {
      "type": "alignment",
      "slide": 2,
      "objects": [4, 7, 10],
      "edge": "left",
      "tolerance_pt": 0.75
    },
    {
      "type": "text_alignment",
      "slide": 2,
      "objects": [4],
      "horizontal": "left",
      "vertical": "top"
    },
    {
      "type": "containment",
      "slide": 6,
      "parent": 3,
      "children": [4, 5],
      "padding_pt": [24, 9, 9, 9]
    },
    {
      "type": "gap",
      "slide": 6,
      "first": 4,
      "second": 5,
      "axis": "x",
      "minimum_pt": 12
    },
    {
      "type": "directed_edge",
      "slide": 6,
      "connector": 9,
      "source": 4,
      "target": 5,
      "source_port": "right",
      "target_port": "left",
      "maximum_endpoint_gap_pt": 2
    }
  ]
}
```

- `padding_pt` is ordered top, right, bottom, left. A shape's explicit text
  inset is already part of its native content box, so containment uses the
  larger of the requested padding and the explicit inset on each side; the two
  are not added together.
- A route made of several segments is written `connectors: [9, 10, 11]`, in
  source-to-target order. Only the last segment carries the target arrow; the
  segments in between simply meet.
- A table-wide `text_alignment` contract applies to every paragraph in every
  cell. Headers, descriptions and numbers usually need different alignment, so
  write separate contracts for those cell roles instead of one uniform rule.

## Procedure

1. Record the artifact hash and the shape IDs you will reference.
2. Convert every measurement to points (or EMU) using the units above.
3. Compare like with like, using the role map:

   | Role | Compare it with |
   |---|---|
   | Deck heading | The same master or content band |
   | Paragraph | Actual text start after bullets or rules; line rhythm |
   | Node label | The owner's content box, its icon rail, sibling nodes |
   | Scope heading | The reserved header band and the first child |
   | Table | Each column's data type, header/body inset, numeric precision |
   | Edge label | Its route corridor, the nearest unrelated node, what the branch means |
   | Footer/page | Footer baseline and safe area; the body type minimum does not apply |

   Do not run pairwise overlap checks over every rectangle. Text inside a
   container, a background behind content, and an icon inside a node are all
   intended containment. Judge unexpected overlap by ownership and z-order.
4. Write the expectations that matter as a contract file and run
   `inspect-layout.py --contracts <file>`. Without contracts the run is an
   inventory only, with status `inspected`.
5. Read the exit code: `0` inventory succeeded or every declared check passed;
   `1` a failure was proven; `2` invalid input or I/O failure; `3` some checks
   are unverified and none proved a failure.
6. Combine four kinds of evidence when you have them: the source declaration
   (design intent), the OOXML (stored native properties), the application output
   (rendering in that environment), and visual review (composition and semantic
   clarity). Whether a node can be dragged with its lines attached is a separate
   editability check on top of these.

## Report

Every role writes this shape:

```json
{
  "role": "typography",
  "artifact": "out/deck.pptx",
  "artifact_sha256": "computed hash",
  "coverage": [
    {"slide": 1, "checks": ["alignment", "spacing"], "status": "reviewed"}
  ],
  "findings": [
    {
      "id": "type-001",
      "slide": 3,
      "object": "node-title",
      "severity": "major",
      "evidence": "Rendered line crosses its owner boundary by 4.5 pt.",
      "recommendation": "Widen the node and preserve the sibling gap.",
      "status": "open"
    }
  ],
  "exceptions": [],
  "limitations": []
}
```

Severity reflects the effect on the audience: `critical` changes meaning or
loses content, `major` hurts readability or blocks a required edit, `minor` is a
visible inconsistency. A matter of taste can be noted as an observation without
calling it a defect. A finding's status is `open`, `fixed`, `accepted` or
`unverified`. Report only what you found; do not pad a role with invented
findings.

## Pitfalls

An automated pass covers only the declared checks, within the scope the
inspector supports. What each check does and does not establish:

| Check | What it verifies in the stored file | What it leaves open |
|---|---|---|
| `alignment` | Requested edges or centers of the outer shape bounds | Insets, paragraph starts, optical alignment |
| `gap` | Signed distance from the end of the first shape to the start of the second on the chosen axis | Rendered glyph clearance, intended ownership |
| `text_alignment` | Explicit paragraph alignment and text-body anchor; table anchors come from `tcPr` | Inherited or missing properties, the actual visible text position |
| `containment` | Child outer bounds inside the parent's supported content envelope | Non-rectangular text geometry, nested content, rendered glyph fit |
| `directed_edge` | Straight segment endpoints, flips, direction and explicit arrow decorations | Semantic intent, generic site-index meanings, attachment while dragging |

- Missing properties are `unverified`. Do not treat them as zero or assume a
  convenient inherited value.
- The script understands straight-line flips and explicit head/tail
  decorations. Curved or bent geometry, rotation, inherited defaults and nested
  text geometry need extra inspection, and that limitation stays visible in the
  report.
- Table `frame_bbox_pt`, `grid_size_pt` and the structural cell rectangles are
  three separate measurements. A frame/grid mismatch is reported, not repaired
  by scaling stored row heights. Merged-cell effective geometry and nested table
  transforms remain unverified. Ordinary-shape `bodyPr` insets are not table
  `tcPr` margins.
- Axis-aligned group coordinates are inventoried recursively, but contracts
  select top-level shape IDs only. Group scaling does not scale physical text
  insets, so nested text content stays unresolved. Envelopes that are zero or
  negative keep their sign; they signal a structural risk, not proof that an
  application clips the text.
- A stored connector endpoint ID names the attachment target; its site index
  depends on that target's geometry. Neither proves the attachment survives
  when a node is moved: editable lines are not the same as lines that stay
  attached.
- The CLI never edits its input. It refuses an output path that resolves to the
  input file (including through symlinks and hard links), and records source
  hashes before and after reading. Its structural checks cover duplicate shape
  IDs and duplicate paragraph-property elements; it is not a full OOXML schema
  validator.
