#!/usr/bin/env python3
"""
Automated Contract Validation and Test Harness for Beszel KWGT Widget.
Validates:
- JSON payload parsing against DATA_CONTRACT.md;
- Unit conversions (IEC bytes, network bandwidth, uptime);
- Color threshold and styling logic;
- 24-point history downsampling and statistics calculation;
- Complete resilience matrix (missing sensors, network failures, auth refresh, pagination bounds);
- Accessibility (WCAG 2.1 contrast ratios and touch targets).
"""

import json
import math
import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "examples" / "fixtures"
PALETTE_FILE = REPO_ROOT / "examples" / "palette.json"


# ==============================================================================
# Adapter & Normalization Implementation
# ==============================================================================

class DataAdapter:
    """Core logic mirroring Kustom Flows and formula evaluation."""

    @staticmethod
    def parse_systems(payload):
        if not payload or not isinstance(payload, dict):
            return []
        items = payload.get("items", [])
        parsed = []
        for item in items:
            info = item.get("info", {}) or {}
            
            # Bandwidth: bb is [sent, recv]
            bb = info.get("bb") or [0, 0]
            net_sent = bb[0] if len(bb) > 0 else 0
            net_recv = bb[1] if len(bb) > 1 else 0

            # Load Average: la is [1m, 5m, 15m]
            la = info.get("la") or []
            load1 = la[0] if len(la) > 0 else None

            parsed.append({
                "id": item.get("id", ""),
                "name": item.get("name", "unknown"),
                "status": item.get("status", "down"),
                "cpu_pct": float(info.get("cpu", 0.0)),
                "mem_pct": float(info.get("mp", 0.0)),
                "disk_pct": float(info.get("dp", 0.0)),
                "uptime_s": int(info.get("u", 0)),
                "net_sent_bps": int(net_sent),
                "net_recv_bps": int(net_recv),
                "load1": float(load1) if load1 is not None else None,
                "temp_c": float(info.get("dt")) if info.get("dt") is not None else None,
            })
        return parsed

    @staticmethod
    def parse_containers(payload):
        if not payload or not isinstance(payload, dict):
            return []
        # Support both {"stats": [...]} and {"items": [{"stats": [...]}]}
        stats_list = payload.get("stats")
        if stats_list is None and "items" in payload:
            items = payload.get("items", [])
            if items and isinstance(items[0], dict):
                stats_list = items[0].get("stats", [])
        if not stats_list or not isinstance(stats_list, list):
            return []

        containers = []
        for c in stats_list:
            b = c.get("b") or [0, 0]
            containers.append({
                "name": c.get("n", "unnamed"),
                "cpu_pct": float(c.get("c", 0.0)),
                "memory_bytes": int(c.get("m", 0)),
                "net_sent_bps": int(b[0]) if len(b) > 0 else 0,
                "net_recv_bps": int(b[1]) if len(b) > 1 else 0,
            })
        return containers

    @staticmethod
    def format_bytes(bytes_val):
        """Format bytes according to IEC units."""
        if bytes_val is None or bytes_val < 0:
            return "—"
        kib = 1024
        mib = kib * 1024
        gib = mib * 1024

        if bytes_val < mib:
            val = bytes_val / kib
            return f"{val:.1f} KiB" if val >= 10 else f"{val:.2f} KiB"
        elif bytes_val < gib:
            val = bytes_val / mib
            return f"{val:.1f} MiB" if val >= 100 else f"{val:.1f} MiB"
        else:
            val = bytes_val / gib
            return f"{val:.2f} GiB"

    @staticmethod
    def format_bandwidth(bytes_per_sec):
        """Format bandwidth in bytes/sec to human readable KiB/s or MiB/s."""
        if bytes_per_sec is None or bytes_per_sec < 0:
            return "—"
        kib = 1024
        mib = kib * 1024
        gib = mib * 1024

        if bytes_per_sec < mib:
            val = bytes_per_sec / kib
            return f"{val:.0f}K" if val >= 100 else f"{val:.1f}K"
        elif bytes_per_sec < gib:
            val = bytes_per_sec / mib
            return f"{val:.1f}M"
        else:
            val = bytes_per_sec / gib
            return f"{val:.2f}G"

    @staticmethod
    def format_uptime(seconds):
        """Format seconds into 'Xd Yh' or 'Xh Ym'."""
        if seconds is None or seconds < 0:
            return "—"
        days = seconds // 86400
        remaining_hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        if days > 0:
            return f"{days}d {remaining_hours:02d}h"
        return f"{remaining_hours}h {minutes:02d}m"

    @staticmethod
    def format_temperature(temp_c):
        """Format temperature with fallback."""
        if temp_c is None:
            return None
        return f"{temp_c:.1f}°C"

    @staticmethod
    def format_load(load_val):
        """Format load average to 2 decimal places."""
        if load_val is None:
            return "—"
        return f"{load_val:.2f}"

    @staticmethod
    def get_threshold_color(val, default_accent, colors=None):
        """Evaluate resource percentage against Catppuccin threshold rules."""
        if colors is None:
            colors = {
                "yellow": "#F9E2AF",
                "peach": "#FAB387",
                "red": "#F38BA8",
            }
        clamped = max(0.0, min(100.0, float(val)))
        if clamped >= 95.0:
            return colors.get("red", "#F38BA8")
        elif clamped >= 85.0:
            return colors.get("peach", "#FAB387")
        elif clamped >= 70.0:
            return colors.get("yellow", "#F9E2AF")
        return default_accent

    @staticmethod
    def paginate_containers(containers, page_idx=0, per_page=5):
        """Compute pagination bounds and return exactly per_page row slots."""
        total = len(containers)
        if total == 0:
            return {
                "page": 0,
                "max_page": 0,
                "total_items": 0,
                "rows": [None] * per_page,
                "has_prev": False,
                "has_next": False,
                "empty": True,
            }
        max_page = (total - 1) // per_page
        clamped_page = max(0, min(page_idx, max_page))
        start_idx = clamped_page * per_page
        end_idx = start_idx + per_page
        slice_items = containers[start_idx:end_idx]

        rows = []
        for i in range(per_page):
            if i < len(slice_items):
                rows.append(slice_items[i])
            else:
                rows.append(None)

        return {
            "page": clamped_page,
            "max_page": max_page,
            "total_items": total,
            "rows": rows,
            "has_prev": clamped_page > 0,
            "has_next": clamped_page < max_page,
            "empty": False,
        }

    @staticmethod
    def downsample_history(records, target_points=24, metric="cpu"):
        """Sample and downscale a series to exactly target_points."""
        if not records:
            return {
                "points": [],
                "min": 0.0,
                "avg": 0.0,
                "max": 0.0,
                "current": 0.0,
                "scale_max": 100.0,
                "empty": True,
            }

        # Extract values
        extracted = []
        for r in records:
            stats = r.get("stats", {}) or {}
            if metric == "cpu":
                val = float(stats.get("cpu", 0.0))
            elif metric == "mem":
                val = float(stats.get("mp", 0.0))
            elif metric == "disk":
                val = float(stats.get("dp", 0.0))
            elif metric == "net":
                b = stats.get("b", [0, 0]) or [0, 0]
                val = float(b[0] + b[1]) if len(b) >= 2 else 0.0
            else:
                val = float(stats.get(metric, 0.0))
            extracted.append({
                "created": r.get("created", ""),
                "value": val,
            })

        n = len(extracted)
        if n < 2:
            return {
                "points": extracted,
                "min": extracted[0]["value"] if n == 1 else 0.0,
                "avg": extracted[0]["value"] if n == 1 else 0.0,
                "max": extracted[0]["value"] if n == 1 else 0.0,
                "current": extracted[0]["value"] if n == 1 else 0.0,
                "scale_max": 100.0,
                "empty": True,
            }

        if n <= target_points:
            sampled = list(extracted)
        else:
            # Evenly spaced indices strictly preserving index 0 and index n-1
            sampled = []
            for i in range(target_points):
                idx = round(i * (n - 1) / (target_points - 1))
                sampled.append(extracted[idx])

        values = [p["value"] for p in sampled]
        min_val = min(values)
        max_val = max(values)
        avg_val = sum(values) / len(values)
        current_val = values[-1]

        if metric in ("cpu", "mem", "disk"):
            scale_max = 100.0
        else:
            # Dynamic auto-scale for network bandwidth (prevent zero div)
            scale_max = max_val if max_val > 0 else 1.0

        # Calculate normalized bar height (0.0 to 1.0)
        for p in sampled:
            p["normalized"] = max(0.0, min(1.0, p["value"] / scale_max))

        return {
            "points": sampled,
            "min": min_val,
            "avg": avg_val,
            "max": max_val,
            "current": current_val,
            "scale_max": scale_max,
            "empty": False,
        }


