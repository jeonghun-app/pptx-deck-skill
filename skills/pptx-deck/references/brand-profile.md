# Brand profile — how your design reaches every slide

`brand/brand.yaml` is the only place design values live. Layouts, custom
slides, the linter and the design lint all read it. A partial profile is
valid: missing keys inherit the neutral defaults in the skill's own
`brand/brand.yaml`, so an organization can start with colors and fonts and add
the rest later (see `examples/brands/warm-editorial/brand.yaml`).

Units are points (1 in = 72 pt). Colors are 6-digit hex without `#`; anywhere
a color is expected you may also write a token name (`accent`, `muted`).

## Three ways to adopt a design

1. **Edit the tokens.** Change colors, fonts, type scale and grid in
   `brand.yaml`. The skill draws its own backgrounds, headline band and footer.
   Best for organizations without a slide template.
2. **Build on the company template.** Set `template.path` and map
   `template.layouts`. Slides are created from the template's layouts, so
   masters supply backgrounds, logos, title styles and placeholders; the skill
   fills titles into placeholders and draws the body with brand tokens.
   `extract_brand.py` drafts this setup from the template.
3. **Both.** Template for masters and placeholders, tokens for everything the
   skill draws in the body (cards, tables, charts, diagrams).

Write the rules that are not numbers in `brand/guidelines.md`.

## Token reference

### `canvas`
`width`, `height` — slide size. 960 × 540 is 16:9 (13.333 × 7.5 in). In
template mode it must match the template; the builder warns when it does not.

### `template`
| Key | Effect |
|---|---|
| `path` | Company `.pptx` (relative to the brand file). Its slides are removed; its masters and layouts are used |
| `layouts.cover / section / content / closing / blank` | Layout *names* in the template for each slide role. `extract_brand.py` lists them |
| `use_placeholders` | Put titles and subtitles into the layout's placeholders (keeps the template's title styling) |
| `draw_backgrounds` | Also draw `backgrounds.*` on template slides (normally the master does) |
| `draw_chrome` | Also draw footer text, page number and logo (normally the master does) |

### `fonts`
`heading`, `body`, `mono`, each `{latin, east_asian}`. Both faces are written
on every run, so mixed-script text renders in the intended fonts. Choose fonts
your audience has installed or that your template embeds; install them on the
machine that renders QA images, or the contact sheet will show substitutes.

### `type`
| Key | Used for |
|---|---|
| `hero` | Cover and closing title |
| `statement` | Statement and quote slides; stat values |
| `section` | Section divider title and number |
| `title` | Content headline — must fit `layout.title_lines` lines |
| `lead` | Full-width reading text: lead, bullets, column headings |
| `body` | Narrow-column text: cards, table cells, diagram nodes |
| `caption` | Sources, captions, chart labels, table headers |
| `label` | Eyebrow, footer, page number |
| `min` | Hard floor; smaller requests are raised and reported |
| `max_measure` | Longest line of reading text, in average Latin characters (default 75; a CJK character counts about two). The lead, bullets, subtitles and statement support are drawn no wider than this at their size; `null` turns the cap off |
| `table_min`, `readable_min` | Optional, read by the design lint only: a lower floor for dense table cells, and the size below which readable (non-footer) text is warned. Both default to `min` |
| `line_spacing`, `heading_line_spacing` | Paragraph line spacing multiples |
| `heading_bold` | Default false: size already creates hierarchy |
| `eyebrow_uppercase` | Render eyebrows in capitals |

Keep `lead` readable when projected (roughly 1/30 of the slide height or more)
and `body` one step smaller. Do not introduce sizes outside the scale.

### `colors`
| Token | Role |
|---|---|
| `ink` | Headlines and primary text |
| `body` | Body text |
| `muted` | Small text that must still be read (captions, sources, labels) — keep ≥ 4.5:1 on `surface` |
| `chrome` | Decoration only — never information (footer text and page numbers use `muted`) |
| `line` | Hairlines and table rules |
| `surface`, `surface_alt` | Slide background; quiet panels |
| `accent` | Eyebrow, rule, the one highlight per slide |
| `accent_2` | Optional second accent; most decks never need it |
| `on_accent` | Text on accent fills |
| `dark`, `on_dark`, `on_dark_body` | Dark slides and their text |
| `positive`, `warning`, `negative` | Status — always paired with a word or shape, never color alone (table check marks and status dots use them) |
| `series` | Chart series in order; the first is the highlight series |

