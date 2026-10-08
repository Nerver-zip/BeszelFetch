"""Regression coverage for the preview's generated-tree/native semantics."""
from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.generate_clip import build_kustom_clip
from scripts.kustom_preview import KustomRenderer, VIEWS, STATES, fixture_globals
from scripts.theme_catalog import list_themes, resolve_theme
from scripts.theme_preview import generate_html_gallery
from scripts.widget_layout import walk

NS = {"s": "http://www.w3.org/2000/svg"}


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = build_kustom_clip(write_outputs=False, theme=resolve_theme("catppuccin-latte"))

    def render(self, view="overview", state="normal", page=0, root=None, width=660, height=424):
        renderer = KustomRenderer(root or self.root, width, height, view, state, page)
        svg = renderer.render()
        return renderer, ET.fromstring(svg)

    def node(self, svg, title):
        return svg.find(f'.//s:g[@data-node="{title}"]', NS)

    def test_masks_clip_values_without_painting_badge_boxes(self):
        _, svg = self.render("containers")
        clips = svg.findall('.//s:clipPath', NS)
        self.assertEqual(len(clips), 15)  # row and two value masks, five rows
        self.assertTrue(all(c.find('s:rect', NS) is not None for c in clips))
        for badge in svg.findall('.//s:g', NS):
            if badge.attrib.get('data-node', '').startswith('Badge'):
                self.assertIsNone(badge.find('s:rect', NS))
        self.assertIn('351.5 MiB', ''.join(svg.itertext()))

    def test_missing_native_binding_remains_visible_to_review(self):
        root = deepcopy(self.root)
        for node in walk(root):
            if node.get('internal_title') in ('NetDownLabel', 'ColLabelCPU', 'ColLabelRAM'):
                node['internal_toggles'].pop('paint_color')
                node.pop('paint_color')
        renderer, svg = self.render(root=root)
        text = self.node(svg, 'NetDownLabel').find('s:text', NS)
        self.assertEqual(text.attrib['fill'], '#FFFFFFFF')
        self.assertTrue(any('NetDownLabel' in warning for warning in renderer.warnings))
        _, docker = self.render('containers', root=root)
        for title in ('ColLabelCPU', 'ColLabelRAM'):
            self.assertEqual(self.node(docker, title).find('s:text', NS).attrib['fill'], '#FFFFFFFF')

    def test_three_separate_views_and_observed_text_visibility(self):
        for view in VIEWS:
            _, svg = self.render(view)
            for title, matching in [('ViewOverview', 'overview'), ('ViewContainers', 'containers'), ('ViewInfo', 'info')]:
                self.assertEqual(self.node(svg, title) is not None, view == matching)
            # Native TextModule ignores layer config_visible; uptime is present.
            self.assertIn('up 15d 9h', ''.join(self.node(svg, 'TimeText').itertext()))

    def test_source_changes_drive_mock_geometry_and_text(self):
        root = deepcopy(self.root)
        nodes = {n.get('internal_title'): n for n in walk(root)}
        nodes['Ring_CPU']['style_size'] = 90
        nodes['NetTitle']['text_expression'] = 'Changed in canonical tree'
        nodes['NetTitle'].get('internal_toggles', {}).pop('text_expression', None)
        renderer, svg = self.render(root=root)
        self.assertEqual(renderer.positions['Ring_CPU'][2:], (98, 98))
        self.assertIn('Changed in canonical tree', ''.join(svg.itertext()))

    def test_all_themes_preserve_rendered_geometry_in_each_view(self):
        baseline = {}
        for entry in list_themes():
            root = build_kustom_clip(write_outputs=False, theme=resolve_theme(entry['id']))
            for view in VIEWS:
                renderer, _ = self.render(view, root=root)
                if view not in baseline:
                    baseline[view] = renderer.positions
                self.assertEqual(renderer.positions, baseline[view], (entry['id'], view))

    def test_stale_fixture_keeps_cached_metrics(self):
        normal, stale = fixture_globals(), fixture_globals('stale')
        for key in ('latest', 'sys_json', 'cnt_json', 'info_sys', 'info_meta', 'info_stats'):
            self.assertEqual(normal[key], stale[key])
        renderer, svg = self.render(state='stale')
        self.assertIn('3.5 / 15.5 GiB', ''.join(svg.itertext()))
        self.assertEqual(renderer.kode.gv('stale'), 1)

    def test_fallback_states_sizes_and_docker_pages(self):
        for state in STATES:
            for width, height in ((480, 376), (660, 424), (720, 440)):
                for view in VIEWS:
                    _, svg = self.render(view, state, width=width, height=height)
                    self.assertEqual(svg.attrib['viewBox'], f'0 0 {width} {height}')
        for page in range(3):
            _, svg = self.render('containers', page=page)
            self.assertIn(f'Page {page + 1} / 3', ''.join(svg.itertext()))
        _, empty = self.render('containers', 'empty')
        self.assertIn('No containers', ''.join(empty.itertext()))

    def test_unsupported_modules_and_bindings_fail_explicitly(self):
        for mutate in (lambda n: n.update(internal_type='UnsupportedModule'),
                       lambda n: n.setdefault('internal_toggles', {}).update(paint_color=42),
                       lambda n: n.update(bitmap_bitmap='unsupported.png', internal_type='BitmapModule')):
            root = deepcopy(self.root)
            mutate(root['viewgroup_items'][0])
            with self.assertRaises(ValueError):
                self.render(root=root)

    def test_gallery_includes_all_views_pages_and_offline_font(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'theme-preview.html'
            generate_html_gallery([resolve_theme('catppuccin-latte'), resolve_theme('nord')], output)
            content = output.read_text()
            self.assertEqual(content.count('class="view-panel"'), 6)
            self.assertEqual(content.count('class="page"'), 10)
            self.assertIn('data:font/ttf;base64,', content)
            self.assertNotIn('<script src=', content)
            self.assertIn('id="theme-nord"', content)


if __name__ == '__main__':
    unittest.main()
