#!/usr/bin/env python3
"""
Kustom Clip & Preset Generator for Beszel Homelab Monitoring Widget.
Generates:
- widget/beszel_monitor.kwgt (standalone Kustom widget archive with embedded Nerd Font)
- widget/beszel_monitor.clip (Komponent clip)
- widget/beszel_monitor_loose.clip (Loose modules clip)
- dist/ mirrors for deployment.

Features:
- Celestia Shell / Linux Ricing 2x2 grid layout
- Catppuccin Mocha aesthetic
- Verified circular gauge rings (style_style=CIRCLE, style_width=360.0)
- Embedded JetBrainsMono Nerd Font (Docker, CPU, RAM, Network, Disk glyphs)
- Bulletproof arithmetic formulas (pure literal JSON paths matching ghinfo)
- 100% English strings
- Dynamic server name support (setup.py configurable)
- Native Kustom Flow data ingestion (CRON + ONCE + TRIGGER_FLOW)
"""

import copy
import json
import shutil
import zipfile
from pathlib import Path

if __package__:
    from .widget_layout import fix_layout
    from .widget_info import build_info
    from .widget_transport import build_flows
    from .theme_catalog import resolve_theme, DEFAULT_THEME_ID, ResolvedTheme
    from .widget_theme import apply_theme
else:
    from widget_layout import fix_layout
    from widget_info import build_info
    from widget_transport import build_flows
    from theme_catalog import resolve_theme, DEFAULT_THEME_ID, ResolvedTheme
    from widget_theme import apply_theme

REPO_ROOT = Path(__file__).resolve().parent.parent
PALETTE_FILE = REPO_ROOT / "examples" / "palette.json"
CLIP_FILE = REPO_ROOT / "widget" / "beszel_monitor.clip"
KWGT_FILE = REPO_ROOT / "widget" / "beszel_monitor.kwgt"
FONT_SRC = REPO_ROOT / "widget" / "fonts" / "JetBrainsMonoNerdFont.ttf"


