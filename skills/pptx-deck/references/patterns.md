# Patterns — keep what the content was trying to say

The slide layouts (`layout:` values in `deck.yaml`) are the catalog of what to
use. This file covers **constructions the catalog does not name, which therefore
get silently flattened into paragraphs or cards** — when migrating an old deck and
when building a new one alike.

Why this matters: structural and visual QA check whether something is *broken*.
They cannot see whether *meaning disappeared*. A typical failure: a Gantt slide
holding eight workstreams with start dates, progress, plans, and a "today" line
becomes eight empty cards with two dates each — and passes every check, because
alignment and contrast are fine. What vanished was the meaning.

For a migration, render both decks (`python scripts/render_deck.py <file>.pptx`)
and **compare the contact sheets one slide at a time by eye.** Automated checks do
not catch this.

Patterns marked `custom` are built in Python with `scripts/deckkit` primitives
(`text`, `box`, `line`, `connect()` for glued connectors, `path()` for open
polylines such as loops, `table`, `chart`) and brand tokens only. All geometry
below is a starting value on the 960 × 540 pt canvas.

---

## Decision order

For each construction in the content, decide one of three:

1. **An existing layout covers it** → pick it from the layout catalog. If a
   converter flattened it into paragraphs, that is a converter bug, not a design choice.
2. **It matches a pattern below** → use the pattern.
3. **It is a boundary, branching, or multi-layer relationship** →
   `layout: diagram` ([visuals.md](visuals.md) §4). Never place boxes by hand.

If none applies, ask whether the construction is needed at all. If it is
decoration, drop it.

---

## Progress-reporting patterns

These recur in decks that put the status of many workstreams on one slide:
portfolio status, sprint reviews, program reviews.

### 1. Gantt — from start to today, then the plan (`custom`)

**When**: three or more workstreams, each with a start, a current point, and a
target. A table of dates does not show who is ahead and who is behind.

**Core rule**: position bars by **0–1 fractions of the time axis**, converted from
dates by the author, then multiplied by the track width. Hard-coded point
positions break as soon as the number of month columns changes.

Construction:

- Left label column about 180 pt: a two-digit number, the workstream name, and its
  category one step smaller in `colors.muted`.
- Header row: month labels evenly spaced across the track, `type.caption`.
- Per row (about 39 pt high): a "done" bar from start to today in
  `colors.accent`, then a "plan" bar from today to target in a light neutral or
  outlined. Start and end dates as small tick labels on the done bar.
- One vertical "today" line across all rows, labeled ("Today W6"). Every
  done/plan boundary must meet this line exactly.
- A **legend is mandatory** ("Progress (start → today)", "Planned"). Never convey
  meaning by color alone.
- More than eight rows → two slides (eight rows plus the header fill the body band).

### 2. Status dashboard table — workstreams × attributes (`layout: table`)

**When**: each workstream has several attributes of **different kinds** — stage,
priority, status, target date, latest progress. As cards, the columns do not line
up and nothing can be compared.

Example header: Workstream · Area · Current stage · Status · Target · Latest progress.
Example row: "01 Billing migration / Finance" · "Finance systems" · "Build" ·
● In progress · "W14" · "Invoice export passes parallel run".

- Status is a dot **plus a label** (`colors.positive` "In progress",
  `colors.warning` "Needs discussion", `colors.negative` "Stalled"). A dot alone
  loses the information for color-blind readers.
- The first column holds two lines: name and category.
- A legend under the table defines each status ("In progress — next action is clear").
- More than 7 rows or 7 columns → split, repeating the header row on every slide.

### 3. Dark stat row — pin down two or three numbers first (`layout: stats` or `custom`)

**When**: an executive summary where "remember these three numbers" is the whole
point. Light stat tiles carry the same weight as the body and do not read as a
summary; a dark fill (`colors.dark`, text `colors.on_dark`) lifts them.

- **Two to three per row.** At four or more the numbers shrink and the effect is gone.
- Numbers in a flat solid color on dark fills; gradients turn muddy on dark backgrounds.
- Two lines under each number: **what it counts + so what**
  ("6 workstreams — 4 on track, 2 at risk / both risks have a mitigation owner").

### 4. Stage rail — a process gated by exit criteria (`custom`)

**When**: a fixed sequence of stages (Scope → Design → Build → Pilot → Rollout) and you need to show where things stand now. Unlike
`layout: process` (3–4 boxes) or `layout: timeline` (a date axis), five or six
stages still read comfortably.

- Each stage: a name (`type.body`) and a two-line description in `colors.muted`,
  separated by thin chevrons or separators in `colors.line`.
- Exactly **one** stage is "current" (accent rule or tinted fill).
- If the current stage differs per workstream, this is the wrong pattern — use the
  status dashboard table (§2).

### 5. One-line summary — pin the conclusion at the bottom (`custom`)

**When**: evidence fills the slide and one concluding sentence should close it.
Written as a source line it looks like a citation and nobody reads it.

- A callout band above `layout.body_bottom`: a small tag ("In one line",
  `type.label`, accent) and one sentence at `type.lead`, with at most one bolded phrase.
- Example: "Four of six workstreams are on plan; the two at risk both slip on the
  same vendor dependency."
- One per slide. Two and neither is read.

---

## 6. Co-branding chrome

Decks made with a partner need different chrome; without it, the reader cannot
tell whose deck it is.

- Logo lockup at top-right: your logo, a small "×", the partner logo, at equal
  optical height. Default order: host organization first; `brand/guidelines.md`
  may specify otherwise.
- Keep partner logos with the deck's own assets, not in the shared brand icon
  set, and use them only with permission.
- If the source carries a distribution marking ("Confidential" and the like),
  **always carry it over** — in `chrome.footer_text` or on the cover.
- A sub-lead under the headline may replace the short accent rule
  (`layout.rule_y: null`) when the brand prefers it. Do not show both a rule and
  an accent underline.

---

## 7. Open columns — when cards are not needed (`custom` or `two_column`)

**When**: three or four groups where each group is a **list**. Three filled cards
add weight and, with their minimum heights, grow tall. Separate with hairlines only.

- Each column: a head (`type.body`, ink), a short bullet list, and an optional
  one-line foot in `colors.muted` ("Owned by the platform team").
- Hairline separators in `colors.line`; no fills.
- Column markers in `colors.accent`, `colors.accent_2`, or neutral at most. Three
  or more accent colors look machine-made.

---

## 8. What migrations lose — checklist

Record in the deck plan **which source construction became which layout or
pattern**, so the next person does not repeat the judgment. Then, with the two
contact sheets side by side, check in this order:

- [ ] **Was there a time axis?** → Did a Gantt or timeline collapse into a card list?
- [ ] **Was there status?** → Are the dots, colors, and legend still there?
- [ ] **Were numbers the lead?** → Did a dark stat row sink to body size?
- [ ] **Were there boundaries or branches?** → Did the architecture become a card list? (→ `layout: diagram`)
- [ ] **Was there a concluding sentence?** → Did the one-line summary shrink into a source line?
- [ ] **Partner logos and distribution markings** → Is the chrome intact?
- [ ] **Meaningful colors** → If color encoded a distinction in the source (build vs pilot work), does it survive?
- [ ] **Did one slide scatter into three?** → A comparison only means something on one slide.

If any item fails, **rebuild that slide.** Do not leave an automatic conversion
as it is.
