# Composition — polish comes from restraint

A deck looks high-end when its **logical structure is visible on the page**, not
when decoration is added. This file covers deck-level story structure and
slide-level composition. Word choice is in [writing.md](writing.md); choosing a
table, chart, or diagram is in [visuals.md](visuals.md); reading layers and
emphasis are in [reader-craft.md](reader-craft.md).

Principles used throughout: conclusion first, headlines that state the
conclusion, one governing message per slide, groups with no overlaps and no
gaps (MECE), a source and a "so what" for every exhibit, and restrained
design (few colors, one type family, generous whitespace).

Every style choice below is a **default**. Precedence: explicit user request >
company template / brand profile ([`../brand/brand.yaml`](../brand/brand.yaml)) >
[`../brand/guidelines.md`](../brand/guidelines.md) > these defaults.

---

## 1. Deck level — the titles alone must tell the story

### Order the deck by the reader's question

Write the deck objective as one sentence, then lay the supporting arguments
underneath it.

- Executives who already know the situation and must decide: conclusion and the
  conditions of the decision first.
- Workshops that define a problem together or test alternatives: question →
  evidence → synthesis can work better.
- Choose by the audience's prior knowledge and the evidence this decision needs.
  Do not force the order of a source document onto the new deck.

### Horizontal logic — the sequence of headlines is the story

Extract the content-slide headlines top to bottom and read them. The argument
must stand on those alone. If it does not, a headline is a label
(see [writing.md](writing.md) §1), the slide order is wrong, or the slide is
unnecessary.

- Cover, section, and closing slides have different jobs; do not force
  conclusion headlines on them. Read the slide roles separately to check that
  chapter transitions and the closing slide are in place.
- When going from overview to detail, keep the same item IDs and comparison
  criteria, and make clear which conclusion the appendix returns to.

```
✗  Architecture overview → Cost analysis → Migration plan          (labels)
✓  Every request passes through only three tiers
   → Consolidating the databases cuts monthly cost by 61%
   → We validate with one workload in August                       (a story)
```

### Decide how the deck will be consumed

Set `meta.mode` before writing headlines.

- **present** — shown and spoken. One-line headlines (about 8–14 words; Korean
  about 25–40 characters). The presenter carries the reasoning aloud.
- **read** — sent ahead, left behind, read on screen or paper. The reader
  controls the pace and the headline carries claim and consequence: up to two
  lines, one sentence, about 15–25 words, optionally "claim – consequence" after
  an en dash. If it needs three lines, the page has two messages.

In a read deck that becomes a document page (two or more paragraphs), bold the
topic sentence of each paragraph instead of adding sub-headings.

### The executive summary is the table of contents of the argument

For any deck with 3+ sections or 10+ content slides, and for every read deck,
put a `summary` slide right after the cover (before the agenda):

1. One block per section, in deck order, headed with **the same wording as that
   section's divider** (`section: n` pulls it), with the section's thesis
   (`subtitle`) and 2–3 supporting points.
2. One full-width `so_what` band at the bottom that states the ask.
3. The summary headline is the deck's governing conclusion.

A reader who stops after page 2 has the whole argument; a reader who jumps to a
section recognises the sentence and knows where they are. It also turns "the
headlines tell the story" into a check: if a section's thesis does not support
the summary headline, the section or the headline is wrong. Skip the summary in
5-slide updates, where the headlines already are the summary.

For long or read decks, add a section tracker (`chrome.tracker` / `meta.tracker`)
so every page shows where it sits ([layouts.md](layouts.md), fixed frame).

### Numbered overview, then one page per item

When a page lists 3–5 drivers, levers or recommendations, number them, and give
each later deep-dive page the same number and the same short name — in the
eyebrow (`02 · Pricing`) and at the start of the headline when it helps. Close
the run by returning to the overview with the numbers intact, or with the
summary. The number is a cheap, unambiguous link between overview and detail
and survives skimming better than colour. Do not number unrelated topics just
to look orderly.

When one claim needs two exhibits, the headline may continue across the pair
("… (1/2)", "… (2/2)", Korean "(계속)"); for three or more pages, use `(1/N)` in
the eyebrow.

### End each chapter with what it means

In read decks and reports with 3+ chapters, close each substantive chapter with
a small implication page: 2–4 numbered actions or questions for the reader, each
a verb-first bold phrase plus one line. Build it with
`cards: {style: open, numbered: true}` (large numerals over each heading, no
boxes). Where a full page is too much, put the same 2–4 items in a `next_steps`
band on the chapter's last page. Choose one place per deck — chapter-end pages
**or** chapter-opening key messages, not both — and keep the label stable
("What this means", Korean "시사점"). In a short presented deck, one
recommendations slide before the closing is enough.

### Vertical logic — no overlaps, no gaps (MECE) within a slide

The items on one slide must **not overlap and must not leave gaps**.

- Two of three cards say the same thing → merge them.
- An axis of the argument is missing → add it.
- A bucket called "Other" means the classification criterion is wrong.

### One governing message, with the evidence it needs

Keep one principal conclusion and one visual focus. Two or three complementary
exhibits may support that conclusion: a trend and its driver breakdown, or a
comparison and the condition behind a recommendation. Use aligned panels and a
clear reading order; never show the same data twice.

