# Data visualization: choose the relationship, then draw it accurately

Use this when a number, comparison, trend, distribution, or assessment needs a
visual. A chart earns its place when its geometry makes the reader's question
easier to answer. An exact-value lookup may be a `table`. One important figure
may be a `stats` slide with a claim, unit, and source. Do not add a chart only
to look analytical.

## 1. Choose by question and data

| Question | Representation | Conditions / alternatives |
|---|---|---|
| Which category is larger? | Horizontal bar | Comparable units and scope; sort deliberately; zero baseline |
| How did it change over time? | Line; column for a short sequence | Chronological spacing; show gaps and relevant events |
| What changed between two states? | Paired bars or a `stats` delta | Same definition and basis; distinguish absolute vs relative change |
| How does a total divide into parts? | Stacked bar or column | State the denominator; show totals if share alone misleads |
| Parts of one whole, ≤ 5 parts | Pie or doughnut (allowed) | Only true parts-of-whole summing to 100%; otherwise bars |
| Which contributors explain an additive change? | Waterfall (`custom`) | Signed changes reconcile start to end |
| How do two measured variables relate? | Scatter (`custom`) | Units and scales explicit; correlation is not mechanism |
| Which actions fit two criteria? | Priority matrix (`custom` or `diagram`) | Define criteria and thresholds; qualitative regions if no scores |
| Several entities on the same dimensions | Aligned bars or small multiples | Shared scales, same criterion order, direct labels |
| Normalized capability profile | Radar only if profile shape matters | Same axes, rubric, and direction; else aligned bars |
| Exact value at row × column | `table` | Keep units visible; respect table density |

The default for shares is a bar. Use a pie or doughnut only for parts of a whole
with at most five parts; never for comparisons across categories or over time.

Many series or many time points do not automatically require a table or dropping
evidence. Keep the relationship that matters, then use small multiples or a
linked detail slide. Aggregate only on a stated basis; keep exceptions.

## 2. The native `chart` layout

