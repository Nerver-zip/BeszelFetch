# Reusable Widget Components

## MetricRing

Inputs:
- `value`: Number `0..100`
- `label`: String (`CPU`, `RAM`, `DISK`)
- `icon`: Glyph / symbol
- `accent`: Hex color token

Children:
- Circular progress track;
- Circular progress stroke;
- Center percentage text;
- Bottom metric label;
- Optional icon.

Fallback:
- Missing value -> render `—`, progress set to 0, muted text.

## MiniStat

Inputs:
- `icon`: Glyph / direction indicator
- `text`: Primary stat text
- `secondary`: Optional secondary unit / timestamp.

Examples:
- `↓ 2.1M`
- `LA 0.42`
- `43°C`

## ContainerRow

Inputs:
- `absolute_index`: Number (`0..N`)
- `name`: Container name string
- `cpu`: Formatted CPU utilization
- `memory`: Formatted memory usage
- `status`: Optional health / running state.

Layout:
```text
dot | name ........... | CPU | RAM
```

Name truncation:
- Truncate with ellipsis;
- Fixed right-side padding so metric values never get pushed off-screen.

## FetchLogo / FetchDetails

One left-aligned monospace TextModule reads the selected ASCII from a local
catalog. Do not create one TextModule per distro with visibility formulas:
the supplied native screenshot showed all such modules overlapping.
The source spaces/newlines are preserved, with proportional font sizing.

Eight colon-aligned rows read the manual snapshot adapter in
`scripts/widget_fetch.py`: OS, kernel, CPU, GPU, cores, uptime, memory, temperature.
Labels and palette chips have explicit Catppuccin colors and formula bindings.
Missing GPU names show `Not reported`; other optional metadata uses `N/A`.
Info and its header refresh trigger `fetch_info`; scheduled refreshes do not
write Info snapshots. Failures retain the previous snapshot and display a status.

## BottomNavItem

Inputs:
- `view`: Target tab key (`overview`, `containers`, `info`);
- `icon`: Tab glyph;
- `label`: Tab title.

Active styling:
- High-contrast accent color + indicator pill/underline.

Inactive styling:
- Muted color (`overlay0`).

## StatusBadge

Status states:
- `online` (Green dot + text)
- `stale` (Yellow dot + text + sync time)
- `offline` (Red dot + text + cache time)
- `auth` (Red dot + auth error)
- `forbidden` (Red dot + 403 error)
- `schema` (Peach dot + parse error)

Always pair color indicators with clear textual labels for accessibility.
