# BeszelFetch Theme System

BeszelFetch features a first-class, build-time Linux/Unix ricing theme system supporting 32 curated palettes from popular terminal, editor, and desktop environments.

Themes are applied during generation and compiled directly into Kustom globals. There is **zero runtime overhead** inside KWGT, no external API calls for theming, and no runtime JSON parsing in Android.

---

## Architecture

```text
[themes/*.json]
      │
      ▼
[theme_catalog.py] ──> [setup.py] ──> [generate_clip.py] ──> [.clip / .kwgt]
      │                     │
      ▼                     ▼
[validate_themes.py]  [Interactive Arrow Selector]
[theme_preview.py]    [TrueColor ANSI Swatches]
```

### Key Principles

1. **Build-Time Selection:** Theme selection happens when configuring and generating the widget via `setup.py` or `generate_clip.py`.
2. **Structural Invariance:** Every theme produces the exact same widget tree, shapes, touch targets, and formulas. Only colors change.
3. **Semantic Decoupling:** Generator code references normalized semantic roles (`c_base`, `c_text`, `c_cpu`, `c_accent`, etc.), preventing vendor lock-in to specific palette naming conventions.
4. **WCAG 2.1 AA Contrast Compliance:** All themes are validated to guarantee at least 4.5:1 contrast for primary text against effective backgrounds over dark and light backdrops.
5. **No Palette Leakage:** Generator and layout templates contain zero hardcoded Catppuccin literals. Non-Catppuccin builds are mathematically free of Catppuccin color values.
6. **Catppuccin Mocha as Default:** Running without `--theme` defaults to `catppuccin-mocha`, preserving existing visual identity.

---

## Curated Themes Catalog

The repository includes 32 curated themes:

