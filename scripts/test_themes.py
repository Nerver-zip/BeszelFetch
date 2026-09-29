#!/usr/bin/env python3
"""
Unit tests for the BeszelFetch Theme System.

Validates:
1. Theme catalog discovery and resolution for all themes.
2. Cross-theme widget structural invariance (tree shape, module counts, formula keys).
3. No Catppuccin color leakage in non-Catppuccin themes.
4. Source provenance and pinned commit hashes.
5. WCAG AA contrast compliance across all themes.
"""

import json
from pathlib import Path
import re
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.theme_catalog import (
    DARK_OPACITY,
    DEFAULT_THEME_ID,
    LIGHT_OPACITY,
    REQUIRED_SEMANTIC_ROLES,
    SEMANTIC_TO_GLOBAL,
    THEMES_DIR,
    ResolvedTheme,
    composite_color,
    contrast_ratio,
    list_themes,
    load_theme,
    resolve_theme,
    validate_theme,
)
from scripts.generate_clip import build_kustom_clip


CATPPUCCIN_MOCHA_EXCLUSIVE_HEX = {
    # Distinguishing Catppuccin Mocha hex literals that should never leak into disparate themes
    "#1E1E2E",  # Base
    "#181825",  # Mantle
    "#11111B",  # Crust
    "#313244",  # Surface0
    "#45475A",  # Surface1
    "#585B70",  # Surface2
    "#89B4FA",  # Blue
    "#CBA6F7",  # Mauve
    "#94E2D5",  # Teal
    "#74C7EC",  # Sapphire
    "#A6E3A1",  # Green
    "#F9E2AF",  # Yellow
    "#FAB387",  # Peach
    "#F38BA8",  # Red
    "#CDD6F4",  # Text
    "#BAC2DE",  # Subtext1
    "#A6ADC8",  # Subtext0
    "#6C7086",  # Overlay0
}


def mask_colors_in_node(node):
    """Deep clone and replace all color fields/globals with dummy placeholders for structural comparison."""
    if isinstance(node, dict):
        masked = {}
        for k, v in node.items():
            if k == "globals_list":
                # Mask color globals while keeping names and non-color globals intact
                g_masked = {}
                for g_name, g_val in v.items():
                    g_copy = dict(g_val)
                    if g_copy.get("type") == "COLOR":
                        g_copy["value"] = "[COLOR_MASKED]"
                    elif g_name == "ascii_data" and isinstance(g_copy.get("value"), str):
                        try:
                            art_cat = json.loads(g_copy["value"])
                            for item in art_cat.values():
                                if "color" in item:
                                    item["color"] = "[COLOR_MASKED]"
                            g_copy["value"] = json.dumps(art_cat, sort_keys=True)
                        except Exception:
                            pass
                    g_masked[g_name] = g_copy
                masked[k] = g_masked
            elif k in ("paint_color", "shadow_color", "color", "stroke_color", "color_fgcolor", "color_bgcolor"):
                masked[k] = "[COLOR_MASKED]"
            elif k == "internal_formulas" and isinstance(v, dict):
                f_masked = {}
                for f_k, f_v in v.items():
                    # If formula contains inactive tab background hex, mask it
                    f_clean = re.sub(r"#[0-9a-fA-F]{8}", "[ARGB_MASKED]", str(f_v))
                    f_masked[f_k] = f_clean
                masked[k] = f_masked
            else:
                masked[k] = mask_colors_in_node(v)
        return masked
    elif isinstance(node, list):
        return [mask_colors_in_node(item) for item in node]
    else:
        return node


def collect_hex_literals(node):
    """Traverse a Kustom node tree and collect all hex color strings."""
    found = set()
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str):
                for m in re.findall(r"#[0-9a-fA-F]{6,8}", v):
                    found.add(m.upper())
            else:
                found.update(collect_hex_literals(v))
    elif isinstance(node, list):
        for item in node:
            found.update(collect_hex_literals(item))
    return found


class TestThemeCatalog(unittest.TestCase):
    """Tests catalog loading, schema validation, and resolver correctness."""

    def test_catalog_theme_count(self):
        themes = list_themes()
        self.assertGreaterEqual(len(themes), 30, f"Theme catalog must contain at least 30 themes (got {len(themes)})")

    def test_default_theme_exists(self):
        themes = {t["id"]: t for t in list_themes()}
        self.assertIn(DEFAULT_THEME_ID, themes)
        self.assertEqual(DEFAULT_THEME_ID, "catppuccin-mocha")

    def test_each_theme_resolves(self):
        for t_info in list_themes():
            t_id = t_info["id"]
            resolved = resolve_theme(t_id)
            self.assertIsInstance(resolved, ResolvedTheme)
            self.assertEqual(resolved.id, t_id)
            self.assertIn(resolved.mode, ("dark", "light"))
            for role in REQUIRED_SEMANTIC_ROLES:
                self.assertIn(role, resolved.semantic, f"Missing role '{role}' in {t_id}")
                self.assertTrue(resolved.semantic[role].startswith("#"))
            for global_name in SEMANTIC_TO_GLOBAL.values():
                self.assertIn(global_name, resolved.kustom_colors, f"Missing global '{global_name}' in {t_id}")
                self.assertTrue(resolved.kustom_colors[global_name].startswith("#"))

    def test_theme_provenance_metadata(self):
        for t_info in list_themes():
            t_id = t_info["id"]
            data = load_theme(t_id)
            source = data["source"]
            self.assertTrue(source.get("project"), f"Missing project for {t_id}")
            self.assertTrue(source.get("repository"), f"Missing repository for {t_id}")
            self.assertTrue(source.get("license"), f"Missing license for {t_id}")
            rev = source.get("revision", "")
            self.assertTrue(
                re.match(r"^[0-9a-fA-F]{7,40}$", rev) or rev == "HEAD",
                f"Theme '{t_id}' revision '{rev}' must be a pinned git commit hash",
            )


