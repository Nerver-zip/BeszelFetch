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

## ChartBar

Inputs:
- `value`: Raw metric value;
- `normalized_height`: Scaled height (`0..100%`);
- `is_last`: Boolean flag indicating most recent point.

Bar styling:
- Bottom-aligned inside horizontal series container;
- Subtle corner radius (`2–4 dp`);
- Identical width and proportional gap across all 24 datapoints.

## MetricChip

Inputs:
- `metric`: Metric key (`cpu`, `mem`, `disk`, `net`);
- `label`: Button text (`CPU`, `RAM`, `DISK`, `NET`);
- `accent`: Theme color token;
- `is_active`: Boolean active state.

Touch action:
- Mutates `metric` global;
- Instantly re-renders series from current history cache;
- Dispatches refetch only if required metrics are missing from cache.

## BottomNavItem

Inputs:
- `view`: Target tab key (`overview`, `containers`, `chart`);
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
