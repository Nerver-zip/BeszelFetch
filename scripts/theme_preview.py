#!/usr/bin/env python3
"""
Synthetic visual theme preview generator for BeszelFetch.

Renders self-contained HTML/SVG preview specimens of the widget for each theme
in the catalog, showing palette swatches, header telemetry, metric gauge cards,
Fastfetch system info with ASCII art, Docker rows, and navigation tabs.

Zero external dependencies: pure HTML5, CSS3, and inline SVG.
"""

import argparse
import html
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.theme_catalog import (
    DEFAULT_THEME_ID,
    REQUIRED_SEMANTIC_ROLES,
    SEMANTIC_TO_GLOBAL,
    THEMES_DIR,
    ResolvedTheme,
    composite_color,
    contrast_ratio,
    list_themes,
    resolve_theme,
)


def render_widget_svg(theme: ResolvedTheme, width: int = 560, height: int = 340) -> str:
    """Generate an inline SVG rendering of the widget using resolved theme colors."""
    s = theme.semantic
    is_dark = theme.is_dark

    bg = s["background"]
    bg_alt = s["background_alt"]
    surface = s["surface"]
    border = s["border"]
    text_pri = s["text_primary"]
    text_sec = s["text_secondary"]
    text_muted = s["text_muted"]
    accent = s["accent"]
    cpu = s["cpu"]
    mem = s["memory"]
    disk = s["disk"]
    net = s["network"]
    ok = s["success"]
    warn = s["warning"]
    peach = s["high"]
    err = s["error"]

    # Effective background simulating opacity over backdrop
    backdrop = "#0D1117" if is_dark else "#F0F2F5"
    eff_bg = composite_color(bg, backdrop, 0xD9 if is_dark else 0xF2)
    eff_surface = composite_color(surface, eff_bg, 0.9)

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" class="widget-preview-svg">'
    )

    # Defs: drop shadows, clipping paths
    svg.append('<defs>')
    svg.append(
        f'<filter id="shadow-{theme.id}" x="-5%" y="-5%" width="110%" height="115%">'
        f'<feDropShadow dx="0" dy="6" stdDeviation="12" flood-color="#000000" flood-opacity="0.3"/>'
        f'</filter>'
    )
    svg.append('</defs>')

    # Card background (rounded rectangle)
    svg.append(
        f'<rect x="10" y="10" width="{width-20}" height="{height-20}" rx="18" '
        f'fill="{eff_bg}" stroke="{border}" stroke-width="1.2" filter="url(#shadow-{theme.id})"/>'
    )

    # 1. Header Area: Hostname, status dot, uptime, refresh button
    svg.append(f'<circle cx="32" cy="38" r="4.5" fill="{ok}"/>')
    svg.append(
        f'<text x="44" y="42" fill="{text_pri}" font-family="JetBrains Mono, monospace" '
        f'font-size="14" font-weight="bold">atlas</text>'
    )
    svg.append(
        f'<text x="92" y="42" fill="{text_muted}" font-family="JetBrains Mono, monospace" '
        f'font-size="12">· up 11d 2h</text>'
    )

    # Refresh icon
    svg.append(
        f'<g transform="translate({width-48}, 28)">'
        f'<rect width="24" height="24" rx="6" fill="{surface}" stroke="{border}" stroke-width="0.8"/>'
        f'<text x="12" y="17" fill="{text_sec}" font-family="JetBrains Mono, monospace" '
        f'font-size="12" text-anchor="middle">󰑐</text>'
        f'</g>'
    )

    # 2. Metric Ring Cards (CPU, RAM, Disk, Net)
    card_w = (width - 60) // 4
    card_h = 100
    card_y = 62

    metrics = [
        ("CPU", cpu, "24%", "43.7°C", "Load: 0.57"),
        ("RAM", mem, "58%", "9.2 GiB", "16.0 GiB"),
        ("DISK", disk, "41%", "198 GiB", "Healthy"),
        ("NET", net, "↑ 42K", "↓ 128K", "24h: 12G"),
    ]

    for idx, (label, color, val, sub1, sub2) in enumerate(metrics):
        cx_card = 20 + idx * (card_w + 7)
        svg.append(
            f'<rect x="{cx_card}" y="{card_y}" width="{card_w}" height="{card_h}" rx="10" '
            f'fill="{eff_surface}" stroke="{border}" stroke-width="0.8"/>'
        )

        # Header of card
        svg.append(
            f'<text x="{cx_card+10}" y="{card_y+18}" fill="{color}" '
            f'font-family="JetBrains Mono, monospace" font-size="11" font-weight="bold">{label}</text>'
        )

        # Gauge / value
        svg.append(
            f'<text x="{cx_card+card_w-10}" y="{card_y+19}" fill="{text_pri}" '
            f'font-family="JetBrains Mono, monospace" font-size="13" font-weight="bold" text-anchor="end">{val}</text>'
        )

        # Gauge track & fill bar
        bar_y = card_y + 30
        bar_w = card_w - 20
        svg.append(
            f'<rect x="{cx_card+10}" y="{bar_y}" width="{bar_w}" height="5" rx="2.5" fill="{border}"/>'
        )
        fill_pct = 0.24 if idx == 0 else (0.58 if idx == 1 else (0.41 if idx == 2 else 0.70))
        svg.append(
            f'<rect x="{cx_card+10}" y="{bar_y}" width="{bar_w*fill_pct}" height="5" rx="2.5" fill="{color}"/>'
        )

        # Subtext 1 and 2
        svg.append(
            f'<text x="{cx_card+10}" y="{card_y+60}" fill="{text_sec}" '
            f'font-family="JetBrains Mono, monospace" font-size="10">{sub1}</text>'
        )
        svg.append(
            f'<text x="{cx_card+10}" y="{card_y+78}" fill="{text_muted}" '
            f'font-family="JetBrains Mono, monospace" font-size="9.5">{sub2}</text>'
        )

    # 3. Middle Section: Docker Containers / Fastfetch Preview
    mid_y = 176
    mid_w_left = (width - 48) * 0.48
    mid_w_right = (width - 48) * 0.50
    mid_x_right = 20 + mid_w_left + 8
    mid_h = 100

    # Left: Docker mini list
    svg.append(
        f'<rect x="20" y="{mid_y}" width="{mid_w_left}" height="{mid_h}" rx="10" '
        f'fill="{eff_surface}" stroke="{border}" stroke-width="0.8"/>'
    )
    svg.append(
        f'<text x="32" y="{mid_y+18}" fill="{accent}" font-family="JetBrains Mono, monospace" '
        f'font-size="11" font-weight="bold"> Containers</text>'
    )
    svg.append(
        f'<text x="{20+mid_w_left-12}" y="{mid_y+18}" fill="{text_muted}" font-family="JetBrains Mono, monospace" '
        f'font-size="10" text-anchor="end">4 running</text>'
    )

    containers = [
        ("traefik", "0.4%", "38 MiB", ok),
        ("pocketbase", "1.1%", "64 MiB", ok),
        ("adguard-home", "0.2%", "28 MiB", ok),
    ]
    for c_idx, (c_name, c_cpu, c_ram, c_stat) in enumerate(containers):
        row_y = mid_y + 36 + c_idx * 20
        svg.append(f'<circle cx="32" cy="{row_y-3}" r="3" fill="{c_stat}"/>')
        svg.append(
            f'<text x="42" y="{row_y}" fill="{text_pri}" font-family="JetBrains Mono, monospace" font-size="10">{c_name}</text>'
        )
        svg.append(
            f'<text x="{20+mid_w_left-12}" y="{row_y}" fill="{text_sec}" font-family="JetBrains Mono, monospace" font-size="9.5" text-anchor="end">{c_cpu} · {c_ram}</text>'
        )

    # Right: Fastfetch / System Info
    svg.append(
        f'<rect x="{mid_x_right}" y="{mid_y}" width="{mid_w_right}" height="{mid_h}" rx="10" '
        f'fill="{eff_surface}" stroke="{border}" stroke-width="0.8"/>'
    )
    svg.append(
        f'<text x="{mid_x_right+12}" y="{mid_y+18}" fill="{accent}" font-family="JetBrains Mono, monospace" '
        f'font-size="11" font-weight="bold">󰋼 Host Info</text>'
    )

    info_lines = [
        ("OS", "Arch Linux x86_64"),
        ("Kernel", "Linux 6.12.8-arch"),
        ("CPU", "Intel i5-12400 (6C/12T)"),
    ]
    for i_idx, (k_lbl, v_val) in enumerate(info_lines):
        row_y = mid_y + 36 + i_idx * 20
        svg.append(
            f'<text x="{mid_x_right+12}" y="{row_y}" fill="{text_muted}" font-family="JetBrains Mono, monospace" font-size="10">{k_lbl}</text>'
        )
        svg.append(
            f'<text x="{mid_x_right+64}" y="{row_y}" fill="{text_pri}" font-family="JetBrains Mono, monospace" font-size="10">{v_val}</text>'
        )

    # 4. Bottom Tab Bar
    tab_y = height - 44
    tab_w = (width - 48) // 3
    tabs = [
        ("󰍛 Overview", True),
        (" Docker", False),
        ("󰋼 Info", False),
    ]

    for t_idx, (tab_label, is_active) in enumerate(tabs):
        tx = 20 + t_idx * (tab_w + 4)
        t_bg = surface if is_active else theme.inactive_tab_bg
        t_border = border if is_active else "transparent"
        t_text = text_pri if is_active else text_muted
        svg.append(
            f'<rect x="{tx}" y="{tab_y}" width="{tab_w}" height="28" rx="7" '
            f'fill="{t_bg}" stroke="{t_border}" stroke-width="1.0"/>'
        )
        svg.append(
            f'<text x="{tx+tab_w/2}" y="{tab_y+18}" fill="{t_text}" '
            f'font-family="JetBrains Mono, monospace" font-size="11" font-weight="{"bold" if is_active else "normal"}" '
            f'text-anchor="middle">{tab_label}</text>'
        )

    svg.append('</svg>')
    return "".join(svg)


