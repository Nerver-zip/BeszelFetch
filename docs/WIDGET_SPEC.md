# Visual & Interaction Specification

## 1. Design Language

Theme: **Linux/Unix Ricing**, inspired by:
- Modern terminal emulators;
- Minimalist status bars (Waybar, Polybar);
- TUI system dashboards (btop, htop);
- Hyprland / Wayland rice aesthetics;
- Catppuccin Mocha color system.

The design avoids literal terminal emulation: the core priority remains rapid visual scanning and legibility on an Android home screen.

## 2. Widget Grid & Dimensions

Target design baseline:
- `4x2` or `4x3` on Android launcher grid;
- Responsive layout based on relative proportional sizing;
- Outer padding: `12–16 dp` equivalent;
- Card corner radius: `20–28 dp`;
- Card border: `1 dp` solid `surface1` with subtle opacity.

A `4x3` grid allocation provides optimal vertical space for the Containers list and Chart sparklines.

## 3. Color Palette & Semantic Roles

BeszelFetch uses a decoupled semantic role system supporting 32 curated Linux/Unix ricing palettes (see [docs/THEMES.md](THEMES.md)), with **Catppuccin Mocha** serving as the reference specification and default palette.

| Semantic Role | Global Variable | Catppuccin Mocha Token | Default Hex Value | Usage |
|---|---|---|---|---|
| `background` | `c_base` | `base` | `#D91E1E2E` (85%) | Main widget card background |
| `background_alt` | `c_mantle` | `mantle` | `#B3181825` (70%) | Sub-surface / nested container background |
| `surface` | `c_surface0` | `surface0` | `#FF313244` | Progress bar tracks / button fills / active tab |
| `border` | `c_surface1` | `surface1` | `#FF45475A` | Card borders / dividers |
| `text_primary` | `c_text` | `text` | `#FFCDD6F4` | Primary high-contrast text |
| `text_secondary` | `c_subtext` | `subtext1` | `#FFBAC2DE` | Secondary labels / units / sensors |
| `text_muted` | `c_muted` | `overlay0` | `#FF6C7086` | Inactive icons / tertiary text / tab labels |
| `accent` | `c_accent` | `mauve` | `#FFCBA6F7` | Heading, ASCII distro art highlight, general accent |
| `cpu` | `c_cpu` | `blue` | `#FF89B4FA` | CPU accent color |
| `memory` | `c_ram` | `mauve` | `#FFCBA6F7` | Memory / RAM accent color |
| `disk` | `c_disk` | `teal` | `#FF94E2D5` | Disk / Storage accent color |
| `network` | `c_net` | `sapphire` | `#FF74C7EC` | Network I/O accent color |
| `success` | `c_ok` | `green` | `#FFA6E3A1` | Online status / healthy indicator |
| `warning` | `c_warn` | `yellow` | `#FFF9E2AF` | Warning / stale cache badge |
| `high` | `c_peach` | `peach` | `#FFFAB387` | High resource utilization warning (>85%) |
| `error` | `c_err` | `red` | `#FFF38BA8` | Critical load / offline / auth failure |

## 4. Typography

Font guidelines:
- Primary: A clean monospace typeface (e.g. JetBrains Mono, Fira Code);
- Fallback: System default monospace;
- Header: Monospace Semibold;
- Gauge values: Monospace Bold;
- Labels & Subtitles: Monospace Regular / Medium;
- Metadata & Timestamps: Monospace Regular.

## 5. Persistent Header

```text
┌─────────────────────────────────────────┐
│ ● ~/homelab          atlas ▾       ↻    │
│   4 systems · 4 up          14:32       │
└─────────────────────────────────────────┘
```

Header Elements:
- `●` Real-time status dot of selected host;
- `~/homelab` Project identity text;
- Selected system hostname with dropdown indicator (`▾`);
- Touch action on hostname: Cycles through available monitored systems;
- Touch action on `↻`: Triggers immediate manual refresh;
- Secondary line: Total systems count and timestamp of last successful sync.

## 6. View: Overview

```text
┌─────────────────────────────────────────┐
│ ● ~/homelab              atlas     ↻    │
│                                         │
│     ╭────╮      ╭────╮      ╭────╮     │
│     │ 18%│      │ 62%│      │ 47%│     │
│     ╰────╯      ╰────╯      ╰────╯     │
│      CPU          RAM         DISK      │
│                                         │
│  ↓ 2.1M  ↑ 410K   LA 0.42   43°C       │
│  uptime 12d 04h              ● online   │
│                                         │
│   [ overview ] [ containers ] [ chart ] │
└─────────────────────────────────────────┘
```

