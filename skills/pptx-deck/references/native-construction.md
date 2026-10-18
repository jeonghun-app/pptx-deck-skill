# Native construction — building slides PowerPoint can edit

Use this when writing a `custom` slide with `scripts/deckkit`, extending a
layout in the generator, or debugging why a built PPTX looks or edits wrong.
Choose the layout first ([layout-craft.md](layout-craft.md),
[composition.md](composition.md)); this file is about reproducing that intent
with native objects. A request for PPTX is never satisfied by an image of a
slide.

Precedence for every default below: explicit user request > company template /
brand profile (`brand/brand.yaml`) > `brand/guidelines.md` > this file.

## 1. Units: position, size and type are different properties

```text
1 in  = 72 pt = 914400 EMU
1 pt  = 12700 EMU
1 px (96 dpi) = 9525 EMU = 0.75 pt
Default canvas: 960 × 540 pt = 13.333 × 7.5 in (16:9)
```

- deckkit takes **points** for coordinates and font sizes and converts with
  `Pt()`. Do not pre-multiply by 0.75 (or any factor) yourself — that is a
  double conversion. When calling python-pptx directly, wrap every number in
  `Pt()`, `Inches()` or `Emu()`; a bare integer is EMU.
- A design measured in px on a 1280-wide canvas maps to pt by
  `slide_width_pt / 1280` (×0.75 on the default canvas). Record the factor.
- Read the actual slide size (`presentation.xml` `sldSz cx/cy`, or
  `prs.slide_width`) — do not assume 16:9 from the file extension, and do not
  assume a company template uses the default canvas. `brand.yaml canvas` must
  match the template.

## 2. Text frames: set every property explicitly

PowerPoint's defaults (0.1 in left/right and 0.05 in top/bottom inset,
shrink-on-overflow in some templates, inherited anchors) make boxes drift.
deckkit's `text()` sets these explicitly; when you go below it, do the same.

| Property | python-pptx | Default in this skill | Why |
|---|---|---|---|
| Insets | `tf.margin_left/right/top/bottom` | `0` for free text; a fixed inset (e.g. `layout.gutter / 2`) inside panels | The text's visible start must equal the grid line you computed |
| Autofit | `tf.auto_size = MSO_AUTO_SIZE.NONE` | off | Shrink-to-fit silently breaks the type scale; fix copy or space instead |
| Word wrap | `tf.word_wrap = True` | on (headlines included); off only for code blocks and one-line labels you have measured | Wrapping must happen at the box width you measured |
| Vertical anchor | `tf.vertical_anchor` (`bodyPr anchor`) | `top` for reading text; `middle` only for short labels in fixed-height chips | Top anchor keeps first lines of sibling blocks on one baseline |
| Paragraph align | `p.alignment` | left; center only for short symmetric labels; right for comparable numbers | See [layout-craft.md](layout-craft.md) |
| Line spacing | `p.line_spacing` | `type.line_spacing` (body), `type.heading_line_spacing` | Ratio, not points — record which one you set |
| Space before/after | `p.space_before/after` | `0`, with gaps between blocks set by geometry | Empty paragraphs as spacers break editing and measurement |
| Fonts | run `font.name` + `a:ea` typeface | `fonts.<role>.latin` / `.east_asian` | Latin and East Asian faces are separate attributes; set both for CJK text |

Horizontal paragraph alignment and vertical anchor are two independent
settings. Check both.

## 3. Build one representative component first

For example, a node with icon, name and a short description:

1. Decide its role and expected line count. A name-only node gets no
   description area.
2. Fix its position and size numerically and reuse them for every node of the
   same role.
3. Check the icon's real bounds and internal transparent padding; keep the
   icon's aspect ratio.
4. Set left/right/top/bottom inset, vertical anchor and paragraph alignment
   separately.
5. Set title and description font, size, line spacing and the gap between them.
6. Test with the **longest realistic** text, then group the component.
7. Only then duplicate it and apply alignment and distribution.

Duplicating many boxes first spreads the same defect across the slide.
Inner width is arithmetic, not a fixed component spec:

```text
node w = 168, insets 12 + 12, icon 24, icon/text gap 9
text width = 168 − 12 − 12 − 24 − 9 = 111 pt
```

Centering text across the whole shape ignores the icon column. Separate text
boxes are fine when title and description differ in size or alignment; group
them with the node so they move as one part, not as loose pieces.

