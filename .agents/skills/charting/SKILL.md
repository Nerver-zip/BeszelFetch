---
name: charting
description: Implements metric history and sparkline bar visualizations in KWGT using Beszel aggregation ranges.
---

# Charting in KWGT

## MVP Implementation

Use 24 vertical bars arranged in a horizontal stack group.

Reasons:
- Simple and predictable rendering;
- Reliable performance in KWGT;
- No dependency on web canvases or external SVG rendering;
- Native support via Horizontal Stack Groups.

## Inputs

- `metric`: Active metric key (`cpu`, `mem`, `disk`, `net`)
- `range`: Selected time window (`1h`, `12h`, `24h`, `7d`, `30d`)
- `history_json`: Cached historical payload
- `chart_points`: 24 datapoints

## Scaling Rules

CPU / RAM / Disk:
```text
Fixed scale: 0 .. 100%
```

Network:
- Preferred: Dynamic auto-scaling to range maximum (`scale_max = max(series)`);
- Display explicit unit label (`KiB/s`, `MiB/s`);
- Optional fallback: Static ceiling via `gv(net_max)`.

## Downsampling Strategy

If payload contains more than 24 records:
- Sample evenly distributed indices;
- Strictly preserve chronological ordering;
- Always preserve the most recent datapoint (last index).

If fewer than 24 records exist:
- Render available bars;
- Hide unused trailing bars (`visibility: REMOVE`).

## Summary Statistics

Calculate and display:
- `min`
- `avg`
- `max`
- `current` (last value)

Compute in the Flow if nested formulas become cumbersome.

## Color Coding

- CPU -> Blue (`#89B4FA`)
- RAM -> Mauve (`#CBA6F7`)
- Disk -> Teal (`#94E2D5`)
- Network -> Sapphire (`#74C7EC`)

Optionally highlight bars exceeding 85% or 95% thresholds with warning/critical tones, but avoid visual clutter.

## Reference Gridlines

Optional subtle horizontal reference lines:
- 25%, 50%, 75%
- Low opacity `surface0` (`#313244`).

## Empty State

Fewer than 2 valid datapoints:
```text
Insufficient history yet
```

## Post-MVP Roadmap

Continuous SVG bezier sparklines can be considered as a post-MVP enhancement. Do not start with SVG paths in the MVP.