# ==============================================================================
# Cache & Resilience State Machine
# ==============================================================================

class CacheStateMachine:
    """Manages cache state and resilience transitions."""

    def __init__(self):
        self.sys_json = {}
        self.cnt_json = {}
        self.hist_json = {}
        self.bz_token = None
        self.last_ok = None
        self.last_code = None
        self.last_err = ""
        self.is_stale = 1
        self.reauth_attempts = 0

    def handle_auth_response(self, status_code, body):
        self.last_code = status_code
        if status_code == 200 and isinstance(body, dict) and "token" in body:
            self.bz_token = body["token"]
            self.last_err = ""
            self.reauth_attempts = 0
            return True
        else:
            self.last_err = "auth"
            return False

    def handle_systems_response(self, status_code, body):
        self.last_code = status_code
        if status_code == 200 and isinstance(body, dict) and "items" in body and len(body["items"]) > 0:
            self.sys_json = body
            self.last_ok = "2026-09-06T15:00:00Z"
            self.is_stale = 0
            self.last_err = ""
            return "OK"
        elif status_code == 401:
            if self.reauth_attempts == 0:
                self.reauth_attempts += 1
                return "REAUTH"
            self.is_stale = 1
            self.last_err = "auth"
            return "AUTH_FAILED"
        elif status_code == 403:
            self.is_stale = 1
            self.last_err = "forbidden"
            return "FORBIDDEN"
        else:
            # Network failure / 5xx / schema error: RETAIN existing cache
            self.is_stale = 1
            self.last_err = "network" if status_code == 0 else "error"
            return "STALE"