### Centering name and description boxes on a node

If name and description are separate boxes, place each by its own width:

```text
node x = 300, w = 180      → center x = 390
name box w = 74            → x = 390 − 74/2  = 353
description box w = 106    → x = 390 − 106/2 = 337
```

Both paragraphs may keep `align=left` and the two boxes still share a center.
When text or font changes, re-measure (deckkit `measure.text_width`) and
recompute. Do not confuse "the box moved to center" with "the paragraph became
centered", and do not apply both. Multi-line descriptions or nodes with an icon
column usually read better on a shared left edge.

### After moving an image and caption

Keep their shared offset, left edge and vertical gap. If the caption box used
to span the full column, recompute its width from the new right edge instead of
reusing the old width; recompute wrap and height too. Keep the image's aspect
ratio and crop. Text that *looks* inside the slide is not the same as the
editable box being inside its column — check the box.

## 4. Content-slide headline band (brand-token defaults)

Every content slide uses the same fixed band. Never vary its size or position
per slide; the reader learns where to look.

| Element | Token |
|---|---|
| Eyebrow / section label | `layout.eyebrow_y`, `type.label`, `colors.accent`, uppercase if `type.eyebrow_uppercase` |
| Headline | `layout.title_y`, height `layout.title_h`, width = content width, `type.title`, `colors.ink`, weight per `type.heading_bold`; **one line, word wrap on** so an over-long headline wraps visibly instead of running off the slide; the builder and `lint_deck.py` warn when it wraps past one line |
| Accent rule | `layout.rule_y`, `layout.rule_w × layout.rule_h`, `colors.accent`; hidden when `rule_y` is null |
| Body | starts at `layout.body_top`, ends by `layout.body_bottom` |
| Footer | `layout.footer_y`; optional hairline in `colors.line` at 0.5 pt; footer text and page number in `colors.muted` |

If the headline does not fit on one line at `type.title`, shorten the wording;
do not shrink the font. The `agenda` layout uses the same band with
`copy.agenda_eyebrow`. A company template's title placeholder replaces this band
when `template.use_placeholders` is on.

## 5. Tables: the quiet default

Prefer a native table (deckkit `table()` / the `table` layout) for any
comparison the reader may edit or copy. Default style — override in
`brand/guidelines.md` if your organization has a house table:

- Remove the PowerPoint table style (`NO_STYLE_TABLE`) so rules come only from
  the brand. No banded fills, no vertical lines, no solid header block.
- Horizontal rules only: header bottom and table end in `colors.line` at 1 pt;
  row separators in `colors.line` at 0.5 pt.
- Header row: `type.caption`, regular weight, `colors.muted`, bottom-anchored.
- Cells: `type.body`. A two-level cell is a bold `colors.ink` keyword over a
  `colors.muted` detail line. First-column row labels are regular ink, not bold.
- Recommended column: a light tint of `colors.accent`, accent header text and a
  short accent cap (≈`layout.rule_h`) above the column. A text label such as
  "Recommended" only when the meaning is not already clear.
- Totals: bold row with a `colors.muted` 1 pt rule above. Numbers right-aligned, same precision.
- Header text may go one step below body (down to `type.min`), never below.
- In python-pptx, set each cell's complete border set (`a:lnT/lnB/lnL/lnR` in
  `tcPr`) once; partial assignments leave theme borders behind.
- Stored row height is a minimum. PowerPoint grows rows to fit text, so check
  the rendered table against the source line, footer and nearby badges.

## 6. Groups, z-order and connectors

- Group only meaningful parts (a node with its icon, label and badge) and name
  them (`name=` in deckkit). Moving a node must move everything that belongs
  to it.
- Z-order by role, back to front: background panels → boundaries/zones →
  connectors → nodes → labels. Lines and panels must never cover text.
- Group children have their own coordinate space (`chOff/chExt` vs `off/ext`).
  Do not read child coordinates as slide coordinates.
- Use **glued connectors** (deckkit `connect(a, b, a_side=, b_side=)`) when the
  user may move nodes: they store `stCxn/endCxn` and follow the shapes. A loose
  `line()` is editable but does not follow.
- Arrow direction: the API's `head`/`tail` names describe the line's native
  start and end, not the flow's meaning. Check the stored start/end shape IDs
  *and* the rendered arrowhead. Prove direction once on a tiny example
  (draft → approved), then reuse.
