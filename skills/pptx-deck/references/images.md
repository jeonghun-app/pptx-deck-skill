# Images and existing PPTX material

Two principles, in order:

1. **Bring the original whenever you can.** Photos, screenshots, logos supplied by
   the owner, and captures of measured dashboards cannot be redrawn. A redrawn
   one is no longer a fact and costs trust.
2. **Rebuild when the asset conflicts with the brand.** Shape-drawn diagrams,
   charts carrying another template's colors and fonts, and blown-up low-resolution
   images make the whole deck look cheap.

This is not one choice for the whole file: **judge each asset.**

## 1. Extracting from an existing PPTX

python-pptx can read picture shapes directly. A minimal pass:

```python
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
import hashlib, pathlib

prs = Presentation("original.pptx")
out = pathlib.Path("assets/from-pptx"); out.mkdir(parents=True, exist_ok=True)
seen = {}

def walk(shapes):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from walk(sh.shapes)
        elif sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
            yield sh

for i, slide in enumerate(prs.slides, 1):
    for pic in walk(slide.shapes):
        blob = pic.image.blob
        key = hashlib.sha1(blob).hexdigest()[:10]          # de-duplicate
        if key in seen:
            continue
        name = f"s{i:02d}-{key}.{pic.image.ext}"
        (out / name).write_bytes(blob)
        seen[key] = dict(slide=i, file=name, px=pic.image.size,
                         placed_pt=(pic.width.pt, pic.height.pt))
    notes = slide.notes_slide.notes_text_frame.text if slide.has_notes_slide else ""
```

Also collect per slide: title and body text, speaker notes (often the most
valuable part: what the presenter actually said), tables, charts (their data via
`shape.chart.plots`), and connectors. Pictures used as placeholder fills or slide
backgrounds live in the layout/master, not the slide; inspect those separately.

Check the original's aspect ratio. Moving 4:3 content to 16:9 creates margins or
crops: recompose, do not stretch.

Effective resolution of a placed picture:
`dpi = pixel width / (placed width pt / 72)`. Below about 150 dpi at its placed
size it will look soft when projected; below about 96 dpi, treat it as unusable.

To draft a brand profile from a company template instead, use
`python scripts/extract_brand.py template.pptx`.

## 2. Judgement per asset

### Reuse

- Photos: site, people, product.
- Real UI screenshots; redrawing them makes them false.
- Captures of measured dashboards or plots that are themselves evidence.
- Customer or partner logos you have permission to use.
- Vector art (SVG/EMF) that is not tied to another brand's style.

Place with the `image` layout. Screenshots are fitted, never cropped through
content; full-bleed photos with text on top always get a scrim for contrast.
Every image gets alt text that says what is shown ("Order editor with the
approval step selected"), not "screenshot".

### Redraw

- Diagrams drawn from grouped shapes: there is no image; use the labels and
  connections as the starting point for a `diagram` slide ([diagrams.md](diagrams.md)).
- Native charts: take the data and rebuild with the `chart` layout ([data-viz.md](data-viz.md)).
- Tables: re-set with the `table` layout.
- Low-resolution images that would be enlarged.
- Exhibits baked in another template's colors and fonts.
- Pictures of whole slides: their text cannot be searched, edited, or resized.

### Review

Large rasters cannot be classified automatically. Open them and decide: photo or
screenshot → keep; picture of shapes → redraw.

## 3. Icons are not screenshots

An icon placed as a full-width image takes over the slide. Classify by size before
placing:

| Short side | Aspect ratio | Treat as | Place as |
|---|---|---|---|
| ≤ 256 px | ≤ 1.6 | Icon | Small fixed-size icon in a card, node, or icon row |
| otherwise | — | Screenshot / photo | `image` layout or a sized picture region |

Icons from your organization's set (brand `icons.path`, found with
`python scripts/find_icon.py <keyword>`) always go in nodes, cards, or icon rows,
never in a full-width picture region.

## 4. When unsure

1. Is it **evidence of a fact** (real screen, measurement, site)? Keep the original.
2. Is it **an explanation of a concept** (boxes and arrows)? Redraw.
3. Is text baked into the picture? Redraw, or keep it and add a caption.
4. Is it blurry at the placed size? Redraw, or ask for a better original.
5. Still unclear? **Ask the user.** Do not invent.

## 5. Asset housekeeping

```text
<deck folder>/
├── deck.yaml
├── assets/
│   ├── from-pptx/     extracted from the original (kept separate so provenance is clear)
│   └── ...            supplied or captured by you
└── diagrams/          sources for any externally laid-out diagram
```

- Screenshots as PNG, photos as JPEG. Downscale anything far larger than its
  placed size (about 2x the placed pixel size is plenty); oversized images bloat
  the PPTX.
- Delete images that are no longer used.

## 6. Copyright and usage scope

- Assets supplied for one presentation are used for that purpose only; do not
  carry them into other decks.
- Do not use images found on the web without checking source and license.
- Confirm permission before using a third-party logo. If unsure, reserve the
  space with a clearly marked placeholder and ask.
- Use icons and logos only from packages your organization is licensed to use,
  unmodified, following their usage terms. Record any required attribution in
  `brand/guidelines.md`.

## 7. When no photo exists

Do not force a stock photo; a picture that explains nothing wastes space.
Alternatives, in order:

1. Check whether the content is really a diagram, chart, or table.
2. A `statement` slide with one large sentence.
3. A `quote` slide, if there is a real quotation.
4. Whitespace. Empty is better than a meaningless image.
