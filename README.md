# Server Monitor Widget — KWGT + Beszel

A complete blueprint and reference implementation for an Android/KWGT widget monitoring your homelab directly via the **Beszel Hub REST API**, without requiring any third-party proxy, auxiliary backend, or middleman service.

## Goals

Build a widget with a **Linux/Unix ricing + Catppuccin Mocha** aesthetic that is clean, compact, highly legible, and features three switchable views:

1. **Overview** — CPU, RAM, Disk, Network I/O, Load Average, Temperature, Uptime, and System Status.
2. **Containers** — Paginated container list showing status, CPU%, memory usage, and network I/O.
3. **Charts** — Historical bar/sparkline metrics for CPU, RAM, Disk, and Network with configurable time ranges.

Key architectural design goals:
- Direct execution via **KWGT/Kustom Flows**;
- Direct authentication against Beszel/PocketBase;
- Encapsulated credentials inside global variables (never hardcoded into formulas or components);
- Stale-while-revalidate local caching (network failure never wipes the last valid data);
- Contract adapter layer isolating schema differences between Beszel versions;
- Multi-agent orchestration support via dedicated skills in `.agents/`.

## Repository Contents

```text
server-monitor/
├── README.md
├── ARCHITECTURE.md
├── WIDGET_SPEC.md
├── KWGT_BUILD_GUIDE.md
├── DATA_CONTRACT.md
├── SECURITY.md
├── SOURCES.md
├── AGENTS.md
├── manifest.json
├── .agents/
│   ├── README.md
│   └── skills/
│       ├── orchestrator/SKILL.md
│       ├── kwgt-kustom/SKILL.md
│       ├── beszel-pocketbase/SKILL.md
│       ├── kustom-data/SKILL.md
│       ├── frontend-visual/SKILL.md
│       ├── charting/SKILL.md
│       ├── test-debug/SKILL.md
│       └── docs-release/SKILL.md
├── examples/
│   ├── palette.json
│   ├── globals.md
│   ├── flows.md
│   ├── formulas.md
│   ├── endpoints.md
│   └── fixtures/
│       ├── auth-response.json
│       ├── systems-response.json
│       ├── system-stats-response.json
│       └── container-stats-response.json
├── mockups/
│   ├── overview.txt
│   ├── containers.txt
│   └── chart.txt
├── scripts/
│   └── ai-jail.sh
└── widget/
    ├── TREE.md
    ├── COMPONENTS.md
    └── KWGT_PRESET_NOT_INCLUDED.md
```

## Central Architecture

```text
┌─────────────┐       HTTPS / REST        ┌──────────────┐
│ Android     │ ────────────────────────▶ │ Beszel Hub   │
│ KWGT/Kustom │ ◀──────────────────────── │ PocketBase   │
└──────┬──────┘                           └──────────────┘
       │
       ├── Secret globals: URL / login / token
       ├── Flows: auth / fetch / retry / cache
       ├── JSON cache: systems / containers / history
       └── UI: overview / containers / chart
```

No intermediate proxy or middleware is used.

## Setup Guide

### Prerequisites
1. **Beszel Hub**: An accessible instance of Beszel Hub (v0.7.0+ or v0.10.0+).
2. **Network Access**: Your Android device must be able to reach Beszel Hub via HTTPS (e.g., LAN, Tailscale/WireGuard, or reverse proxy with SSL).
3. **Dedicated User**: In Beszel Hub, create a dedicated non-admin user (read-only) with access restricted to the systems you intend to monitor.
4. **KWGT Kustom Widget Pro**: Installed on your Android device (Pro key is required for importing presets and using Flows).

### Step-by-Step Configuration

1. **Configure Global Variables**
   - Open KWGT, create a new 4x2 or 4x3 widget.
   - In the **Globals** tab, create the variables documented in [examples/globals.md](file:///home/nerver/Desktop/dev/server-monitor/examples/globals.md):
     - `bz_url`: Base URL of your Beszel instance (e.g., `https://beszel.yourdomain.com`).
     - `bz_email`: Dedicated Beszel user email.
     - `bz_pass`: Dedicated Beszel user password.
     - `bz_token`: Leave empty (populated automatically by the auth flow).
     - Visual tokens (colors and fonts) from [examples/palette.json](file:///home/nerver/Desktop/dev/server-monitor/examples/palette.json).

2. **Configure Kustom Flows**
   - Implement the Flows defined in [examples/flows.md](file:///home/nerver/Desktop/dev/server-monitor/examples/flows.md):
     - `auth_beszel`: Authenticates with PocketBase `/api/collections/users/auth-with-password` and stores `token`.
     - `fetch_systems`: Queries `/api/collections/systems/records`, handles 401 token refresh, and caches `sys_json`.
     - `fetch_containers`: Queries container metrics and updates `cnt_json`.
     - `fetch_history`: Retrieves historical datapoints for the Chart view and populates `hist_json`.
     - `refresh_current_view`: Dispatches requests based on the active tab (`gv(view)`).

3. **Verify API Connection**
   - Trigger `auth_beszel` manually. Verify `gv(bz_token)` gets populated.
   - Trigger `fetch_systems`. Verify `gv(sys_json)` contains the systems payload.
   - Ensure the last valid JSON cache is retained on simulated network disconnection.

4. **Build the Visual Hierarchy**
   - Construct the component tree as detailed in [widget/TREE.md](file:///home/nerver/Desktop/dev/server-monitor/widget/TREE.md) and [widget/COMPONENTS.md](file:///home/nerver/Desktop/dev/server-monitor/widget/COMPONENTS.md).
   - Apply the Catppuccin Mocha color tokens and typography.
   - Connect formula bindings from [examples/formulas.md](file:///home/nerver/Desktop/dev/server-monitor/examples/formulas.md).

5. **Test & Export**
   - Validate failure states (expired token, network loss, stale cache).
   - Export the preset directly from the KWGT editor menu to preserve device and version-specific metadata.

## Recommended Defaults

| Setting | Default | Description |
|---|---|---|
| Background Refresh | 5 minutes | Balanced between battery life and data freshness |
| Manual Refresh | Header button | Triggers `refresh_current_view` on demand |
| Stale Threshold | 2 missed cycles | Displays subtle warning badge when cache is older than 10m |
| Containers per Page | 5 | Optimizes touch target height and readability |
| Chart Data Points | 24 bars | Clean alignment for hourly and daily sparklines |
| Default Range | 24h | Initial historical range for charts |
| Default Metric | CPU | Initial metric tab for charts |
| Color Theme | Catppuccin Mocha | High-contrast dark ricing theme |
| Network Units | Auto | Dynamic formatting (`KiB/s`, `MiB/s`) |

## Recommended Reading Order

1. [ARCHITECTURE.md](file:///home/nerver/Desktop/dev/server-monitor/ARCHITECTURE.md)
2. [DATA_CONTRACT.md](file:///home/nerver/Desktop/dev/server-monitor/DATA_CONTRACT.md)
3. [KWGT_BUILD_GUIDE.md](file:///home/nerver/Desktop/dev/server-monitor/KWGT_BUILD_GUIDE.md)
4. [WIDGET_SPEC.md](file:///home/nerver/Desktop/dev/server-monitor/WIDGET_SPEC.md)
5. [.agents/README.md](file:///home/nerver/Desktop/dev/server-monitor/.agents/README.md)