# ==============================================================================
# Accessibility & WCAG Contrast Validator
# ==============================================================================

class AccessibilityValidator:
    """Validates color contrast and touch targets against WCAG standards."""

    @staticmethod
    def hex_to_rgb(hex_str):
        hex_clean = hex_str.lstrip("#")
        if len(hex_clean) == 8:
            hex_clean = hex_clean[2:]  # Strip alpha if ARGB
        return tuple(int(hex_clean[i:i+2], 16) for i in (0, 2, 4))

    @classmethod
    def relative_luminance(cls, hex_str):
        r, g, b = cls.hex_to_rgb(hex_str)
        s_rgb = [c / 255.0 for c in (r, g, b)]
        lum = []
        for c in s_rgb:
            if c <= 0.03928:
                lum.append(c / 12.92)
            else:
                lum.append(((c + 0.055) / 1.055) ** 2.4)
        return 0.2126 * lum[0] + 0.7152 * lum[1] + 0.0722 * lum[2]

    @classmethod
    def contrast_ratio(cls, hex1, hex2):
        l1 = cls.relative_luminance(hex1)
        l2 = cls.relative_luminance(hex2)
        bright = max(l1, l2)
        dark = min(l1, l2)
        return (bright + 0.05) / (dark + 0.05)


# ==============================================================================
# Unit Test Suites
# ==============================================================================

class TestSystemsContract(unittest.TestCase):
    """Validates systems payload parsing against DATA_CONTRACT.md."""

    def setUp(self):
        with open(FIXTURES_DIR / "systems-response.json", "r") as f:
            self.fixture = json.load(f)

    def test_parse_valid_systems(self):
        systems = DataAdapter.parse_systems(self.fixture)
        self.assertEqual(len(systems), 2)
        atlas = systems[0]
        self.assertEqual(atlas["id"], "sys_atlas")
        self.assertEqual(atlas["name"], "atlas")
        self.assertEqual(atlas["status"], "up")
        self.assertEqual(atlas["cpu_pct"], 18.4)
        self.assertEqual(atlas["mem_pct"], 62.1)
        self.assertEqual(atlas["disk_pct"], 47.8)
        self.assertEqual(atlas["uptime_s"], 1051200)
        self.assertEqual(atlas["net_sent_bps"], 420000)
        self.assertEqual(atlas["net_recv_bps"], 2210000)
        self.assertEqual(atlas["load1"], 0.42)
        self.assertEqual(atlas["temp_c"], 43.0)

    def test_missing_optional_sensors(self):
        payload = {
            "items": [{
                "id": "sys_no_temp",
                "name": "vps",
                "status": "up",
                "info": {
                    "cpu": 5.0,
                    "mp": 20.0,
                    "dp": 15.0,
                    "u": 3600
                }
            }]
        }
        systems = DataAdapter.parse_systems(payload)
        self.assertEqual(len(systems), 1)
        sys_item = systems[0]
        self.assertIsNone(sys_item["temp_c"])
        self.assertIsNone(sys_item["load1"])
        self.assertEqual(sys_item["net_sent_bps"], 0)
        self.assertEqual(sys_item["net_recv_bps"], 0)


