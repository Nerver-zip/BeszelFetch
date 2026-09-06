---
name: frontend-visual
description: Translates frontend design system principles into KWGT primitives and Unix ricing / Catppuccin aesthetics.
---

# Frontend Visual for KWGT

## Objective

Apply rigorous frontend engineering design systems to KWGT without assuming HTML/CSS capabilities.

## Design Tokens

Never pick arbitrary ad-hoc hex values.
Reference `examples/palette.json`.

Semantic Tokens:
- `bg`
- `bg_alt`
- `border`
- `text`
- `muted`
- `cpu`
- `memory`
- `disk`
- `network`
- `success`
- `warning`
- `danger`

## Visual Hierarchy

Order of visual attention:
1. Host status & identity;
2. Core primary metrics (CPU, RAM, Disk);
3. Active tab content (containers list / sparkline);
4. Secondary metadata (timestamps, uptime);
5. Bottom navigation.

## Spacing Grid

Use a compact 4dp base scale:
```text
4, 8, 12, 16, 24 dp
```

Prioritize proportional consistency across views.

## Component Contract

- `Header`
- `MetricRing`
- `MiniStat`
- `ContainerRow`
- `ChartBar`
- `MetricChip`
- `BottomNavItem`
- `StatusBadge`

Each component must define:
- Inputs / properties;
- Normal render state;
- Empty / fallback state;
- Active / alert state (if applicable).

## Unix / Ricing Aesthetic

Emphasize:
- Clean monospace fonts;
- `~/homelab` path header styling;
- Minimalist status dots;
- Terse uppercase labels;
- Low-density borders with subtle opacity;
- Distinct Catppuccin Mocha accents.

Avoid:
- Neon glows or heavy drop-shadows;
- Excessive clashing accent colors;
- Illegible micro-text;
- Ambiguous decorative glyphs.

## Accessibility & Usability

- High text contrast against dark backgrounds;
- Color paired with text labels (never rely solely on hue for status);
- Touch targets minimum 44x44 dp;
- Truncate long container and host names gracefully with ellipsis.

## Layout Adaptability

Validate across:
- `4x2` and `4x3` launcher grid allocations;
- Android display scaling and font scaling;
- Extra-long container names;
- Extra-long hostnames.
