# Native PowerPoint output review

Checks the PPTX package structure, whether content survived, whether the
required objects are editable, and what the target application actually shows.
Structural evidence and visual evidence are recorded separately.

## When to use

- Before delivering a PPTX that others will edit, present, or repackage.
- When a deck opens with errors, loses notes or links, or renders differently in
  PowerPoint than in the preview.
- As the native-output role inside a full [layout review](layout-review.sop.md).

## Inputs

| Input | Needed | Notes |
|---|---|---|
| Artifact path | yes | Absolute `.pptx` path |
| Report path | yes | Absolute path for this role's findings |
| Source path | no | Authoring content with the expected notes, links, tables or diagrams |
| Render path | no | PNG/PDF exported by `render_deck.py` (LibreOffice) or PowerPoint |
| Application owner | no | The one agent allowed to open or drive the presentation application; defaults to the coordinator |

If the artifact or report path is missing, ask for both in one question.

## Procedure

1. **Inventory the package.** Look at slide size, native objects,
   relationships, notes and text metadata.
   - Record the artifact hash and slide count.
   - Run `scripts/inspect-layout.py` and whatever package integrity checks are
     available.
   - Confirm that required tables, body text and diagrams are native, editable
     objects, and tell them apart from source screenshots, logos, and icons from
     the organization's icon set (`brand.yaml` `icons.path`).
   - Check table cell margins, explicit font runs, paragraph alignment and line
     flips.
   - Follow the real presentation order and the layout/master chain each slide
     uses; part filenames and the first master do not describe the deck.
   - In every paragraph, `a:pPr` appears at most once and first, and
     `a:endParaRPr` at most once and last. Native IDs are unique across all
     object classes on each slide.
   - When repairing repeated properties, keep every rich-text run and hyperlink.
     If a referenced ID is ambiguous, reject it rather than guessing its owner.
2. **Compare with real output.** Check content coverage and how the target
   application renders it.
   - Use output from the target application whenever it is available, and go
     through the application owner so sessions do not collide.
   - Confirm required speaker notes and hyperlinks survive packaging.
   - Look for clipping and font substitution, not only for extracted text.
   - Tie the artifact hash and export hash to the application version actually
     used, and require a readable export file even if the application's API
     reports success.
   - Check which fonts actually paint symbols, not only the declared font
     names.
   - If custom route geometry does not render reliably, a matching native preset
     connector is an acceptable substitute; keep the source/target meaning and
     recheck the final route.
   - Tell a real group apart from independent shapes that only look grouped.
   - Check connector target IDs and the rendered arrow direction; head/tail
     naming in the API does not by itself establish the intended flow.
   - When shapes must move with their nodes, try a representative edit on a
     private copy.
   - List unsupported transformations and untested environments.
3. **Close the structural checks.** Confirm that meaningful section dividers are
   present and that the closing slide is the last physical page of a
   multi-slide deck, unless the template or an explicit slide count says
   otherwise. For defects that reproduce, name the fix at the source level.

## Report

Save the report only to its assigned path. Keep three outcomes apart: structural
PASS, content coverage, and visual review. Name the application and version
only if it was actually used. Record the input hash before and after export so
a concurrent edit cannot silently swap the reviewed revision.

Worked example: four native tables and complete extracted text are structural
evidence. They say nothing about cell padding, readable row height or uncut
glyphs until the application render has been reviewed.

## Pitfalls

- Installed fonts are not embedded fonts; these are different portability
  properties.
- Never delete relationships or referenced parts to quiet a validator; that can
  corrupt content.
- An unused content-type entry: first establish that nothing references it
  before normalizing anything.
- The application cannot open the file: keep the failing draft, and fix the
  authoring cause in a new revision.