Choose this only when the relationship helps the reader. If the exhibits answer
different questions, or labels no longer fit at readable sizes, split overview
and detail into linked slides. Automatic splitting cannot decide which
analytical relationship must stay visible — that is an authoring decision.

---

## 2. Slide level — design the path of the eye

### Z-pattern

Reading order is **top-left → top-right → bottom-left → bottom-right**. So:

- The headline sits top-left (the generator's fixed band: `layout.title_y`).
- The conclusion or key number goes **top-left to center**. Bottom-right is
  reached last.
- Sources, legends, and footnotes go bottom-right or along the bottom — things
  that can be read last.
- With three cards, **the leftmost is the most important**. Order is never
  arbitrary.

### One focus; everything else steps back

Three or more highlights cancel each other.

- Of three cards, only one gets the accent treatment: a light accent tint with
  an accent outline (cards `highlight`).
- Of several bars, only the highlighted one uses `colors.accent`
  (`colors.series[0]`); the rest are muted.
- One highlighted row per table.
- Bold covers **one phrase** per sentence at most.

### Whitespace is not failure

When the fixed vertical band is respected (`layout.body_top` to
`layout.body_bottom`), 40–190 pt is often left over at the bottom. That is
normal. **Do not add content to fill space.** A stretched card — two lines of
text floating in a tall box — is worse than empty space.

### Alignment comes from the grid, not the eye

- Try a named layout first (`cards`, `two_column`, `stats`, `table`, ...), then
  the 12-column grid (`layout.columns`, `layout.gutter`), and only then
  free placement in a `custom` slide.
- Elements in one row **share a top edge**.
- Generate diagrams from a node/edge source (`layout: diagram`), never by
  nudging boxes by hand. Complex topologies need explicit groups and routing;
  small repeated row/column diagrams fit the diagram grid directly.
- Optical alignment: an icon beside text aligns on the **visual center**, not on
  the text baseline.

### Density — the ceiling per slide

| Element | Ceiling | Beyond it |
|---|---|---|
| Bullets | 5 | Two slides, or cards |
| Cards | 4 per row | A compact icon grid (`custom`) or two slides |
| Table rows | 5 (default) · 7 (dense) | Split, repeating the header row |
| Simple categorical chart items | 8 | For meaningful time series or linked analyses, keep the required evidence and see [visuals.md](visuals.md) §3 |
| Diagram nodes | No fixed number | Measure real label sizes, traceable paths, and room for boundaries and notes; split into overview/detail if needed |
| Agenda items | 6 | Group into chapters |
| Visual focus per slide | **1** | Two slides |

---

## 3. What cheapens a deck

These create the "machine-made" impression. Avoid all of them by default; an
organization may override individual items in `brand/guidelines.md`.

| Avoid | Why / default instead |
|---|---|
| Heavy bold headlines | Weight as emphasis becomes noise, not hierarchy. Headlines regular (`type.heading_bold: false`); bold only for the one emphasized phrase |
| Drop shadows, gradient-filled boxes | The mark of dated templates. Fills use `colors.surface_alt`; lines are hairlines in `colors.line` |
| Three or more accent colors | One or two per deck (`colors.accent`, optionally `colors.accent_2`). A third color only when it carries meaning |
| Emoji | See [writing.md](writing.md) §4 |
| Decorative icons | A picture that points at nothing is noise |
| Mixed or overused rounded corners | One corner radius for all panels (`layout.radius`); no swarm of circular badges |
| Animation on everything | At most one to three patterns per deck. The argument must stand with all motion removed |
| A packed slide | Whitespace signals confidence |
| Centered body text | Left-aligned. Centering only on cover, section, and statement slides |
| More than one type family | `fonts.heading` / `fonts.body`, plus `fonts.mono` for code |
| Ad-hoc sizes and colors | Brand tokens only — never a literal hex value or point size in a slide spec |

---

## 4. Before designing — the headline-only skeleton

Before any visual work, build a **skeleton of headlines only**: the `title`
lines of each slide in `deck.yaml`.

1. Write the objective in one sentence.
2. Choose three to five supporting arguments with no overlaps and no gaps (MECE).
3. Write each argument as a section thesis, then each slide headline under it
   (a conclusion sentence).
4. **Read only the headlines.** Do they tell the story? In a deck with a
   summary, do the section theses read as the summary's blocks?
5. Then pick the means of expression for each slide
   ([visuals.md](visuals.md) decision table).
6. Build the slides last.

Reversing this order (making attractive slides first and sequencing them later)
reliably produces overlapping slides and missing arguments.

---

## 5. Composition check on the contact sheet

Render with `python scripts/render_deck.py out/deck.pptx` and, separately from
the defect list, check:

- [ ] **Do the headlines alone tell the story?** (most important)
- [ ] Does the summary repeat each section's wording, in deck order?
- [ ] One visual focus per slide?
- [ ] Any slide with three or more highlights?
- [ ] Are cards and items in order of importance (leftmost most important)?
- [ ] The same layout three times in a row without a reason?
- [ ] Is the **amount** of bottom whitespace consistent? (Erratic gaps break rhythm.)
- [ ] Two slides saying overlapping things → merge.
- [ ] A missing argument → check against the objective.
- [ ] Any number without a source?
- [ ] Any emoji or decorative icon left?
