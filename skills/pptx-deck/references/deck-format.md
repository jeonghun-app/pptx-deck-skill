# `deck.yaml` — the plan file

The plan is the single source of truth for a deck. It is written in PLAN,
approved by the user, and built as-is. People may edit it directly and ask for
a rebuild; the build follows the file, not the conversation.

Complete examples in `examples/decks/`: `sample.deck.yaml` (the core layouts,
English), `ko-sample.deck.yaml` (Korean, with a custom slide), `story.deck.yaml`
(a read-mode pre-read with summary, tracker and the reading bands),
`exhibits.deck.yaml` (chart options) and `frameworks.deck.yaml` (matrix, shift,
symbol tables, chevrons). Between them every built-in layout appears at least once.

## Top level

```yaml
meta:
  # -- narrative contract (required; lint_deck.py blocks the build without it)
  audience: Engineering managers and team leads
  objective: Agree to run release checks on every pull request
  desired_action: Approve a four-week pilot with two teams
  # -- optional
  title: Moving release checks earlier      # also written to the file properties
  author: Presenter Name
  language: en                              # en | ko | ... (affects default labels)
  mode: present                             # present (shown and spoken) | read (sent ahead, read alone)
  tracker: none                             # none | tabs | dots; overrides chrome.tracker
  brand: ../brand/brand.yaml                # relative to this file; --brand overrides
  sources:                                  # evidence used; keep for the presenter
    - "Internal incident review, Q3 (owner: platform team)"

slides:
  - layout: cover
    ...
```

`objective` is what changes for the audience; `desired_action` is what they
should do after the talk. If either cannot be written, the deck is not ready to
plan — go back to the questions in SKILL.md 1b.

`mode` decides the headline budget for the whole deck: one line in `present`,
up to two lines (about 25 words, one sentence) in `read`, with the title band
reserved for two lines on every content slide. `tracker` shows the current
section on content slides ([layouts.md](layouts.md), fixed frame).

## Keys every slide accepts

| Key | Meaning |
|---|---|
| `layout` | One of the layouts in [layouts.md](layouts.md). Default `bullets` |
| `title` | Headline. On content slides: a full sentence stating the conclusion; one line (two in `meta.mode: read`) |
| `eyebrow` | Small topic label above the headline (chapter or theme). `auto` = the enclosing section's number and short label |
| `lead` | One or two sentences under the headline that frame the body (content layouts) |
| `lead_style` | `band`: the lead as a full-width tinted band — the answer under a question headline |
| `next_steps` | `{label, items: [2–4]}`: numbered row at the bottom of the body; the body ends above it |
| `source` | Source or footnote line at the bottom of the body. Required wherever numbers appear |
| `notes` | Speaker notes — the words the presenter will say. Every slide |
| `dark` | `true` draws the slide on `colors.dark` |
| `no_footer` | `true` hides footer, page number and logo on a content slide |
| `no_rule` | `true` hides the accent rule under the headline on this slide |

**Quote text that contains a comma inside `[ ... ]` lists.** In YAML, a comma
separates items in a bracketed list, so `[Faster, cheaper reviews]` is two
bullets. Write `["Faster, cheaper reviews"]`, or use one `- item` per line.
In a table, `[keyword, detail]` is deliberately two parts.

Text values may use `**bold**` for the one phrase that carries the point. On
statement and chart-takeaway text, bold renders in the accent color.

## Writing the slots

- **Final copy, not a draft.** If a slot cannot be filled with a concrete
  sentence or a sourced number, the plan is not ready.
- **Never fabricate.** Unknown numbers, quotes, names, logos and screenshots
  become `TODO: what is needed and who has it`. The linter warns on every
  `TODO`, `TBD` and `???` so none reaches the audience.
- **Notes are spoken language.** Write what the presenter says, including the
  transition to the next slide when it is not obvious.
- **One message per slide.** If the headline needs "and", it is two slides.

## Rules the linter enforces

ERROR (blocks the build): empty narrative contract, unknown layout, content
slide without a headline, emoji, unsupported chart type, table rows with the wrong cell count, chart
series whose length differs from the categories, missing image or custom
renderer, diagram edges to unknown nodes, unknown `meta.mode`, tracker or
`lead_style`, a summary block that refers to a section the deck does not have.

WARN (decide and either fix or accept): headline wraps past one line (two in
read mode) or has more than 25 words in read mode,
headline reads like a topic label, more than 5 bullets, table over 7 × 7,
numbers without a source, more than 4 cards (5 with `style: open`), image without alt text, the same
layout three times in a row, multi-slide deck without cover or closing, 8+
content slides without an agenda, 10+ content slides without a `summary`, a
summary block heading that differs from its section's title, a summary outside
2–4 blocks, a single section divider, a tracker without two sections (or with
more than 6 tabs), `eyebrow: auto` before the first section, `lead_style: band`
without a lead, `next_steps` outside 2–4 items or on more than a quarter of the
content slides, a caption that runs over several full-width lines, `%p` mixed
with `%포인트`, more than one source prefix in a deck (자료 / 출처 / Source), open
`TODO`s, missing speaker notes.

INFO (a suggestion; some organizations decide otherwise): a Korean headline
ending in `~습니다` or `~합니다` (headlines default to a noun-phrase conclusion or `~다`),
`eyebrow: auto` under tracker tabs (the tab already names the section).

## Version control

Keep `deck.yaml`, custom renderers and assets in version control; treat the
PPTX as a build output. A diff of `deck.yaml` is a readable review of what
changed in the story.
