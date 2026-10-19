# Reader craft — pages the reader can predict

A deck feels well made not because of decoration but because **on every slide the
reader can predict where to look first and what to compare with what**. This file
covers reading layers, relationships between panels, splitting hard slides over
time, density, emphasis, shape, and type. Story structure is in
[composition.md](composition.md); word choice in [writing.md](writing.md); the
choice of exhibit in [visuals.md](visuals.md).

All numbers below are **starting values**, not pass/fail thresholds. Adjust them
to the actual content and to your brand profile
([`../brand/brand.yaml`](../brand/brand.yaml)). Units are points on the 960 × 540
canvas.

---

## 1. Reading layers — never mix roles

| Layer | Where | Job |
|---|---|---|
| Eyebrow | Above the headline (`layout.eyebrow_y`, `type.label`) | Topic and position — section number and name (`eyebrow: auto`), the item number on a drill-down page, `REFERENCE`, `(2/3)`. Never a second claim |
| Headline | Title band (`layout.title_y`, `type.title`) | The conclusion — or, when evidence is incomplete, the research question |
| **Sub-lead** (optional) | Directly under the headline, `type.lead` | **One reason or condition** the headline could not hold. Never repeats the headline |
| **Exhibit label** (optional) | One line directly above the exhibit | **What is measured and by what criterion** — metric, unit, period, and n if there is a sample |
| Exhibit → implication → source | Body band | The source stays grouped with its exhibit as one unit of meaning |

- Headline: one line in the fixed title band (`layout.title_y`, `layout.title_h`)
  when presented; up to two lines (about 25 words, one sentence) in a read deck
  (`meta.mode: read`), where the band reserves two lines on every content slide.
  If it does not fit, shorten the sentence; do not shrink the type or let it wrap
  into the body.
- Reading text keeps its measure: a lead or list line holds at most
  `type.max_measure` characters (75 by default, CJK counting about two). The
  generator draws the lead and bullets that wide and leaves the rest of the row
  empty; do not stretch reading text across the slide to fill it.
- Question headline: answer it directly below in one sentence
  (`lead_style: band` draws the lead as a tinted answer band).
- Sub-lead: one line by default, up to two on reading slides. It does not need
  reason → number → prescription every time.
  Example — headline "Review wait time, not coding time, sets our lead time" /
  sub-lead "Changes spend a median 2.3 days waiting for a first review, 61% of lead time".
- The exhibit label never states the conclusion. Omit it on concept diagrams with
  no measured values. Above a table, drop the label's bottom rule — the table's
  header rule already marks that edge; do not draw the same boundary twice.
- Both optional layers take their height out of the body budget
  (`layout.body_top` to `layout.body_bottom`). A one-line sub-lead costs about
  37 pt, two lines about 60 pt; an exhibit label (label at `type.body` plus a
  criterion line at `type.caption`) about 27 pt. Compute from real line heights.
- **Numbers must trace.** A number in the headline or sub-lead connects to a value
  in the exhibit through the same data, unit, period, and denominator, or through a
  stated calculation. This does not mean repeating the same number three times.

## 2. Decide the relationship in one sentence before drawing two panels

A starting set, not a complete list:

| Relationship | Sentence form | Starting arrangement |
|---|---|---|
| Comparison | "A and B differ this way on the same criteria" | No symbol; same rows, same scale; if symmetric, split at the canvas center (x = 480) |
| Inference | "The interpretation on the right follows from the evidence on the left" | One block arrow between the panels. If the causality is a hypothesis, say so |
| Row-wise transition | "Each item changes from current to proposed" | A small arrow per row; left neutral, right highlighted |
| Combination | "The two must be used together" | A plus sign in the middle |

- Gaps: columns of one list or table use `layout.gutter`; panels answering
  different questions about 2 × `layout.gutter`; a gap that holds an inference
  arrow 48–72 pt. Adjust for panel width, labels, and arrow clearance.
- For asymmetric splits, allocate the space the evidence needs first, then place
  the interpretation where the reading order expects it (usually right, sometimes below).
- Build the block arrow once as a light neutral solid shape and reuse it. Align it
  vertically to what it connects (panel center or the highlighted row).
- Test: delete the symbol — is the relationship still legible? If it now reads as
  a different relationship, the symbol was wrong.