- After adjusting a connector's length or bend, recheck both attachments. A
  nicer-looking line with a lost start connection is a regression.
- Distribute vs center: "equal gaps" and "equal center spacing" differ when
  objects differ in size. Decide which one is constant, then check optical
  balance of icons and text after any automatic alignment.

## 7. Check what was stored, not what you asked for

Builder input, stored OOXML and rendered output are three different pieces of
evidence. Properties can be dropped or inherited from the theme.

| Concern | Where it lives | Pitfall |
|---|---|---|
| Real slide order | `presentation.xml` `sldIdLst` + rels | `slide7.xml` is not necessarily slide 7 |
| Template in use | slide → slideLayout → slideMaster → theme | The first master does not represent every slide |
| Shape/group geometry | `xfrm` `off/ext`, group `chOff/chExt` | Child vs slide coordinates |
| Insets and anchor | `bodyPr` `lIns/rIns/tIns/bIns`, `anchor` | A missing attribute is inherited, not zero |
| Paragraph align / spacing | `pPr` `algn`, `lnSpc`, `spcBef/spcAft` | `spcPct` (ratio) vs `spcPts` (points) |
| Fonts and size | run `rPr`, `defRPr`, `latin`/`ea` | Theme fonts (`+mj-lt`) and installed fallbacks |
| Tables | `tblGrid`, `tr`, `tcPr`, cell `txBody` | Stored row height ≠ rendered height |
| Connectors | `stCxn`/`endCxn` id + idx, line geometry | Editable line ≠ attached line |

`python ../pptx-layout-audit/scripts/inspect-layout.py out/deck.pptx --output audit/layout.json`
dumps these properties in points. Rotations, flips and custom geometry outside
its supported scope are reported as limitations — do not turn them into a pass.

If you post-process OOXML, work on a copy, keep schema child order, and preserve
relationships, notes and image alt text. Never delete relationships or tags by
string replacement. A workaround for one renderer's bug stays scoped to that
renderer, not baked in permanently.

## 8. Editability contract by content type

- Comparison tables: native table (rows, columns, cells editable).
- Charts where the numbers matter: native chart (deckkit `chart()` / `chart`
  layout) so data, units and scale stay editable.
- Diagrams: native shapes plus glued connectors (`diagram` layout). Native
  shapes with unattached lines are only partly editable — say so.
- An embedded SVG/PNG with its source file is *source* editability; it is not
  the same as editing individual shapes in PowerPoint.
- Screenshots, logos and icons from your icon set (brand.yaml `icons.path`,
  `python scripts/find_icon.py <keyword>`) are original assets: use them as is;
  do not redraw or distort them for "editability".

## 9. Verify the final file

1. Hash the source and the output before review (`sha256sum`).
2. Check fonts, line spacing, tables, groups and connector attachments in the
   inventory.
3. Render: `python scripts/render_deck.py out/deck.pptx` (LibreOffice → PNG +
   contact sheet). Confirm the page count matches the plan.
4. Confirm the file's hash did not change during rendering.
5. Review every changed slide at bounded size: one image at a time, at most
   1280×800 px / ~200 KB, and write findings down at least every four slides.
6. When move-with-node editing matters, test it on a copy: move a node, edit a
   cell, check what follows.

A LibreOffice (or Keynote, or browser) render is evidence for that renderer,
not a PowerPoint test. Record font substitution, hidden slides, slide-number
fields and renderer-specific table growth. Open the file in real PowerPoint
before claiming PowerPoint behavior. Keep the reviewed revision at its own path;
the user may be editing the working file at the same time. A log line saying
PASS does not identify which file was reviewed — the hash does.

## 10. Structural slides in the final file

Plan each slide's role (`cover`, `section`, content layouts, appendix,
`closing`). For a multi-slide deck, section dividers and the closing slide count
toward the requested total. Check in the render and the native text list:

- Does each section title match the chapter that follows it?
- Do dividers have more air than content slides while keeping the same type
  family and the `backgrounds.section` treatment?
- Is text and logo color correct for the background (`colors.on_dark` and
  `chrome.logo.path_on_dark` only on dark backgrounds)?
- Is the physical last slide — after any appendix — the closing slide
  (`copy.closing_title` or the template's closing layout)?
- Does it close without unverified presenter details, contact data or new claims?

The closing words appearing in notes or a middle slide do not pass this check.