def build_kustom_clip(
    hub_url=None,
    token=None,
    email=None,
    password=None,
    server_name=None,
    systems_data=None,
    containers_data=None,
    history_data=None,
    latest_data=None,
    wallpaper_path=None,
    write_outputs=True,
    theme=None,
    output_dir=None,
):
    if theme is None:
        theme = DEFAULT_THEME_ID
    resolved_theme = resolve_theme(theme)
    k_colors = resolved_theme.kustom_colors

    # Pre-load realistic fixtures from examples/fixtures as initial cache
    fixtures_dir = REPO_ROOT / "examples" / "fixtures"
    default_systems = "{}"
    default_containers = "{}"
    default_history = "{}"
    if (fixtures_dir / "systems-response.json").exists():
        with open(fixtures_dir / "systems-response.json", "r", encoding="utf-8") as f:
            default_systems = json.dumps(json.load(f))
    if (fixtures_dir / "container-stats-response.json").exists():
        with open(fixtures_dir / "container-stats-response.json", "r", encoding="utf-8") as f:
            default_containers = json.dumps(json.load(f))
    if (fixtures_dir / "system-stats-response.json").exists():
        with open(fixtures_dir / "system-stats-response.json", "r", encoding="utf-8") as f:
            default_history = json.dumps(json.load(f))

    if systems_data is not None and isinstance(systems_data.get("items"), list):
        default_systems = json.dumps(systems_data)

    cnt_count_val = 5
    if containers_data is not None and isinstance(containers_data.get("stats"), list):
        default_containers = json.dumps(containers_data)
        cnt_count_val = len(containers_data.get("stats", []))

    if history_data is not None and isinstance(history_data.get("items"), list):
        default_history = json.dumps(history_data)
    if latest_data is None and history_data is None:
        latest_fixture = fixtures_dir / "system-latest-response.json"
        if latest_fixture.exists():
            latest_data = json.loads(latest_fixture.read_text(encoding="utf-8"))

    hub_url_val = hub_url if hub_url is not None else "http://localhost:8090"
    token_val = token if token is not None else ""
    email_val = email if email is not None else ""
    pass_val = password if password is not None else ""
    srv_name_val = server_name if server_name is not None else "localhost"

    # Self-contained globals embedded inside Komponent and preset_root
    globals_list = {
        "server_name": {
            "index": 0,
            "type": "TEXT",
            "title": "Server Display Name",
            "description": "Friendly name of primary server",
            "value": srv_name_val
        },
        "bz_url": {
            "index": 1,
            "type": "TEXT",
            "title": "Beszel Hub URL",
            "description": "Base URL of Beszel instance (e.g. http://localhost:8090)",
            "value": hub_url_val
        },
        "bz_email": {
            "index": 2,
            "type": "TEXT",
            "title": "Beszel User Email",
            "description": "PocketBase Admin or regular user email",
            "value": email_val
        },
        "bz_pass": {
            "index": 3,
            "type": "TEXT",
            "title": "Beszel Password",
            "description": "PocketBase Admin or regular user password",
            "value": pass_val
        },
        "bz_token": {
            "index": 4,
            "type": "TEXT",
            "title": "PocketBase Auth Token",
            "description": "Bearer token populated dynamically by Auth Flow",
            "value": token_val
        },
        "sys_id": {
            "index": 5,
            "type": "TEXT",
            "title": "System ID",
            "description": "Current system record ID (e.g. sys_atlas)",
            "value": ""
        },
        "view": {
            "index": 6,
            "type": "TEXT",
            "title": "Active View",
            "description": "Current active view: overview | containers | info",
            "value": "overview"
        },
        "sys_idx": {
            "index": 7,
            "type": "TEXT",
            "title": "Active System Index",
            "value": "0"
        },
        "container_page": {
            "index": 8,
            "type": "NUMBER",
            "title": "Containers Page",
            "value": 0
        },
        "container_count": {
            "index": 9,
            "type": "NUMBER",
            "title": "Containers Total Count",
            "value": cnt_count_val
        },
        # Cache globals
        "sys_json": {
            "index": 10,
            "type": "TEXT",
            "title": "Systems Cache",
            "value": default_systems
        },
        "latest": {
            "index": 11,
            "type": "TEXT",
            "title": "Latest System Cache",
            "value": json.dumps(latest_data) if latest_data is not None else "{}"
        },
        "tmp_now": {
            "index": 12,
            "type": "TEXT",
            "title": "Temporary Latest Cache",
            "value": ""
        },
        "cnt_json": {
            "index": 13,
            "type": "TEXT",
            "title": "Containers Cache",
            "value": default_containers
        },
        "day_json": {
            "index": 14,
            "type": "TEXT",
            "title": "24h Network Cache",
            "value": default_history
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
        # Semantic Theme Color Tokens
        "c_base": {"index": 18, "type": "COLOR", "title": "Base Background", "value": k_colors["c_base"]},
        "c_mantle": {"index": 19, "type": "COLOR", "title": "Mantle Background", "value": k_colors["c_mantle"]},
        "c_surface0": {"index": 20, "type": "COLOR", "title": "Surface0 Track", "value": k_colors["c_surface0"]},
        "c_surface1": {"index": 21, "type": "COLOR", "title": "Surface1 Border", "value": k_colors["c_surface1"]},
        "c_text": {"index": 22, "type": "COLOR", "title": "Primary Text", "value": k_colors["c_text"]},
        "c_subtext": {"index": 23, "type": "COLOR", "title": "Secondary Label", "value": k_colors["c_subtext"]},
        "c_muted": {"index": 24, "type": "COLOR", "title": "Muted Text", "value": k_colors["c_muted"]},
        "c_cpu": {"index": 25, "type": "COLOR", "title": "CPU Accent", "value": k_colors["c_cpu"]},
        "c_ram": {"index": 26, "type": "COLOR", "title": "RAM Accent", "value": k_colors["c_ram"]},
        "c_disk": {"index": 27, "type": "COLOR", "title": "Disk Accent", "value": k_colors["c_disk"]},
        "c_net": {"index": 28, "type": "COLOR", "title": "Network Accent", "value": k_colors["c_net"]},
        "c_ok": {"index": 29, "type": "COLOR", "title": "Online / OK", "value": k_colors["c_ok"]},
        "c_warn": {"index": 30, "type": "COLOR", "title": "Warning / Stale", "value": k_colors["c_warn"]},
        "c_peach": {"index": 31, "type": "COLOR", "title": "High Usage Warning", "value": k_colors["c_peach"]},
        "c_err": {"index": 32, "type": "COLOR", "title": "Error / Offline", "value": k_colors["c_err"]},
        "c_accent": {"index": 33, "type": "COLOR", "title": "Semantic UI Accent", "value": k_colors["c_accent"]},
    }

    for name, value in {**k_colors, "c_tab_inactive": resolved_theme.inactive_tab_bg}.items():
        if name not in globals_list:
            globals_list[name] = {"index": len(globals_list), "type": "COLOR", "title": name, "value": value}

    # Direct cache globals expression according to AGENTS.md decoupled architecture
    sys_expr = "gv(sys_json)"
    cnt_expr = "gv(cnt_json)"

    font_path = "kfile://org.kustom.provider/fonts/JetBrainsMonoNerdFont.ttf"
    card_w_formula = "$mu(max, 150, mu(round, (si(rwidth) - 36) / 2))$"

    # Helper for building a Celestia Shell style circular gauge card
    def make_circular_card(glyph, title, field_key, color_global, fg_hex, subtext_expr=None, second_subtext_expr=None):
        val_path0 = f".items[0].info.{field_key}"
        val_path1 = f".items[1].info.{field_key}"
        p0 = f"tc(json, {sys_expr}, \"{val_path0}\")"
        p1 = f"tc(json, {sys_expr}, \"{val_path1}\")"

        # Safe progress level formula (0..100) - avoids if() inside mu()
        ring_formula = f"$if(gv(sys_idx) = 1, if({p1} != \"\", mu(min, 100, mu(max, 0, mu(round, {p1}))), 0), if({p0} != \"\", mu(min, 100, mu(max, 0, mu(round, {p0}))), 0))$"

        # Safe percentage formula - guarantees integer percent or 0%, never empty
        pct_formula = f"$if(gv(sys_idx) = 1, if({p1} != \"\", mu(round, {p1}), 0), if({p0} != \"\", mu(round, {p0}), 0))$%"

        right_items = [
            {
                "internal_type": "TextModule",
                "internal_title": f"Title_{title}",
                "text_expression": f"{glyph} {title}",
                "text_family": font_path,
                "text_size": 19.0,
                "paint_color": fg_hex,
                "internal_globals": {"paint_color": color_global}
            }
        ]
        if subtext_expr:
            right_items.append({
                "internal_type": "TextModule",
                "internal_title": f"Sub_{title}",
                "text_expression": "—",
                "text_family": font_path,
                "text_size": 16.5,
                "paint_color": k_colors["c_subtext"],
                "internal_globals": {"paint_color": "c_subtext"},
                "internal_formulas": {"text_expression": subtext_expr},
                "internal_toggles": {"text_expression": 10}
            })
        if second_subtext_expr:
            right_items.append({
                "internal_type": "TextModule",
                "internal_title": f"Sub2_{title}",
                "text_expression": "—",
                "text_family": font_path,
                "text_size": 15.5,
                "paint_color": k_colors["c_muted"],
                "internal_globals": {"paint_color": "c_muted"},
                "internal_formulas": {"text_expression": second_subtext_expr},
                "internal_toggles": {"text_expression": 10}
            })

        return {
            "internal_type": "OverlapLayerModule",
            "internal_title": f"Card_{title}",
            "viewgroup_items": [
                # Card Background Shape
                {
                    "internal_type": "ShapeModule",
                    "internal_title": f"Bg_{title}",
                    "shape_type": "RECT",
                    "shape_width": 160.0,
                    "shape_height": 120.0,
                    "shape_corners": 16.0,
                    "paint_color": k_colors["c_mantle"],
                    "internal_globals": {"paint_color": "c_mantle"},
                    "internal_formulas": {"shape_width": card_w_formula},
                    "internal_toggles": {"shape_width": 10}
                },
                # Card Border Stroke
                {
                    "internal_type": "ShapeModule",
                    "internal_title": f"Border_{title}",
                    "shape_type": "RECT",
                    "shape_width": 160.0,
                    "shape_height": 120.0,
                    "shape_corners": 16.0,
                    "paint_style": "STROKE",
                    "stroke_width": 1.0,
                    "paint_color": k_colors["c_surface0"],
                    "internal_globals": {"paint_color": "c_surface0"},
                    "internal_formulas": {"shape_width": card_w_formula},
                    "internal_toggles": {"shape_width": 10}
                },
                # Inner Horizontal Layout: Circular Ring (Left) + Details (Right)
                {
                    "internal_type": "OverlapLayerModule",
                    "internal_title": f"Inner_{title}",
                    "viewgroup_items": [
                        {
                            "internal_type": "ShapeModule",
                            "shape_type": "RECT",
                            "shape_height": 120.0,
                            "paint_color": "#00000000",
                            "internal_formulas": {"shape_width": card_w_formula},
                            "internal_toggles": {"shape_width": 10}
                        },
                        # Circular Ring with center percentage
                        {
                            "internal_type": "OverlapLayerModule",
                            "internal_title": f"Gauge_{title}",
                            "position_anchor": "CENTERLEFT",
                            "position_offset_x": 12.0,
                            "position_padding_left": 12.0,
                            "viewgroup_items": [
                                {
                                    "internal_type": "ProgressModule",
                                    "internal_title": f"Ring_{title}",
                                    "progress_progress": "CUSTOM",
                                    "progress_mode": "CUSTOM",
                                    "style_style": "CIRCLE",
                                    "style_size": 72.0,
                                    "style_height": 8.0,
                                    "style_width": 360.0,
                                    "color_mode": "FLAT",
                                    "color_fgcolor": fg_hex,
                                    "color_bgcolor": k_colors["c_surface0"],
                                    "internal_globals": {
                                        "color_fgcolor": color_global,
                                        "color_bgcolor": "c_surface0"
                                    },
                                    "progress_level": 50.0,
                                    "internal_formulas": {
                                        "progress_level": ring_formula
                                    },
                                    "internal_toggles": {"progress_level": 10}
                                },
                                {
                                    "internal_type": "TextModule",
                                    "internal_title": f"Pct_{title}",
                                    "text_expression": "0%",
                                    "text_family": font_path,
                                    "text_size": 17.5,
                                    "paint_color": k_colors["c_text"],
                                    "internal_globals": {"paint_color": "c_text"},
                                    "internal_formulas": {
                                        "text_expression": pct_formula
                                    },
                                    "internal_toggles": {"text_expression": 10}
                                }
                            ]
                        },
                        # Right side text details
                        {
                            "internal_type": "StackLayerModule",
                            "internal_title": f"Details_{title}",
                            "position_anchor": "CENTERLEFT",
                            "position_offset_x": 108.0,
                            "position_padding_left": 108.0,
                            "config_stacking": "VERTICAL",
                            "config_margin": 4.0,
                            "viewgroup_items": right_items
                        }
                    ]
                }
            ]
        }

    # Helper for Network Card with live sparkline graph and current bandwidth
    def make_network_card():
        return {
            "internal_type": "OverlapLayerModule",
            "internal_title": "Card_Network",
            "viewgroup_items": [
                # Card Background Shape
                {
                    "internal_type": "ShapeModule",
                    "internal_title": "Bg_Network",
                    "shape_type": "RECT",
                    "shape_width": 160.0,
                    "shape_height": 120.0,
                    "shape_corners": 16.0,
                    "paint_color": k_colors["c_mantle"],
                    "internal_globals": {"paint_color": "c_mantle"},
                    "internal_formulas": {"shape_width": card_w_formula},
                    "internal_toggles": {"shape_width": 10}
                },
                # Card Border Stroke
                {
                    "internal_type": "ShapeModule",
                    "internal_title": "Border_Network",
                    "shape_type": "RECT",
                    "shape_width": 160.0,
                    "shape_height": 120.0,
                    "shape_corners": 16.0,
                    "paint_style": "STROKE",
                    "stroke_width": 1.0,
                    "paint_color": k_colors["c_surface0"],
                    "internal_globals": {"paint_color": "c_surface0"},
                    "internal_formulas": {"shape_width": card_w_formula},
                    "internal_toggles": {"shape_width": 10}
                },
                # Card Inner Layout: Header + Mini Sparkline + Bandwidth
                {
                    "internal_type": "StackLayerModule",
                    "internal_title": "Inner_Network",
                    "config_stacking": "VERTICAL",
                    "config_margin": 6.0,
                    "viewgroup_items": [
                        # Header: Glyph + Title + Live Rate
                        {
                            "internal_type": "StackLayerModule",
                            "internal_title": "NetHeader",
                            "config_stacking": "HORIZONTAL_CENTER",
                            "config_margin": 6.0,
                            "viewgroup_items": [
                                {
                                    "internal_type": "TextModule",
                                    "internal_title": "NetTitle",
                                    "text_expression": "󰀂 Network",
                                    "text_family": font_path,
                                    "text_size": 19.0,
                                    "paint_color": k_colors["c_net"],
                                    "internal_globals": {"paint_color": "c_net"}
                                },
                                {
                                    "internal_type": "TextModule",
                                    "internal_title": "NetRate",
                                    "text_expression": "▲ 0 KB/s",
                                    "text_family": font_path,
                                    "text_size": 15.5,
                                    "paint_color": k_colors["c_text"],
                                    "internal_globals": {"paint_color": "c_text"},
                                    "internal_formulas": {
                                        "text_expression": "0 KiB/s"
                                    },
                                    "internal_toggles": {"text_expression": 10}
                                }
                            ]
                        },
                        # Mini Sparkline Graph
                        {
                            "internal_type": "StackLayerModule",
                            "internal_title": "NetSparkline",
                            "config_stacking": "HORIZONTAL_CENTER",
                            "config_margin": 3.0,
                            "viewgroup_items": []
                        },
                        # Subtitle
                        {
                            "internal_type": "TextModule",
                            "internal_title": "NetSub",
                            "text_expression": "Realtime Traffic",
                            "text_family": font_path,
                            "text_size": 14.0,
                            "paint_color": k_colors["c_muted"],
                            "internal_globals": {"paint_color": "c_muted"}
                        }
                    ]
                }
            ]
        }

    # Helper for container row (0..4) with Docker glyph and full-width card
    def make_container_row(idx):
        return {
            "internal_type": "OverlapLayerModule",
            "internal_title": f"ContainerRow_{idx}",
            "internal_formulas": {
                "config_visible": f"$if(gv(container_page) * 5 + {idx} < gv(container_count), ALWAYS, REMOVE)$"
            },
            "internal_toggles": {"config_visible": 10},
            "viewgroup_items": [
                # Row background card
                {
                    "internal_type": "ShapeModule",
                    "internal_title": f"RowBg_{idx}",
                    "shape_type": "RECT",
                    "shape_width": 320.0,
                    "shape_height": 36.0,
                    "shape_corners": 9.0,
                    "paint_color": k_colors["c_mantle"],
                    "internal_globals": {"paint_color": "c_mantle"},
                    "internal_formulas": {"shape_width": "$si(rwidth) - 36$"},
                    "internal_toggles": {"shape_width": 10}
                },
                # Row border stroke
                {
                    "internal_type": "ShapeModule",
                    "internal_title": f"RowBorder_{idx}",
                    "shape_type": "RECT",
                    "shape_width": 320.0,
                    "shape_height": 36.0,
                    "shape_corners": 9.0,
                    "paint_style": "STROKE",
                    "stroke_width": 1.0,
                    "paint_color": k_colors["c_surface0"],
                    "internal_globals": {"paint_color": "c_surface0"},
                    "internal_formulas": {"shape_width": "$si(rwidth) - 36$"},
                    "internal_toggles": {"shape_width": 10}
                },
                # Left side: Status dot + Docker name (anchored left)
                {
                    "internal_type": "StackLayerModule",
                    "internal_title": f"RowLeft_{idx}",
                    "position_anchor": "CENTER_LEFT",
                    "position_x": 12.0,
                    "config_stacking": "HORIZONTAL_CENTER",
                    "config_margin": 8.0,
                    "viewgroup_items": [
                        {
                            "internal_type": "ShapeModule",
                            "internal_title": "Dot",
                            "shape_type": "CIRCLE",
                            "shape_width": 6.5,
                            "shape_height": 6.5,
                            "paint_color": k_colors["c_ok"],
                            "internal_globals": {"paint_color": "c_ok"}
                        },
                        {
                            "internal_type": "TextModule",
                            "internal_title": "Name",
                            "text_expression": f" container-{idx}",
                            "text_family": font_path,
                            "text_size": 15.5,
                            "paint_color": k_colors["c_text"],
                            "internal_globals": {"paint_color": "c_text"},
                            "internal_formulas": {
                                "text_expression": f"$if(gv(container_page) = 1, if(tc(json, {cnt_expr}, \".stats[{idx+5}].n\") != \"\", \" \" + tc(ell, tc(json, {cnt_expr}, \".stats[{idx+5}].n\"), 16), \" container-{idx+5}\"), if(tc(json, {cnt_expr}, \".stats[{idx}].n\") != \"\", \" \" + tc(ell, tc(json, {cnt_expr}, \".stats[{idx}].n\"), 16), \" container-{idx}\"))$"
                            },
                            "internal_toggles": {"text_expression": 10}
                        }
                    ]
                },
                # Right side: CPU & Memory metrics (anchored right)
                {
                    "internal_type": "StackLayerModule",
                    "internal_title": f"RowRight_{idx}",
                    "position_anchor": "CENTER_RIGHT",
                    "position_x": 12.0,
                    "config_stacking": "HORIZONTAL_CENTER",
                    "config_margin": 10.0,
                    "viewgroup_items": [
                        {
                            "internal_type": "TextModule",
                            "internal_title": "Cpu",
                            "text_expression": "0.0%",
                            "text_family": font_path,
                            "text_size": 14.5,
                            "paint_color": k_colors["c_cpu"],
                            "internal_globals": {"paint_color": "c_cpu"},
                            "internal_formulas": {
                                "text_expression": f"$if(gv(container_page) = 1, if(tc(json, {cnt_expr}, \".stats[{idx+5}].c\") != \"\", tc(json, {cnt_expr}, \".stats[{idx+5}].c\") + \"%\", \"0.0%\"), if(tc(json, {cnt_expr}, \".stats[{idx}].c\") != \"\", tc(json, {cnt_expr}, \".stats[{idx}].c\") + \"%\", \"0.0%\"))$"
                            },
                            "internal_toggles": {"text_expression": 10}
                        },
                        {
                            "internal_type": "TextModule",
                            "internal_title": "Mem",
                            "text_expression": "0 MB",
                            "text_family": font_path,
                            "text_size": 14.5,
                            "paint_color": k_colors["c_ram"],
                            "internal_globals": {"paint_color": "c_ram"},
                            "internal_formulas": {
                                "text_expression": f"$if(gv(container_page) = 1, if(tc(json, {cnt_expr}, \".stats[{idx+5}].m\") != \"\", mu(round, tc(json, {cnt_expr}, \".stats[{idx+5}].m\") / 1048576) + \" MB\", \"0 MB\"), if(tc(json, {cnt_expr}, \".stats[{idx}].m\") != \"\", mu(round, tc(json, {cnt_expr}, \".stats[{idx}].m\") / 1048576) + \" MB\", \"0 MB\"))$"
                            },
                            "internal_toggles": {"text_expression": 10}
                        }
                    ]
                }
            ]
        }

    # Construct the entire Komponent tree
    komponent = {
        "internal_type": "KomponentModule",
        "internal_title": "Beszel Monitor",
        "globals_list": globals_list,
        "viewgroup_items": [
            # Main Background Card
            {
                "internal_type": "ShapeModule",
                "internal_title": "CardBackground",
                "shape_type": "RECT",
                "shape_width": 640.0,
                "shape_height": 360.0,
                "shape_corners": 22.0,
                "paint_color": k_colors["c_base"],
                "internal_globals": {"paint_color": "c_base"},
                "internal_formulas": {
                    "shape_width": "$si(rwidth)$",
                    "shape_height": "$si(rheight)$"
                },
                "internal_toggles": {
                    "shape_width": 10,
                    "shape_height": 10
                }
            },
            # Glossy Wallpaper Background Image Placeholder
            {
                "internal_type": "BitmapModule",
                "internal_title": "GlossyWallpaper",
                "bitmap_bitmap": "",
                "bitmap_width": 1000.0,
                "bitmap_alpha": 60.0,
                "bitmap_blur": 50.0,
                "bitmap_dim": 30.0,
                "position_anchor": "CENTER",
                "position_offset_x": 0.0,
                "position_offset_y": 0.0,
                "position_padding_left": 0.0,
                "position_padding_top": 0.0,
                "position_padding_right": 0.0,
                "position_padding_bottom": 0.0
            },
            # Border Stroke (set to 0 width & transparent to eliminate outer shadow / double layer)
            {
                "internal_type": "ShapeModule",
                "internal_title": "CardBorder",
                "shape_type": "RECT",
                "shape_width": 640.0,
                "shape_height": 360.0,
                "shape_corners": 22.0,
                "paint_style": "STROKE",
                "stroke_width": 0.0,
                "paint_color": "#00000000",
                "internal_formulas": {
                    "shape_width": "$si(rwidth)$",
                    "shape_height": "$si(rheight)$"
                },
                "internal_toggles": {
                    "shape_width": 10,
                    "shape_height": 10
                }
            },
            # Main Layout Vertical Flow
            {
                "internal_type": "StackLayerModule",
                "internal_title": "ContentFlow",
                "config_stacking": "VERTICAL",
                "config_margin": 8.0,
                "viewgroup_items": [
                    # Header Bar (Host, Health status, Uptime & refresh)
                    {
                        "internal_type": "StackLayerModule",
                        "internal_title": "Header",
                        "config_stacking": "HORIZONTAL_CENTER",
                        "config_margin": 6.0,
                        "viewgroup_items": [
                            # Health Status Dot (positioned with balanced spacing, not squashed)
                            {
                                "internal_type": "ShapeModule",
                                "internal_title": "StatusIndicator",
                                "shape_type": "CIRCLE",
                                "shape_width": 8.0,
                                "shape_height": 8.0,
                                "paint_color": k_colors["c_ok"],
                                "internal_formulas": {
                                    "paint_color": f"$if(gv(stale) = 1, gv(c_warn), if(tc(json, {sys_expr}, \".items[0].status\") = \"up\", gv(c_ok), gv(c_err)))$"
                                },
                                "internal_toggles": {"paint_color": 10}
                            },
                            # Server Name (clean, prominent, single tap switches system)
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "HostSelector",
                                "internal_events": [
                                    {
                                        "type": "SINGLE_TAP",
                                        "action": "SWITCH_GLOBAL",
                                        "switch": "sys_idx",
                                        "switch_text": "$if(gv(sys_idx) = 0, 1, 0)$"
                                    }
                                ],
                                "viewgroup_items": [
                                    {
                                        "internal_type": "ShapeModule",
                                        "internal_title": "HostTouchArea",
                                        "shape_type": "RECT",
                                        "shape_width": 76.0,
                                        "shape_height": 36.0,
                                        "paint_color": "#01000000"
                                    },
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "HostnameText",
                                        "text_expression": srv_name_val,
                                        "text_family": font_path,
                                        "text_size": 20.0,
                                        "paint_color": k_colors["c_text"],
                                        "internal_globals": {"paint_color": "c_text"},
                                        "internal_formulas": {
                                            "text_expression": f"$if(gv(server_name) != \"\", gv(server_name), if(tc(json, {sys_expr}, \".items[0].name\") != \"\", tc(json, {sys_expr}, \".items[0].name\"), \"{srv_name_val}\"))$"
                                        },
                                        "internal_toggles": {"text_expression": 10}
                                    }
                                ]
                            },
                            # Separator
                            {
                                "internal_type": "TextModule",
                                "internal_title": "DotSep",
                                "text_expression": "·",
                                "text_family": font_path,
                                "text_size": 16.0,
                                "paint_color": k_colors["c_muted"],
                                "internal_globals": {"paint_color": "c_muted"}
                            },
                            # Uptime display
                            {
                                "internal_type": "TextModule",
                                "internal_title": "TimeText",
                                "text_expression": "up 0d 0h",
                                "text_family": font_path,
                                "text_size": 16.0,
                                "paint_color": k_colors["c_subtext"],
                                "internal_globals": {"paint_color": "c_subtext"},
                                "internal_formulas": {
                                    "text_expression": f"$if(tc(json, {sys_expr}, \".items[0].info.u\") != \"\", \"up \" + mu(floor, tc(json, {sys_expr}, \".items[0].info.u\") / 86400) + \"d \" + mu(floor, (tc(json, {sys_expr}, \".items[0].info.u\") % 86400) / 3600) + \"h\", \"online\")$"
                                },
                                "internal_toggles": {"text_expression": 10}
                            },
                            # Refresh Button (Min 44dp touch target, triggers Flow)
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "RefreshTouchTarget",
                                "internal_events": [
                                    {
                                        "type": "SINGLE_TAP",
                                        "action": "TRIGGER_FLOW",
                                        "flow_id": "FvLj5OVJ"
                                    }
                                ],
                                "viewgroup_items": [
                                    {
                                        "internal_type": "ShapeModule",
                                        "internal_title": "RefreshArea",
                                        "shape_type": "RECT",
                                        "shape_width": 44.0,
                                        "shape_height": 44.0,
                                        "shape_corners": 10.0,
                                        "paint_color": k_colors["c_surface0"],
                                        "internal_globals": {"paint_color": "c_surface0"}
                                    },
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "RefreshGlyph",
                                        "text_expression": "↻",
                                        "text_family": font_path,
                                        "text_size": 16.0,
                                        "paint_color": k_colors["c_subtext"],
                                        "internal_globals": {"paint_color": "c_subtext"}
                                    }
                                ]
                            }
                        ]
                    },
                    # Main Dynamic View Area
                    {
                        "internal_type": "OverlapLayerModule",
                        "internal_title": "ViewArea",
                        "viewgroup_items": [
                            # Fixed Height Spacer to guarantee 248dp bounding box across all 3 views
                            {
                                "internal_type": "ShapeModule",
                                "internal_title": "ViewAreaSpacer",
                                "shape_type": "RECT",
                                "shape_width": 320.0,
                                "shape_height": 248.0,
                                "paint_color": "#00000000",
                                "internal_formulas": {"shape_width": "$si(rwidth) - 36$"},
                                "internal_toggles": {"shape_width": 10}
                            },
                            # VIEW 1: Overview (Celestia Shell 2x2 Grid of Circular Cards)
                            {
                                "internal_type": "StackLayerModule",
                                "internal_title": "ViewOverview",
                                "config_stacking": "VERTICAL",
                                "config_margin": 8.0,
                                "internal_formulas": {
                                    "config_visible": "$if(gv(view) = \"overview\", ALWAYS, REMOVE)$"
                                },
                                "internal_toggles": {"config_visible": 10},
                                "viewgroup_items": [
                                    # Row 1: CPU and Memory Cards
                                    {
                                        "internal_type": "StackLayerModule",
                                        "internal_title": "OverviewRow1",
                                        "config_stacking": "HORIZONTAL_CENTER",
                                        "config_margin": 8.0,
                                        "viewgroup_items": [
                                            make_circular_card(
                                                glyph="󰍛",
                                                title="CPU",
                                                field_key="cpu",
                                                color_global="c_cpu",
                                                fg_hex=k_colors["c_cpu"],
                                                subtext_expr=f"$if(tc(json, {sys_expr}, \".items[0].info.dt\") != \"\", \" \" + mu(round, tc(json, {sys_expr}, \".items[0].info.dt\")) + \"°C\", \" —\")$",
                                                second_subtext_expr=f"$if(tc(json, {sys_expr}, \".items[0].info.la[0]\") != \"\", \"Load Avg: \" + mu(round, tc(json, {sys_expr}, \".items[0].info.la[0]\"), 2), if(tc(json, {sys_expr}, \".items[0].info.la\") != \"\", \"Load Avg: \" + mu(round, tc(json, {sys_expr}, \".items[0].info.la\"), 2), \"Load Avg: 0.00\"))$"
                                            ),
                                            make_circular_card(
                                                glyph="",
                                                title="Memory",
                                                field_key="mp",
                                                color_global="c_ram",
                                                fg_hex=k_colors["c_ram"],
                                                subtext_expr=f"$if(tc(json, {sys_expr}, \".items[0].info.mp\") != \"\", \"RAM: \" + mu(round, tc(json, {sys_expr}, \".items[0].info.mp\")) + \"%\", \"RAM: 0%\")$",
                                                second_subtext_expr=f"$if(tc(json, {sys_expr}, \".items[0].info.mp\") != \"\", if(tc(json, {sys_expr}, \".items[0].info.mp\") > 85, \"High Load\", \"Normal\"), \"Normal\")$"
                                            )
                                        ]
                                    },
                                    # Row 2: Disk and Network Cards
                                    {
                                        "internal_type": "StackLayerModule",
                                        "internal_title": "OverviewRow2",
                                        "config_stacking": "HORIZONTAL_CENTER",
                                        "config_margin": 8.0,
                                        "viewgroup_items": [
                                            make_circular_card(
                                                glyph="󰋊",
                                                title="Disk",
                                                field_key="dp",
                                                color_global="c_disk",
                                                fg_hex=k_colors["c_disk"],
                                                subtext_expr=f"$if(tc(json, {sys_expr}, \".items[0].info.dp\") != \"\", \"Storage: \" + mu(round, tc(json, {sys_expr}, \".items[0].info.dp\")) + \"%\", \"Storage: 0%\")$",
                                                second_subtext_expr=f"$if(tc(json, {sys_expr}, \".items[0].info.dp\") != \"\", if(tc(json, {sys_expr}, \".items[0].info.dp\") > 90, \"Critical\", \"Healthy\"), \"Healthy\")$"
                                            ),
                                            make_network_card()
                                        ]
                                    }
                                ]
                            },
                            # VIEW 2: Containers (Docker List with  glyphs)
                            {
                                "internal_type": "StackLayerModule",
                                "internal_title": "ViewContainers",
                                "config_stacking": "VERTICAL",
                                "config_margin": 6.0,
                                "internal_formulas": {
                                    "config_visible": "$if(gv(view) = \"containers\", ALWAYS, REMOVE)$"
                                },
                                "internal_toggles": {"config_visible": 10},
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
                                        "config_margin": 12.0,
                                        "viewgroup_items": [
                                            {
                                                "internal_type": "OverlapLayerModule",
                                                "internal_title": "BtnPrev",
                                                "internal_events": [
                                                    {
                                                        "type": "SINGLE_TAP",
                                                        "action": "SWITCH_GLOBAL",
                                                        "switch": "container_page",
                                                        "switch_text": "$mu(max, 0, gv(container_page) - 1)$"
                                                    }
                                                ],
                                                "viewgroup_items": [
                                                    {
                                                        "internal_type": "ShapeModule",
                                                        "shape_type": "RECT",
                                                        "shape_width": 100.0,
                                                        "shape_height": 38.0,
                                                        "shape_corners": 10.0,
                                                        "paint_color": k_colors["c_surface0"],
                                                        "internal_globals": {"paint_color": "c_surface0"}
                                                    },
                                                    {
                                                        "internal_type": "ShapeModule",
                                                        "shape_type": "RECT",
                                                        "shape_width": 100.0,
                                                        "shape_height": 38.0,
                                                        "shape_corners": 10.0,
                                                        "paint_style": "STROKE",
                                                        "stroke_width": 1.0,
                                                        "paint_color": k_colors["c_surface1"],
                                                        "internal_globals": {"paint_color": "c_surface1"}
                                                    },
                                                    {
                                                        "internal_type": "TextModule",
                                                        "text_expression": "◀ Prev",
                                                        "text_family": font_path,
                                                        "text_size": 16.0,
                                                        "paint_color": k_colors["c_text"],
                                                        "internal_globals": {"paint_color": "c_text"}
                                                    }
                                                ]
                                            },
                                            {
                                                "internal_type": "TextModule",
                                                "internal_title": "PageText",
                                                "text_expression": "Page 1 / 1",
                                                "text_family": font_path,
                                                "text_size": 15.0,
                                                "paint_color": k_colors["c_subtext"],
                                                "internal_globals": {"paint_color": "c_subtext"},
                                                "internal_formulas": {
                                                    "text_expression": "$if(gv(container_count) > 0, \"Page \" + (gv(container_page) + 1) + \" / \" + (mu(floor, (gv(container_count) - 1) / 5) + 1), \"Page 1 / 1\")$"
                                                },
                                                "internal_toggles": {"text_expression": 10}
                                            },
                                            {
                                                "internal_type": "OverlapLayerModule",
                                                "internal_title": "BtnNext",
                                                "internal_events": [
                                                    {
                                                        "type": "SINGLE_TAP",
                                                        "action": "SWITCH_GLOBAL",
                                                        "switch": "container_page",
                                                        "switch_text": "$if((gv(container_page) + 1) * 5 < gv(container_count), gv(container_page) + 1, gv(container_page))$"
                                                    }
                                                ],
                                                "viewgroup_items": [
                                                    {
                                                        "internal_type": "ShapeModule",
                                                        "shape_type": "RECT",
                                                        "shape_width": 100.0,
                                                        "shape_height": 38.0,
                                                        "shape_corners": 10.0,
                                                        "paint_color": k_colors["c_surface0"],
                                                        "internal_globals": {"paint_color": "c_surface0"}
                                                    },
                                                    {
                                                        "internal_type": "ShapeModule",
                                                        "shape_type": "RECT",
                                                        "shape_width": 100.0,
                                                        "shape_height": 38.0,
                                                        "shape_corners": 10.0,
                                                        "paint_style": "STROKE",
                                                        "stroke_width": 1.0,
                                                        "paint_color": k_colors["c_surface1"],
                                                        "internal_globals": {"paint_color": "c_surface1"}
                                                    },
                                                    {
                                                        "internal_type": "TextModule",
                                                        "text_expression": "Next ▶",
                                                        "text_family": font_path,
                                                        "text_size": 16.0,
                                                        "paint_color": k_colors["c_text"],
                                                        "internal_globals": {"paint_color": "c_text"}
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            },
                            # ViewInfo is populated by the shared scalar adapter/layout.
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "ViewInfo",
                                "viewgroup_items": []
                            }
                        ]
                    },
                    # Bottom Navigation Bar (Large, accessible, thumb-friendly buttons)
                    {
                        "internal_type": "StackLayerModule",
                        "internal_title": "BottomNav",
                        "config_stacking": "HORIZONTAL_CENTER",
                        "config_margin": 6.0,
                        "viewgroup_items": [
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "TabOverview",
                                "internal_events": [
                                    {
                                        "type": "SINGLE_TAP",
                                        "action": "SWITCH_GLOBAL",
                                        "switch": "view",
                                        "switch_text": "overview"
                                    }
                                ],
                                "viewgroup_items": [
                                    {
                                        "internal_type": "ShapeModule",
                                        "shape_type": "RECT",
                                        "shape_width": 105.0,
                                        "shape_height": 46.0,
                                        "shape_corners": 12.0,
                                        "paint_color": k_colors["c_surface0"],
                                        "internal_formulas": {
                                            "shape_width": "$mu(round, (si(rwidth) - 48) / 3)$",
                                            "paint_color": f"$if(gv(view) = \"overview\", gv(c_surface0), {resolved_theme.inactive_tab_bg})$"
                                        },
                                        "internal_toggles": {"shape_width": 10, "paint_color": 10}
                                    },
                                    {
                                        "internal_type": "ShapeModule",
                                        "shape_type": "RECT",
                                        "shape_width": 105.0,
                                        "shape_height": 46.0,
                                        "shape_corners": 12.0,
                                        "paint_style": "STROKE",
                                        "stroke_width": 1.2,
                                        "paint_color": k_colors["c_surface1"],
                                        "internal_formulas": {
                                            "shape_width": "$mu(round, (si(rwidth) - 48) / 3)$",
                                            "paint_color": "$if(gv(view) = \"overview\", gv(c_surface1), gv(c_surface0))$"
                                        },
                                        "internal_toggles": {"shape_width": 10, "paint_color": 10}
                                    },
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "TextOverview",
                                        "text_expression": "󰍛 Overview",
                                        "text_family": font_path,
                                        "text_size": 17.5,
                                        "paint_color": k_colors["c_text"],
                                        "internal_formulas": {"paint_color": "$if(gv(view) = \"overview\", gv(c_text), gv(c_muted))$"},
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
                                        "action": "SWITCH_GLOBAL",
                                        "switch": "view",
                                        "switch_text": "containers"
                                    }
                                ],
                                "viewgroup_items": [
                                    {
                                        "internal_type": "ShapeModule",
                                        "shape_type": "RECT",
                                        "shape_width": 105.0,
                                        "shape_height": 46.0,
                                        "shape_corners": 12.0,
                                        "paint_color": k_colors["c_surface0"],
                                        "internal_formulas": {
                                            "shape_width": "$mu(round, (si(rwidth) - 48) / 3)$",
                                            "paint_color": f"$if(gv(view) = \"containers\", gv(c_surface0), {resolved_theme.inactive_tab_bg})$"
                                        },
                                        "internal_toggles": {"shape_width": 10, "paint_color": 10}
                                    },
                                    {
                                        "internal_type": "ShapeModule",
                                        "shape_type": "RECT",
                                        "shape_width": 105.0,
                                        "shape_height": 46.0,
                                        "shape_corners": 12.0,
                                        "paint_style": "STROKE",
                                        "stroke_width": 1.2,
                                        "paint_color": k_colors["c_surface1"],
                                        "internal_formulas": {
                                            "shape_width": "$mu(round, (si(rwidth) - 48) / 3)$",
                                            "paint_color": "$if(gv(view) = \"containers\", gv(c_surface1), gv(c_surface0))$"
                                        },
                                        "internal_toggles": {"shape_width": 10, "paint_color": 10}
                                    },
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "TextContainers",
                                        "text_expression": " Docker",
                                        "text_family": font_path,
                                        "text_size": 17.5,
                                        "paint_color": k_colors["c_muted"],
                                        "internal_formulas": {"paint_color": "$if(gv(view) = \"containers\", gv(c_text), gv(c_muted))$"},
                                        "internal_toggles": {"paint_color": 10}
                                    }
                                ]
                            },
                            {
                                "internal_type": "OverlapLayerModule",
                                "internal_title": "TabInfo",
                                "internal_events": [
                                    {
                                        "type": "SINGLE_TAP",
                                        "action": "SWITCH_GLOBAL",
                                        "switch": "view",
                                        "switch_text": "info"
                                    }
                                ],
                                "viewgroup_items": [
                                    {
                                        "internal_type": "ShapeModule",
                                        "shape_type": "RECT",
                                        "shape_width": 105.0,
                                        "shape_height": 46.0,
                                        "shape_corners": 12.0,
                                        "paint_color": k_colors["c_surface0"],
                                        "internal_formulas": {
                                            "shape_width": "$mu(round, (si(rwidth) - 48) / 3)$",
                                            "paint_color": f"$if(gv(view) = \"info\", gv(c_surface0), {resolved_theme.inactive_tab_bg})$"
                                        },
                                        "internal_toggles": {"shape_width": 10, "paint_color": 10}
                                    },
                                    {
                                        "internal_type": "ShapeModule",
                                        "shape_type": "RECT",
                                        "shape_width": 105.0,
                                        "shape_height": 46.0,
                                        "shape_corners": 12.0,
                                        "paint_style": "STROKE",
                                        "stroke_width": 1.2,
                                        "paint_color": k_colors["c_surface1"],
                                        "internal_formulas": {
                                            "shape_width": "$mu(round, (si(rwidth) - 48) / 3)$",
                                            "paint_color": "$if(gv(view) = \"info\", gv(c_surface1), gv(c_surface0))$"
                                        },
                                        "internal_toggles": {"shape_width": 10, "paint_color": 10}
                                    },
                                    {
                                        "internal_type": "TextModule",
                                        "internal_title": "TextInfo",
                                        "text_expression": "󰋼 Info",
                                        "text_family": font_path,
                                        "text_size": 17.5,
                                        "paint_color": k_colors["c_muted"],
                                        "internal_formulas": {"paint_color": "$if(gv(view) = \"info\", gv(c_text), gv(c_muted))$"},
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

    fix_layout(komponent)
    build_info(komponent)
    apply_theme(komponent)

    # Embed flow in Komponent
    flows = build_flows(globals_list, latest_data=latest_data)
    komponent["internal_flows"] = flows

    if not write_outputs:
        return komponent

    if output_dir is not None:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        clip_target = out_dir / "beszel_monitor.clip"
        loose_target = out_dir / "beszel_monitor_loose.clip"
        kwgt_target = out_dir / "beszel_monitor.kwgt"
    else:
        out_dir = REPO_ROOT / "widget"
        out_dir.mkdir(parents=True, exist_ok=True)
        clip_target = CLIP_FILE
        loose_target = REPO_ROOT / "widget" / "beszel_monitor_loose.clip"
        kwgt_target = KWGT_FILE

    # Top-level Clip structure expected by KWGT clipboard
    clip_data = {
        "clip_version": 1,
        "clip_cut": [],
        "clip_modules": [komponent]
    }

    clip_json = json.dumps(clip_data, indent=2, ensure_ascii=False)
    clip_content = f"##KUSTOMCLIP##\n{clip_json}\n##KUSTOMCLIP##\n"

    with open(clip_target, "w", encoding="utf-8") as f:
        f.write(clip_content)

    # Also generate loose modules clip
    loose_clip_data = {
        "clip_version": 1,
        "clip_cut": [],
        "clip_modules": komponent["viewgroup_items"]
    }
    loose_clip_json = json.dumps(loose_clip_data, indent=2, ensure_ascii=False)
    loose_clip_content = f"##KUSTOMCLIP##\n{loose_clip_json}\n##KUSTOMCLIP##\n"
    with open(loose_target, "w", encoding="utf-8") as f:
        f.write(loose_clip_content)

    # Package as standalone .kwgt archive (directly mirroring ghinfo.kwgt)
    preset_wrapper = {
        "preset_info": {
            "archive": "",
            "author": "Nerver & Antigravity",
            "description": "Beszel Homelab Monitor KWGT Widget",
            "email": "",
            "features": "",
            "pflags": 0,
            "hash": None,
            "height": 652,
            "id": "beszel-monitor-widget",
            "locked": False,
            "release": 382621115,
            "ts": 1788108106931,
            "title": "Beszel Monitor",
            "version": 17,
            "width": 1076,
            "xscreens": 0,
            "yscreens": 0
        },
        "preset_root": {
            "internal_events": [{"action": "KUSTOM_ACTION"}],
            "internal_type": "RootLayerModule",
            "globals_list": globals_list,
            "internal_flows": flows,
            "viewgroup_items": komponent["viewgroup_items"]
        }
    }
    preset_json_str = json.dumps(preset_wrapper, indent=2, ensure_ascii=False)

    with zipfile.ZipFile(kwgt_target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("preset.json", preset_json_str)
        zf.write(REPO_ROOT / "widget/assets/fastfetch/LICENSE.fastfetch", arcname="licenses/fastfetch.txt")
        if FONT_SRC.exists():
            zf.write(FONT_SRC, arcname="fonts/JetBrainsMonoNerdFont.ttf")

    if output_dir is None:
        # Mirror outputs to dist/
        dist_dir = REPO_ROOT / "dist"
        dist_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(clip_target, dist_dir / "beszel_monitor.clip")
        shutil.copy2(loose_target, dist_dir / "beszel_monitor_loose.clip")
        shutil.copy2(kwgt_target, dist_dir / "beszel_monitor.kwgt")

    print(f"✓ Kustom Clip successfully generated at: {clip_target}")
    print(f"✓ Loose Modules Clip generated at: {loose_target}")
    print(f"✓ Standalone KWGT package generated at: {kwgt_target}")
    if output_dir is None:
        print(f"✓ Mirrored to dist/ directory.")
    return komponent


if __name__ == "__main__":
    import argparse
    import sys
    if __package__:
        from .theme_catalog import list_themes
    else:
        from theme_catalog import list_themes

    parser = argparse.ArgumentParser(description="Generate Beszel KWGT clip and package.")
    parser.add_argument("--theme", default=DEFAULT_THEME_ID, help="Theme ID (default: catppuccin-mocha)")
    parser.add_argument("--output-dir", help="Output directory for generated files (default: widget/ and dist/)")
    parser.add_argument("--list-themes", action="store_true", help="List all available themes and exit")
    args = parser.parse_args()

    if args.list_themes:
        themes = list_themes()
        print(f"Available themes ({len(themes)}):")
        for t in themes:
            print(f"  - {t['id']:<26} [{t['mode']:<5}] {t['name']}")
        sys.exit(0)

    build_kustom_clip(theme=args.theme, output_dir=args.output_dir)