def generate_html_gallery(themes: List[ResolvedTheme], target_path: Path) -> None:
    """Generate a self-contained HTML visual preview gallery."""
    target_path.parent.mkdir(parents=True, exist_ok=True)

    dark_count = sum(1 for t in themes if t.is_dark)
    light_count = sum(1 for t in themes if t.is_light)

    theme_cards_html = []
    for t in themes:
        svg_preview = render_widget_svg(t)
        source = t.source
        repo = source.get("repository", "unknown")
        rev = source.get("revision", "")[:8]
        license_name = source.get("license", "Unknown")

        # Palette color circles
        palette_circles = []
        for role in ("cpu", "memory", "disk", "network", "success", "warning", "high", "error", "accent"):
            color = t.semantic[role]
            palette_circles.append(
                f'<span class="color-dot" style="background-color: {color};" title="{role}: {color}"></span>'
            )
        palette_html = "".join(palette_circles)

        card_html = f"""
        <div class="theme-card" data-mode="{t.mode}" id="theme-{t.id}">
            <div class="theme-header">
                <div class="theme-title-area">
                    <span class="theme-name">{html.escape(t.name)}</span>
                    <span class="theme-id"><code>{html.escape(t.id)}</code></span>
                </div>
                <div class="theme-meta-badges">
                    <span class="badge badge-mode badge-{t.mode}">{t.mode.upper()}</span>
                    <span class="badge badge-license">{html.escape(license_name)}</span>
                </div>
            </div>
            
            <div class="preview-container">
                {svg_preview}
            </div>

            <div class="theme-footer">
                <div class="palette-swatches">
                    {palette_html}
                </div>
                <div class="source-info">
                    <a href="https://github.com/{html.escape(repo)}" target="_blank" rel="noopener">
                        {html.escape(repo)}@{html.escape(rev)}
                    </a>
                </div>
            </div>
        </div>
        """
        theme_cards_html.append(card_html)

    cards_joined = "\n".join(theme_cards_html)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BeszelFetch — Linux Ricing Theme Gallery</title>
    <style>
        :root {{
            --bg-color: #0F1117;
            --surface-color: #161B22;
            --surface-border: #30363D;
            --text-color: #C9D1D9;
            --text-muted: #8B949E;
            --accent-blue: #58A6FF;
            --accent-green: #3FB950;
            --accent-purple: #BC8CFF;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            padding: 32px 24px;
            line-height: 1.5;
        }}

        header {{
            max-width: 1280px;
            margin: 0 auto 32px auto;
            border-bottom: 1px solid var(--surface-border);
            padding-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .brand-title {{
            font-size: 28px;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #FFFFFF;
        }}

        .brand-title span {{
            color: var(--accent-purple);
        }}

        .brand-subtitle {{
            font-size: 14px;
            color: var(--text-muted);
            margin-top: 4px;
        }}

        .controls {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}

        .filter-btn {{
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            color: var(--text-color);
            padding: 8px 14px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.15s ease;
        }}

        .filter-btn:hover, .filter-btn.active {{
            background: var(--surface-border);
            color: #FFFFFF;
            border-color: var(--accent-blue);
        }}

        .catalog-grid {{
            max-width: 1280px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(560px, 1fr));
            gap: 28px;
        }}

        .theme-card {{
            background: var(--surface-color);
            border: 1px solid var(--surface-border);
            border-radius: 14px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 16px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}

        .theme-card:hover {{
            border-color: #58A6FF55;
            transform: translateY(-2px);
        }}

        .theme-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .theme-title-area {{
            display: flex;
            align-items: baseline;
            gap: 10px;
        }}

        .theme-name {{
            font-size: 17px;
            font-weight: 700;
            color: #FFFFFF;
        }}

        .theme-id code {{
            font-size: 12px;
            color: var(--text-muted);
            background: #21262D;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }}

        .theme-meta-badges {{
            display: flex;
            gap: 6px;
        }}

        .badge {{
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge-dark {{
            background: #1F242C;
            color: #79C0FF;
            border: 1px solid #388BFD33;
        }}

        .badge-light {{
            background: #FFF8C522;
            color: #F2CC60;
            border: 1px solid #D2992244;
        }}

        .badge-license {{
            background: #23863622;
            color: #56D364;
            border: 1px solid #23863644;
        }}

        .preview-container {{
            width: 100%;
            display: flex;
            justify-content: center;
            overflow: hidden;
            background: #090B0E;
            border-radius: 10px;
            padding: 12px;
            border: 1px solid #21262D;
        }}

        .widget-preview-svg {{
            width: 100%;
            height: auto;
            max-width: 560px;
            display: block;
        }}

        .theme-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-top: 8px;
            border-top: 1px solid #21262D;
        }}

        .palette-swatches {{
            display: flex;
            gap: 6px;
        }}

        .color-dot {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 2px rgba(0,0,0,0.5);
            cursor: pointer;
        }}

        .source-info a {{
            color: var(--text-muted);
            text-decoration: none;
            font-size: 12px;
            font-family: monospace;
        }}

        .source-info a:hover {{
            color: var(--accent-blue);
            text-decoration: underline;
        }}

        @media (max-width: 640px) {{
            .catalog-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div>
            <div class="brand-title">Beszel<span>Fetch</span> Theme Gallery</div>
            <div class="brand-subtitle">
                {len(themes)} curated Linux/Unix ricing palettes · {dark_count} dark, {light_count} light · Zero-dependency synthetic specimens
            </div>
        </div>
        <div class="controls">
            <button class="filter-btn active" onclick="filterThemes('all', this)">All ({len(themes)})</button>
            <button class="filter-btn" onclick="filterThemes('dark', this)">Dark ({dark_count})</button>
            <button class="filter-btn" onclick="filterThemes('light', this)">Light ({light_count})</button>
        </div>
    </header>

    <main class="catalog-grid">
        {cards_joined}
    </main>

    <script>
        function filterThemes(mode, btn) {{
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.theme-card').forEach(card => {{
                if (mode === 'all' || card.getAttribute('data-mode') === mode) {{
                    card.style.display = 'flex';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""
    target_path.write_text(html_content, encoding="utf-8")
    print(f"✓ Synthetic theme preview gallery generated: {target_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic visual preview specimens for BeszelFetch themes.")
    parser.add_argument("--all", action="store_true", default=True, help="Render all themes in the catalog (default)")
    parser.add_argument("--theme", help="Render only a specific theme ID")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "dist" / "theme-preview.html", help="Output file path")
    args = parser.parse_args()

    all_themes = list_themes()
    if args.theme:
        target_themes = [resolve_theme(args.theme)]
    else:
        target_themes = [resolve_theme(t["id"]) for t in all_themes]

    generate_html_gallery(target_themes, args.output)


if __name__ == "__main__":
    main()
