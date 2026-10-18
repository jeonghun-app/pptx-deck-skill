# Brand guidelines

The rules of your organization's decks that are not numbers. `brand.yaml` holds
the measurable design (colors, fonts, sizes, positions, template); this file
holds voice, vocabulary, patterns and exceptions. The skill reads both before
planning a deck.

**Precedence:** an explicit request in the conversation > this file and
`brand.yaml` > the defaults in `references/`.

Replace every section below with your own rules. Delete the sections you do
not need. Keep each rule short and say *why* — a rule with a reason is applied
with judgement; a rule without one is applied blindly.

---

## Identity

- Organization name as written on slides: `Example Corp`
- Product and team names that must keep their exact spelling:
- Words that are trademarks and need ™/® on first use (if any):

## Voice

- Default deck language: English
- Headline form: a full sentence that states the conclusion
- Person and tone: "we" for the organization, plain verbs, no hype
- Words we do not use (and what to write instead):
  | Avoid | Write |
  |---|---|
  | best-in-class | the measured result, with its source |
  | leverage | use |

## Required slides and text

- Cover shows: title, subtitle, presenter, date
- Confidentiality label: none by default; when a deck is internal, set
  `chrome.footer_text` to the approved label
- Legal or disclaimer slide: none by default
- Closing slide text: `brand.yaml` `copy.closing_title`

## Approved patterns

List the slide patterns your team reuses, with the layout that builds each.

| Pattern | Layout | Notes |
|---|---|---|
| Executive summary | `bullets` with `lead` | three points, each a full sentence |
| Option comparison | `table` with `highlight_col` | recommended option highlighted, never color alone |
| Roadmap | `timeline` | quarters as dates, current period highlighted |

## Diagrams

- Boundary colors per kind (if your organization defines them):
  | Boundary | Line | Fill |
  |---|---|---|
  | system | `chrome` | none |
  | trust zone | `chrome`, dashed | none |
- Icon library: `brand.yaml` `icons.path`. Use only icons the organization licenses.

## Charts

- Series order and colors: `brand.yaml` `colors.series`
- Number format: thousands separator, units in the axis label, not in every value

## Exceptions

Rules from `references/` your organization deliberately overrides, with the reason.

- (example) Headlines are bold in our template — the master defines it; do not
  remove it.

## Learned from revisions

Rules learned by comparing generated decks with the versions people edited
(see `references/revision-learning.md`). Record the change, the inferred
intent and where it applies. No personal data.
