# Slide layout review (orchestration)

The coordinating agent runs the whole review: it hands out the specialist checks,
merges what comes back, makes every source edit itself, and delivers the final
artifact.

## When to use

- A user asks for a deck-wide layout review, or a correction pass across many
  slides.
- Several specialist checks (typography, diagrams, native output) apply to the
  same artifact and their results must be reconciled before editing.

For a single concrete defect, go straight to the matching specialist procedure
instead.

## Inputs

| Input | Needed | Notes |
|---|---|---|
| Artifact path | yes | Absolute path to the presentation being reviewed |
| Source path | no | Editable source (`deck.yaml` or a deckkit build script); take it from the task if it is evident there |
| Review directory | no | Separate directory for reports and previews; defaults to an audit directory next to the artifact |
| Delegation | no | Whether the user or the governing instructions allow subagents; defaults to what the session already permits |

Resolve paths from the task first. If the artifact path is still unknown, ask
once, listing everything that is missing in the same question.

## Procedure

1. **Pin the revision.** Note the artifact hash, slide count, output format and
   active theme. Assign which specialist checks apply to which slides. Layout
   work never changes the user's content or factual claims. Use the report
   format in [contracts.md](contracts.md).
2. **Run the specialist reviews.** Apply [typography](typography.sop.md),
   [diagrams](diagrams.sop.md) and [native output](native-output.sop.md) where
   they are relevant.
   - Use subagents only if delegation is allowed. Give each one absolute input
     paths, its own writable report path, and an explicit slide range.
   - Keep the source files under the coordinator's control so two agents never
     edit them at once.
   - While reviews run, the coordinator can prepare integration or notes.
   - Without subagents or tools, run the same roles one after another.
   - Say plainly in the final report if a role covered only part of the deck or
     did not run.
3. **Fix the source.** Merge the reports by slide and object, then correct the
   verified defects.
   - When two recommendations conflict, decide against the slide's intent and
     the rendered evidence.
   - Keep real defects apart from accepted optical or semantic exceptions.
   - Prefer adjusting the owning shape's geometry, its padding, or the copy
     before making type smaller.
   - Do not alter what an arrow means or what release status a slide reports;
     a cleaner look is never a reason to change facts.
   - Build into a new revision so earlier evidence still points at the file it
     came from:
     `python ../pptx-deck/scripts/build_deck.py deck.yaml -o out/deck-r2.pptx`
4. **Verify and deliver.**
   - After source changes, rerun the relevant checks: `inspect-layout.py`,
     `deck-craft-lint.py`, and `python ../pptx-deck/scripts/lint_deck.py deck.yaml`
     for the spec.
   - Re-render changed slides with
     `python ../pptx-deck/scripts/render_deck.py <deck.pptx>`.
   - Look at every changed slide in its final output, and keep coverage of the
     full deck.
   - View at most four bounded previews between recorded checkpoints.
   - Link the final artifact and list any environment that was not tested.

## Report

Return a link to the final artifact, per-role coverage (full, partial, or
missing), the findings closed with their evidence, accepted exceptions, and
untested environments. Detailed findings stay in the report files.

Worked example: for an 18-slide PPTX, typography covers every slide, the
diagram review is pointed at the slide IDs that actually contain diagrams, and
the native-output review covers text, tables, notes and links across the file.
A diagram fix triggers a fresh render of those slides plus content checks over
the whole artifact.

## Pitfalls

- An automated PASS is not aesthetic approval. Geometry checks cannot judge
  meaning or optical balance.
- A subagent that returns no report: salvage any partial work, then finish that
  role locally or reassign only that role.
- PowerPoint unavailable: record the gap and use the LibreOffice render, without
  claiming the deck was tested in PowerPoint.
