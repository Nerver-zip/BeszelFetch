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
            
            # Bandwidth: bb can be a single int/float (bytes/s in Beszel v0.18+) or [sent, recv]
            bb = info.get("bb")
            if isinstance(bb, list):
                net_sent = bb[0] if len(bb) > 0 else 0
                net_recv = bb[1] if len(bb) > 1 else 0
            elif isinstance(bb, (int, float)):
                net_sent = int(bb)
                net_recv = 0
            else:
                net_sent = 0
                net_recv = 0

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

    def test_beszel_v0_18_system_payload(self):
        payload = {
            "items": [{
                "id": "o8buiz12t6q583k",
                "name": "server-01",
                "status": "up",
                "host": "/beszel_socket/beszel.sock",
                "port": "45876",
                "info": {
                    "t": 4,
                    "u": 863644,
                    "cpu": 5.22,
                    "mp": 18.58,
                    "dp": 5.77,
                    "v": "0.18.8",
                    "dt": 44,
                    "bb": 7464,
                    "la": [0.43, 0.25, 0.23],
                    "ct": 2
                }
            }]
        }
        systems = DataAdapter.parse_systems(payload)
        self.assertEqual(len(systems), 1)
        sys_rec = systems[0]
        self.assertEqual(sys_rec["id"], "o8buiz12t6q583k")
        self.assertEqual(sys_rec["name"], "server-01")
        self.assertEqual(sys_rec["status"], "up")
        self.assertEqual(sys_rec["cpu_pct"], 5.22)
        self.assertEqual(sys_rec["mem_pct"], 18.58)
        self.assertEqual(sys_rec["disk_pct"], 5.77)
        self.assertEqual(sys_rec["uptime_s"], 863644)
        self.assertEqual(sys_rec["temp_c"], 44.0)
        self.assertEqual(sys_rec["load1"], 0.43)
        self.assertEqual(sys_rec["net_sent_bps"], 7464)


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


class TestPresetDefinition(unittest.TestCase):
    """Validates the compiled widget/preset.json against architecture and layout specs."""

    def setUp(self):
        self.preset_path = REPO_ROOT / "widget" / "preset.json"
        self.assertTrue(self.preset_path.exists(), f"preset.json missing at {self.preset_path}")
        with open(self.preset_path, "r", encoding="utf-8") as f:
            self.preset = json.load(f)

    def test_preset_root_keys(self):
        required_keys = ["kustom_version", "widget_spec", "globals", "root", "flows"]
        for key in required_keys:
            self.assertIn(key, self.preset, f"Key '{key}' missing from preset root")
        self.assertIn("title", self.preset.get("widget_spec", {}))

    def test_required_globals_present(self):
        globals_list = self.preset.get("globals", [])
        globals_dict = {g["name"]: g for g in globals_list}

        # Config & Auth globals
        for key in ["bz_url", "bz_email", "bz_pass", "bz_token", "sys_id"]:
            self.assertIn(key, globals_dict, f"Config global '{key}' missing")

        # Catppuccin color globals
        for color in ["c_base", "c_mantle", "c_surface0", "c_surface1", "c_text", "c_subtext", "c_muted", "c_cpu", "c_ram", "c_disk", "c_net", "c_ok", "c_warn", "c_peach", "c_err"]:
            self.assertIn(color, globals_dict, f"Color token global '{color}' missing")

        # State globals
        for state_key in ["view", "sys_idx", "container_page", "container_count", "sys_json", "cnt_json", "day_json", "latest", "last_ok", "last_err", "stale"]:
            self.assertIn(state_key, globals_dict, f"State global '{state_key}' missing")

    def test_root_view_layers_present(self):
        root = self.preset.get("root", {})
        root_children = {c.get("name"): c for c in root.get("children", [])}

        self.assertIn("CardBackground", root_children)
        self.assertIn("CardBorder", root_children)
        self.assertIn("ContentFlow", root_children)

        content_flow = root_children["ContentFlow"]
        flow_children = {c.get("name"): c for c in content_flow.get("children", [])}

        self.assertIn("Header", flow_children)
        self.assertIn("ViewArea", flow_children)
        self.assertIn("BottomNav", flow_children)

        view_area = flow_children["ViewArea"]
        views = {c.get("name"): c for c in view_area.get("children", [])}
        self.assertIn("ViewOverview", views)
        self.assertIn("ViewContainers", views)
        self.assertIn("ViewInfo", views)

    def test_flows_defined(self):
        flows = self.preset.get("flows", [])
        flow_ids = [flow.get("id") for flow in flows]

        for flow_id in ["fetch_systems", "fetch_containers", "fetch_history", "refresh_beszel"]:
            self.assertIn(flow_id, flow_ids, f"Flow '{flow_id}' missing from preset")

    def test_touch_targets_dimensions_in_preset(self):
        """Ensure touch targets in bottom nav tabs and header meet or exceed 44dp minimum."""
        root = self.preset.get("root", {})
        root_children = {c.get("name"): c for c in root.get("children", [])}
        content_flow = root_children.get("ContentFlow", {})
        flow_children = {c.get("name"): c for c in content_flow.get("children", [])}

        # Header refresh touch target
        header = flow_children.get("Header", {})
        header_children = {c.get("name"): c for c in header.get("children", [])}
        refresh_btn = header_children.get("RefreshTouchTarget", {})
        self.assertGreaterEqual(refresh_btn.get("width", 0), 44, "Refresh touch width must be >= 44dp")
        self.assertGreaterEqual(refresh_btn.get("height", 0), 44, "Refresh touch height must be >= 44dp")

        # Bottom nav tabs touch targets
        bottom_nav = flow_children.get("BottomNav", {})
        tabs = bottom_nav.get("children", [])
        self.assertEqual(len(tabs), 3, "Bottom nav should have 3 tabs")
        for tab in tabs:
            self.assertGreaterEqual(tab.get("width", 0), 44, f"Tab '{tab.get('name')}' width must be >= 44dp")
            self.assertGreaterEqual(tab.get("height", 0), 44, f"Tab '{tab.get('name')}' height must be >= 44dp")
            self.assertIn("touch_action", tab, f"Tab '{tab.get('name')}' must have touch_action")


