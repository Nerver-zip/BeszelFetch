# KWGT Build Guide

## 1. Prerequisites

- KWGT / Kustom Widget Pro with Flows support.
- Network access from Android device to Beszel Hub.
- Valid HTTPS endpoint (SSL certificate trusted by Android).
- Dedicated Beszel user account (read-only recommended).
- Familiarity with Kustom globals, formulas, stacks, and touch actions.

## 2. Declare Globals

Refer to [examples/globals.md](file:///home/nerver/Desktop/dev/server-monitor/examples/globals.md) for full definitions.

Core minimal set:

```text
bz_url
bz_email
bz_pass
bz_token

view=overview
sys_idx=0
sys_id=
metric=cpu
range=24h
container_page=0

systems_json={}
containers_json={}
history_json={}

last_ok=
last_code=
is_stale=1
```

Mark credentials and tokens as Secret Globals whenever supported by your Kustom version.

## 3. Construct `auth_beszel` Flow

Flow Definition:

```text
Trigger: manual
  ↓
Web Get Action:
  Method: POST
  URL: {bz_url}/api/collections/users/auth-with-password
  Headers: Content-Type: application/json
  Body:
    {"identity":"<bz_email>","password":"<bz_pass>"}
  ↓
Condition: if HTTP 2xx
  ↓
Parse: extract .token
  ↓
Assign: set global bz_token
```

Never render the raw token string in any UI component.

## 4. Construct `fetch_systems` Flow

```text
GET {bz_url}/api/collections/systems/records?perPage=100&fields=id,name,status,info&sort=name
Header: Authorization: {bz_token}
```

Flow logic:

```text
Request
 ├─ 2xx -> Verify .items exists -> systems_json=response -> last_ok=now -> is_stale=0
 ├─ 401 -> Run auth_beszel -> Retry request ONCE
 └─ Error/Other -> is_stale=1 (retain existing systems_json)
```

On initial success:
- If `sys_id` is empty, set `sys_id` to `.items[0].id`;
- Preserve the active system selection across subsequent refresh runs.

## 5. Build Overview First

Before building containers or charts, construct and stabilize:
- Hostname display;
- Online / offline status;
- CPU gauge;
- RAM gauge;
- Disk gauge.

Once these five elements are verified and stable, add:
- Network I/O metrics;
- 1-minute load average;
- Temperature badge;
- System uptime.

This keeps troubleshooting focused and isolated.

## 6. Component Hierarchy & Tabs

Create root overlap/stack containers:
- `Header`
- `ViewOverview`
- `ViewContainers`
- `ViewChart`
- `BottomNav`
- `StatusBadge`

In KWGT, use visibility formulas driven by `gv(view)`:

```text
ViewOverview layer visibility: $if(gv(view) = overview, ALWAYS, REMOVE)$
ViewContainers layer visibility: $if(gv(view) = containers, ALWAYS, REMOVE)$
ViewChart layer visibility: $if(gv(view) = chart, ALWAYS, REMOVE)$
```

## 7. Circular Gauges

Create three identical progress groups:
- Circular progress bar;
- Center percentage value;
- Metric label (CPU, RAM, DISK);
- Optional glyph/icon.

Input mappings:
- CPU = `info.cpu`
- RAM = `info.mp`
- DISK = `info.dp`

Configure scale: `0..100`.

Threshold color formula:
- Default: Catppuccin accent color (e.g., `#89b4fa` blue);
- `>= 70`: Warning yellow (`#f9e2af`);
- `>= 85`: Peach / orange (`#fab387`);
- `>= 95`: Alert red (`#f38ba8`).

## 8. Containers View

### Architecture

Use a fixed 5-row layout:
- `row_0`
- `row_1`
- `row_2`
- `row_3`
- `row_4`

Item indexing:

```text
absolute_index = gv(container_page) * 5 + row_index
```

Each row queries the container at its calculated index.

Hide rows (`visibility: REMOVE`) when no container exists at that index.

### Pagination

Previous button touch action:
```text
$mu(max, 0, gv(container_page) - 1)$
```

Next button touch action:
```text
$mu(min, gv(container_max_page), gv(container_page) + 1)$
```

## 9. History / Charts View

Upon switching to `chart`:
- If historical cache is stale, trigger `fetch_history`.

The Flow maps:
- Active `range` -> Beszel `type` and starting timestamp.

The UI renders 24 vertical bars.

Two implementation approaches:

### A. Downsampling in Flow (Recommended)
The Flow computes or filters the dataset down to 24 values stored in global variables or a compact JSON array.
- Advantages: Simplified UI formulas, better rendering performance, high predictability.

### B. Direct JSON Indexing
Each bar directly accesses an index within `history_json`.
- Advantages: Fewer global variables.
- Disadvantages: Complex formulas, sensitive to JSON array bounds.

## 10. Refresh Schedule

Recommended triggers:
- Preset load: `fetch_systems`;
- Periodic: every 5 minutes;
- Manual: Touch action on ↻ header icon;
- Tab switch to Containers: if stale, trigger `fetch_containers`;
- Tab switch to Chart: if stale, trigger `fetch_history`.

Avoid polling every few seconds.

## 11. Stale Indicator Logic

Track:
- `last_ok` (timestamp of last successful response)
- `last_code` (HTTP status code)
- `is_stale` (boolean flag)

Header status badge:
- Normal: `● online` (Green)
- Stale: `● stale · 14:25` (Yellow)
- Offline: `● offline · cached 14:25` (Red)

## 12. Host Switching

Touch action on system name:
- Cycles `sys_idx = (gv(sys_idx) + 1) % gv(sys_count)`;
- Updates `sys_id`;
- Clears view-specific caches;
- Dispatches immediate refresh.

## 13. Debug Mode

Global toggle:
```text
debug=0
```

When `debug=1`, render a diagnostic footer:
```text
HTTP 200 · sys=abc123 · view=overview · cache=14:25
```

Never display:
- Passwords;
- Secret tokens;
- Sensitive internal hostnames in shared presets.

## 14. Preset Export Checklist

Before exporting a `.kwgt` file for sharing:
1. Replace `bz_url` with placeholder (e.g. `https://beszel.example.com`);
2. Clear `bz_email`;
3. Clear `bz_pass`;
4. Clear `bz_token`;
5. Flush cached JSON payloads;
6. Set `debug=0`;
7. Export directly via KWGT app.