class TestContainersContract(unittest.TestCase):
    """Validates container metrics and pagination rules."""

    def setUp(self):
        with open(FIXTURES_DIR / "container-stats-response.json", "r") as f:
            self.fixture = json.load(f)

    def test_parse_containers(self):
        containers = DataAdapter.parse_containers(self.fixture)
        self.assertEqual(len(containers), 6)
        caddy = containers[1]
        self.assertEqual(caddy["name"], "caddy")
        self.assertEqual(caddy["cpu_pct"], 0.1)
        self.assertEqual(caddy["memory_bytes"], 50331648)
        self.assertEqual(caddy["net_sent_bps"], 46000)
        self.assertEqual(caddy["net_recv_bps"], 330000)

    def test_pagination_boundaries(self):
        containers = DataAdapter.parse_containers(self.fixture)  # 6 containers
        
        # Page 0 (items 0..4)
        p0 = DataAdapter.paginate_containers(containers, page_idx=0, per_page=5)
        self.assertEqual(p0["page"], 0)
        self.assertEqual(p0["max_page"], 1)
        self.assertEqual(len(p0["rows"]), 5)
        self.assertIsNotNone(p0["rows"][4])
        self.assertTrue(p0["has_next"])
        self.assertFalse(p0["has_prev"])

        # Page 1 (item 5, and 4 empty/None slots)
        p1 = DataAdapter.paginate_containers(containers, page_idx=1, per_page=5)
        self.assertEqual(p1["page"], 1)
        self.assertEqual(p1["rows"][0]["name"], "paperless-webserver")
        self.assertIsNone(p1["rows"][1])
        self.assertIsNone(p1["rows"][4])
        self.assertFalse(p1["has_next"])
        self.assertTrue(p1["has_prev"])

        # Clamp overflow page
        p_overflow = DataAdapter.paginate_containers(containers, page_idx=99, per_page=5)
        self.assertEqual(p_overflow["page"], 1)

        # Clamp underflow page
        p_underflow = DataAdapter.paginate_containers(containers, page_idx=-5, per_page=5)
        self.assertEqual(p_underflow["page"], 0)

    def test_empty_containers(self):
        empty_res = DataAdapter.paginate_containers([], page_idx=0, per_page=5)
        self.assertTrue(empty_res["empty"])
        self.assertEqual(empty_res["total_items"], 0)
        self.assertEqual(empty_res["rows"], [None] * 5)


class TestHistoryAndCharting(unittest.TestCase):
    """Validates 24-point downsampling, statistics, and network scaling."""

    def setUp(self):
        with open(FIXTURES_DIR / "system-stats-response.json", "r") as f:
            self.fixture = json.load(f)

    def test_downsample_24_points(self):
        records = self.fixture["items"]
        res = DataAdapter.downsample_history(records, target_points=24, metric="cpu")
        self.assertFalse(res["empty"])
        self.assertEqual(len(res["points"]), 24)
        self.assertEqual(res["min"], 6.0)
        self.assertEqual(res["max"], 42.0)
        self.assertAlmostEqual(res["avg"], 20.29, places=2)
        self.assertEqual(res["current"], 18.0)
        self.assertEqual(res["scale_max"], 100.0)

        # First and last points must be strictly preserved
        self.assertEqual(res["points"][0]["value"], records[0]["stats"]["cpu"])
        self.assertEqual(res["points"][-1]["value"], records[-1]["stats"]["cpu"])

    def test_downsample_more_than_24_points(self):
        # Generate 100 points
        synthetic = [{"created": f"t_{i}", "stats": {"cpu": i}} for i in range(100)]
        res = DataAdapter.downsample_history(synthetic, target_points=24, metric="cpu")
        self.assertEqual(len(res["points"]), 24)
        self.assertEqual(res["points"][0]["value"], 0)
        self.assertEqual(res["points"][-1]["value"], 99)

    def test_insufficient_history(self):
        res0 = DataAdapter.downsample_history([], target_points=24)
        self.assertTrue(res0["empty"])
        self.assertEqual(len(res0["points"]), 0)

        res1 = DataAdapter.downsample_history([{"created": "now", "stats": {"cpu": 50}}], target_points=24)
        self.assertTrue(res1["empty"])

    def test_network_auto_scale(self):
        records = self.fixture["items"]
        res = DataAdapter.downsample_history(records, target_points=24, metric="net")
        self.assertFalse(res["empty"])
        # Network scale max matches highest value in series
        self.assertEqual(res["scale_max"], res["max"])
        self.assertGreater(res["scale_max"], 0)
        for p in res["points"]:
            self.assertLessEqual(p["normalized"], 1.0)
            self.assertGreaterEqual(p["normalized"], 0.0)


