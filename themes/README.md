# BeszelFetch Theme Catalog

This directory contains curated Linux/Unix ricing themes for BeszelFetch. Each theme is stored as an independent, machine-readable JSON definition conforming to `schema_version: 1`.

Themes are resolved and compiled into the widget at setup/build time:
```text
setup.py --theme <theme-id> -> generator -> generated .clip / .kwgt
```

Catppuccin Mocha (`catppuccin-mocha`) remains the default theme.

---

## Catalog Overview

The catalog includes 32 curated themes covering both dark and light modes across renowned rice, terminal, and editor palettes:

| Theme ID | Display Name | Mode | Upstream Project | License |
| :--- | :--- | :--- | :--- | :--- |
| `ayu-dark` | Ayu Dark | Dark | `ayu-theme/ayu-colors` | MIT |
| `ayu-light` | Ayu Light | Light | `ayu-theme/ayu-colors` | MIT |
| `ayu-mirage` | Ayu Mirage | Dark | `ayu-theme/ayu-colors` | MIT |
| `catppuccin-frappe` | Catppuccin Frappé | Dark | `catppuccin/palette` | MIT |
| `catppuccin-latte` | Catppuccin Latte | Light | `catppuccin/palette` | MIT |
| `catppuccin-macchiato` | Catppuccin Macchiato | Dark | `catppuccin/palette` | MIT |
| `catppuccin-mocha` | Catppuccin Mocha | Dark | `catppuccin/palette` | MIT |
| `dracula` | Dracula | Dark | `dracula/dracula-theme` | MIT |
| `everforest-dark` | Everforest Dark | Dark | `sainnhe/everforest` | MIT |
| `everforest-light` | Everforest Light | Light | `sainnhe/everforest` | MIT |
| `gruvbox-dark` | Gruvbox Dark | Dark | `morhetz/gruvbox` | MIT |
| `gruvbox-light` | Gruvbox Light | Light | `morhetz/gruvbox` | MIT |
| `kanagawa-dragon` | Kanagawa Dragon | Dark | `rebelot/kanagawa.nvim` | MIT |
| `kanagawa-lotus` | Kanagawa Lotus | Light | `rebelot/kanagawa.nvim` | MIT |
| `kanagawa-wave` | Kanagawa Wave | Dark | `rebelot/kanagawa.nvim` | MIT |
| `monokai` | Monokai | Dark | `tinted-theming/schemes` | MIT |
| `nightfox` | Nightfox | Dark | `EdenEast/nightfox.nvim` | MIT |
| `nord` | Nord | Dark | `nordtheme/nord` | MIT |
| `one-dark` | One Dark | Dark | `tinted-theming/schemes` | MIT |
| `one-light` | One Light | Light | `tinted-theming/schemes` | MIT |
| `oxocarbon-dark` | Oxocarbon Dark | Dark | `nyoom-engineering/oxocarbon.nvim` | MIT |
| `palenight` | Material Palenight | Dark | `tinted-theming/schemes` | MIT |
| `rose-pine` | Rosé Pine | Dark | `rose-pine/palette` | MIT |
| `rose-pine-dawn` | Rosé Pine Dawn | Light | `rose-pine/palette` | MIT |
| `rose-pine-moon` | Rosé Pine Moon | Dark | `rose-pine/palette` | MIT |
| `solarized-dark` | Solarized Dark | Dark | `altercation/solarized` | MIT |
| `solarized-light` | Solarized Light | Light | `altercation/solarized` | MIT |
| `tokyo-night` | Tokyo Night | Dark | `folke/tokyonight.nvim` | Apache-2.0 |
| `tokyo-night-day` | Tokyo Night Day | Light | `folke/tokyonight.nvim` | Apache-2.0 |
| `tokyo-night-moon` | Tokyo Night Moon | Dark | `folke/tokyonight.nvim` | Apache-2.0 |
| `tokyo-night-storm` | Tokyo Night Storm | Dark | `folke/tokyonight.nvim` | Apache-2.0 |
| `tomorrow-night` | Tomorrow Night | Dark | `chriskempson/tomorrow-theme` | MIT |

---

## Theme File Contract

Every file in `themes/<theme-id>.json` must follow this structure:

```json
{
  "schema_version": 1,
  "id": "theme-id",
  "name": "Theme Name",
  "mode": "dark",
  "source": {
    "project": "Upstream Project Name",
    "repository": "owner/repo",
    "revision": "pinned-40-char-git-commit-sha",
    "path": "path/in/upstream/repo",
    "license": "SPDX-License-Identifier"
  },
  "colors": {
    "color_name": "#RRGGBB"
  },
  "semantic": {
    "background": "base_color",
    "background_alt": "mantle_color",
    "surface": "surface_color",
    "border": "border_color",
    "text_primary": "text_color",
    "text_secondary": "subtext_color",
    "text_muted": "muted_color",
    "accent": "accent_color",
    "cpu": "cpu_color",
    "memory": "mem_color",
    "disk": "disk_color",
    "network": "net_color",
    "success": "ok_color",
    "warning": "warn_color",
    "high": "high_color",
    "error": "err_color"
  }
}
```

### Required Semantic Roles & Kustom Mapping

All 16 semantic roles are required and map to Kustom globals:

| Semantic Role | Global Variable | Description |
| :--- | :--- | :--- |
| `background` | `c_base` | Main widget backdrop (translucent) |
| `background_alt` | `c_mantle` | Header and outer card background (translucent) |
| `surface` | `c_surface0` | Metric cards, badges, and active tab surfaces |
| `border` | `c_surface1` | Card outlines and dividers |
| `text_primary` | `c_text` | Main telemetry values, hostnames, and headings |
| `text_secondary` | `c_subtext` | Subtext, secondary sensors, and units |
| `text_muted` | `c_muted` | Inactive tabs, labels, and timestamps |
| `accent` | `c_accent` | Distro art, headings, and active accents |
| `cpu` | `c_cpu` | CPU metric bar and temperature |
| `memory` | `c_ram` | RAM metric bar and usage |
| `disk` | `c_disk` | Storage metric bar and capacity |
| `network` | `c_net` | Network transfer rates and 24h totals |
| `success` | `c_ok` | System online status and normal thresholds |
| `warning` | `c_warn` | Elevated load / warning threshold (>70%) |
| `high` | `c_peach` | High load / alert threshold (>85%) |
| `error` | `c_err` | Host offline status, container failure, critical threshold |

---

## Opacity & ARGB Policy

BeszelFetch uses translucent card backgrounds. The opacity policy is separated from upstream palette colors:

- **Dark Themes:**
  - Base: 85% opacity (`#D9RRGGBB`)
  - Mantle: 70% opacity (`#B3RRGGBB`)
  - Inactive tab background: 15% opacity (`#25RRGGBB`)
- **Light Themes:**
  - Base: 95% opacity (`#F2RRGGBB`)
  - Mantle: 90% opacity (`#E6RRGGBB`)
  - Inactive tab background: 15% opacity (`#25RRGGBB`)

---

## Adding a New Theme

1. Research the canonical open-source upstream repository.
2. Pin the exact git commit SHA and identify the license.
3. Create `themes/<theme-id>.json`.
4. Validate the theme using:
   ```bash
   python scripts/validate_themes.py --theme <theme-id>
   ```
5. Run the full test suite:
   ```bash
   python -m unittest discover -s scripts -p "test_*.py" -v
   ```
6. Generate the visual preview specimen:
   ```bash
   python scripts/theme_preview.py
   ```
