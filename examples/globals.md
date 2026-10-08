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

## Color Palette Tokens (Themed Globals)

Color globals compiled into the widget according to the selected theme (see [docs/THEMES.md](../docs/THEMES.md)):
- `c_base`: Main card background (translucent, e.g. `#D91E1E2E`)
- `c_mantle`: Header & sub-container background (translucent, e.g. `#B3181825`)
- `c_surface0`: Progress tracks, button fills, active tab (`#FF313244`)
- `c_surface1`: Card borders, dividers (`#FF45475A`)
- `c_text`: Primary text, hostnames, headings (`#FFCDD6F4`)
- `c_subtext`: Secondary labels, sensors, units (`#FFBAC2DE`)
- `c_muted`: Muted labels, inactive tabs (`#FF6C7086`)
- `c_accent`: General accent, headings, ASCII distro art (`#FFCBA6F7`)
- `c_cpu`: CPU accent (`#FF89B4FA`)
- `c_ram`: RAM accent (`#FFCBA6F7`)
- `c_disk`: Storage accent (`#FF94E2D5`)
- `c_net`: Network accent (`#FF74C7EC`)
- `c_ok`: Online / Normal status (`#FFA6E3A1`)
- `c_warn`: Elevated load / Warning threshold (`#FFF9E2AF`)
- `c_peach`: High load threshold (`#FFFAB387`)
- `c_err`: Offline / Critical threshold (`#FFF38BA8`)
