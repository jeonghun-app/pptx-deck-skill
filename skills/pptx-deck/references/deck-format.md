# `deck.yaml` — the plan file

The plan is the single source of truth for a deck. It is written in PLAN,
approved by the user, and built as-is. People may edit it directly and ask for
a rebuild; the build follows the file, not the conversation.

Complete examples: `examples/decks/sample.deck.yaml` (every built-in layout, English)
and `examples/decks/ko-sample.deck.yaml` (Korean, with a custom slide).

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

## Keys every slide accepts

| Key | Meaning |
|---|---|
| `layout` | One of the layouts in [layouts.md](layouts.md). Default `bullets` |
| `title` | Headline. On content slides: one line, a full sentence stating the conclusion |
| `eyebrow` | Small topic label above the headline (chapter or theme) |
| `lead` | One or two sentences under the headline that frame the body (content layouts) |
| `source` | Source or footnote line at the bottom of the body. Required wherever numbers appear |
| `notes` | Speaker notes — the words the presenter will say. Every slide |
| `dark` | `true` draws the slide on `colors.dark` |
| `no_footer` | `true` hides footer, page number and logo on a content slide |
| `no_rule` | `true` hides the accent rule under the headline on this slide |

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
renderer, diagram edges to unknown nodes.

WARN (decide and either fix or accept): headline wraps past one line,
headline reads like a topic label, more than 5 bullets, table over 7 × 7,
numbers without a source, more than 4 cards, image without alt text, the same
layout three times in a row, multi-slide deck without cover or closing, 8+
content slides without an agenda, a single section divider, open `TODO`s,
missing speaker notes.

## Version control

Keep `deck.yaml`, custom renderers and assets in version control; treat the
PPTX as a build output. A diff of `deck.yaml` is a readable review of what
changed in the story.
