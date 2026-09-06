---
name: beszel-pocketbase
description: Validates authentication, endpoints, query filters, schemas, and permissions for Beszel/PocketBase.
---

# Beszel / PocketBase

## Objective

Treat Beszel as a versioned API rather than an immutable static schema.

## Authentication

Endpoint:
```text
POST /api/collections/users/auth-with-password
```

Payload:
```json
{"identity":"USER","password":"PASS"}
```

Extract:
```text
.token
```

Pass in query headers:
```text
Authorization: TOKEN
```

Do not add `Bearer ` prefix when PocketBase expects raw token.

## Core Collections

- `systems`
- `system_stats`
- `container_stats`
- `containers` (must verify schema before utilizing rich metadata)

## Operational Rules

- Query only systems assigned to the dedicated user;
- Always recommend read-only accounts;
- Never attempt write operations from the widget;
- Use `fields` parameter to minimize network payloads;
- Use `sort` to guarantee ordering;
- Perform filtering server-side via `filter` query parameter.

## Schema Change Procedure

Before introducing a new JSON path:
1. Observe actual network payload from live instance;
2. Save a sanitized fixture in `examples/fixtures/`;
3. Document target Beszel version;
4. Update `DATA_CONTRACT.md`;
5. Ensure a graceful UI fallback exists.

## History Range Mapping

- 1h -> `1m`
- 12h -> `10m`
- 24h -> `20m`
- 7d -> `120m`
- 30d -> `480m`

## Known Overview Keys

Inside `systems.info`:
- `u`: Uptime in seconds
- `cpu`: CPU %
- `mp`: Memory %
- `dp`: Disk %
- `bb`: Bandwidth `[sent, recv]`
- `la`: Load average `[1m, 5m, 15m]`
- `dt`: Dashboard temperature

Treat sensor fields as optional.

## Known Container Stats Keys

Inside `container_stats.stats`:
- `n`: Container name
- `c`: CPU %
- `m`: Memory bytes
- `b`: Bandwidth `[sent, recv]`

Do not infer health, image, or ports from this metric object.

## Diagnostics

Log:
- Logical endpoint name;
- HTTP response code;
- Items count;
- Sanitized system ID;
- Target Beszel version.

Never log:
- Passwords;
- Raw auth tokens;
- Session cookies.