### Circular Metrics

Each circular gauge contains:
- Background track (`surface0`);
- Color-coded progress stroke;
- Centered percentage text (`%`);
- Metric title underneath (CPU, RAM, DISK).

Dynamic Threshold Coloring:
- `0–69%`: Normal metric accent (Blue, Mauve, Teal);
- `70–84%`: Warning Yellow (`#F9E2AF`);
- `85–94%`: High utilization Peach (`#FAB387`);
- `≥95%`: Critical Alert Red (`#F38BA8`).

Red is reserved exclusively for critical thresholds and failure states.

## 7. View: Containers

```text
┌─────────────────────────────────────────┐
│ ● ~/homelab              atlas     ↻    │
│ CONTAINERS                     8 total  │
│                                         │
│ ● beszel-agent       CPU 0.4%  RAM 31M  │
│ ● caddy              CPU 0.1%  RAM 48M  │
│ ● immich-server      CPU 3.8%  RAM 612M │
│ ● postgres           CPU 1.2%  RAM 244M │
│ ● redis              CPU 0.2%  RAM 18M  │
│                                         │
│              ‹   1 / 2   ›              │
│   [ overview ] [ containers ] [ chart ] │
└─────────────────────────────────────────┘
```

### Fixed-Row Pagination Architecture

KWGT does not support native virtual scrolling lists. The recommended architecture uses:
- 5 fixed row component groups (`row_0` to `row_4`);
- Item indexing: `index = page * 5 + row_offset`;
- Previous / Next pagination touch controls (`‹`, `›`);
- Row visibility: `REMOVE` when no container exists at the target index.

### Row Content
- Status dot (green if running);
- Truncated container name;
- CPU utilization;
- Memory usage with automatic unit scaling (`MiB`, `GiB`);
- Network throughput in secondary subtitle (if available).

## 8. View: Chart

```text
┌─────────────────────────────────────────┐
│ ● ~/homelab              atlas     ↻    │
│ CPU HISTORY                  24h   18%  │
│                                         │
│  100 ┤                                    │
│   75 ┤      ▂                             │
│   50 ┤   ▂  ▅ ▃        ▃                  │
│   25 ┤▂ ▃▅▂▆▃▂▂ ▂▃▂▂▃▅▂▃▂▂▃▂▂▃▂▂      │
│    0 ┴────────────────────────────       │
│       -24h                       now     │
│                                         │
│ [CPU] [RAM] [DISK] [NET]      [24h ▾]  │
│ min 4%     avg 22%       max 71%        │
│   [ overview ] [ containers ] [ chart ] │
└─────────────────────────────────────────┘
```

### Sparkline Implementation
- 24 vertical bar rectangles arranged in a horizontal stack;
- Uniform bar width and proportional spacing;
- Bottom-aligned;
- Height driven by normalized metric value;
- Most recent datapoint highlighted with higher opacity or bright accent;
- Horizontal reference gridlines at 25%, 50%, 75%, 100%.

Scale Configuration:
- CPU, RAM, Disk: Fixed 0–100% scale;
- Network: Dynamic auto-scaling to max value in selected range with clear bandwidth unit labels (`KiB/s`, `MiB/s`).

## 9. Bottom Navigation Bar

Three navigation buttons:
- Overview: Grid / pulse icon;
- Containers: Cube / container icon;
- Chart: Sparkline / chart bar icon.

Active State Styling:
- Accent text color;
- Subtle underline pill marker;
- Inactive tabs rendered in `overlay0`.

Touch Actions:
- `overview`: Sets `view=overview`;
- `containers`: Sets `view=containers`; fetches containers if cache is older than 5m;
- `chart`: Sets `view=chart`; fetches history if cache is older than 15m.

## 10. UI State Machine

### Loading State
- Preserves existing cached data on screen;
- Animates refresh icon;
- Never clears the screen to blank canvas.

### Stale Cache State
- Displays yellow `● stale · <time>` badge in header;
- Visualizes the last valid payload with low opacity timestamp.

### Offline State
- Displays red `● offline` badge;
- Retains last valid cached metrics.

### Authentication Error
- Displays red `● auth` badge;
- Hides sensitive payload strings.

### Empty State: Containers
```text
No running containers reported
```

### Empty State: History
```text
Insufficient historical data
```

## 11. Microcopy Conventions

Terse Unix/TUI labels:
- `CPU`
- `RAM`
- `DISK`
- `NET`
- `LA` (Load Average)
- `UP` (Uptime)
- `stale`
- `offline`
- `auth`
- `now`