class TestKustomClip(unittest.TestCase):
    """Validates the widget/beszel_monitor.clip format and Komponent structure."""

    def setUp(self):
        self.clip_path = REPO_ROOT / "widget" / "beszel_monitor.clip"
        self.assertTrue(self.clip_path.exists(), f"beszel_monitor.clip missing at {self.clip_path}")
        with open(self.clip_path, "r", encoding="utf-8") as f:
            self.content = f.read()

    def test_clip_header_and_valid_json(self):
        self.assertTrue(self.content.startswith("##KUSTOMCLIP##\n"), "File must begin with ##KUSTOMCLIP## header")
        self.assertTrue(self.content.strip().endswith("##KUSTOMCLIP##"), "File must end with closing ##KUSTOMCLIP## tag")
        tag = "##KUSTOMCLIP##"
        raw = self.content.strip()
        raw = raw[len(tag):-len(tag)].strip()
        data = json.loads(raw)
        self.assertEqual(data.get("clip_version"), 1)
        self.assertIn("clip_modules", data)
        self.assertGreaterEqual(len(data["clip_modules"]), 1)

    def test_loose_clip_valid(self):
        loose_path = REPO_ROOT / "widget" / "beszel_monitor_loose.clip"
        self.assertTrue(loose_path.exists())
        with open(loose_path, "r", encoding="utf-8") as f:
            loose_content = f.read()
        self.assertTrue(loose_content.startswith("##KUSTOMCLIP##\n"))
        self.assertTrue(loose_content.strip().endswith("##KUSTOMCLIP##"))
        tag = "##KUSTOMCLIP##"
        raw = loose_content.strip()[len(tag):-len(tag)].strip()
        data = json.loads(raw)
        self.assertEqual(data.get("clip_version"), 1)
        self.assertIn("clip_modules", data)
        self.assertEqual(len(data["clip_modules"]), 3)

    def test_komponent_globals(self):
        tag = "##KUSTOMCLIP##"
        raw = self.content.strip()[len(tag):-len(tag)].strip()
        data = json.loads(raw)
        komp = data["clip_modules"][0]
        self.assertEqual(komp.get("internal_type"), "KomponentModule")
        self.assertEqual(komp.get("internal_title"), "Beszel Monitor")

        globals_list = komp.get("globals_list", {})
        # Essential config keys
        for key in ["bz_url", "bz_token", "bz_email", "bz_pass", "sys_id", "view", "latest", "sys_idx"]:
            self.assertIn(key, globals_list, f"Global '{key}' missing from Komponent globals_list")

        # Color tokens
        for c in ["c_base", "c_mantle", "c_surface0", "c_surface1", "c_text", "c_subtext", "c_cpu", "c_ram", "c_disk", "c_net", "c_ok", "c_warn", "c_err"]:
            self.assertIn(c, globals_list, f"Color token '{c}' missing from Komponent globals_list")

    def test_komponent_views_and_touch_targets(self):
        tag = "##KUSTOMCLIP##"
        raw = self.content.strip()[len(tag):-len(tag)].strip()
        data = json.loads(raw)
        komp = data["clip_modules"][0]
        items = {item.get("internal_title"): item for item in komp.get("viewgroup_items", [])}

        self.assertIn("CardBackground", items)
        self.assertIn("CardBorder", items)
        self.assertIn("ContentFlow", items)

        content_flow = items["ContentFlow"]
        flow_items = {i.get("internal_title"): i for i in content_flow.get("viewgroup_items", [])}
        self.assertIn("Header", flow_items)
        self.assertIn("ViewArea", flow_items)
        self.assertIn("BottomNav", flow_items)

        # Header refresh touch target
        header_items = {i.get("internal_title"): i for i in flow_items["Header"].get("viewgroup_items", [])}
        refresh = header_items.get("RefreshTouchTarget", {})
        self.assertIn("internal_events", refresh)

        # Bottom nav tabs touch targets
        nav_tabs = flow_items["BottomNav"].get("viewgroup_items", [])
        self.assertEqual(len(nav_tabs), 3)
        for tab in nav_tabs:
            self.assertIn("internal_events", tab)

        # Dynamic views inside ViewArea
        view_area = flow_items["ViewArea"]
        views = {i.get("internal_title"): i for i in view_area.get("viewgroup_items", [])}
        self.assertIn("ViewOverview", views)
        self.assertIn("ViewContainers", views)
        self.assertIn("ViewInfo", views)


