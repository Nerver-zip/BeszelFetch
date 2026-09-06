# Global Variables Reference

> Names are concise for comfortable editing within Kustom while remaining self-descriptive.

## Configuration & Credentials

| Global | Type | Default | Secret? | Description |
|---|---|---|---|---|
| `bz_url` | Text | `https://beszel.example.com` | Optional | Beszel Hub base URL |
| `bz_email` | Text | *(empty)* | Yes | Dedicated user email |
| `bz_pass` | Text | *(empty)* | Yes | Dedicated user password |
| `bz_token` | Text | *(empty)* | Yes | PocketBase JWT auth token |

## Navigation & UI State

| Global | Type | Default | Description |
|---|---|---|---|
| `view` | Text | `overview` | Active tab (`overview`, `containers`, `chart`) |
| `sys_idx` | Number | `0` | Visual index of active system |
| `sys_id` | Text | *(empty)* | Active PocketBase system record ID |
| `metric` | Text | `cpu` | Active chart metric (`cpu`, `mem`, `disk`, `net`) |
| `range` | Text | `24h` | Active time range (`1h`, `12h`, `24h`, `7d`, `30d`) |
| `container_page` | Number | `0` | Active container pagination page index |
| `debug` | Number | `0` | Debug overlay toggle (`0` = off, `1` = on) |

## Cache Storage

| Global | Type | Default | Description |
|---|---|---|---|
| `sys_json` | Text | `{}` | Cached systems record payload |
| `cnt_json` | Text | `{}` | Cached container stats payload |
| `hist_json` | Text | `{}` | Cached historical metric series |

Note: If text global size limits become restrictive on older Kustom versions, store payloads in local files via Flow and reference file paths in globals.

## Operational & Network State

| Global | Type | Default | Description |
|---|---|---|---|
| `last_ok` | Text | *(empty)* | Timestamp of last successful API response |
| `last_code` | Text | *(empty)* | HTTP status code of last response |
| `last_err` | Text | *(empty)* | Error classification (`auth`, `network`, etc.) |
| `stale` | Number | `1` | Stale cache indicator (`1` = stale, `0` = fresh) |
| `busy` | Number | `0` | Request in-flight flag (`1` = active, `0` = idle) |

## Layout & Sizing

| Global | Type | Default | Description |
|---|---|---|---|
| `perpage` | Number | `5` | Maximum containers rendered per page |
| `points` | Number | `24` | Datapoints in historical chart |
| `net_max` | Number | `0` | Dynamic network ceiling (`0` = auto-scale) |

## Color Palette Tokens (Optional Globals)

Recommended color globals for theme flexibility:
- `c_base`: `#1E1E2E` (Card background)
- `c_text`: `#CDD6F4` (Primary text)
- `c_muted`: `#6C7086` (Muted labels)
- `c_cpu`: `#89B4FA` (CPU accent)
- `c_ram`: `#CBA6F7` (RAM accent)
- `c_disk`: `#94E2D5` (Disk accent)
- `c_net`: `#74C7EC` (Network accent)
- `c_ok`: `#A6E3A1` (Online / OK)
- `c_warn`: `#F9E2AF` (Warning / Stale)
- `c_err`: `#F38BA8` (Error / Offline)