| Theme ID | Display Name | Mode | Upstream Project | Pinned Revision | License |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ayu-dark` | Ayu Dark | Dark | [ayu-colors](https://github.com/ayu-theme/ayu-colors) | `07450008` | MIT |
| `ayu-light` | Ayu Light | Light | [ayu-colors](https://github.com/ayu-theme/ayu-colors) | `07450008` | MIT |
| `ayu-mirage` | Ayu Mirage | Dark | [ayu-colors](https://github.com/ayu-theme/ayu-colors) | `07450008` | MIT |
| `catppuccin-frappe` | Catppuccin Frappé | Dark | [catppuccin/palette](https://github.com/catppuccin/palette) | `07d02aa1` | MIT |
| `catppuccin-latte` | Catppuccin Latte | Light | [catppuccin/palette](https://github.com/catppuccin/palette) | `07d02aa1` | MIT |
| `catppuccin-macchiato` | Catppuccin Macchiato | Dark | [catppuccin/palette](https://github.com/catppuccin/palette) | `07d02aa1` | MIT |
| `catppuccin-mocha` | Catppuccin Mocha *(default)* | Dark | [catppuccin/palette](https://github.com/catppuccin/palette) | `07d02aa1` | MIT |
| `dracula` | Dracula | Dark | [dracula-theme](https://github.com/dracula/dracula-theme) | `1e04a4b7` | MIT |
| `everforest-dark` | Everforest Dark | Dark | [everforest](https://github.com/sainnhe/everforest) | `85a86eb6` | MIT |
| `everforest-light` | Everforest Light | Light | [everforest](https://github.com/sainnhe/everforest) | `85a86eb6` | MIT |
| `gruvbox-dark` | Gruvbox Dark | Dark | [gruvbox](https://github.com/morhetz/gruvbox) | `ef8864bb` | MIT |
| `gruvbox-light` | Gruvbox Light | Light | [gruvbox](https://github.com/morhetz/gruvbox) | `ef8864bb` | MIT |
| `kanagawa-dragon` | Kanagawa Dragon | Dark | [kanagawa.nvim](https://github.com/rebelot/kanagawa.nvim) | `bb85e4bf` | MIT |
| `kanagawa-lotus` | Kanagawa Lotus | Light | [kanagawa.nvim](https://github.com/rebelot/kanagawa.nvim) | `bb85e4bf` | MIT |
| `kanagawa-wave` | Kanagawa Wave | Dark | [kanagawa.nvim](https://github.com/rebelot/kanagawa.nvim) | `bb85e4bf` | MIT |
| `monokai` | Monokai | Dark | [tinted-theming](https://github.com/tinted-theming/schemes) | `001af361` | MIT |
| `nightfox` | Nightfox | Dark | [nightfox.nvim](https://github.com/EdenEast/nightfox.nvim) | `4dacd3f0` | MIT |
| `nord` | Nord | Dark | [nord](https://github.com/nordtheme/nord) | `1cef7160` | MIT |
| `one-dark` | One Dark | Dark | [tinted-theming](https://github.com/tinted-theming/schemes) | `d70255b7` | MIT |
| `one-light` | One Light | Light | [tinted-theming](https://github.com/tinted-theming/schemes) | `d70255b7` | MIT |
| `oxocarbon-dark` | Oxocarbon Dark | Dark | [oxocarbon.nvim](https://github.com/nyoom-engineering/oxocarbon.nvim) | `cd6523a0` | MIT |
| `palenight` | Material Palenight | Dark | [tinted-theming](https://github.com/tinted-theming/schemes) | `d70255b7` | MIT |
| `rose-pine` | Rosé Pine | Dark | [rose-pine/palette](https://github.com/rose-pine/palette) | `e2e7b5e4` | MIT |
| `rose-pine-dawn` | Rosé Pine Dawn | Light | [rose-pine/palette](https://github.com/rose-pine/palette) | `e2e7b5e4` | MIT |
| `rose-pine-moon` | Rosé Pine Moon | Dark | [rose-pine/palette](https://github.com/rose-pine/palette) | `e2e7b5e4` | MIT |
| `solarized-dark` | Solarized Dark | Dark | [solarized](https://github.com/altercation/solarized) | `62f656a0` | MIT |
| `solarized-light` | Solarized Light | Light | [solarized](https://github.com/altercation/solarized) | `62f656a0` | MIT |
| `tokyo-night` | Tokyo Night | Dark | [tokyonight.nvim](https://github.com/folke/tokyonight.nvim) | `cdc07ac7` | Apache-2.0 |
| `tokyo-night-day` | Tokyo Night Day | Light | [tokyonight.nvim](https://github.com/folke/tokyonight.nvim) | `cdc07ac7` | Apache-2.0 |
| `tokyo-night-moon` | Tokyo Night Moon | Dark | [tokyonight.nvim](https://github.com/folke/tokyonight.nvim) | `cdc07ac7` | Apache-2.0 |
| `tokyo-night-storm` | Tokyo Night Storm | Dark | [tokyonight.nvim](https://github.com/folke/tokyonight.nvim) | `cdc07ac7` | Apache-2.0 |
| `tomorrow-night` | Tomorrow Night | Dark | [tomorrow-theme](https://github.com/chriskempson/tomorrow-theme) | `ccf6666d` | MIT |

---

## Selecting a Theme

### 1. Interactive Setup Wizard

Running `setup.py` on a standard terminal launches an interactive theme selector:

```bash
python setup.py
```

- **↑ / ↓** or **k / j**: Navigate themes
- **Enter**: Confirm selection
- **Esc**: Revert to default (`catppuccin-mocha`)
- Scrolling viewport shows 8 themes at a time with indicators when additional themes exist above or below.
- TrueColor ANSI swatches display core metric and accent colors live in your terminal.

### 2. Command-Line Flag

Pass `--theme <id>` to bypass interactive selection:

```bash
python setup.py --theme tokyo-night-storm
```

Or when generating clips directly:

```bash
python scripts/generate_clip.py --theme nord --output-dir dist/
```

### 3. Listing Available Themes

```bash
python setup.py --list-themes
```

---

## Accessibility and Contrast

Every theme in the catalog is tested for WCAG 2.1 AA compliance:
- **Primary Text (`c_text`):** >= 4.5:1 against effective background (composited over `#000000` and `#FFFFFF` backdrops).
- **Secondary Text (`c_subtext`):** >= 3.0:1 against effective background.
- **UI Indicators / Graphs:** >= 3.0:1 against card background.

### Opacity Policy

- **Dark Themes:**
  - Base (`c_base`): 85% opacity (`0xD9`)
  - Mantle (`c_mantle`): 70% opacity (`0xB3`)
  - Tab Inactive: 15% opacity (`0x25`)
- **Light Themes:**
  - Base (`c_base`): 95% opacity (`0xF2`)
  - Mantle (`c_mantle`): 90% opacity (`0xE6`)
  - Tab Inactive: 15% opacity (`0x25`)

---

## Visual Preview Gallery

Generate an offline HTML specimen of all 32 themes rendered with simulated widget components:

```bash
python scripts/theme_preview.py
```

The resulting file is saved at `dist/theme-preview.html`. Open it in any browser to inspect themes side-by-side with dark/light filtering.