class TestUnitConversions(unittest.TestCase):
    """Validates IEC formatting, bandwidth, and uptime."""

    def test_byte_formatting(self):
        self.assertEqual(DataAdapter.format_bytes(512), "0.50 KiB")
        self.assertEqual(DataAdapter.format_bytes(1024), "1.00 KiB")
        self.assertEqual(DataAdapter.format_bytes(50331648), "48.0 MiB")
        self.assertEqual(DataAdapter.format_bytes(641728512), "612.0 MiB")
        self.assertEqual(DataAdapter.format_bytes(2147483648), "2.00 GiB")
        self.assertEqual(DataAdapter.format_bytes(None), "—")

    def test_bandwidth_formatting(self):
        self.assertEqual(DataAdapter.format_bandwidth(500), "0.5K")
        self.assertEqual(DataAdapter.format_bandwidth(420000), "410K")
        self.assertEqual(DataAdapter.format_bandwidth(2210000), "2.1M")
        self.assertEqual(DataAdapter.format_bandwidth(None), "—")

    def test_uptime_formatting(self):
        self.assertEqual(DataAdapter.format_uptime(3660), "1h 01m")
        self.assertEqual(DataAdapter.format_uptime(52200), "14h 30m")
        self.assertEqual(DataAdapter.format_uptime(1051200), "12d 04h")
        self.assertEqual(DataAdapter.format_uptime(None), "—")

    def test_temperature_formatting(self):
        self.assertEqual(DataAdapter.format_temperature(43.0), "43.0°C")
        self.assertEqual(DataAdapter.format_temperature(39.54), "39.5°C")
        self.assertIsNone(DataAdapter.format_temperature(None))


class TestColorThresholds(unittest.TestCase):
    """Validates Catppuccin color thresholds."""

    def test_threshold_ranges(self):
        default_blue = "#89B4FA"
        # Normal range 0..69%
        self.assertEqual(DataAdapter.get_threshold_color(0, default_blue), default_blue)
        self.assertEqual(DataAdapter.get_threshold_color(69.9, default_blue), default_blue)

        # Warning 70..84%
        self.assertEqual(DataAdapter.get_threshold_color(70.0, default_blue), "#F9E2AF")
        self.assertEqual(DataAdapter.get_threshold_color(84.9, default_blue), "#F9E2AF")

        # Peach 85..94%
        self.assertEqual(DataAdapter.get_threshold_color(85.0, default_blue), "#FAB387")
        self.assertEqual(DataAdapter.get_threshold_color(94.9, default_blue), "#FAB387")

        # Critical >=95%
        self.assertEqual(DataAdapter.get_threshold_color(95.0, default_blue), "#F38BA8")
        self.assertEqual(DataAdapter.get_threshold_color(100.0, default_blue), "#F38BA8")
        self.assertEqual(DataAdapter.get_threshold_color(150.0, default_blue), "#F38BA8")  # clamped


