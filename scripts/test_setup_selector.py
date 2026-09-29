#!/usr/bin/env python3
"""
Unit tests for the setup.py ThemeSelector state machine and interactive UX.
"""

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from setup import ThemeSelector, interactive_theme_select
from scripts.theme_catalog import DEFAULT_THEME_ID, list_themes


class TestSetupThemeSelector(unittest.TestCase):
    """Tests ThemeSelector keyboard handling, viewport scrolling, and rendering."""

    def setUp(self):
        self.themes = list_themes()
        self.selector = ThemeSelector(self.themes, default_id=DEFAULT_THEME_ID, viewport_size=8)

    def test_initial_state_defaults_to_catppuccin_mocha(self):
        selected = self.selector.get_selected()
        self.assertEqual(selected["id"], DEFAULT_THEME_ID)
        self.assertEqual(selected["id"], "catppuccin-mocha")

    def test_custom_default_initialization(self):
        drac_selector = ThemeSelector(self.themes, default_id="dracula", viewport_size=8)
        self.assertEqual(drac_selector.get_selected()["id"], "dracula")

    def test_navigation_down_and_up(self):
        initial_idx = self.selector.selected_index
        self.selector.move_down()
        self.assertEqual(self.selector.selected_index, initial_idx + 1)
        self.selector.move_up()
        self.assertEqual(self.selector.selected_index, initial_idx)

    def test_upper_and_lower_boundaries(self):
        # Move up to 0
        for _ in range(50):
            self.selector.move_up()
        self.assertEqual(self.selector.selected_index, 0)
        self.assertEqual(self.selector.scroll_offset, 0)
        # Attempt moving up past 0
        self.selector.move_up()
        self.assertEqual(self.selector.selected_index, 0)

        # Move down to end
        for _ in range(len(self.themes) + 10):
            self.selector.move_down()
        self.assertEqual(self.selector.selected_index, len(self.themes) - 1)
        self.assertEqual(self.selector.scroll_offset, len(self.themes) - self.selector.viewport_size)
        # Attempt moving down past end
        self.selector.move_down()
        self.assertEqual(self.selector.selected_index, len(self.themes) - 1)

    def test_scrolling_viewport_window(self):
        # Start at 0
        selector = ThemeSelector(self.themes, default_id=self.themes[0]["id"], viewport_size=5)
        self.assertEqual(selector.selected_index, 0)
        self.assertEqual(selector.scroll_offset, 0)

        # Move down 5 times -> should shift scroll_offset
        for _ in range(5):
            selector.move_down()
        self.assertEqual(selector.selected_index, 5)
        self.assertGreater(selector.scroll_offset, 0)
        self.assertLessEqual(selector.selected_index, selector.scroll_offset + selector.viewport_size - 1)

    def test_render_output_contains_active_marker_and_swatches(self):
        lines = self.selector.render()
        text = "\n".join(lines)
        self.assertIn("Catppuccin Mocha", text)
        self.assertIn("❯", text)
        self.assertIn("Theme Selection", text)

    def test_non_tty_fallback(self):
        import unittest.mock
        with unittest.mock.patch("sys.stdin.isatty", return_value=False):
            result = interactive_theme_select(self.themes, default_id="nord")
            self.assertEqual(result, "nord")

    def test_interactive_key_injection_enter(self):
        import unittest.mock
        with unittest.mock.patch("sys.stdin.isatty", return_value=True), \
             unittest.mock.patch("sys.stdin.fileno", return_value=0), \
             unittest.mock.patch("termios.tcgetattr", return_value=[]), \
             unittest.mock.patch("termios.tcsetattr", return_value=None), \
             unittest.mock.patch("tty.setraw", return_value=None), \
             unittest.mock.patch("sys.stdin.read", side_effect=["\r"]):
            result = interactive_theme_select(self.themes, default_id="dracula")
            self.assertEqual(result, "dracula")

    def test_interactive_key_injection_arrow_down_enter(self):
        import unittest.mock
        inputs = ["\x1b", "[", "B", "\r"]
        with unittest.mock.patch("sys.stdin.isatty", return_value=True), \
             unittest.mock.patch("sys.stdin.fileno", return_value=0), \
             unittest.mock.patch("termios.tcgetattr", return_value=[]), \
             unittest.mock.patch("termios.tcsetattr", return_value=None), \
             unittest.mock.patch("tty.setraw", return_value=None), \
             unittest.mock.patch("sys.stdin.read", side_effect=inputs):
            first_id = self.themes[0]["id"]
            second_id = self.themes[1]["id"]
            result = interactive_theme_select(self.themes, default_id=first_id)
            self.assertEqual(result, second_id)


if __name__ == "__main__":
    unittest.main()

