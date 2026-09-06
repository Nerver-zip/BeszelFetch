# KWGT Preset Hierarchy Tree

```text
ROOT
└── Card (Overlap Group)
    ├── Background
    │   ├── Base shape (Rectangle, #1E1E2E, rounded corners)
    │   └── Border shape (Stroke, #45475A)
    │
    ├── Content (Vertical Stack)
    │   ├── Header
    │   │   ├── Left
    │   │   │   ├── StatusDot
    │   │   │   └── Title "~/homelab"
    │   │   ├── Spacer
    │   │   ├── HostName
    │   │   └── RefreshButton
    │   │
    │   ├── HeaderMeta
    │   │   ├── SystemCount
    │   │   ├── Spacer
    │   │   └── CacheTime
    │   │
    │   ├── ViewArea (Overlap Group)
    │   │   ├── ViewOverview
    │   │   │   ├── Gauges (Horizontal Stack)
    │   │   │   │   ├── MetricRingCPU
    │   │   │   │   ├── MetricRingRAM
    │   │   │   │   └── MetricRingDisk
    │   │   │   └── MiniStats
    │   │   │       ├── NetDown
    │   │   │       ├── NetUp
    │   │   │       ├── Load
    │   │   │       ├── Temp
    │   │   │       └── Uptime/Status
    │   │   │
    │   │   ├── ViewContainers
    │   │   │   ├── SectionHeader
    │   │   │   ├── ContainerRow0
    │   │   │   ├── ContainerRow1
    │   │   │   ├── ContainerRow2
    │   │   │   ├── ContainerRow3
    │   │   │   ├── ContainerRow4
    │   │   │   ├── EmptyState
    │   │   │   └── Pager
    │   │   │
    │   │   └── ViewChart
    │   │       ├── ChartHeader
    │   │       ├── Plot (Overlap Group)
    │   │       │   ├── Gridlines
    │   │       │   └── Bars (Horizontal Stack)
    │   │       │       ├── Bar00
    │   │       │       ├── ...
    │   │       │       └── Bar23
    │   │       ├── MetricChips
    │   │       └── StatsMinAvgMax
    │   │
    │   ├── StatusBadge
    │   └── BottomNav
    │       ├── NavOverview
    │       ├── NavContainers
    │       └── NavChart
    │
    └── DebugOverlay (Visibility: $if(gv(debug) = 1, ALWAYS, REMOVE)$)
```

## Visibility Matrix

| Component Group | Visibility Condition Formula |
|---|---|
| ViewOverview | `$if(gv(view) = overview, ALWAYS, REMOVE)$` |
| ViewContainers | `$if(gv(view) = containers, ALWAYS, REMOVE)$` |
| ViewChart | `$if(gv(view) = chart, ALWAYS, REMOVE)$` |
| Containers EmptyState | `$if(gv(container_count) = 0, ALWAYS, REMOVE)$` |
| Containers Pager | `$if(gv(container_count) > 5, ALWAYS, REMOVE)$` |
| Stale Status Badge | `$if(gv(stale) = 1, ALWAYS, REMOVE)$` |
| DebugOverlay | `$if(gv(debug) = 1, ALWAYS, REMOVE)$` |

## Component Replication Guidelines

Because KWGT functions via declarative layer trees rather than dynamic component templates:
- Adhere to consistent, structured naming conventions;
- Bind exclusively to centralized global variables;
- Modify only index offsets and metric keys when replicating rows and bars;
- Document any layer-specific overrides.