## 3. Split hard slides over time

Two concrete forms of overview → detail:

**Wide → pick one → why (spotlight).** The first slide shows the whole; the
second **regenerates it with the same coordinates and IDs** and lets everything
outside the focus step back. The second slide may add an explanation,
annotation, or excerpt panel.

- How to step back: recolor out-of-focus text and marks in a neutral light color
  (for example `colors.chrome` — still legible, but it does not come forward). If
  you use an overlay, choose its transparency by how much context is still needed;
  there is no fixed value.
- One focus device is enough (a tinted row plus a side marker, for example). Do not
  stack fill, check mark, side line, double arrow, and dimming on one target.
  Color plus a label for accessibility is not decorative duplication.
- The two slides must make the argument without clicks or animation in the
  distributed file.

**Summary → detail (1/N).** Detail slides share the same plot frame, axes, and
color key. Context data stays in neutral at the same coordinates; only that
slide's subset is highlighted. Put a small `(1/3)` at the end of the eyebrow or
headline. If the summary already settled the judgment, do not add another
synthesis slide.

**Pass criterion for repetition.** In a sequence of analyses, note briefly in the
speaker notes "what carries over from the previous slide / what is new". An
alternative view with nothing new comes out of the main deck, unless the purpose
is teaching or comparison.

## 4. Density — empty area is not the same as reading load

- Count **independent questions and kinds of encoding** before counting objects.
  More than two on a presentation slide, or three on a reading slide → consider
  splitting.
- Body text (excluding the headline) of about 60 words on a presentation slide or
  130 words on a reading slide is a **warning signal** (Korean: about 180 and 400
  non-space characters). Technical slides made mostly of table or diagram labels
  may exceed it. A `REFERENCE` or `(1/N)` marker tells the reader how to read the
  slide; it does not excuse overcrowding.
- Check **local congestion** separately: clusters of small labels, charts that
  force back-and-forth between labels and a legend, a detached legend, too many
  compared items at one spot. A page can look empty overall and still be heavy.
- If a value label has no room, do not shrink it. Try outside direct labels,
  a different chart type, or a split first.
- When content overflows, in order: shorten sentences → split or spotlight →
  move to the appendix. Never reduce letter spacing or font size of reading text.

## 5. Emphasis — one against many grays

Separate color roles first: **editorial focus** (`colors.accent`), data series
(`colors.series`), status (`colors.positive` / `warning` / `negative`), and
official product icons or boundary colors. The rules below are about editorial
focus; do not judge by the total count of saturated colors.

1. One focus set per slide. A series of many points counts as one focus. The
   focus is what the headline talks about.
2. Focus and adjacent context differ **not only in hue but also in at least one of
   lightness, direct label, or shape**. Check that the focus still comes first in
   a grayscale render.
3. If a context mark itself conveys a value, it needs ≥ 3:1 contrast with the
   background. A lighter context gray (below 3:1) is acceptable **only when values
   are read from direct labels**. Readable labels stay at ≥ 4.5:1 (`colors.muted`
   or darker). A gray that meets 3:1 on white sits close to the accent in
   lightness, so then separate the focus by hue plus label.
4. When two saturated colors of similar lightness sit side by side (`accent` and
   `accent_2`), add another cue: direct labels, line style, or shape.
5. Current vs recommended = neutral vs accent (a plain "Recommended" label is
   fine). Never use the risk color for recommendation or emphasis.
6. Check white text on accent fills against the actual brand colors
   (`colors.on_accent` on `colors.accent`); large text needs ≥ 3:1, small text ≥ 4.5:1.
7. A conclusion box is optional. If used, a tinted fill plus an accent line or
   label. Grouping fills carry no emphasis meaning.
8. In a series of slides, the same entity ID keeps the same color. Do not reassign
   the accent or data color key per section.
9. Do not recolor official icons or brand-defined boundary colors in architecture
   diagrams. Mark risk with a separate annotation.

## 6. Shape — same role, same shape

- Use the same shape for the same role. Never put a long sentence in a circle.
- When the **difference** between two or three values per item on one scale is
  the point, consider a dot plot (dumbbell). When absolute size or lookup is the
  point, use bars or a table.
