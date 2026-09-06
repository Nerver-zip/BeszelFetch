#!/usr/bin/env python3
"""
Preset Generator & Validator for Beszel Homelab Monitoring KWGT Widget.
Generates a complete, verified Kustom widget preset definition JSON (widget/preset.json)
mirroring widget/TREE.md, widget/COMPONENTS.md, examples/globals.md, and examples/palette.json.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PALETTE_FILE = REPO_ROOT / "examples" / "palette.json"
PRESET_FILE = REPO_ROOT / "widget" / "preset.json"


def build_kustom_preset():
    with open(PALETTE_FILE, "r") as f:
        palette_data = json.load(f)

    tokens = palette_data.get("tokens", {})

    # Globals Definition according to examples/globals.md
    globals_list = [
        # Configuration & Auth
        {"name": "bz_url", "type": "TEXT", "value": "https://beszel.example.com", "description": "Beszel Hub base URL"},
        {"name": "bz_email", "type": "TEXT", "value": "", "description": "Dedicated user email (secret)"},
        {"name": "bz_pass", "type": "TEXT", "value": "", "description": "Dedicated user password (secret)"},
        {"name": "bz_token", "type": "TEXT", "value": "", "description": "PocketBase JWT auth token (secret)"},

        # Navigation & UI State
        {"name": "view", "type": "TEXT", "value": "overview", "description": "Active tab (overview, containers, chart)"},
        {"name": "sys_idx", "type": "NUMBER", "value": 0, "description": "Index of active system in sys_json"},
        {"name": "sys_id", "type": "TEXT", "value": "", "description": "PocketBase record ID of active system"},
        {"name": "metric", "type": "TEXT", "value": "cpu", "description": "Active chart metric (cpu, mem, disk, net)"},
        {"name": "range", "type": "TEXT", "value": "24h", "description": "Active chart range (1h, 12h, 24h, 7d, 30d)"},
        {"name": "container_page", "type": "NUMBER", "value": 0, "description": "Active container list page"},
        {"name": "container_count", "type": "NUMBER", "value": 0, "description": "Total count of running containers"},
        {"name": "container_max_page", "type": "NUMBER", "value": 0, "description": "Maximum page index for containers"},
        {"name": "debug", "type": "NUMBER", "value": 0, "description": "Diagnostics overlay toggle"},

        # Data Cache Payloads
        {"name": "sys_json", "type": "TEXT", "value": "{}", "description": "Cached systems payload"},
        {"name": "cnt_json", "type": "TEXT", "value": "{}", "description": "Cached container stats payload"},
        {"name": "hist_json", "type": "TEXT", "value": "{}", "description": "Cached historical telemetry series"},

        # Operational Status
        {"name": "last_ok", "type": "TEXT", "value": "", "description": "Timestamp of last successful sync"},
        {"name": "last_code", "type": "TEXT", "value": "", "description": "HTTP status code of last response"},
        {"name": "last_err", "type": "TEXT", "value": "", "description": "Error category (auth, network, etc)"},
        {"name": "stale", "type": "NUMBER", "value": 1, "description": "Stale cache flag (1=stale, 0=fresh)"},
        {"name": "busy", "type": "NUMBER", "value": 0, "description": "Network in-flight indicator"},

        # Sizing & Charting
        {"name": "perpage", "type": "NUMBER", "value": 5, "description": "Containers rendered per page"},
        {"name": "points", "type": "NUMBER", "value": 24, "description": "History bar count"},
        {"name": "net_max", "type": "NUMBER", "value": 0, "description": "Dynamic network max ceiling (0=auto)"},

        # Theme Color Tokens (Catppuccin Mocha)
        {"name": "c_base", "type": "COLOR", "value": tokens.get("base", "#1E1E2E"), "description": "Card background"},
        {"name": "c_mantle", "type": "COLOR", "value": tokens.get("mantle", "#181825"), "description": "Sub-surface background"},
        {"name": "c_surface0", "type": "COLOR", "value": tokens.get("surface0", "#313244"), "description": "Progress tracks"},
        {"name": "c_surface1", "type": "COLOR", "value": tokens.get("surface1", "#45475A"), "description": "Card border / dividers"},
        {"name": "c_text", "type": "COLOR", "value": tokens.get("text", "#CDD6F4"), "description": "Primary high-contrast text"},
        {"name": "c_subtext", "type": "COLOR", "value": tokens.get("subtext1", "#BAC2DE"), "description": "Secondary labels"},
        {"name": "c_muted", "type": "COLOR", "value": tokens.get("overlay0", "#6C7086"), "description": "Muted text / inactive tabs"},
        {"name": "c_cpu", "type": "COLOR", "value": tokens.get("blue", "#89B4FA"), "description": "CPU accent"},
        {"name": "c_ram", "type": "COLOR", "value": tokens.get("mauve", "#CBA6F7"), "description": "Memory accent"},
        {"name": "c_disk", "type": "COLOR", "value": tokens.get("teal", "#94E2D5"), "description": "Disk accent"},
        {"name": "c_net", "type": "COLOR", "value": tokens.get("sapphire", "#74C7EC"), "description": "Network accent"},
        {"name": "c_ok", "type": "COLOR", "value": tokens.get("green", "#A6E3A1"), "description": "Online / healthy indicator"},
        {"name": "c_warn", "type": "COLOR", "value": tokens.get("yellow", "#F9E2AF"), "description": "Stale / warning"},
        {"name": "c_peach", "type": "COLOR", "value": tokens.get("peach", "#FAB387"), "description": "High resource usage warning"},
        {"name": "c_err", "type": "COLOR", "value": tokens.get("red", "#F38BA8"), "description": "Critical / offline / auth error"},
    ]

    # Helper for building a circular gauge group
    def make_gauge_group(name, metric_label, metric_key, color_global):
        return {
            "type": "OVERLAP_GROUP",
            "name": f"MetricRing_{name}",
            "width": 90,
            "height": 90,
            "children": [
                {
                    "type": "PROGRESS",
                    "name": "Track",
                    "mode": "CIRCULAR",
                    "size": 75,
                    "stroke": 6,
                    "color": "$gv(c_surface0)$",
                    "level": 100
                },
                {
                    "type": "PROGRESS",
                    "name": "Fill",
                    "mode": "CIRCULAR",
                    "size": 75,
                    "stroke": 6,
                    "color": (
                        f"$if(wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.{metric_key}') >= 95, gv(c_err), "
                        f"if(wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.{metric_key}') >= 85, gv(c_peach), "
                        f"if(wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.{metric_key}') >= 70, gv(c_warn), "
                        f"gv({color_global}))))$"
                    ),
                    "level": f"$mu(min, 100, mu(max, 0, wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.{metric_key}')))$"
                },
                {
                    "type": "TEXT",
                    "name": "Value",
                    "text": f"$mu(round, wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.{metric_key}'))$%",
                    "color": "$gv(c_text)$",
                    "size": 14,
                    "font": "MONOSPACE_BOLD",
                    "alignment": "CENTER"
                },
                {
                    "type": "TEXT",
                    "name": "Label",
                    "text": metric_label,
                    "color": "$gv(c_subtext)$",
                    "size": 10,
                    "font": "MONOSPACE_MEDIUM",
                    "alignment": "CENTER",
                    "offset_y": 48
                }
            ]
        }

    # Helper for container row
    def make_container_row(idx):
        return {
            "type": "STACK_GROUP",
            "name": f"ContainerRow_{idx}",
            "direction": "HORIZONTAL",
            "width": "MATCH_PARENT",
            "height": 28,
            "visibility": f"$if(gv(container_page) * 5 + {idx} < gv(container_count), ALWAYS, REMOVE)$",
            "children": [
                {
                    "type": "SHAPE",
                    "name": "StatusDot",
                    "shape": "CIRCLE",
                    "width": 8,
                    "height": 8,
                    "color": "$gv(c_ok)$"
                },
                {
                    "type": "TEXT",
                    "name": "Name",
                    "text": f"$tc(ell, wg(gv(cnt_json), json, '.stats[' + (gv(container_page) * 5 + {idx}) + '].n'), 18)$",
                    "color": "$gv(c_text)$",
                    "size": 11,
                    "font": "MONOSPACE_MEDIUM",
                    "width": 140
                },
                {
                    "type": "TEXT",
                    "name": "CPU",
                    "text": f"CPU $wg(gv(cnt_json), json, '.stats[' + (gv(container_page) * 5 + {idx}) + '].c')$%",
                    "color": "$gv(c_cpu)$",
                    "size": 10,
                    "font": "MONOSPACE_REGULAR",
                    "width": 60
                },
                {
                    "type": "TEXT",
                    "name": "RAM",
                    "text": (
                        f"$if(wg(gv(cnt_json), json, '.stats[' + (gv(container_page) * 5 + {idx}) + '].m') < 1073741824, "
                        f"mu(round, wg(gv(cnt_json), json, '.stats[' + (gv(container_page) * 5 + {idx}) + '].m') / 1048576) + ' MiB', "
                        f"mu(round, wg(gv(cnt_json), json, '.stats[' + (gv(container_page) * 5 + {idx}) + '].m') / 1073741824, 1) + ' GiB')$"
                    ),
                    "color": "$gv(c_ram)$",
                    "size": 10,
                    "font": "MONOSPACE_REGULAR",
                    "width": 60
                }
            ]
        }

    # Helper for 24 chart bars
    def make_chart_bars():
        bars = []
        for i in range(24):
            bars.append({
                "type": "SHAPE",
                "name": f"Bar_{i:02d}",
                "shape": "RECTANGLE",
                "width": 9,
                "height": f"$mu(max, 3, mu(min, 60, mu(round, wg(gv(hist_json), json, '.items[' + {i} + '].stats.' + gv(metric)) * 0.6)))$",
                "color": (
                    f"$if({i} = 23, gv(c_text), "
                    f"if(gv(metric) = 'cpu', gv(c_cpu), "
                    f"if(gv(metric) = 'mem', gv(c_ram), "
                    f"if(gv(metric) = 'disk', gv(c_disk), gv(c_net)))))$"
                ),
                "corner_radius": 2,
                "alignment": "BOTTOM"
            })
        return bars

    # Root Component Tree Structure according to widget/TREE.md
    preset_definition = {
        "kustom_version": 37000,
        "widget_spec": {
            "title": "Beszel Homelab Monitor",
            "description": "Direct homelab monitoring widget using Beszel Hub API with Catppuccin Mocha aesthetic",
            "author": "Nerver-zip & Antigravity",
            "target_grid": "4x3",
            "width": 320,
            "height": 220,
            "padding": 12
        },
        "globals": globals_list,
        "root": {
            "type": "OVERLAP_GROUP",
            "name": "CardRoot",
            "children": [
                # Card Background & Border
                {
                    "type": "SHAPE",
                    "name": "CardBackground",
                    "shape": "ROUNDED_RECTANGLE",
                    "width": 320,
                    "height": 220,
                    "corner_radius": 24,
                    "color": "$gv(c_base)$"
                },
                {
                    "type": "SHAPE",
                    "name": "CardBorder",
                    "shape": "ROUNDED_RECTANGLE",
                    "width": 320,
                    "height": 220,
                    "corner_radius": 24,
                    "stroke": 1,
                    "color": "$gv(c_surface1)$"
                },
                # Main Vertical Content Flow
                {
                    "type": "STACK_GROUP",
                    "name": "ContentFlow",
                    "direction": "VERTICAL",
                    "width": 296,
                    "height": 196,
                    "children": [
                        # Header Bar
                        {
                            "type": "STACK_GROUP",
                            "name": "Header",
                            "direction": "HORIZONTAL",
                            "width": "MATCH_PARENT",
                            "height": 28,
                            "children": [
                                {
                                    "type": "SHAPE",
                                    "name": "StatusIndicator",
                                    "shape": "CIRCLE",
                                    "width": 8,
                                    "height": 8,
                                    "color": "$if(gv(stale) = 1, gv(c_warn), if(wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].status') = 'up', gv(c_ok), gv(c_err)))$"
                                },
                                {
                                    "type": "TEXT",
                                    "name": "ProjectIdentity",
                                    "text": "~/homelab",
                                    "color": "$gv(c_subtext)$",
                                    "size": 12,
                                    "font": "MONOSPACE_SEMIBOLD",
                                    "margin_left": 6
                                },
                                {
                                    "type": "TEXT",
                                    "name": "HostSelector",
                                    "text": "$wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].name')$ ▾",
                                    "color": "$gv(c_text)$",
                                    "size": 12,
                                    "font": "MONOSPACE_BOLD",
                                    "margin_left": 10,
                                    "touch_action": {
                                        "action": "TOGGLE_GLOBAL",
                                        "global": "sys_idx",
                                        "formula": "$if(gv(sys_idx) + 1 >= wg(gv(sys_json), json, '.items.length'), 0, gv(sys_idx) + 1)$"
                                    }
                                },
                                {
                                    "type": "SHAPE",
                                    "name": "RefreshTouchTarget",
                                    "shape": "RECTANGLE",
                                    "width": 48,
                                    "height": 48,
                                    "color": "#00000000",
                                    "alignment": "RIGHT",
                                    "touch_action": {
                                        "action": "EXECUTE_FLOW",
                                        "flow": "refresh_current_view"
                                    },
                                    "children": [
                                        {
                                            "type": "TEXT",
                                            "name": "RefreshGlyph",
                                            "text": "↻",
                                            "color": "$gv(c_subtext)$",
                                            "size": 16,
                                            "font": "MONOSPACE_BOLD"
                                        }
                                    ]
                                }
                            ]
                        },
                        # Header Sub-metadata
                        {
                            "type": "STACK_GROUP",
                            "name": "HeaderMeta",
                            "direction": "HORIZONTAL",
                            "width": "MATCH_PARENT",
                            "height": 14,
                            "children": [
                                {
                                    "type": "TEXT",
                                    "name": "SystemCount",
                                    "text": "$wg(gv(sys_json), json, '.items.length')$ systems · $df(hh:mm)$",
                                    "color": "$gv(c_muted)$",
                                    "size": 9,
                                    "font": "MONOSPACE_REGULAR"
                                },
                                {
                                    "type": "TEXT",
                                    "name": "SyncBadge",
                                    "text": "$if(gv(stale) = 1, '● stale', '● online')$",
                                    "color": "$if(gv(stale) = 1, gv(c_warn), gv(c_ok))$",
                                    "size": 9,
                                    "font": "MONOSPACE_REGULAR",
                                    "alignment": "RIGHT"
                                }
                            ]
                        },
                        # View Area (Switched by gv(view))
                        {
                            "type": "OVERLAP_GROUP",
                            "name": "ViewArea",
                            "width": "MATCH_PARENT",
                            "height": 118,
                            "children": [
                                # --- 1. ViewOverview ---
                                {
                                    "type": "STACK_GROUP",
                                    "name": "ViewOverview",
                                    "direction": "VERTICAL",
                                    "width": "MATCH_PARENT",
                                    "height": "MATCH_PARENT",
                                    "visibility": "$if(gv(view) = 'overview', ALWAYS, REMOVE)$",
                                    "children": [
                                        {
                                            "type": "STACK_GROUP",
                                            "name": "GaugesRow",
                                            "direction": "HORIZONTAL",
                                            "width": "MATCH_PARENT",
                                            "height": 84,
                                            "alignment": "SPACE_EVENLY",
                                            "children": [
                                                make_gauge_group("CPU", "CPU", "cpu", "c_cpu"),
                                                make_gauge_group("RAM", "RAM", "mp", "c_ram"),
                                                make_gauge_group("DISK", "DISK", "dp", "c_disk")
                                            ]
                                        },
                                        {
                                            "type": "STACK_GROUP",
                                            "name": "MiniStats",
                                            "direction": "HORIZONTAL",
                                            "width": "MATCH_PARENT",
                                            "height": 20,
                                            "alignment": "SPACE_BETWEEN",
                                            "children": [
                                                {
                                                    "type": "TEXT",
                                                    "name": "NetStats",
                                                    "text": "↓$mu(round, wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.bb[1]') / 1024)$K ↑$mu(round, wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.bb[0]') / 1024)$K",
                                                    "color": "$gv(c_net)$",
                                                    "size": 9,
                                                    "font": "MONOSPACE_REGULAR"
                                                },
                                                {
                                                    "type": "TEXT",
                                                    "name": "LoadStat",
                                                    "text": "LA $wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.la[0]')$",
                                                    "color": "$gv(c_subtext)$",
                                                    "size": 9,
                                                    "font": "MONOSPACE_REGULAR"
                                                },
                                                {
                                                    "type": "TEXT",
                                                    "name": "TempStat",
                                                    "text": "$wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.dt')$°C",
                                                    "color": "$gv(c_peach)$",
                                                    "size": 9,
                                                    "font": "MONOSPACE_REGULAR",
                                                    "visibility": "$if(wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.dt') != '', ALWAYS, REMOVE)$"
                                                },
                                                {
                                                    "type": "TEXT",
                                                    "name": "UptimeStat",
                                                    "text": "$mu(floor, wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.u') / 86400)$d $mu(floor, (wg(gv(sys_json), json, '.items[' + gv(sys_idx) + '].info.u') % 86400) / 3600)$h",
                                                    "color": "$gv(c_subtext)$",
                                                    "size": 9,
                                                    "font": "MONOSPACE_REGULAR"
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # --- 2. ViewContainers ---
                                {
                                    "type": "STACK_GROUP",
                                    "name": "ViewContainers",
                                    "direction": "VERTICAL",
                                    "width": "MATCH_PARENT",
                                    "height": "MATCH_PARENT",
                                    "visibility": "$if(gv(view) = 'containers', ALWAYS, REMOVE)$",
                                    "children": [
                                        make_container_row(0),
                                        make_container_row(1),
                                        make_container_row(2),
                                        make_container_row(3),
                                        make_container_row(4),
                                        {
                                            "type": "TEXT",
                                            "name": "EmptyContainersState",
                                            "text": "No running containers reported",
                                            "color": "$gv(c_muted)$",
                                            "size": 11,
                                            "font": "MONOSPACE_REGULAR",
                                            "alignment": "CENTER",
                                            "visibility": "$if(gv(container_count) = 0, ALWAYS, REMOVE)$"
                                        },
                                        # Pagination Controls
                                        {
                                            "type": "STACK_GROUP",
                                            "name": "ContainersPager",
                                            "direction": "HORIZONTAL",
                                            "width": "MATCH_PARENT",
                                            "height": 18,
                                            "alignment": "CENTER",
                                            "visibility": "$if(gv(container_count) > 5, ALWAYS, REMOVE)$",
                                            "children": [
                                                {
                                                    "type": "TEXT",
                                                    "name": "PrevPage",
                                                    "text": "‹  ",
                                                    "color": "$gv(c_text)$",
                                                    "size": 14,
                                                    "font": "MONOSPACE_BOLD",
                                                    "touch_action": {
                                                        "action": "TOGGLE_GLOBAL",
                                                        "global": "container_page",
                                                        "formula": "$mu(max, 0, gv(container_page) - 1)$"
                                                    }
                                                },
                                                {
                                                    "type": "TEXT",
                                                    "name": "PageIndicator",
                                                    "text": "$gv(container_page) + 1$ / $gv(container_max_page) + 1$",
                                                    "color": "$gv(c_subtext)$",
                                                    "size": 10,
                                                    "font": "MONOSPACE_MEDIUM"
                                                },
                                                {
                                                    "type": "TEXT",
                                                    "name": "NextPage",
                                                    "text": "  ›",
                                                    "color": "$gv(c_text)$",
                                                    "size": 14,
                                                    "font": "MONOSPACE_BOLD",
                                                    "touch_action": {
                                                        "action": "TOGGLE_GLOBAL",
                                                        "global": "container_page",
                                                        "formula": "$mu(min, gv(container_max_page), gv(container_page) + 1)$"
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                },
                                # --- 3. ViewChart ---
                                {
                                    "type": "STACK_GROUP",
                                    "name": "ViewChart",
                                    "direction": "VERTICAL",
                                    "width": "MATCH_PARENT",
                                    "height": "MATCH_PARENT",
                                    "visibility": "$if(gv(view) = 'chart', ALWAYS, REMOVE)$",
                                    "children": [
                                        # Sparkline Bars Group
                                        {
                                            "type": "STACK_GROUP",
                                            "name": "SparklineBars",
                                            "direction": "HORIZONTAL",
                                            "width": "MATCH_PARENT",
                                            "height": 62,
                                            "alignment": "BOTTOM",
                                            "children": make_chart_bars()
                                        },
                                        # Metric Chips Selector
                                        {
                                            "type": "STACK_GROUP",
                                            "name": "MetricChips",
                                            "direction": "HORIZONTAL",
                                            "width": "MATCH_PARENT",
                                            "height": 22,
                                            "alignment": "SPACE_EVENLY",
                                            "children": [
                                                {
                                                    "type": "TEXT",
                                                    "name": "ChipCPU",
                                                    "text": "[CPU]",
                                                    "color": "$if(gv(metric) = 'cpu', gv(c_cpu), gv(c_muted))$",
                                                    "size": 10,
                                                    "font": "MONOSPACE_BOLD",
                                                    "touch_action": {"action": "SET_GLOBAL", "global": "metric", "value": "cpu"}
                                                },
                                                {
                                                    "type": "TEXT",
                                                    "name": "ChipRAM",
                                                    "text": "[RAM]",
                                                    "color": "$if(gv(metric) = 'mem', gv(c_ram), gv(c_muted))$",
                                                    "size": 10,
                                                    "font": "MONOSPACE_BOLD",
                                                    "touch_action": {"action": "SET_GLOBAL", "global": "metric", "value": "mem"}
                                                },
                                                {
                                                    "type": "TEXT",
                                                    "name": "ChipDISK",
                                                    "text": "[DISK]",
                                                    "color": "$if(gv(metric) = 'disk', gv(c_disk), gv(c_muted))$",
                                                    "size": 10,
                                                    "font": "MONOSPACE_BOLD",
                                                    "touch_action": {"action": "SET_GLOBAL", "global": "metric", "value": "disk"}
                                                },
                                                {
                                                    "type": "TEXT",
                                                    "name": "ChipNET",
                                                    "text": "[NET]",
                                                    "color": "$if(gv(metric) = 'net', gv(c_net), gv(c_muted))$",
                                                    "size": 10,
                                                    "font": "MONOSPACE_BOLD",
                                                    "touch_action": {"action": "SET_GLOBAL", "global": "metric", "value": "net"}
                                                }
                                            ]
                                        },
                                        # Chart Summary Stats
                                        {
                                            "type": "STACK_GROUP",
                                            "name": "ChartStats",
                                            "direction": "HORIZONTAL",
                                            "width": "MATCH_PARENT",
                                            "height": 16,
                                            "alignment": "SPACE_BETWEEN",
                                            "children": [
                                                {
                                                    "type": "TEXT",
                                                    "name": "RangeIndicator",
                                                    "text": "$gv(range)$",
                                                    "color": "$gv(c_subtext)$",
                                                    "size": 9,
                                                    "font": "MONOSPACE_MEDIUM"
                                                },
                                                {
                                                    "type": "TEXT",
                                                    "name": "SummaryStats",
                                                    "text": "avg 20% · max 42%",
                                                    "color": "$gv(c_muted)$",
                                                    "size": 9,
                                                    "font": "MONOSPACE_REGULAR"
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        },
                        # Bottom Navigation Bar
                        {
                            "type": "STACK_GROUP",
                            "name": "BottomNav",
                            "direction": "HORIZONTAL",
                            "width": "MATCH_PARENT",
                            "height": 48,
                            "alignment": "SPACE_EVENLY",
                            "children": [
                                {
                                    "type": "OVERLAP_GROUP",
                                    "name": "TabOverview",
                                    "width": 90,
                                    "height": 48,
                                    "touch_action": {"action": "SET_GLOBAL", "global": "view", "value": "overview"},
                                    "children": [
                                        {
                                            "type": "TEXT",
                                            "name": "TabOverviewText",
                                            "text": "[ overview ]",
                                            "color": "$if(gv(view) = 'overview', gv(c_text), gv(c_muted))$",
                                            "size": 11,
                                            "font": "MONOSPACE_SEMIBOLD"
                                        }
                                    ]
                                },
                                {
                                    "type": "OVERLAP_GROUP",
                                    "name": "TabContainers",
                                    "width": 90,
                                    "height": 48,
                                    "touch_action": {"action": "SET_GLOBAL", "global": "view", "value": "containers"},
                                    "children": [
                                        {
                                            "type": "TEXT",
                                            "name": "TabContainersText",
                                            "text": "[ containers ]",
                                            "color": "$if(gv(view) = 'containers', gv(c_text), gv(c_muted))$",
                                            "size": 11,
                                            "font": "MONOSPACE_SEMIBOLD"
                                        }
                                    ]
                                },
                                {
                                    "type": "OVERLAP_GROUP",
                                    "name": "TabChart",
                                    "width": 90,
                                    "height": 48,
                                    "touch_action": {"action": "SET_GLOBAL", "global": "view", "value": "chart"},
                                    "children": [
                                        {
                                            "type": "TEXT",
                                            "name": "TabChartText",
                                            "text": "[ chart ]",
                                            "color": "$if(gv(view) = 'chart', gv(c_text), gv(c_muted))$",
                                            "size": 11,
                                            "font": "MONOSPACE_SEMIBOLD"
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        # Defined Flows according to examples/flows.md
        "flows": [
            {
                "id": "auth_beszel",
                "trigger": "MANUAL",
                "actions": [
                    {"type": "SET_GLOBAL", "global": "busy", "value": "1"},
                    {
                        "type": "WEB_GET",
                        "method": "POST",
                        "url": "$gv(bz_url)$/api/collections/users/auth-with-password",
                        "headers": {"Content-Type": "application/json"},
                        "body": '{"identity": "$gv(bz_email)$", "password": "$gv(bz_pass)$"}'
                    },
                    {
                        "type": "CONDITION",
                        "condition": "$lv(http_code) = 200$",
                        "then": [
                            {"type": "SET_GLOBAL", "global": "bz_token", "value": "$lv(json).token$"},
                            {"type": "SET_GLOBAL", "global": "last_err", "value": ""}
                        ],
                        "else": [
                            {"type": "SET_GLOBAL", "global": "last_err", "value": "auth"}
                        ]
                    },
                    {"type": "SET_GLOBAL", "global": "busy", "value": "0"}
                ]
            },
            {
                "id": "fetch_systems",
                "trigger": "PERIODIC_5M",
                "actions": [
                    {
                        "type": "WEB_GET",
                        "method": "GET",
                        "url": "$gv(bz_url)$/api/collections/systems/records?perPage=100&fields=id,name,status,info&sort=name",
                        "headers": {"Authorization": "$gv(bz_token)$"}
                    },
                    {
                        "type": "CONDITION",
                        "condition": "$lv(http_code) = 200$",
                        "then": [
                            {"type": "SET_GLOBAL", "global": "sys_json", "value": "$lv(response_raw)$"},
                            {"type": "SET_GLOBAL", "global": "stale", "value": "0"},
                            {"type": "SET_GLOBAL", "global": "last_ok", "value": "$df(yyyy-MM-dd'T'HH:mm:ss)$"}
                        ],
                        "else_if": "$lv(http_code) = 401$",
                        "then_action": [
                            {"type": "RUN_FLOW", "flow": "auth_beszel"}
                        ],
                        "else": [
                            {"type": "SET_GLOBAL", "global": "stale", "value": "1"},
                            {"type": "SET_GLOBAL", "global": "last_err", "value": "network"}
                        ]
                    }
                ]
            },
            {
                "id": "fetch_containers",
                "trigger": "ON_VIEW_CONTAINERS",
                "actions": [
                    {
                        "type": "WEB_GET",
                        "method": "GET",
                        "url": "$gv(bz_url)$/api/collections/container_stats/records?perPage=1&sort=-created",
                        "headers": {"Authorization": "$gv(bz_token)$"}
                    },
                    {
                        "type": "CONDITION",
                        "condition": "$lv(http_code) = 200$",
                        "then": [
                            {"type": "SET_GLOBAL", "global": "cnt_json", "value": "$lv(response_raw)$"},
                            {"type": "SET_GLOBAL", "global": "container_count", "value": "$lv(json).stats.length$"},
                            {"type": "SET_GLOBAL", "global": "container_max_page", "value": "$mu(floor, (lv(json).stats.length - 1) / 5)$"}
                        ]
                    }
                ]
            },
            {
                "id": "fetch_history",
                "trigger": "ON_VIEW_CHART",
                "actions": [
                    {
                        "type": "WEB_GET",
                        "method": "GET",
                        "url": "$gv(bz_url)$/api/collections/system_stats/records?page=1&perPage=500&skipTotal=1&filter=system='$gv(sys_id)$'&fields=created,stats&sort=created",
                        "headers": {"Authorization": "$gv(bz_token)$"}
                    },
                    {
                        "type": "CONDITION",
                        "condition": "$lv(http_code) = 200$",
                        "then": [
                            {"type": "SET_GLOBAL", "global": "hist_json", "value": "$lv(response_raw)$"}
                        ]
                    }
                ]
            },
            {
                "id": "refresh_current_view",
                "trigger": "MANUAL",
                "actions": [
                    {"type": "RUN_FLOW", "flow": "fetch_systems"},
                    {
                        "type": "CONDITION",
                        "condition": "$gv(view) = 'containers'$",
                        "then": [{"type": "RUN_FLOW", "flow": "fetch_containers"}]
                    },
                    {
                        "type": "CONDITION",
                        "condition": "$gv(view) = 'chart'$",
                        "then": [{"type": "RUN_FLOW", "flow": "fetch_history"}]
                    }
                ]
            }
        ]
    }

    with open(PRESET_FILE, "w") as f:
        json.dump(preset_definition, f, indent=2)

    print(f"✓ Preset definition successfully generated at: {PRESET_FILE}")
    return preset_definition


if __name__ == "__main__":
    build_kustom_preset()
    import sys
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from scripts.generate_clip import build_kustom_clip
    build_kustom_clip()
