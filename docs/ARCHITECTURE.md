# Architecture

## 1. Overview

The project employs a direct integration pattern:

```text
KWGT
 ├─ Secret Globals
 ├─ Flow: auth_beszel
 ├─ Flow: fetch_systems
 ├─ Flow: fetch_containers
 ├─ Flow: fetch_history
 ├─ Flow: refresh_current_view
 ├─ JSON Cache
 └─ UI
      ├─ Overview
      ├─ Containers
      └─ Info (manual Fastfetch-style snapshot)

          │ HTTPS REST
          ▼

Beszel Hub
 └─ PocketBase REST API
```

Beszel Hub is built on top of PocketBase; authentication and data querying utilize standard PocketBase REST endpoints.

## 2. Architectural Layers

### 2.1 Configuration

Responsibility: Keep environment variables, endpoints, and credentials separated from UI components.

Global variables:
- `bz_url`: Base Hub URL
- `bz_email`: User email
- `bz_pass`: User password
- `bz_token`: JWT token
- `sys_id`: Active PocketBase system record ID
- `sys_idx`: Active visual index in system list
- `view`: Current tab (`overview` | `containers` | `info`)
- `container_page`: Active container pagination page (`0..N`)

Sensitive credentials should use Secret Globals whenever supported by the Kustom version.

### 2.2 Transport & Authentication

A dedicated Flow handles authentication:

```http
POST {bz_url}/api/collections/users/auth-with-password
Content-Type: application/json

{
  "identity": "<email>",
  "password": "<password>"
}
```

Extract `.token` from the JSON response and store in `bz_token`.

Subsequent requests pass the token directly:

```http
Authorization: <token>
```

Note: PocketBase accepts the token directly without a `Bearer ` prefix.

### 2.3 Acquisition

Acquisition flows are segregated by domain:
- `fetch_systems`
- `fetch_containers`
- `fetch_history`

Benefits of separation:
- Independent refresh intervals;
- Reduced payload size;
- Simplified debugging;
- Localized schema updates;
- Info uses separate button-triggered snapshots; no chart rendering.

### 2.4 Cache Strategy

Never bind individual visual elements directly to remote WebGet calls.

Follow the pattern:

```text
WebGet -> Validate HTTP -> Validate JSON -> Save Cache -> Update last_ok
                                         └-> UI reads Cache
```

Cache Globals:
- `systems_json` (or `sys_json`)
- `containers_json` (or `cnt_json`)
- `day_json`: 24h network aggregates
- `latest`: newest scalar system stats

On failure:
- Never overwrite or wipe the last valid JSON;
- Update `last_code` / `last_error`;
- Flag `is_stale=1`.

### 2.5 Adapter / Normalization

Beszel API fields may shift between minor versions. The UI should only know a normalized data contract.

Desired visual contract:

```text
overview.cpu_pct
overview.mem_pct
overview.disk_pct
overview.status
overview.uptime
overview.temp
overview.load1
overview.net_sent
overview.net_recv

container[i].name
container[i].cpu_pct
container[i].mem
container[i].net_sent
container[i].net_recv
container[i].health?     # optional

history[i].time
history[i].value
```

In KWGT, the adapter is implemented via:
- Centralized JSON paths in global formulas;
- Auxiliary parser formulas;
- Or Flow steps storing normalized values into globals.

### 2.6 UI State

```text
view = overview | containers | info
sys_id = PocketBase system record id
sys_idx = Visual position in systems list
container_page = 0..N
```

Button touches mutate this state and, when appropriate, trigger the corresponding acquisition flow.

## 3. Auth & Retry Flow

```text
refresh
  │
  ▼
request
  │
  ├── 2xx + valid JSON ──▶ cache ──▶ last_ok ──▶ render
  │
  ├── 401 ──▶ auth_beszel ──▶ retry ONCE
  │                         ├── success ──▶ cache
  │                         └── failure ──▶ stale/error
  │
  └── timeout / 5xx / offline ────────────▶ stale/error
```

Infinite retry loops must be strictly avoided.

## 4. Logical Endpoints

### Systems / Overview

```text
GET /api/collections/systems/records
```

Key fields:
- `id`
- `name`
- `status`
- `info`

Inside `info`, current Beszel versions use compact keys:
- `cpu`: CPU %
- `mp`: Memory %
- `dp`: Disk %
- `bb`: Bandwidth `[sent, recv]`
- `la`: Load averages `[1m, 5m, 15m]`
- `dt`: Dashboard temperature
- `u`: Uptime in seconds

### System History

```text
GET /api/collections/system_stats/records
```

Query filters:
- `system='<sys_id>'`
- `created > '<timestamp>'`
- `type='<resolution>'`

Selected fields:
- `created`
- `stats`

### Containers

For container metrics:

```text
GET /api/collections/container_stats/records
```

The current `stats` object includes compact fields:
- `n`: Container name
- `c`: CPU %
- `m`: Memory bytes
- `b`: Bandwidth `[sent, recv]`

For extended metadata (health, image, ports), inspect the `containers` collection in your specific Beszel deployment before assuming schema paths.

## 5. History Resolutions

Beszel provides tiered aggregation types suitable for widget sparklines:

| `type` | Recommended Widget Range |
|---|---|
| `1m` | 1h |
| `10m` | 12h |
| `20m` | 24h |
| `120m` | 7d |
| `480m` | 30d |

The current widget only uses `20m` for daily traffic integration and `1m` for latest scalar stats. The other resolutions are API reference, not active UI controls. No chart points or SVG paths are rendered.

## 6. Refresh Policy

KWGT is designed for battery-efficient widget rendering, not sub-second telemetry.

Recommended schedule:
- Overview: 5 minutes;
- Containers: 5 minutes or upon opening the tab;
- Daily network history: Every 15 minutes;
- Overview latest scalars: Every 5 minutes with systems;
- Info metadata/runtime/host snapshots: buttons only, no cron or initial trigger;
- Manual refresh: Available at all times via header icon.

## 7. Network Connectivity

The mobile device must reach `bz_url`.

Compatible architectures:
- Local LAN;
- VPN;
- Tailscale / WireGuard;
- Existing HTTPS reverse proxy.

Do not spin up additional proxies or custom backends solely for the widget.

## 8. Failure Handling Matrix

| Scenario | Behavior |
|---|---|
| Offline / Network Loss | Retain cache + display `offline` indicator |
| HTTP 401 Unauthorized | Re-authenticate once and retry request |
| HTTP 403 Forbidden | Display `forbidden` badge; do not retry automatically |
| HTTP 404 / Schema Error | Display `schema` badge; log path for debugging |
| HTTP 5xx Server Error | Retain cache + mark stale |
| Empty / Malformed JSON | Do not overwrite existing cache |
| Expired / Invalid Token | Trigger `auth_beszel` flow |
| Active System Removed | Fallback to first available system |
| Daily History Empty | Display formatted zero totals |
| Container Count > 5 | Paginate with page indicator |

## 9. Security

The primary consideration with direct client architecture is credential storage on the device.

Mitigations:
- Dedicated, non-root user in Beszel;
- Read-only permission scope;
- Restrict access strictly to monitored systems;
- HTTPS transport required;
- Use Secret Globals in KWGT;
- Exclude secrets when sharing or exporting presets;
- Never output tokens into debug text strings.

See [SECURITY.md](file:///home/nerver/Desktop/dev/server-monitor/SECURITY.md).