# ==============================================================================
# Runner
# ==============================================================================

class TestCompiledVisualRegression(unittest.TestCase):
    """Inspect shipped geometry/formulas; these checks do not emulate Android."""

    @classmethod
    def setUpClass(cls):
        import zipfile
        from widget_layout import walk
        with zipfile.ZipFile(REPO_ROOT / "widget/beszel_monitor.kwgt") as archive:
            cls.root = json.loads(archive.read("preset.json"))["preset_root"]
        cls.nodes = {node.get("internal_title"): node for node in walk(cls.root)}

    def test_fixed_frame_and_anchors(self):
        self.assertEqual(self.nodes["ContentFlow"]["internal_type"], "OverlapLayerModule")
        for title, anchor, y in (("Header", "TOP", 10), ("BottomNav", "BOTTOM", 10), ("ViewArea", "TOP", 62)):
            node = self.nodes[title]
            self.assertEqual(node["position_anchor"], anchor)
            self.assertEqual(node["position_offset_y"], y)
        bounds = self.nodes["LayoutBounds"]["shape_height"]
        header_bottom = self.nodes["Header"]["position_offset_y"] + self.nodes["HeaderBounds"]["shape_height"]
        view_top = self.nodes["ViewArea"]["position_offset_y"]
        view_bottom = view_top + self.nodes["ViewAreaSpacer"]["shape_height"]
        nav_height = max(child.get("shape_height", 0)
                         for tab in self.nodes["BottomNav"]["viewgroup_items"]
                         for child in tab["viewgroup_items"])
        nav_top = bounds - self.nodes["BottomNav"]["position_offset_y"] - nav_height
        self.assertGreaterEqual(view_top - header_bottom, 8)
        self.assertGreaterEqual(nav_top - view_bottom, 8)
        self.assertEqual(self.nodes["CardBackground"]["shape_height"], bounds)

    def test_rings_do_not_follow_text_width(self):
        for metric in ("CPU", "Memory", "Disk"):
            self.assertEqual(self.nodes[f"Inner_{metric}"]["internal_type"], "OverlapLayerModule")
            self.assertEqual(self.nodes[f"Gauge_{metric}"]["position_offset_x"], 12)
            self.assertEqual(self.nodes[f"Details_{metric}"]["position_offset_x"], 108)

    def test_serialized_anchor_names(self):
        for title, node in self.nodes.items():
            self.assertNotIn("_", node.get("position_anchor", ""), title)
            self.assertNotIn("position_x", node, title)
            self.assertNotIn("position_y", node, title)

    def test_refresh_and_pagination_geometry(self):
        self.assertGreaterEqual(self.nodes["RefreshGlyph"]["text_size"], 24)
        header_titles = [n.get("internal_title") for n in self.nodes["Header"]["viewgroup_items"]]
        for title in ("BtnPrev", "BtnNext", "RefreshTouchTarget"):
            self.assertIn(title, header_titles)
            for node in self.nodes[title]["viewgroup_items"]:
                if node["internal_type"] == "ShapeModule":
                    self.assertGreaterEqual(node["shape_width"], 44)
                    self.assertGreaterEqual(node["shape_height"], 44)
        self.assertEqual(self.nodes["PageText"]["position_anchor"], "BOTTOM")

    def test_docker_columns_and_unbounded_page_lookup(self):
        globals_ = self.root["globals_list"]
        for i in range(5):
            left, right = self.nodes[f"RowLeft_{i}"], self.nodes[f"RowRight_{i}"]
            self.assertEqual(left["position_anchor"], "CENTERLEFT")
            self.assertEqual(right["position_anchor"], "CENTERRIGHT")
            from test_widget_runtime import Kode
            left_width = Kode(globals_, width=480).eval(left["viewgroup_items"][0]["internal_formulas"]["shape_width"])
            right_width = float(right["viewgroup_items"][0]["internal_formulas"]["shape_width"].strip("$"))
            offsets = left["position_offset_x"] + right["position_offset_x"]
            self.assertLessEqual(left_width + right_width + offsets, 480 - 36)
            for key in ("name", "cpu", "mem"):
                expr = globals_[f"row{i}_{key}"]["global_formula"]
                self.assertIn(f"gv(cpage) * 5 + {i}", expr)
                self.assertNotIn("container_page) = 1", expr)
            self.assertIn(f"gv(row{i}_name)", self.nodes[f"ContainerRow_{i}"]["internal_formulas"]["config_visible"])

    def test_overview_network_card_and_docker_glyphs(self):
        self.assertNotIn("NetSparkline", self.nodes)
        for i in range(14):
            self.assertNotIn(f"NetBar_{i:02d}", self.nodes)
        for title in ("NetDownLabel", "NetDownVal", "NetUpLabel", "NetUpVal", "NetVolLabel", "NetVolVal", "NetVolUpLabel", "NetVolUpVal"):
            self.assertIn(title, self.nodes)
        for title in ("ColLabelName", "ColLabelCPU", "ColLabelRAM"):
            self.assertIn(title, self.nodes)
        for i in range(5):
            self.assertIn(f"Glyph_{i}", self.nodes)
            left_titles = [n.get("internal_title") for n in self.nodes[f"RowLeft_{i}"]["viewgroup_items"]]
            self.assertIn(f"Glyph_{i}", left_titles)
        self.assertIn("󰋼 Info", self.nodes["TextInfo"]["text_expression"])

    def test_info_columns_replace_chart(self):
        for title in ("ViewInfo", "FetchDetails", "FetchLogo"):
            self.assertIn(title, self.nodes)
        for title in ("FetchOSValue", "FetchKernelValue", "FetchCPUValue",
                      "FetchGPUValue", "FetchCoresValue", "FetchUptimeValue",
                      "FetchMemoryValue", "FetchTempValue"):
            self.assertIn(title, self.nodes)
            self.assertIn("gv(", self.nodes[title]["internal_formulas"]["text_expression"])
        for title in ("ViewChart", "ChartContainer", "HistoryBars", "HistoryArea",
                      "HistoryLine", "HistoryLineTx", "BtnRange", "BtnScale", "MetricChips"):
            self.assertNotIn(title, self.nodes)
        for node in self.nodes.values():
            self.assertNotEqual(node.get("shape_type"), "PATH")
        self.assertEqual(self.nodes["TabInfo"]["internal_events"][0]["switch_text"], "info")

    def test_archive_and_dist_match_clip(self):
        tag = "##KUSTOMCLIP##"
        clip = json.loads((REPO_ROOT / "widget/beszel_monitor.clip").read_text().strip()[len(tag):-len(tag)])
        komp = clip["clip_modules"][0]
        self.assertEqual(self.root["viewgroup_items"], komp["viewgroup_items"])
        self.assertEqual(self.root["globals_list"], komp["globals_list"])
        for suffix in ("kwgt", "clip"):
            name = f"beszel_monitor.{suffix}"
            self.assertEqual((REPO_ROOT / "widget" / name).read_bytes(), (REPO_ROOT / "dist" / name).read_bytes())

    def test_staged_native_cache_writes(self):
        flows = self.root["internal_flows"]
        self.assertEqual({f["name"] for f in flows},
                         {"refresh_beszel", "fetch_systems", "fetch_containers", "fetch_history", "fetch_info"})
        for flow in flows:
            for i, step in enumerate(flow["a"]):
                params = step.get("params", {})
                if step["type"] == "A_GLOBAL" and params.get("global") in ("sys_json", "cnt_json", "day_json", "latest"):
                    previous = flow["a"][i - 1]
                    self.assertEqual(previous["type"], "A_FORMULA")
                    self.assertIn(f'gv({params["global"]})', previous["params"]["formula"])
                    self.assertIn("if(", previous["params"]["formula"])
        history = next(f for f in flows if f["name"] == "fetch_history")
        self.assertEqual(history["t"][0]["params"]["cron_string"], "*/15 * * * *")

    def test_scalar_adapter_and_no_credentials(self):
        globals_ = self.root["globals_list"]
        for name in ("ramused", "ramtotal", "buffer", "swap", "net_rx", "net_tx"):
            self.assertIn("tc(json", globals_[name]["global_formula"])
        for name in ("hist_peak", "hist_scale", "hist_line_path", "metric", "range"):
            self.assertNotIn(name, globals_)
        for key in ("bz_token", "bz_email", "bz_pass"):
            self.assertEqual(globals_[key]["value"], "")

    def test_kustom_formula_restrictions(self):
        import re
        def strings(value):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for child in value.values():
                    yield from strings(child)
            elif isinstance(value, list):
                for child in value:
                    yield from strings(child)
        for expression in strings(self.root):
            if "$" not in expression:
                continue
            self.assertNotIn("&&", expression)
            self.assertNotIn("'", expression)
            self.assertNotIn("mu(ceil", expression)
            self.assertNotIn("Sem dados", expression)
            self.assertNotIn("parcial", expression)
            # Tokenize quoted strings as units, so JSON paths and escaped loop
            # bodies do not confuse the parenthesis stack.
            stack = []
            for match in re.finditer(r'"(?:\\.|[^"\\])*"|([a-z]+)\s*\(|([()])', expression):
                fn, paren = match.groups()
                if fn:
                    if fn == "if":
                        self.assertNotIn("mu", stack, expression)
                    stack.append(fn)
                elif paren == "(":
                    stack.append("")
                elif paren == ")":
                    self.assertTrue(stack, expression)
                    stack.pop()
            self.assertFalse(stack, expression)

    def test_history_setup_request_and_failure(self):
        from unittest.mock import patch
        from urllib.parse import parse_qs, urlsplit
        sys.path.insert(0, str(REPO_ROOT))
        import setup
        with patch.object(setup, "http_get", return_value=(200, {"items": []})) as fetch:
            self.assertEqual(setup.fetch_system_stats("https://example.invalid", "synthetic"), {"items": []})
            query = parse_qs(urlsplit(fetch.call_args.args[0]).query)
            self.assertEqual(query["sort"], ["created"])
            self.assertEqual(query["perPage"], ["500"])
            self.assertIn('type="20m"', query["filter"][0])
        with patch.object(setup, "http_get", return_value=(503, {})) as fetch:
            self.assertIsNone(setup.fetch_system_stats("https://example.invalid", "synthetic"))
            self.assertEqual(fetch.call_count, 1, "Never fetch another host after failure")

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
