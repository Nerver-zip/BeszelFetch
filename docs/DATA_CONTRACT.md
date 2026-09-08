# Data Contract

This document decouples UI presentation requirements from the raw Beszel/PocketBase schema.

## 1. Core Rule

**No visual component should depend directly on raw JSON paths scattered across formulas.**

Centralize all JSON paths into dedicated adapter formulas or global variables. If a Beszel upgrade alters an internal key, fixes must happen in a single place.

## 2. Systems

Conceptual endpoint:

```http
GET {bz_url}/api/collections/systems/records
Authorization: {bz_token}
```

Recommended query string:

```text
?perPage=100&fields=id,name,status,info&sort=name
```

Minimum expected response payload:

```json
{
  "items": [
    {
      "id": "SYSTEM_ID",
      "name": "atlas",
      "status": "up",
      "info": {
        "u": 1051200,
        "cpu": 18.4,
        "mp": 62.1,
        "dp": 47.8,
        "bb": [420000, 2210000],
        "la": [0.42, 0.38, 0.31],
        "dt": 43.0
      }
    }
  ]
}
```

### Field Mapping

| UI Field | Beszel Key | Description |
|---|---|---|
| `system.id` | `.id` | System record UUID |
| `system.name` | `.name` | Hostname |
| `system.status` | `.status` | `up` or `down` |
| `overview.cpu_pct` | `.info.cpu` | CPU usage % |
| `overview.mem_pct` | `.info.mp` | Memory usage % |
| `overview.disk_pct` | `.info.dp` | Root disk usage % |
| `overview.uptime_s` | `.info.u` | Uptime in seconds |
| `overview.net_sent_bps` | `.info.bb[0]` | Upload bandwidth (bytes/s) |
| `overview.net_recv_bps` | `.info.bb[1]` | Download bandwidth (bytes/s) |
| `overview.load1` | `.info.la[0]` | 1-minute load average |
| `overview.temp_c` | `.info.dt` | Dashboard temperature (°C) |

Note: Some keys are optional depending on host OS, sensors, and configuration. The UI must provide graceful fallbacks.

## 3. System History

Endpoint:

```http
GET {bz_url}/api/collections/system_stats/records
Authorization: {bz_token}
```

Sample query:

```text
page=1
perPage=500
skipTotal=1
filter=system='SYSTEM_ID' && created > 'ISO_DATE' && type='20m'
fields=created,stats
sort=created
```

Inside `stats`, relevant metric keys include:

| Metric | Key | Description |
|---|---|---|
| CPU % | `cpu` | Overall CPU utilization |
| Memory Used % | `mp` | Memory percentage |
| Disk Used % | `dp` | Disk percentage |
| Bandwidth | `b` | `[sent_bytes, recv_bytes]` |
| Load Average | `la` | `[1m, 5m, 15m]` |

Beszel uses ultra-compact keys to minimize storage and transmission overhead.

## 4. Range to Resolution Mapping

| UI Range | Beszel `type` | Time Window |
|---|---|---|
| `1h` | `1m` | Last 1 hour |
| `12h` | `10m` | Last 12 hours |
| `24h` | `20m` | Last 24 hours |
| `7d` | `120m` | Last 7 days |
| `30d` | `480m` | Last 30 days |

The acquisition flow converts the selected UI range into:
- An ISO 8601 start timestamp;
- The corresponding aggregation `type`.

## 5. Container Stats

Conceptual endpoint:

```http
GET {bz_url}/api/collections/container_stats/records
```

Agent stats payload format:

```json
{
  "n": "caddy",
  "c": 0.2,
  "m": 50331648,
  "b": [12000, 180000]
}
```

Field mapping:

| UI Field | Key | Description |
|---|---|---|
| `name` | `n` | Container name |
| `cpu_pct` | `c` | CPU percentage |
| `memory_mb` | `m` | Memory in Megabytes (Beszel v0.18.8+ uses `BytesToMegabytes`; adapter supports both MB and legacy byte payloads > 100000) |
| `net_sent` | `b[0]` | Bytes sent |
| `net_recv` | `b[1]` | Bytes received |

Depending on collection and version, a single record may contain an array of container items. Probe real responses before finalizing JSON paths.

## 6. Containers Collection

Do not hardcode advanced metadata without verifying against your installed Beszel version:

1. Open DevTools in your browser on the Beszel web UI or use PocketBase API preview;
2. Observe actual payload responses for `/api/collections/containers/records`;
3. Save a sanitized fixture in `examples/fixtures/`;
4. Map only the necessary fields;
5. Maintain robust fallbacks.

Useful optional fields (if available):
- Container ID;
- Image;
- Health status;
- Running status;
- Port mappings.

## 7. Graceful Fallbacks

| Metric / Scenario | Fallback Behavior |
|---|---|
| Temperature missing | Hide temperature badge |
| Bandwidth missing | Display `—` |
| Load average missing | Display `—` |
| Uptime missing | Display `—` |
| Container health missing | Render generic status dot |
| Disk missing | Display `—` |
| Network error / Stale | Retain last valid cached value |
| Active system missing | Reset to index 0 |

## 8. Unit Normalization

### Memory Formatting

Given bytes `m`:
- `< 1024 KiB`: format in `KiB`
- `< 1024 MiB`: format in `MiB`
- `>= 1024 MiB`: format in `GiB`

