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
| `memory_bytes` | `m` | Memory in bytes |
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

All fixtures in this repository are synthetic.

When exporting real fixtures:
- Strip public domain URLs and IP addresses;
- Strip email addresses and passwords;
- Strip JWT tokens and session IDs;
- Substitute real hostnames and container names with generic identifiers;
- Remove internal network topologies.