- Arrowheads only on directional lines: transfer, sequence, dependency,
  inference. Not on leader lines or classification lines. Start with 0.75–1 pt
  neutral flow lines and a single 1.5 pt accent line for the one highlighted path;
  a brand's own line grammar overrides this.
- Remove only decorative nested containers (a card inside a card; a filled bar plus
  border plus card). Keep scope groupings, evidence groupings, and plot frames.
- Icons with the same role have the same size. Number badges only where there is a
  reference or an order.
- Build repeated parts with one generator function; never resize a group to fit
  (circles become ellipses).
- For unit grids, verify the unit per cell, the denominator, and the rounded count
  of filled cells. For heatmaps, verify the value → color mapping. Never paint
  missing data as zero.

## 7. Type — readable and consistent

- Never go below `type.min`. Dense reference material with tiny annotations is
  not a reason to lower the floor; split instead.
- Exhibit labels stay within the scale: label at `type.body`, criterion line at
  `type.caption` in `colors.muted`.
- Intermediate weights (medium, semibold) may fall back to regular or bold on
  machines without the font. Do not carry hierarchy on weight alone; check the
  final output's actual font and line breaks in the render.
- Use emphasis sparingly. You may bold a key noun or condition, but write the
  sub-lead without emphasis as the starting point.
- Short bar-row labels read best right-aligned toward the bar. Long names or
  multi-line conditions go left-aligned in a fixed column.
- Bilingual terms only where readers need to search or cross-reference the
  original: first mention `Local term (Original)`, and item labels in the deck
  language with the original one step smaller (keeping the per-role minimum and
  contrast). Keep product names as officially written.

## 8. Deck flow

- Divide sections by the reader's questions: summary → why → where is the
  problem → what to do → how → decision request. Close the substantive body with
  the decision or next action; the last actual page, after any appendix, is the
  closing slide (text from `copy.closing_title`).
- The summary page (`summary`) uses the section titles verbatim and each
  section's thesis; every section divider states that thesis as its `subtitle`.
- Readers of distributed files jump. In long or read decks show the position on
  every content page (`chrome.tracker`: `tabs` or `dots`), never in the body.
- Before the closing slide, restate the numbered conclusions or the ask; the
  closing slide only hands over (one sentence and confirmed contacts).
- Appendix pages keep conclusion headlines; mark "Appendix" or "Backup" in the
  eyebrow, not in the headline.
- Never end with a pile of cases and no conclusion.
- Use question headlines for research questions, workshop questions, or real
  choices. Never rhetorical questions.
- Connectives across pages ("in contrast", "in particular") only when the previous
  slide holds the counterpart statement.

## 9. Verification

Automatic (read-only):

```
python ../pptx-layout-audit/scripts/deck-craft-lint.py out/deck.pptx
```

Typical findings:

- **fail**: text outside the canvas, leftover authoring instructions, text below
  `type.min`, white text failing the large-text contrast threshold, hand-typed
  number labels that differ from the chart data, intrusion into the footer band.
- **warn**: low contrast on small text, reading text below `type.caption`, a headline
  number not found on the slide (verify through data or calculation), squashed
  circles, mixed unit or source notation, too many saturated color families on one
  slide (excluding official assets and status colors).
- **info**: text budget, presence of legend and gridlines, distribution of left
  start lines.

Inherited sizes, theme colors, and rotated groups are not judged. A clean result
is evidence for review, not design approval. On spotlight slides, contrast
warnings on dimmed text are expected — confirm that the dimmed text is context the
reader does not need to read. A text box taller than its text can trigger a footer
warning — shrink the box or check the ink position in the render.

By eye (in the render from `python scripts/render_deck.py out/deck.pptx`):

- [ ] Do the eyebrows alone, and the headlines alone, each give position and logic?
- [ ] Does each reading line stay within the measure (no full-width paragraphs)?
- [ ] Does the focus still come first in grayscale?
- [ ] Does the relationship between two panels match its symbol?
- [ ] Can each headline number be traced to an exhibit value or calculation?
- [ ] Do consecutive slides keep coordinates, scales, and color keys?
- [ ] No local congestion (small-label clusters, label–legend back-and-forth)?
- [ ] Does this slide tell the reader something new?