### Network Formatting

Given bytes/second:
- Auto format as `KiB/s` or `MiB/s`

### Uptime Formatting

Given seconds:
- `< 1 day`: `12h 08m`
- `>= 1 day`: `12d 04h`

## 9. Fixture Sanitization

### Compiled Overview and manual Info adapters (September 2026)

The current tabs are `overview`, `containers`, and `info`. Chart, range/metric
selectors, SVG paths and their sampled-coordinate globals are not emitted.
`scripts/widget_info.py` centralizes Overview decoding; `widget_fetch.py`
decodes the separate manual Info snapshots. UI labels read adapter globals.

| Display | Cached path | Unit / fallback |
|---|---|---|
| Host | selected `sys_json.items[i].name` | server_name fallback |
| Uptime | selected `info.u` | seconds -> days/hours; N/A if absent |
| Temperature | selected `info.dt` | °C; N/A if absent |
| Load average | selected `info.la[1]`, then [2], then [0]; latest stats fallback per field | rounded to 2 decimals; zero valid; N/A |
| RAM used / total | `latest.items[0].stats.mu / m` | GiB; N/A |
| Disk used / total | `latest.items[0].stats.du / d` | GiB; N/A |
| Buffer/cache | `latest.items[0].stats.mb` | GiB; N/A |
| Swap used / total | `latest.items[0].stats.su / s` | GiB; N/A |
| RX / TX | `latest.items[0].stats.b[1] / b[0]` | B/s -> KiB/s or MiB/s; zero |
| Primary partition | not serialized in the referenced API | not displayed |

Info's `fetch_info` Flow requests, only on Info/refresh button taps:

- `system_details/records/<system-id>`: hostname, os_name, os, arch, kernel,
  cpu, cores and threads. A 404/403 keeps same-host metadata if cached.
- `systems/records/<system-id>`: matching host identity, uptime and temperature;
  legacy info.k/m/os/c/t provide optional metadata fallbacks.
- Latest `system_stats` record for that host: RAM and GPU map `stats.g.*.n`.
  Up to two GPU names are displayed, otherwise `Not reported`.

The caches `info_meta`, `info_sys`, `info_stats`, `info_host` and `info_at`
are not written by scheduled flows. Host/runtime snapshots publish only after
validation. Failed refreshes keep the previous snapshot and show an error.
Switching hosts hides the old snapshot until a matching one is available.
The `fetch_*` adapter selects a single logo from the local Fastfetch catalog;
ASCII is display data, never a network request or shell command.

The reference is [Beszel v0.18.8 system types](https://github.com/henrygd/beszel/blob/v0.18.8/internal/entities/system/system.go).
New optional scalar fields were checked against upstream source, not a live
private Hub. Native compatibility remains for manual import testing.
Legacy `stats.nr/ns` rates are converted from MiB/s; an array-valued `info.bb`
is a final directional fallback. A scalar `info.bb` is never split into RX/TX.

`day_json` holds ascending, un-downsampled 24h `20m` aggregates.
`fetch_history` now only fetches that daily cache (500-record response ceiling);
`latest` independently fetches the newest `1m` record for Overview.
Systems/latest and containers refresh every five minutes; daily stats every
fifteen minutes. Manual refresh requests all four. Date filters compensate
the phone timezone with `df(Z)`. Setup preserves all daily records and fetches
a separate latest sample; failed setup requests do not seed another host.

Daily totals integrate available B/s rates over observed time intervals capped
at 1200 seconds per aggregate and clipped to the current 24h window. The fixed
74-slot accumulator covers the standard 72-record daily window plus boundary
records; it contains no runtime `fl()` loops. Each bucket covers its preceding
1200 seconds, clipped at both edges of the day. Gaps are not extrapolated.
Flow actions calculate the sums procedurally and publish `net_24h_rx/tx` as
plain TEXT numeric values. UI formatting no longer follows a recursive chain
of date, duration, subtotal and grand-total global formulas. Legacy
`stats.nr/ns` is converted from MiB/s when `stats.b` is absent.
There is no `day_n >= 70` gate. Even one usable sample contributes; empty
history displays `0 KiB`. Positive estimates carry `≈`; these are rate
integrals, not exact interface counter deltas, and sparse data undercounts
the full day. Invalid responses retain the last valid cache.

`container_count` counts quoted name keys in the latest Docker record,
supporting both `.stats` (setup) and `.items[0].stats` (PocketBase).
TEXT pagination is clamped using `mu(floor, (count - 1) / 5)`; the page count
is at least one. Header centers and metric badge centers coincide.
Container `m` is MiB (no magnitude heuristic). Dots indicate host/cache
availability (green/yellow/red), not unprovided Docker health.

`generate_preset.py` projects the same native tree as `generate_clip.py`;
it no longer maintains separate UI formulas or aspirational auth flows.
The local evaluator tests the emitted formulas, including failed responses,
missing optional fields, daily integration, Info geometry and Docker pages.
These checks are not a substitute for native Kustom/launcher validation.

All fixtures in this repository are synthetic.

When exporting real fixtures:
- Strip public domain URLs and IP addresses;
- Strip email addresses and passwords;
- Strip JWT tokens and session IDs;
- Substitute real hostnames and container names with generic identifiers;
- Remove internal network topologies.
