# Learning from a user's edited deck

Use this when a user has edited a PPTX you delivered and you want to learn what
they changed and why, then make the skill do it right next time. For studying a
template or a set of good decks from scratch, use
[reference-design-study.md](reference-design-study.md).
A request to "learn from my edits" does not authorize regenerating or
overwriting the user's edited file.

## 1. Pin down what you are comparing

- Keep the **original** as delivered and the user's **edited** file as separate
  copies; record a SHA-256 for each. File names and modification times do not
  prove the content changed.
- Do not mistake an editability test copy you made yourself for the user's edit.
- If the user may still be editing, work from a snapshot.
- Match slides by real order (`presentation.xml` `sldIdLst` and rels) and match
  objects across files before comparing text, coordinates and relationships.
  Follow group transforms and the layouts/theme actually used.
- Distinguish the visible name from the internal `cNvPr` name, and an explicit
  line break from the application's automatic wrap.

`python ../pptx-layout-audit/scripts/inspect-layout.py original.pptx --output audit/a.json`
and the same for the edited file give comparable per-object geometry, insets,
alignment and font sizes in points; diff the two JSON files by slide and object.

### The re-saved control

When the user's application rewrote much of the XML, make a third file:
open a **copy of the original** in the same application and save it without
changes. Differences that also appear in this control — empty text bodies,
merged runs with identical formatting, renumbered relationships, tiny rounding
— are save-engine noise, not the user's taste. Use the control when save noise
clouds the analysis; it is not required for a simple wording change. If you
cannot make one, record that save noise may be present and how that limits your
conclusions.

## 2. Separate the actual change from the inferred intent

Slide, object and before/after measurements are **observations**. Why it helps
is an **inference** unless the user said so — label it. What the user left
unchanged is evidence too: if a centered short label sits next to a long
left-aligned description that the user kept, keep that combination.

| Relationship | What to compare | Do not over-generalize into |
|---|---|---|
| Short label and its node | box center, width, actual glyphs, paragraph settings — separately | "the box moved to center" → "center every paragraph" |
| Equal blocks of different height | overall center and the inner row/column rhythm | applying one slide's offset as a global constant |
| Image and caption | shared move, aspect/crop, caption width and bounds | accepting a box that overflows because the visible text happens to fit |
| Node, connector, legend, source line | ownership, flow, attachment, clearance after the move | turning a detached connector or an auto-rerouted elbow into a design rule |
| Cover presenter line | the display name and role the user typed | changing account names, file names or object names to match |

Presenter details on the cover come from what the user provides. Do not infer a
full name or title from an account alias. A name the user corrected is that
presenter's own preference — never a general rule and never copied to other
presenters.

If the user's edit itself introduced a structural problem (a detached
connector, a text box past the slide edge), record it as a separate observation;
do not codify it.

## 3. Review and write the rule back

- Put each changed slide's render next to the original
  (`python scripts/render_deck.py original.pptx` and the edited file) and match
  structural differences with visual ones. Record hashes and the application
  used. Review in batches of at most four slides; count structure-only and
  actually viewed slides separately.
- Decide where the rule belongs:
  - organization-specific preference → `brand/guidelines.md`, section
    **"Learned from revisions"**;
  - a value that is really a token (margin, size, color) → `brand/brand.yaml`;
  - general craft that would help any organization → the relevant reference
    ([layout-craft.md](layout-craft.md) for layout judgment,
    [native-construction.md](native-construction.md) for coordinates, text and
    editing).
- Each rule states its condition and its counter-case, does not duplicate an
  existing rule, and is written as a plain rule with its reason:

```markdown
## Learned from revisions

### Short node labels
- Center a short label's *box* on its node; keep the paragraph left-aligned so
  it stays aligned with multi-line descriptions in sibling nodes.
- Not for nodes with an icon column — center within the remaining text area.
- Check: label box center = node center ± 0.75 pt in inspect-layout output.
```

- No personal data in the rule: no person names, customer names, figures,
  service status, file names or dates. Detailed case notes stay in your private
  project notes, outside the skill.

## 4. Verify the learning

Rebuild the original deck spec with the updated brand and guidelines, render it,
and compare against the user's edit: the edits should now be unnecessary. If
several reviewers were involved, split structure / naming / visual review
between them, let only one control the application, and have one person merge
into the brand files. For a complex change, give an independent reviewer the new
rule and the original case — without the expected answer or your suspected
defect — and check whether they reproduce the user's intent.