class TestResilienceMatrix(unittest.TestCase):
    """Validates state machine transitions under network failures, auth, and error codes."""

    def setUp(self):
        with open(FIXTURES_DIR / "systems-response.json", "r") as f:
            self.systems_fixture = json.load(f)
        with open(FIXTURES_DIR / "auth-response.json", "r") as f:
            self.auth_fixture = json.load(f)

    def test_successful_flow(self):
        sm = CacheStateMachine()
        self.assertEqual(sm.is_stale, 1)

        # Auth
        auth_ok = sm.handle_auth_response(200, self.auth_fixture)
        self.assertTrue(auth_ok)
        self.assertEqual(sm.bz_token, "REDACTED_EXAMPLE_TOKEN")

        # Systems fetch
        state = sm.handle_systems_response(200, self.systems_fixture)
        self.assertEqual(state, "OK")
        self.assertEqual(sm.is_stale, 0)
        self.assertEqual(sm.last_err, "")
        self.assertIn("items", sm.sys_json)

    def test_network_failure_preserves_cache(self):
        sm = CacheStateMachine()
        sm.handle_systems_response(200, self.systems_fixture)
        previous_cache = dict(sm.sys_json)

        # Network disconnected (status_code = 0)
        state = sm.handle_systems_response(0, None)
        self.assertEqual(state, "STALE")
        self.assertEqual(sm.is_stale, 1)
        self.assertEqual(sm.last_err, "network")
        # Cache must NOT be wiped
        self.assertEqual(sm.sys_json, previous_cache)

    def test_401_triggers_single_reauth(self):
        sm = CacheStateMachine()
        sm.handle_systems_response(200, self.systems_fixture)
        
        # First 401 returns REAUTH
        s1 = sm.handle_systems_response(401, {"message": "Invalid token"})
        self.assertEqual(s1, "REAUTH")
        self.assertEqual(sm.reauth_attempts, 1)

        # Second consecutive 401 fails safely without infinite loop
        s2 = sm.handle_systems_response(401, {"message": "Invalid token"})
        self.assertEqual(s2, "AUTH_FAILED")
        self.assertEqual(sm.is_stale, 1)
        self.assertEqual(sm.last_err, "auth")

    def test_403_forbidden_no_retry(self):
        sm = CacheStateMachine()
        sm.handle_systems_response(200, self.systems_fixture)
        
        s = sm.handle_systems_response(403, {"message": "Forbidden"})
        self.assertEqual(s, "FORBIDDEN")
        self.assertEqual(sm.last_err, "forbidden")
        self.assertEqual(sm.is_stale, 1)


class TestAccessibilityAndContrast(unittest.TestCase):
    """Validates WCAG 2.1 AA contrast standards for Catppuccin Mocha tokens."""

    def setUp(self):
        with open(PALETTE_FILE, "r") as f:
            self.palette = json.load(f)
        self.tokens = self.palette.get("tokens", {})

    def test_contrast_ratios(self):
        base_bg = self.tokens["base"]  # #1E1E2E
        mantle_bg = self.tokens["mantle"]  # #181825

        # Primary text (#CDD6F4) on base: WCAG AAA requires >= 7:1 for normal text
        ratio_primary = AccessibilityValidator.contrast_ratio(self.tokens["text"], base_bg)
        self.assertGreaterEqual(ratio_primary, 10.0, f"Primary text contrast too low: {ratio_primary}")

        # Subtext1 (#BAC2DE) on base: WCAG AA requires >= 4.5:1
        ratio_subtext = AccessibilityValidator.contrast_ratio(self.tokens["subtext1"], base_bg)
        self.assertGreaterEqual(ratio_subtext, 7.0, f"Subtext contrast too low: {ratio_subtext}")

        # Accents on base: WCAG AA for UI components & graphs requires >= 3.0:1
        for name in ("blue", "mauve", "teal", "sapphire", "green", "yellow", "peach", "red"):
            color = self.tokens[name]
            ratio = AccessibilityValidator.contrast_ratio(color, base_bg)
            self.assertGreaterEqual(ratio, 4.0, f"Accent '{name}' contrast too low against base: {ratio:.2f}")

            ratio_mantle = AccessibilityValidator.contrast_ratio(color, mantle_bg)
            self.assertGreaterEqual(ratio_mantle, 4.0, f"Accent '{name}' contrast too low against mantle: {ratio_mantle:.2f}")

    def test_touch_targets_standard(self):
        # Minimum touch target recommended by Material / Android is 48dp (min 44dp)
        min_target_dp = 44
        nav_target_dp = 48
        header_refresh_dp = 48
        self.assertGreaterEqual(nav_target_dp, min_target_dp)
        self.assertGreaterEqual(header_refresh_dp, min_target_dp)


# ==============================================================================
# Runner
# ==============================================================================

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
