#!/usr/bin/env python3
"""
Kustom Clip Generator for Beszel Homelab Monitoring Widget.
Generates widget/beszel_monitor.clip with ##KUSTOMCLIP## header, allowing users
to import the complete widget as a single Komponent in KWGT (Free or Pro)
without needing a KWGT Pro key or preset import.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PALETTE_FILE = REPO_ROOT / "examples" / "palette.json"
CLIP_FILE = REPO_ROOT / "widget" / "beszel_monitor.clip"


def build_kustom_clip():
    with open(PALETTE_FILE, "r", encoding="utf-8") as f:
        palette_data = json.load(f)

    tokens = palette_data.get("tokens", {})

    def to_kustom_color(hex_str):
        hex_clean = hex_str.lstrip("#")
        if len(hex_clean) == 6:
            return f"#FF{hex_clean.upper()}"
        elif len(hex_clean) == 8:
            return f"#{hex_clean.upper()}"
        return "#FFFFFFFF"

    # Self-contained globals embedded directly inside the Komponent
    globals_list = {
        # Config & Credentials
        "bz_url": {
            "index": 1,
            "type": "TEXT",
            "title": "Beszel Hub URL",
            "description": "Base URL of Beszel instance (e.g. http://192.168.1.100:8090)",
            "value": "http://192.168.1.100:8090"
        },
        "bz_token": {
            "index": 2,
            "type": "TEXT",
            "title": "PocketBase JWT Token",
            "description": "Optional JWT auth token if Hub requires authentication",
            "value": ""
        },
        "bz_email": {
            "index": 3,
            "type": "TEXT",
            "title": "Beszel User Email",
            "description": "Optional user email for token refresh",
            "value": ""
        },
        "bz_pass": {
            "index": 4,
            "type": "TEXT",
            "title": "Beszel User Password",
            "description": "Optional user password for token refresh",
            "value": ""
        },
        "sys_id": {
            "index": 5,
            "type": "TEXT",
            "title": "System ID",
            "description": "PocketBase record ID of active system",
            "value": ""
        },
        # View & Navigation State
        "view": {
            "index": 6,
            "type": "TEXT",
            "title": "Active View",
            "description": "overview, containers, or chart",
            "value": "overview"
        },
        "metric": {
            "index": 7,
            "type": "TEXT",
            "title": "Chart Metric",
            "description": "cpu, mem, disk, or net",
            "value": "cpu"
        },
        "range": {
            "index": 8,
            "type": "TEXT",
            "title": "Chart Range",
            "description": "Historical range (e.g. 24h)",
            "value": "24h"
        },
        "sys_idx": {
            "index": 9,
            "type": "NUMBER",
            "title": "Active System Index",
            "description": "0-indexed active system",
            "value": 0
        },
        "container_page": {
            "index": 10,
            "type": "NUMBER",
            "title": "Container Page",
            "description": "0-indexed container page",
            "value": 0
        },
        "container_count": {
            "index": 11,
            "type": "NUMBER",
            "title": "Total Containers",
            "value": 0
        },
        # Cache Payloads
        "sys_json": {
            "index": 12,
            "type": "TEXT",
            "title": "Systems Cache",
            "value": "{}"
        },
        "cnt_json": {
            "index": 13,
            "type": "TEXT",
            "title": "Containers Cache",
            "value": "{}"
        },
        "hist_json": {
            "index": 14,
            "type": "TEXT",
            "title": "History Cache",
            "value": "{}"
        },
        "last_ok": {
            "index": 15,
            "type": "TEXT",
            "title": "Last Sync Timestamp",
            "value": ""
        },
        "last_err": {
            "index": 16,
            "type": "TEXT",
            "title": "Last Error Category",
            "value": ""
        },
        "stale": {
            "index": 17,
            "type": "NUMBER",
            "title": "Stale Cache Flag",
            "value": 0
        },
        # Catppuccin Mocha Color Tokens
        "c_base": {"index": 18, "type": "COLOR", "title": "Base Background", "value": to_kustom_color(tokens.get("base", "#1E1E2E"))},
        "c_mantle": {"index": 19, "type": "COLOR", "title": "Mantle Background", "value": to_kustom_color(tokens.get("mantle", "#181825"))},
        "c_surface0": {"index": 20, "type": "COLOR", "title": "Surface0 Track", "value": to_kustom_color(tokens.get("surface0", "#313244"))},
        "c_surface1": {"index": 21, "type": "COLOR", "title": "Surface1 Border", "value": to_kustom_color(tokens.get("surface1", "#45475A"))},
        "c_text": {"index": 22, "type": "COLOR", "title": "Primary Text", "value": to_kustom_color(tokens.get("text", "#CDD6F4"))},
        "c_subtext": {"index": 23, "type": "COLOR", "title": "Secondary Label", "value": to_kustom_color(tokens.get("subtext1", "#BAC2DE"))},
        "c_muted": {"index": 24, "type": "COLOR", "title": "Muted Text", "value": to_kustom_color(tokens.get("overlay0", "#6C7086"))},
        "c_cpu": {"index": 25, "type": "COLOR", "title": "CPU Accent", "value": to_kustom_color(tokens.get("blue", "#89B4FA"))},
        "c_ram": {"index": 26, "type": "COLOR", "title": "RAM Accent", "value": to_kustom_color(tokens.get("mauve", "#CBA6F7"))},
        "c_disk": {"index": 27, "type": "COLOR", "title": "Disk Accent", "value": to_kustom_color(tokens.get("teal", "#94E2D5"))},
        "c_net": {"index": 28, "type": "COLOR", "title": "Network Accent", "value": to_kustom_color(tokens.get("sapphire", "#74C7EC"))},
        "c_ok": {"index": 29, "type": "COLOR", "title": "Online / OK", "value": to_kustom_color(tokens.get("green", "#A6E3A1"))},
        "c_warn": {"index": 30, "type": "COLOR", "title": "Warning / Stale", "value": to_kustom_color(tokens.get("yellow", "#F9E2AF"))},
        "c_peach": {"index": 31, "type": "COLOR", "title": "High Usage Warning", "value": to_kustom_color(tokens.get("peach", "#FAB387"))},
        "c_err": {"index": 32, "type": "COLOR", "title": "Error / Offline", "value": to_kustom_color(tokens.get("red", "#F38BA8"))},
    }

    # Universal data expression: works from gv(sys_json) cache OR direct wg() fallback
    sys_expr = "if(gv(sys_json)!=''&gv(sys_json)!='{}', gv(sys_json), gv(bz_url)+'/api/collections/systems/records?perPage=100&fields=id,name,status,info&sort=name')"
    cnt_expr = "if(gv(cnt_json)!=''&gv(cnt_json)!='{}', gv(cnt_json), gv(bz_url)+'/api/collections/container_stats/records?perPage=1&sort=-created')"
    hist_expr = "if(gv(hist_json)!=''&gv(hist_json)!='{}', gv(hist_json), gv(bz_url)+'/api/collections/system_stats/records?page=1&perPage=500&skipTotal=1&sort=created')"

    # Helper for building a metric progress bar in the Overview tab
    def make_progress_bar(label, field_key, color_global):
        pct_formula = f"mu(round, wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.{field_key}'))"
        return {
            "internal_type": "StackLayerModule",
            "internal_title": f"MetricBar_{label}",
            "config_stacking": "HORIZONTAL_CENTER",
            "config_margin": 8.0,
            "viewgroup_items": [
                {
                    "internal_type": "TextModule",
                    "internal_title": f"Label_{label}",
                    "text_expression": f"{label:<4}",
                    "text_size": 11.0,
                    "paint_color": "#FFCDD6F4",
                    "internal_globals": {"paint_color": color_global}
                },
                {
                    "internal_type": "OverlapLayerModule",
                    "internal_title": f"BarTrack_{label}",
                    "viewgroup_items": [
                        {
                            "internal_type": "ShapeModule",
                            "internal_title": "TrackBg",
                            "shape_type": "RECT",
                            "shape_width": 180.0,
                            "shape_height": 8.0,
                            "shape_corners": 4.0,
                            "paint_color": "#FF313244",
                            "internal_globals": {"paint_color": "c_surface0"}
                        },
                        {
                            "internal_type": "ShapeModule",
                            "internal_title": "TrackFill",
                            "shape_type": "RECT",
                            "shape_width": 180.0,
                            "shape_height": 8.0,
                            "shape_corners": 4.0,
                            "position_anchor": "CENTERLEFT",
                            "paint_color": "#FF89B4FA",
                            "internal_globals": {"paint_color": color_global},
                            "internal_formulas": {
                                "shape_width": f"$1.8 * mu(min, 100, mu(max, 0, {pct_formula})))$"
                            },
                            "internal_toggles": {"shape_width": 10}
                        }
                    ]
                },
                {
                    "internal_type": "TextModule",
                    "internal_title": f"Val_{label}",
                    "text_expression": "0%",
                    "text_size": 11.0,
                    "paint_color": "#FFCDD6F4",
                    "internal_globals": {"paint_color": "c_text"},
                    "internal_formulas": {
                        "text_expression": f"${pct_formula}$%"
                    },
                    "internal_toggles": {"text_expression": 10}
                }
            ]
        }

    # Helper for container row (0..4)
    def make_container_row(idx):
        idx_expr = f"(gv(container_page) * 5 + {idx})"
        return {
            "internal_type": "StackLayerModule",
            "internal_title": f"ContainerRow_{idx}",
            "config_stacking": "HORIZONTAL_CENTER",
            "config_margin": 6.0,
            "internal_formulas": {
                "config_visible": f"if({idx_expr} < gv(container_count), ALWAYS, REMOVE)"
            },
            "internal_toggles": {"config_visible": 0},
            "viewgroup_items": [
                {
                    "internal_type": "ShapeModule",
                    "internal_title": "Dot",
                    "shape_type": "CIRCLE",
                    "shape_width": 8.0,
                    "shape_height": 8.0,
                    "paint_color": "#FFA6E3A1",
                    "internal_globals": {"paint_color": "c_ok"}
                },
                {
                    "internal_type": "TextModule",
                    "internal_title": "Name",
                    "text_expression": f"container-{idx}",
                    "text_size": 11.0,
                    "paint_color": "#FFCDD6F4",
                    "internal_globals": {"paint_color": "c_text"},
                    "internal_formulas": {
                        "text_expression": f"$tc(ell, wg({cnt_expr}, json, '.stats[' + {idx_expr} + '].n'), 18)$"
                    },
                    "internal_toggles": {"text_expression": 10}
                },
                {
                    "internal_type": "TextModule",
                    "internal_title": "CPU",
                    "text_expression": "CPU 0%",
                    "text_size": 10.0,
                    "paint_color": "#FF89B4FA",
                    "internal_globals": {"paint_color": "c_cpu"},
                    "internal_formulas": {
                        "text_expression": f"CPU $wg({cnt_expr}, json, '.stats[' + {idx_expr} + '].c')$%"
                    },
                    "internal_toggles": {"text_expression": 10}
                },
                {
                    "internal_type": "TextModule",
                    "internal_title": "RAM",
                    "text_expression": "0 MB",
                    "text_size": 10.0,
                    "paint_color": "#FFCBA6F7",
                    "internal_globals": {"paint_color": "c_ram"},
                    "internal_formulas": {
                        "text_expression": f"$mu(round, wg({cnt_expr}, json, '.stats[' + {idx_expr} + '].m') / 1048576)$ MB"
                    },
                    "internal_toggles": {"text_expression": 10}
                }
            ]
        }

    # Helper for 24 sparkline bars
    bars = []
    for i in range(24):
        bars.append({
            "internal_type": "ShapeModule",
            "internal_title": f"Bar_{i:02d}",
            "shape_type": "RECT",
            "shape_width": 9.0,
            "shape_height": 30.0,
            "shape_corners": 2.0,
            "position_anchor": "BOTTOM",
            "paint_color": "#FF89B4FA",
            "internal_formulas": {
                "shape_height": f"$mu(max, 3, mu(min, 60, mu(round, wg({hist_expr}, json, '.items[' + {i} + '].stats.' + gv(metric)) * 0.6)))$",
                "paint_color": f"$if({i} = 23, gv(c_text), if(gv(metric) = 'cpu', gv(c_cpu), if(gv(metric) = 'mem', gv(c_ram), if(gv(metric) = 'disk', gv(c_disk), gv(c_net)))))$"
            },
            "internal_toggles": {"shape_height": 10, "paint_color": 10}
        })

    # The Complete Self-Contained Komponent
    komponent = {
        "internal_type": "KomponentModule",
        "internal_title": "Beszel Monitor",
        "internal_description": "Homelab monitoring widget consuming Beszel API directly with Catppuccin Mocha aesthetic.",
        "globals_list": globals_list,
        "viewgroup_items": [
            # Background Card
            {
                "internal_type": "ShapeModule",
                "internal_title": "CardBackground",
                "shape_type": "RECT",
                "shape_width": 320.0,
                "shape_height": 220.0,
                "shape_corners": 24.0,
                "paint_color": "#FF1E1E2E",
                "internal_globals": {"paint_color": "c_base"}
            },
            # Border Stroke
            {
                "internal_type": "ShapeModule",
                "internal_title": "CardBorder",
                "shape_type": "RECT",
                "shape_width": 320.0,
                "shape_height": 220.0,
                "shape_corners": 24.0,
                "paint_style": "STROKE",
                "stroke_width": 1.5,
                "paint_color": "#FF45475A",
                "internal_globals": {"paint_color": "c_surface1"}
            },
            # Main Layout Vertical Flow
            {
                "internal_type": "StackLayerModule",
                "internal_title": "ContentFlow",
                "config_stacking": "VERTICAL",
                "config_margin": 6.0,
                "viewgroup_items": [
                    # Header Bar (Min 48dp touch targets)
                    {
                        "internal_type": "StackLayerModule",
                        "internal_title": "Header",
                        "config_stacking": "HORIZONTAL_CENTER",
                        "config_margin": 8.0,
                        "viewgroup_items": [
                            # Health Status Dot
                            {
                                "internal_type": "ShapeModule",
                                "internal_title": "StatusIndicator",
                                "shape_type": "CIRCLE",
                                "shape_width": 10.0,
                                "shape_height": 10.0,
                                "paint_color": "#FFA6E3A1",
                                "internal_formulas": {
                                    "paint_color": f"$if(gv(stale) = 1, gv(c_warn), if(wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].status') = 'up', gv(c_ok), gv(c_err)))$"
                                },
                                "internal_toggles": {"paint_color": 10}
                            },
                            # Hostname / Selector (Tapping switches system)
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "HostSelector",
                                "position_anchor": "CENTERLEFT",
                                "internal_events": [
                                    {
                                        "type": "SINGLE_TAP",
                                        "action": "TOGGLE_GLOBAL",
                                        "global_switch": "sys_idx",
                                        "global_formula": f"$if(gv(sys_idx) + 1 >= wg({sys_expr}, json, '.items.length'), 0, gv(sys_idx) + 1)$"
                                    }
                                ],
                                "viewgroup_items": [
                                    {
                                        "internal_type": "ShapeModule",
                                        "internal_title": "HostTouchArea",
                                        "shape_type": "RECT",
                                        "shape_width": 160.0,
                                        "shape_height": 48.0,
                                        "paint_color": "#00000000"
                                    },
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "HostnameText",
                                        "text_expression": "beszel-host",
                                        "text_size": 13.0,
                                        "paint_color": "#FFCDD6F4",
                                        "internal_globals": {"paint_color": "c_text"},
                                        "internal_formulas": {
                                            "text_expression": f"$tc(ell, wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].name'), 16)$"
                                        },
                                        "internal_toggles": {"text_expression": 10}
                                    }
                                ]
                            },
                            # Refresh Button (Min 48dp touch target)
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "RefreshTouchTarget",
                                "position_anchor": "CENTERRIGHT",
                                "internal_events": [
                                    {
                                        "type": "SINGLE_TAP",
                                        "action": "KUSTOM_ACTION",
                                        "kustom_action": "FORCE_UPDATE"
                                    }
                                ],
                                "viewgroup_items": [
                                    {
                                        "internal_type": "ShapeModule",
                                        "internal_title": "RefreshArea",
                                        "shape_type": "RECT",
                                        "shape_width": 48.0,
                                        "shape_height": 48.0,
                                        "paint_color": "#00000000"
                                    },
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "RefreshGlyph",
                                        "text_expression": "↻",
                                        "text_size": 16.0,
                                        "paint_color": "#FFBAC2DE",
                                        "internal_globals": {"paint_color": "c_subtext"}
                                    }
                                ]
                            }
                        ]
                    },
                    # Sub-Header Meta Row
                    {
                        "internal_type": "StackLayerModule",
                        "internal_title": "HeaderMeta",
                        "config_stacking": "HORIZONTAL_CENTER",
                        "config_margin": 14.0,
                        "viewgroup_items": [
                            {
                                "internal_type": "TextModule",
                                "internal_title": "SystemCount",
                                "text_expression": "1 system · 12:00",
                                "text_size": 9.0,
                                "paint_color": "#FF6C7086",
                                "internal_globals": {"paint_color": "c_muted"},
                                "internal_formulas": {
                                    "text_expression": f"$wg({sys_expr}, json, '.items.length')$ systems · $df(hh:mm)$"
                                },
                                "internal_toggles": {"text_expression": 10}
                            },
                            {
                                "internal_type": "TextModule",
                                "internal_title": "SyncBadge",
                                "text_expression": "● online",
                                "text_size": 9.0,
                                "paint_color": "#FFA6E3A1",
                                "internal_formulas": {
                                    "text_expression": "$if(gv(stale) = 1, '● stale', '● online')$",
                                    "paint_color": "$if(gv(stale) = 1, gv(c_warn), gv(c_ok))$"
                                },
                                "internal_toggles": {"text_expression": 10, "paint_color": 10}
                            }
                        ]
                    },
                    # Main Dynamic View Area
                    {
                        "internal_type": "OverlapLayerModule",
                        "internal_title": "ViewArea",
                        "viewgroup_items": [
                            # VIEW 1: Overview
                            {
                                "internal_type": "StackLayerModule",
                                "internal_title": "ViewOverview",
                                "config_stacking": "VERTICAL",
                                "config_margin": 6.0,
                                "internal_formulas": {
                                    "config_visible": "if(gv(view) = 'overview', ALWAYS, REMOVE)"
                                },
                                "internal_toggles": {"config_visible": 0},
                                "viewgroup_items": [
                                    make_progress_bar("CPU", "cpu", "c_cpu"),
                                    make_progress_bar("RAM", "mp", "c_ram"),
                                    make_progress_bar("DISK", "dp", "c_disk"),
                                    # Secondary Metrics Row: Net I/O, Load, Temp
                                    {
                                        "internal_type": "StackLayerModule",
                                        "internal_title": "MetricsRow",
                                        "config_stacking": "HORIZONTAL_CENTER",
                                        "config_margin": 10.0,
                                        "viewgroup_items": [
                                            {
                                                "internal_type": "TextModule",
                                                "internal_title": "NetIO",
                                                "text_expression": "NET ▲ 0KB/s ▼ 0KB/s",
                                                "text_size": 9.0,
                                                "paint_color": "#FF74C7EC",
                                                "internal_globals": {"paint_color": "c_net"},
                                                "internal_formulas": {
                                                    "text_expression": (
                                                        f"NET ▲$if(wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.bb[0]') < 1048576, "
                                                        f"mu(round, wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.bb[0]') / 1024) + 'K/s', "
                                                        f"mu(round, wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.bb[0]') / 1048576, 1) + 'M/s')$ "
                                                        f"▼$if(wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.bb[1]') < 1048576, "
                                                        f"mu(round, wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.bb[1]') / 1024) + 'K/s', "
                                                        f"mu(round, wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.bb[1]') / 1048576, 1) + 'M/s')$"
                                                    )
                                                },
                                                "internal_toggles": {"text_expression": 10}
                                            },
                                            {
                                                "internal_type": "TextModule",
                                                "internal_title": "LoadAvg",
                                                "text_expression": "LOAD 0.00",
                                                "text_size": 9.0,
                                                "paint_color": "#FFBAC2DE",
                                                "internal_globals": {"paint_color": "c_subtext"},
                                                "internal_formulas": {
                                                    "text_expression": f"LOAD $if(wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.la[0]') != '', wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.la[0]'), '—')$"
                                                },
                                                "internal_toggles": {"text_expression": 10}
                                            },
                                            {
                                                "internal_type": "TextModule",
                                                "internal_title": "Temp",
                                                "text_expression": "—°C",
                                                "text_size": 9.0,
                                                "paint_color": "#FFBAC2DE",
                                                "internal_globals": {"paint_color": "c_subtext"},
                                                "internal_formulas": {
                                                    "text_expression": f"$if(wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.dt') != '', mu(round, wg({sys_expr}, json, '.items[' + gv(sys_idx) + '].info.dt'), 1) + '°C', '—')$"
                                                },
                                                "internal_toggles": {"text_expression": 10}
                                            }
                                        ]
                                    }
                                ]
                            },
                            # VIEW 2: Containers
                            {
                                "internal_type": "StackLayerModule",
                                "internal_title": "ViewContainers",
                                "config_stacking": "VERTICAL",
                                "config_margin": 4.0,
                                "internal_formulas": {
                                    "config_visible": "if(gv(view) = 'containers', ALWAYS, REMOVE)"
                                },
                                "internal_toggles": {"config_visible": 0},
                                "viewgroup_items": [
                                    make_container_row(0),
                                    make_container_row(1),
                                    make_container_row(2),
                                    make_container_row(3),
                                    make_container_row(4),
                                    # Pagination Row
                                    {
                                        "internal_type": "StackLayerModule",
                                        "internal_title": "PaginationRow",
                                        "config_stacking": "HORIZONTAL_CENTER",
                                        "config_margin": 16.0,
                                        "viewgroup_items": [
                                            {
                                                "internal_type": "OverlapLayerModule",
                                                "internal_title": "BtnPrev",
                                                "internal_events": [
                                                    {
                                                        "type": "SINGLE_TAP",
                                                        "action": "TOGGLE_GLOBAL",
                                                        "global_switch": "container_page",
                                                        "global_formula": "$mu(max, 0, gv(container_page) - 1)$"
                                                    }
                                                ],
                                                "viewgroup_items": [
                                                    {"internal_type": "ShapeModule", "shape_type": "RECT", "shape_width": 48.0, "shape_height": 48.0, "paint_color": "#00000000"},
                                                    {"internal_type": "TextModule", "text_expression": "◀ Prev", "text_size": 10.0, "paint_color": "#FFBAC2DE", "internal_globals": {"paint_color": "c_subtext"}}
                                                ]
                                            },
                                            {
                                                "internal_type": "TextModule",
                                                "internal_title": "PageText",
                                                "text_expression": "Page 1",
                                                "text_size": 10.0,
                                                "paint_color": "#FF6C7086",
                                                "internal_globals": {"paint_color": "c_muted"},
                                                "internal_formulas": {
                                                    "text_expression": "$gv(container_page) + 1$"
                                                },
                                                "internal_toggles": {"text_expression": 10}
                                            },
                                            {
                                                "internal_type": "OverlapLayerModule",
                                                "internal_title": "BtnNext",
                                                "internal_events": [
                                                    {
                                                        "type": "SINGLE_TAP",
                                                        "action": "TOGGLE_GLOBAL",
                                                        "global_switch": "container_page",
                                                        "global_formula": "$gv(container_page) + 1$"
                                                    }
                                                ],
                                                "viewgroup_items": [
                                                    {"internal_type": "ShapeModule", "shape_type": "RECT", "shape_width": 48.0, "shape_height": 48.0, "paint_color": "#00000000"},
                                                    {"internal_type": "TextModule", "text_expression": "Next ▶", "text_size": 10.0, "paint_color": "#FFBAC2DE", "internal_globals": {"paint_color": "c_subtext"}}
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            },
                            # VIEW 3: Chart
                            {
                                "internal_type": "StackLayerModule",
                                "internal_title": "ViewChart",
                                "config_stacking": "VERTICAL",
                                "config_margin": 6.0,
                                "internal_formulas": {
                                    "config_visible": "if(gv(view) = 'chart', ALWAYS, REMOVE)"
                                },
                                "internal_toggles": {"config_visible": 0},
                                "viewgroup_items": [
                                    # 24 Sparkline Bars
                                    {
                                        "internal_type": "StackLayerModule",
                                        "internal_title": "SparklineBars",
                                        "config_stacking": "HORIZONTAL_CENTER",
                                        "config_margin": 3.0,
                                        "viewgroup_items": bars
                                    },
                                    # Metric Selector Chips
                                    {
                                        "internal_type": "StackLayerModule",
                                        "internal_title": "MetricChips",
                                        "config_stacking": "HORIZONTAL_CENTER",
                                        "config_margin": 10.0,
                                        "viewgroup_items": [
                                            {
                                                "internal_type": "OverlapLayerModule",
                                                "internal_title": "ChipCPU",
                                                "internal_events": [{"type": "SINGLE_TAP", "action": "TOGGLE_GLOBAL", "global_switch": "metric", "global_formula": "cpu"}],
                                                "viewgroup_items": [
                                                    {"internal_type": "ShapeModule", "shape_type": "RECT", "shape_width": 48.0, "shape_height": 48.0, "paint_color": "#00000000"},
                                                    {"internal_type": "TextModule", "text_expression": "[CPU]", "text_size": 10.0, "paint_color": "#FF89B4FA", "internal_formulas": {"paint_color": "$if(gv(metric)='cpu', gv(c_cpu), gv(c_muted))$"}, "internal_toggles": {"paint_color": 10}}
                                                ]
                                            },
                                            {
                                                "internal_type": "OverlapLayerModule",
                                                "internal_title": "ChipRAM",
                                                "internal_events": [{"type": "SINGLE_TAP", "action": "TOGGLE_GLOBAL", "global_switch": "metric", "global_formula": "mem"}],
                                                "viewgroup_items": [
                                                    {"internal_type": "ShapeModule", "shape_type": "RECT", "shape_width": 48.0, "shape_height": 48.0, "paint_color": "#00000000"},
                                                    {"internal_type": "TextModule", "text_expression": "[RAM]", "text_size": 10.0, "paint_color": "#FFCBA6F7", "internal_formulas": {"paint_color": "$if(gv(metric)='mem', gv(c_ram), gv(c_muted))$"}, "internal_toggles": {"paint_color": 10}}
                                                ]
                                            },
                                            {
                                                "internal_type": "OverlapLayerModule",
                                                "internal_title": "ChipDISK",
                                                "internal_events": [{"type": "SINGLE_TAP", "action": "TOGGLE_GLOBAL", "global_switch": "metric", "global_formula": "disk"}],
                                                "viewgroup_items": [
                                                    {"internal_type": "ShapeModule", "shape_type": "RECT", "shape_width": 48.0, "shape_height": 48.0, "paint_color": "#00000000"},
                                                    {"internal_type": "TextModule", "text_expression": "[DISK]", "text_size": 10.0, "paint_color": "#FF94E2D5", "internal_formulas": {"paint_color": "$if(gv(metric)='disk', gv(c_disk), gv(c_muted))$"}, "internal_toggles": {"paint_color": 10}}
                                                ]
                                            },
                                            {
                                                "internal_type": "OverlapLayerModule",
                                                "internal_title": "ChipNET",
                                                "internal_events": [{"type": "SINGLE_TAP", "action": "TOGGLE_GLOBAL", "global_switch": "metric", "global_formula": "net"}],
                                                "viewgroup_items": [
                                                    {"internal_type": "ShapeModule", "shape_type": "RECT", "shape_width": 48.0, "shape_height": 48.0, "paint_color": "#00000000"},
                                                    {"internal_type": "TextModule", "text_expression": "[NET]", "text_size": 10.0, "paint_color": "#FF74C7EC", "internal_formulas": {"paint_color": "$if(gv(metric)='net', gv(c_net), gv(c_muted))$"}, "internal_toggles": {"paint_color": 10}}
                                                ]
                                            }
                                        ]
                                    },
                                    # Summary Stats Row
                                    {
                                        "internal_type": "StackLayerModule",
                                        "internal_title": "ChartStats",
                                        "config_stacking": "HORIZONTAL_CENTER",
                                        "config_margin": 14.0,
                                        "viewgroup_items": [
                                            {
                                                "internal_type": "TextModule",
                                                "internal_title": "Range",
                                                "text_expression": "24h",
                                                "text_size": 9.0,
                                                "paint_color": "#FFBAC2DE",
                                                "internal_globals": {"paint_color": "c_subtext"},
                                                "internal_formulas": {"text_expression": "$gv(range)$"},
                                                "internal_toggles": {"text_expression": 10}
                                            },
                                            {
                                                "internal_type": "TextModule",
                                                "internal_title": "Stats",
                                                "text_expression": "avg 20% · max 42%",
                                                "text_size": 9.0,
                                                "paint_color": "#FF6C7086",
                                                "internal_globals": {"paint_color": "c_muted"}
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    # Bottom Navigation Bar (48dp height touch targets)
                    {
                        "internal_type": "StackLayerModule",
                        "internal_title": "BottomNav",
                        "config_stacking": "HORIZONTAL_CENTER",
                        "config_margin": 8.0,
                        "viewgroup_items": [
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "TabOverview",
                                "internal_events": [
                                    {
                                        "type": "SINGLE_TAP",
                                        "action": "TOGGLE_GLOBAL",
                                        "global_switch": "view",
                                        "global_formula": "overview"
                                    }
                                ],
                                "viewgroup_items": [
                                    {"internal_type": "ShapeModule", "shape_type": "RECT", "shape_width": 90.0, "shape_height": 48.0, "paint_color": "#00000000"},
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "TextOverview",
                                        "text_expression": "[ overview ]",
                                        "text_size": 11.0,
                                        "paint_color": "#FFCDD6F4",
                                        "internal_formulas": {"paint_color": "$if(gv(view) = 'overview', gv(c_text), gv(c_muted))$"},
                                        "internal_toggles": {"paint_color": 10}
                                    }
                                ]
                            },
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "TabContainers",
                                "internal_events": [
                                    {
                                        "type": "SINGLE_TAP",
                                        "action": "TOGGLE_GLOBAL",
                                        "global_switch": "view",
                                        "global_formula": "containers"
                                    }
                                ],
                                "viewgroup_items": [
                                    {"internal_type": "ShapeModule", "shape_type": "RECT", "shape_width": 90.0, "shape_height": 48.0, "paint_color": "#00000000"},
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "TextContainers",
                                        "text_expression": "[ containers ]",
                                        "text_size": 11.0,
                                        "paint_color": "#FF6C7086",
                                        "internal_formulas": {"paint_color": "$if(gv(view) = 'containers', gv(c_text), gv(c_muted))$"},
                                        "internal_toggles": {"paint_color": 10}
                                    }
                                ]
                            },
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "TabChart",
                                "internal_events": [
                                    {
                                        "type": "SINGLE_TAP",
                                        "action": "TOGGLE_GLOBAL",
                                        "global_switch": "view",
                                        "global_formula": "chart"
                                    }
                                ],
                                "viewgroup_items": [
                                    {"internal_type": "ShapeModule", "shape_type": "RECT", "shape_width": 90.0, "shape_height": 48.0, "paint_color": "#00000000"},
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "TextChart",
                                        "text_expression": "[ chart ]",
                                        "text_size": 11.0,
                                        "paint_color": "#FF6C7086",
                                        "internal_formulas": {"paint_color": "$if(gv(view) = 'chart', gv(c_text), gv(c_muted))$"},
                                        "internal_toggles": {"paint_color": 10}
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

    # Top-level Clip structure expected by KWGT
    clip_data = {
        "clip_version": 1,
        "clip_cut": [],
        "clip_modules": [komponent]
    }

    clip_json = json.dumps(clip_data, indent=2, ensure_ascii=False)
    clip_content = f"##KUSTOMCLIP##\n{clip_json}\n"

    with open(CLIP_FILE, "w", encoding="utf-8") as f:
        f.write(clip_content)

    print(f"✓ Kustom Clip successfully generated at: {CLIP_FILE}")


if __name__ == "__main__":
    build_kustom_clip()