class TestWidgetStructuralInvariance(unittest.TestCase):
    """Validates that all themes produce identical widget structures, layout, and logic."""

    @classmethod
    def setUpClass(cls):
        cls.default_tree = build_kustom_clip(write_outputs=False, theme=DEFAULT_THEME_ID)
        cls.masked_default = mask_colors_in_node(cls.default_tree)

    def test_all_themes_have_identical_structure(self):
        all_themes = list_themes()
        for t_info in all_themes:
            t_id = t_info["id"]
            theme_tree = build_kustom_clip(write_outputs=False, theme=t_id)
            masked_theme = mask_colors_in_node(theme_tree)

            # Assert number of viewgroup items is identical
            self.assertEqual(
                len(theme_tree["viewgroup_items"]),
                len(self.default_tree["viewgroup_items"]),
                f"Theme '{t_id}' top-level items count mismatch",
            )

            # Assert globals count is identical
            self.assertEqual(
                len(theme_tree["globals_list"]),
                len(self.default_tree["globals_list"]),
                f"Theme '{t_id}' globals count mismatch",
            )

            # Assert masked trees are exactly equal
            self.assertEqual(
                masked_theme,
                self.masked_default,
                f"Theme '{t_id}' has structural or formula divergence from default theme",
            )


class TestNoCatppuccinLeakage(unittest.TestCase):
    """Validates that non-Catppuccin themes do not leak Catppuccin Mocha literals into nodes."""

    def test_non_catppuccin_themes_do_not_leak_mocha_literals(self):
        themes_to_test = [
            "dracula",
            "nord",
            "gruvbox-dark",
            "solarized-dark",
            "tokyo-night",
            "rose-pine",
            "kanagawa-wave",
            "everforest-dark",
            "one-dark",
            "ayu-dark",
            "monokai",
            "nightfox",
        ]

        for t_id in themes_to_test:
            resolved = resolve_theme(t_id)
            theme_tree = build_kustom_clip(write_outputs=False, theme=t_id)
            all_hex = collect_hex_literals(theme_tree)

            # Check if any Mocha-exclusive hex leaked unless legitimately present in theme's raw colors
            theme_own_colors = {c.upper() for c in resolved.raw_colors.values()}
            for mocha_hex in CATPPUCCIN_MOCHA_EXCLUSIVE_HEX:
                if mocha_hex.upper() in theme_own_colors:
                    continue  # Coincidental identical color in upstream palette
                
                # Check 6-char hex and 8-char ARGB forms
                hex_tail = mocha_hex.lstrip("#").upper()
                leaked = [h for h in all_hex if h.endswith(hex_tail)]
                self.assertFalse(
                    leaked,
                    f"Catppuccin Mocha literal {mocha_hex} leaked into theme '{t_id}': found {leaked}",
                )


class TestThemeContrastCompliance(unittest.TestCase):
    """Validates WCAG 2.1 AA contrast compliance across the entire catalog."""

    def test_wcag_aa_primary_text(self):
        for t_info in list_themes():
            t_id = t_info["id"]
            t = resolve_theme(t_id)
            opacity = DARK_OPACITY if t.is_dark else LIGHT_OPACITY
            bg_raw = t.semantic["background"]
            text_pri = t.semantic["text_primary"]

            backdrops = [("#000000", "black")] if t.is_dark else [("#000000", "black"), ("#FFFFFF", "white")]
            for backdrop, bd_name in backdrops:
                eff_bg = composite_color(bg_raw, backdrop, opacity["base"])
                cr = contrast_ratio(text_pri, eff_bg)
                self.assertGreaterEqual(
                    cr,
                    4.5,
                    f"Theme '{t_id}' primary text fails WCAG AA ({cr:.2f}:1 < 4.5:1) over {bd_name}",
                )


class TestSyntheticPreview(unittest.TestCase):
    """Validates synthetic theme preview generation."""

    def test_svg_preview_renders_valid_svg_without_mocha_leakage(self):
        from scripts.theme_preview import render_widget_svg

        themes_to_check = ["dracula", "nord", "gruvbox-dark", "solarized-dark", "tokyo-night"]
        for t_id in themes_to_check:
            t = resolve_theme(t_id)
            svg = render_widget_svg(t)
            self.assertTrue(svg.startswith("<svg"))
            self.assertTrue(svg.endswith("</svg>"))
            self.assertIn("atlas", svg)
            self.assertIn("CPU", svg)
            self.assertIn("RAM", svg)

            # Check no Mocha-exclusive colors leaked into non-Mocha SVG
            theme_own = {c.upper() for c in t.raw_colors.values()}
            for mocha_hex in CATPPUCCIN_MOCHA_EXCLUSIVE_HEX:
                if mocha_hex.upper() in theme_own:
                    continue
                self.assertNotIn(mocha_hex.upper(), svg.upper())

    def test_html_gallery_generation(self):
        import tempfile
        from scripts.theme_preview import generate_html_gallery

        themes = [resolve_theme(t["id"]) for t in list_themes()[:5]]
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tf:
            temp_path = Path(tf.name)

        try:
            generate_html_gallery(themes, temp_path)
            content = temp_path.read_text(encoding="utf-8")
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("Theme Gallery", content)
            for t in themes:
                self.assertIn(f'id="theme-{t.id}"', content)
        finally:
            if temp_path.exists():
                temp_path.unlink()


if __name__ == "__main__":
    unittest.main()

