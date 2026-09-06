# Flows — Blueprint

Action names in the Kustom UI may vary slightly across versions. The essential requirement is preserving the execution logic.

## `auth_beszel`

```text
MANUAL
  -> set busy = 1
  -> WebGet POST:
       URL = bz_url + /api/collections/users/auth-with-password
       Headers:
         Content-Type: application/json
       Body:
         {"identity": bz_email, "password": bz_pass}
  -> if HTTP 2xx and response.token exists:
       bz_token = response.token
       last_code = HTTP code
       last_err = ""
     else:
       last_code = HTTP code
       last_err = "auth"
  -> set busy = 0
```

## `fetch_systems`

```text
MANUAL / PERIODIC
  -> GET /api/collections/systems/records
       ?perPage=100
       &fields=id,name,status,info
       &sort=name
       Header Authorization: bz_token

  -> on 2xx + .items exists:
       sys_json = response
       last_ok = now
       stale = 0
       last_err = ""

  -> on 401:
       run auth_beszel
       retry request ONCE

  -> otherwise:
       stale = 1
       last_err = "network|http|schema"
       RETAIN existing sys_json
```

## `fetch_containers`

Strategy 1 — Historical metrics:
```text
GET /api/collections/container_stats/records
filter by system and recent time
fields=created,stats
sort=-created
```

Extract the most recent record and map container `stats`.

Strategy 2 — Metadata:
```text
GET /api/collections/containers/records
```

Only use after verifying actual collection schema.

## `fetch_history`

Inputs:
- `sys_id`
- `range`
- `metric`

Mapping:

```text
1h  -> type=1m,   start=now-1h
12h -> type=10m,  start=now-12h
24h -> type=20m,  start=now-24h
7d  -> type=120m, start=now-7d
30d -> type=480m, start=now-30d
```

Request:

```text
GET /api/collections/system_stats/records
?page=1
&perPage=500
&skipTotal=1
&filter=system='SYS_ID' && created > 'START' && type='TYPE'
&fields=created,stats
&sort=created
```

On success:
- Optionally downsample to 24 datapoints;
- `hist_json = normalized`;
- Record history-specific sync timestamp.

## `refresh_current_view`

```text
if view == overview:
  fetch_systems

if view == containers:
  fetch_systems
  fetch_containers

if view == chart:
  fetch_systems
  fetch_history
```

## Periodic Trigger

Default schedule:
```text
Every 5 minutes -> fetch_systems
```

Avoid querying full history on every background cycle unless chart tab is active.