Check text tokens with `deckkit.contrast(a, b)`; the extractor and the design
lint report low-contrast pairs. One accent per slide is the default; record a
different rule in `guidelines.md` if your brand has one.

### `layout`
| Key | Meaning |
|---|---|
| `margin_left`, `margin_right` | Content edges; nothing readable outside them |
| `gutter` | Gap between columns and sibling blocks; derive other gaps from it |
| `columns` | Grid for custom renderers: `deckkit.grid_span(canvas, start, span)` returns the x and width of columns on it |
| `radius` | Panel corner radius (0 = square) |
| `eyebrow_y`, `title_y`, `title_h` | The fixed headline band |
| `title_lines` | Headline lines the band reserves (default 1). `title_h`, `rule_y` and `body_top` are given for this many lines; a deck with `meta.mode: read` needs two, and when the brand reserves fewer the builder moves the rule and the body start down by one headline line (`type.title` × 1.2 × `heading_line_spacing`) on every content slide |
| `rule_y`, `rule_w`, `rule_h` | Accent rule under the headline; `rule_y: null` hides it |
| `body_top`, `body_bottom` | The body band; content must end above `body_bottom` |
| `footer_y` | Footer text, page number and logo |

The band is constant across slides so headlines do not move as slides advance.
Leave a clear gap between `body_bottom` and `footer_y` (at least two body lines)
so the footer reads as outside the content.

### `chrome`
`footer_text` (e.g. a confidentiality label), `page_numbers`, `footer_rule`,
`logo.path`, `logo.path_on_dark`, `logo.width`, `logo.position`
(`footer-right`, `footer-left`, `top-right`), `cover_logo_width`. Use logo files
as supplied; never recolor or stretch them.

`tracker` (default `none`): `tabs` or `dots` shows the current section on
content slides inside a section, built from the deck's `section` slides; a deck
overrides it with `meta.tracker`. Tabs replace the eyebrow; dots sit at the
right end of the eyebrow band (left of a `top-right` logo). See
[layouts.md](layouts.md), fixed frame.

### `backgrounds`
`cover`, `section`, `closing`, `content`: `{color: <token>, image: <path>}`.
An image fills the slide (cropped to cover). Text color follows the background:
a dark color switches the slide to `on_dark` tokens. For an image background set
`backgrounds.<role>.dark: true` when text on the image should be light, and make sure the image leaves a calm
area behind the text.

### `copy`
`closing_title`, `agenda_eyebrow`, `source_label` (prefix of source lines;
default "Source", or "출처" in Korean decks; set `자료` here if that is your
convention), `next_steps_label` (label of the `next_steps` band; default "What
this means", or "시사점" in Korean decks), `default_language`.

Words drawn by framework layouts. Each defaults to `null`, which uses the
built-in English or Korean text for the deck's `meta.language`:

| Key | Used for | Built-in text |
|---|---|---|
| `placement_tag` | Tag on a `matrix` whose positions are judged, not measured | "Qualitative placement" / "정성적 배치" |
| `current_label` | Marker beside the period of the current `process` chevron | "Now" / "현재" |
| `symbol_labels` | Legend words for table symbols, per family and value: `{harvey: {0..4, na}, check: {yes, partial, no, na}, rag: {g, a, r, na}, tier: {1, 2, 3, na}}`. Set only the values you want to rename | Harvey "None … Full", check "Met / Partly met / Not met", RAG "On track / At risk / Off track", tier "Tier 1 (strongest) … Tier 3", n/a "Not assessed" |

A slide's own `legend: {value: text}` overrides `symbol_labels` for that table.

### `icons`
`path`: a folder of icons the organization licenses (PNG preferred; SVG needs
`cairosvg` or `rsvg-convert`), `formats`. Search with
`python scripts/find_icon.py <keyword>`; reference by file name in `icon:`.
Never recolor, distort or substitute one product's icon for another.

## Changing the brand safely

1. Edit `brand.yaml` (or re-run the extractor on a new template version).
2. Build both sample decks with it and look at the contact sheets — they use
   every layout, so a token that breaks something shows up immediately.
3. Run the design lint with `--brand` on a real deck
   (`python ../pptx-layout-audit/scripts/deck-craft-lint.py out/deck.pptx --brand brand/brand.yaml`).
   Your `brand.yaml` is merged over the skill defaults, so a partial profile
   only overrides the keys it sets.
4. Commit the brand change separately from deck changes, with the reason.