Charts are native python-pptx charts, editable in PowerPoint with their data
workbook embedded. Supported types: `bar` (horizontal), `column`, `line`,
`stacked_bar`, `stacked_column`, `pie`, `doughnut`.
Example (all keys: [layouts.md](layouts.md#chart)):

```yaml
- layout: chart
  title: Region B drove two thirds of this year's growth
  chart:
    type: column
    categories: [2023, 2024, 2025]
    series:
      - { name: Region B, values: [12, 19, 31] }   # highlight series first
      - { name: Region A, values: [10, 11, 13] }
    unit: "USD m"
    labels: true          # direct data labels; hides the value axis
  source: "Finance ledger, FY2023–FY2025, USD millions"
```

Rules for the generator and for `custom` charts alike:

- **Highlight series = `colors.series[0]`.** The series the headline names comes
  first; the others use muted series colors (`colors.series[1]` or
  `colors.muted`). Do not give every series a saturated color.
- **Direct labels** on bars or line ends where practical; then drop the legend.
  Color alone must not carry meaning: use labels, lightness, or position too.
- **The author computes ratios, shares, and deltas** before writing the spec, and
  records the calculation in notes. The chart plots the given values; it does
  not decide what the denominator is.
- Value labels come from the plotted values. A typed label must equal the plotted
  value at the displayed precision, or be a documented derived value.
- Remove ink only when something else carries its information: drop the chart
  title when the slide headline/caption names metric, unit, and period; drop the
  legend when series are labeled directly; drop gridlines and the value axis
  only when every needed value is labeled. Keep the zero baseline of bars.
- Gridlines, if any, are hairlines in `colors.line`. Labels, captions, and sources
  use `colors.muted` or darker, never `colors.chrome`.
- Fonts come from `fonts.body`; label text is at least `type.min`, usually
  `type.caption`. A half-width chart has a smaller label budget than a
  full-width one: shorten categories rather than shrinking type.
- Horizontal bar charts keep the spec order top-down: the first category is the
  top bar. Write a ranking in the order it should read.
- For a 100% stack, check the unrounded shares sum to 1; rounded labels may
  differ by up to half a display unit per item.
- When bars align with text rows or chips beside the chart, derive the gap width
  from that row pitch.
- An annotation for a headline multiple or range attaches to the actual data
  points (within about 1 pt), not to a guessed position.

## 3. Establish the measurement basis

Before drawing, record:

- Metric definition, unit, period, population or scope, denominator.
- Actual, estimate, target, or illustrative status; do not mix them silently.
- Aggregation, conversion, rounding, normalization, exclusions.
- Comparison baseline and any changed definition.
- Missing values and uncertainty. Missing is not zero; do not connect a line
  across missing periods as if measured.

Show the essential unit, period, and source on the slide (the `source` field or a
caption). Keep calculation detail in notes. Unknown inputs stay explicit TODOs;
never invent or copy sample figures into real material.

When reusing a chart from a supplied PPTX, compare the cached series, the
embedded workbook, the visible labels, and nearby totals. Mockups can contain
default dates, fractional counts, or arithmetic that does not reconcile. Native
editability does not make those values verified. A subgroup's detail needs its
own denominator.

## 4. Connect charts only when the second view adds evidence

A trend can establish the change and a breakdown can name its contributors. Keep
item IDs, periods, units, and series colors stable across both views. Do not
repeat the same values in a chart and an adjacent table without purpose.

Comparable panels need the same axis bounds **and** the same plot-area size.
Matching axis numbers alone is not a shared scale: separate small charts can draw
a larger value shorter if their plot heights differ. Check units per point in the
render.

Pages that continue the same comparison (1/3, 2/3, …) keep the same plot area,
axis bounds, and color key. If a different scale is unavoidable, show each axis
and say so. Keep one direction per exhibit (up/right = more); mark an inverted
metric with "lower is better" instead of flipping one column silently.

For quantities in different units, aligned charts are usually clearer than a dual
axis. Use a dual axis only when reading both at once helps, both axes are clearly
labeled, and the scaling does not manufacture a relationship.

## 5. Geometry for `custom` charts

When a chart type is not available natively (waterfall, scatter, dumbbell, radar,
bubble), draw it with deckkit primitives and compute every coordinate from data.
For a plot rectangle `(left, top, width, height)`:

```text
x(v) = left + (v - xMin) / (xMax - xMin) * width
y(v) = top + height - (v - yMin) / (yMax - yMin) * height
barTop = min(y(v), y(0));  barHeight = abs(y(v) - y(0))
```

Reserve room inside the plot area for ticks, value labels, annotations, and the
legend. Never nudge heights by eye to strengthen a claim. For a constant series,
choose an explicit nonzero display range and label it.

- **Baselines.** Bars start at zero. A line or scatter may use a restricted range
  when it helps; show the bounds and make the restriction explicit.
- **Area encodings.** When circle area encodes a positive value, diameter ∝ √value.
  A 2× label on a circle with 4× the area overstates the difference. Where
  position encodes the value (dot plot), equal-size dots are correct.
- **Differences.** Label a gap in the metric's own unit; use percentage points only
  for differences between ratios. Show both end values when claiming a multiple.
- **Concept curves** with no data say so on the axis and carry no numeric ticks.
- **Waterfall.** Only additive contributions on one basis:
  `end = start + Σ changes`; `stepStart[i] = start + Σ changes before i`.
  Start and end totals rise from zero; contributions float. Check the
  reconciliation including rounding. Overlapping effects or different
  denominators cannot be summed into one bridge.
- **Radar.** Same normalized scale, axis order, rubric, and direction for every
  entity; few series; show missing assessments. Polygon area is not a score.
- **Priority matrix.** Defensible coordinates or an explicitly qualitative
  classification, with criteria and thresholds stated first; keep item IDs linked
  to the action list. Without a justified two-axis assessment, use a ranked list.

## 6. Verify the chart

Build, render, and look at the slide at real size:

```text
python scripts/build_deck.py deck.yaml -o out/deck.pptx
python scripts/render_deck.py out/deck.pptx
```

- The chart answers the stated question better than a simpler form.
- Visible labels match the data; geometry matches the declared scale.
- Parts, totals, waterfall steps, and percentages reconcile.
- Comparison bases and cross-panel scales are compatible.
- Source, unit, period, assumptions, and estimate status are clear.
- Annotations point to actual data and separate observation from inference.
- Every number in the headline or lead traces to the plotted data or a recorded
  calculation.
- The accent (`colors.series[0]`) marks what the headline names; the context is
  distinguishable without hue alone.
- Labels fit inside the plot and stay legible in the render.

Keep the source data and the spec. When values change, rebuild from them and
re-inspect the affected slides.
