"""Custom slide example: a compact Gantt built from deckkit primitives.

deck.yaml:
    - layout: custom
      python: custom/gantt.py
      title: ...
      periods: [W1, W2, W3, W4]
      rows: [{label: ..., start: 0, end: 2, done: true}, ...]
      today: 1.5          # optional, in period units
      today_label: today  # optional

``render(c, spec, ctx, top)`` receives the brand-bound canvas and the y where
the body starts. Use brand tokens only — never literal colors or sizes.
"""
from deckkit import columns  # noqa: F401  (available helpers)


def render(c, spec, ctx, top):
    b = c.brand
    x0, x1 = b.content_left, b.content_right
    label_w = 180.0
    periods = spec.get("periods", [])
    rows = spec.get("rows", [])
    track_x, track_w = x0 + label_w, x1 - x0 - label_w
    unit = track_w / max(1, len(periods))
    row_h = min(34.0, (float(b["layout.body_bottom"]) - top - 24) / max(1, len(rows)))
    for i, p in enumerate(periods):
        c.text(track_x + i * unit, top, unit, 16, str(p), size="label", font="mono",
               color="muted", align="center", check_fit=False)
    y = top + 24
    for row in rows:
        c.text(x0, y, label_w - 12, row_h, row["label"], size="body", color=c.ink,
               anchor="middle", check_fit=False)
        bx = track_x + row["start"] * unit
        bw = (row["end"] - row["start"]) * unit
        c.box(bx + 2, y + row_h * 0.3, bw - 4, row_h * 0.4,
              fill="accent" if row.get("done") else "surface_alt",
              line=None if row.get("done") else "accent", line_width=0.75, radius=0)
        c.line(x0, y + row_h, x1, y + row_h, color="line", width=0.5)
        y += row_h
    if spec.get("today") is not None:
        tx = track_x + float(spec["today"]) * unit
        c.line(tx, top + 20, tx, y, color="accent", width=1.0, dash=True)
        c.text(tx - 40, y + 4, 80, 14, spec.get("today_label", "today"), size="label", color="accent", align="center",
               check_fit=False)
