# Current KWGT tree

```text
Root / Beszel Monitor
├── CardBackground + CardBorder
└── ContentFlow (Overlap, height follows frame)
    ├── Header
    │   ├── StatusIndicator + HostSelector
    │   ├── TimeText (Overview only)
    │   ├── BtnPrev + BtnNext (Docker only)
    │   └── RefreshTouchTarget / InfoRefreshTouchTarget (manual Info only)
    ├── ViewArea
    │   ├── ViewOverview
    │   │   ├── CPU: ring %, temperature, load average
    │   │   ├── Memory: ring %, used / total GiB
    │   │   ├── Disk: ring %, used / total GiB
    │   │   └── Network: Download, Upload, RX 24h, TX 24h
    │   ├── ViewContainers
    │   │   ├── NAME / CPU / RAM headings
    │   │   ├── Five rows: availability dot, Docker glyph, name, badges
    │   │   └── PageText + empty state
    │   └── ViewInfo
    │       ├── FetchLogo (one monospace TextModule, selected ASCII content)
    │       └── FetchDetails
    │           ├── Host@beszel, OS, Kernel, CPU, GPU, Cores
    │           └── Uptime, Memory, Temp, palette, manual-cache status
    └── BottomNav: Overview | Docker | 󰋼 Info
```

Views are mutually exclusive via `gv(view)`: `overview`, `containers`,
`info`. The root height is `max(376, si(rheight))`; header and navigation
retain accessible touch targets while body spacing expands.
There are no metric chips, range controls, SVG paths or history bars.
The remaining daily history cache exists only to integrate network volume.
