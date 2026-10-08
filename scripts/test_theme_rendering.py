"""Source fidelity, native bindings, readable colors and family identity."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.generate_clip import build_kustom_clip
from scripts.kustom_preview import STATES, KustomRenderer
from scripts.theme_audit import binding_failures, contrast_failures
from scripts.theme_catalog import (
    ACCENT_ROLES, GRAPHIC_CONTRAST, TEXT_CONTRAST, SEMANTIC_TO_GLOBAL,
    blend_rgb, contrast_ratio, list_themes, load_theme, resolve_theme,
)
from scripts.theme_sources import MANIFEST, UPSTREAM, canonical_palette, check_palette
from scripts.widget_layout import walk
from scripts.widget_theme import apply_theme


def without_paint(node):
    """Compare everything except paint bindings, preserving geometry and data."""
    paints = {'paint_color', 'color_fgcolor', 'color_bgcolor'}
    if isinstance(node, list):
        return [without_paint(item) for item in node]
    if not isinstance(node, dict):
        return node
    result = {}
    for key, value in node.items():
        if key in paints:
            continue
        if key in ('internal_globals', 'internal_toggles', 'internal_formulas'):
            value = {k: v for k, v in value.items() if k not in paints}
            if not value:
                continue
        result[key] = without_paint(value)
    return result


class SourceTests(unittest.TestCase):
    def test_catalog_matches_exact_pinned_extraction(self):
        for theme in list_themes():
            data = load_theme(theme['id'])
            check_palette(data)
            available = set(data['colors']) | set(data.get('derived_colors', {}))
            self.assertTrue(all(ref in available for ref in data['semantic'].values()), theme['id'])

    def test_support_and_license_snapshots_are_pinned(self):
        manifest = json.loads(MANIFEST.read_text())
        for section in ('sources', 'support_sources', 'licenses'):
            for source in manifest[section].values():
                self.assertRegex(source['revision'], r'^[0-9a-f]{40}$')
                self.assertEqual(hashlib.sha256((UPSTREAM / source['file']).read_bytes()).hexdigest(), source['sha256'])

    def test_corrected_named_colors(self):
        expected = {
            'kanagawa-lotus': {'lotusWhite3': '#F2ECBC', 'lotusViolet4': '#624C83'},
            'tokyo-night-day': {'teal': '#118C74', 'fg': '#3760BF'},
            'one-light': {'hue-2': '#4078F2', 'hue-3': '#A626A4'},
            'oxocarbon-dark': {'base01': '#262626', 'base05': '#F2F2F2'},
        }
        for theme, colors in expected.items():
            canonical, _ = canonical_palette(theme)
            for key, color in colors.items():
                self.assertEqual(canonical[key], color)

    def test_wrong_named_color_and_metadata_are_rejected(self):
        for mutate in (lambda d: d['colors'].update(lotusViolet4='#FFFFFF'),
                       lambda d: d['source'].update(revision='HEAD')):
            data = load_theme('kanagawa-lotus')
            mutate(data)
            with self.assertRaises(ValueError):
                check_palette(data)


class NativeColorTests(unittest.TestCase):
    def test_all_themes_all_views_states_and_sizes_have_readable_colors(self):
        for theme in list_themes():
            root = build_kustom_clip(write_outputs=False, theme=theme['id'])
            self.assertEqual(binding_failures(root), [], theme['id'])
            self.assertEqual(contrast_failures(root, STATES, ((480, 376), (660, 424))), [], theme['id'])

    def test_inactive_binding_is_rejected_even_on_dark_background(self):
        root = build_kustom_clip(write_outputs=False)
        label = next(n for n in walk(root) if n.get('internal_title') == 'NetDownLabel')
        label['internal_toggles'].pop('paint_color')
        self.assertIn('NetDownLabel.paint_color', binding_failures(root))

    def test_color_pass_preserves_geometry_data_and_actions(self):
        root = build_kustom_clip(write_outputs=False)
        before = without_paint(root)
        apply_theme(root)
        self.assertEqual(before, without_paint(root))

    def test_resolved_colors_leave_canonical_palette_intact(self):
        for theme in list_themes():
            data = load_theme(theme['id'])
            before = deepcopy(data)
            resolved = resolve_theme(data)
            self.assertEqual(data, before)
            self.assertEqual(resolved.raw_colors, data['colors'])
            for role in ACCENT_ROLES:
                for bg in resolved.text_backgrounds:
                    self.assertGreaterEqual(contrast_ratio(resolved.text_colors[role], bg), TEXT_CONTRAST)
                color = resolved.kustom_colors[SEMANTIC_TO_GLOBAL[role]]
                for bg in resolved.graphic_backgrounds:
                    self.assertGreaterEqual(contrast_ratio(color, bg), GRAPHIC_CONTRAST)

    def test_light_metric_text_has_separate_readable_companion(self):
        theme = resolve_theme('kanagawa-lotus')
        self.assertNotEqual(theme.kustom_colors['c_ram'], theme.kustom_colors['c_ram_text'])
        root = build_kustom_clip(write_outputs=False, theme=theme)
        nodes = {n.get('internal_title'): n for n in walk(root)}
        self.assertEqual(nodes['Ring_Memory']['internal_globals']['color_fgcolor'], 'c_ram')
        self.assertEqual(nodes['Title_Memory']['internal_globals']['paint_color'], 'c_ram_text')

    def test_navigation_header_and_actions_use_primary_accent(self):
        root = build_kustom_clip(write_outputs=False)
        nodes = {n.get('internal_title'): n for n in walk(root)}
        self.assertEqual(nodes['HostnameText']['internal_globals']['paint_color'], 'c_accent_text')
        for view, title in (('overview', 'TabOverview'), ('containers', 'TabContainers'), ('info', 'TabInfo')):
            renderer = KustomRenderer(root, view=view)
            label = next(n for n in nodes[title]['viewgroup_items'] if n['internal_type'] == 'TextModule')
            self.assertEqual(renderer.prop(label, 'paint_color'), root['globals_list']['c_accent_text']['value'])

    def test_family_assignments_are_distinct_and_siblings_intentional(self):
        cpu_keys = {t: load_theme(t)['semantic']['cpu'] for t in ('gruvbox-dark', 'monokai', 'rose-pine', 'kanagawa-wave', 'nord')}
        self.assertEqual(len(set(cpu_keys.values())), 5)
        for prefix, ids in (
            ('catppuccin', ('mocha', 'macchiato', 'frappe', 'latte')),
            ('tokyo-night', ('', 'storm', 'moon', 'day')),
            ('ayu', ('dark', 'light', 'mirage')),
        ):
            roles = []
            for suffix in ids:
                data = load_theme(prefix + ('-' + suffix if suffix else ''))
                roles.append({k: data['semantic'][k] for k in ('accent', 'cpu', 'memory', 'disk', 'network')})
            self.assertTrue(all(r == roles[0] for r in roles))


if __name__ == '__main__':
    unittest.main()
