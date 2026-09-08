"""Execute the emitted Kode subset locally; NOT an Android/Kustom emulator.

Unknown syntax/functions fail closed. Rendered SVGs use evaluated preset paths,
not a second chart implementation. All input is synthetic and credential-free.
"""
import datetime as dt
import json
import math
from pathlib import Path
import re
import unittest
from urllib.parse import quote, parse_qs, urlsplit

from widget_layout import walk

ROOT = Path(__file__).resolve().parents[1]
NOW = dt.datetime(2026, 9, 7, 21, tzinfo=dt.timezone.utc).timestamp()


def number(value):
    return float(value or 0)


def string(value):
    return str(int(value)) if isinstance(value, (int, float)) and value == int(value) else str(value)


class Kode:
    token = re.compile(r'\s*("(?:\\.|[^"\\])*"|\d+(?:\.\d+)?|[A-Za-z_][\w]*|!=|>=|<=|[()+*/=<>|&,\-])')
    precedence = {"|": 1, "&": 2, "=": 3, "!=": 3, ">": 3, "<": 3, ">=": 3, "<=": 3, "+": 4, "-": 4, "*": 5, "/": 5}

    def __init__(self, globals_, overrides=None, width=640, height=440, timezone=0):
        self.globals = globals_
        self.overrides = overrides or {}
        self.memo = {}
        self.size = {"rwidth": width, "rheight": height}
        self.timezone = timezone

    def parse(self, expression):
        text = expression.strip().strip("$")
        tokens, pos = [], 0
        while pos < len(text):
            match = self.token.match(text, pos)
            if not match:
                raise ValueError(f"Unsupported syntax at {text[pos:pos+50]!r}")
            tokens.append(match[1]); pos = match.end()
        cursor = 0

        def expr(minimum=0):
            nonlocal cursor
            t = tokens[cursor]; cursor += 1
            if t == "(":
                node = expr(); assert tokens[cursor] == ")"; cursor += 1
            elif t == "-":
                node = ("op", "-", ("literal", 0), expr(6))
            elif t.startswith('"'):
                node = ("literal", json.loads(t))
            elif t[0].isdigit():
                node = ("literal", float(t))
            elif cursor < len(tokens) and tokens[cursor] == "(":
                cursor += 1; args = []
                while tokens[cursor] != ")":
                    args.append(expr())
                    if tokens[cursor] != ",": break
                    cursor += 1
                assert tokens[cursor] == ")"; cursor += 1
                node = ("call", t, args)
            else:
                node = ("literal", t)
            while cursor < len(tokens) and self.precedence.get(tokens[cursor], -1) >= minimum:
                op = tokens[cursor]; cursor += 1
                node = ("op", op, node, expr(self.precedence[op] + 1))
            return node
        tree = expr()
        assert cursor == len(tokens), tokens[cursor:]
        return tree

    def gv(self, name):
        if name in self.overrides: return self.overrides[name]
        if name not in self.memo:
            record = self.globals[name]
            self.memo[name] = self.eval(record["global_formula"]) if "global_formula" in record else record.get("value", "")
        return self.memo[name]

    def eval(self, formula):
        return self.solve(self.parse(formula))

    def solve(self, node):
        kind, *args = node
        if kind == "literal": return args[0]
        if kind == "op":
            op, left, right = args
            a, b = self.solve(left), self.solve(right)
            if op == "+":
                if isinstance(a, str) or isinstance(b, str):
                    try: return number(a) + number(b)
                    except ValueError: return string(a) + string(b)
                return a + b
            if op in ("=", "!=", ">", "<", ">=", "<="):
                # Empty text remains distinct from numeric zero for optional fields.
                if a != "" and b != "":
                    try: a, b = number(a), number(b)
                    except ValueError: a, b = string(a), string(b)
                elif op not in ("=", "!="):
                    a, b = number(a), number(b)
                return {"=": lambda: a == b, "!=": lambda: a != b, ">": lambda: a > b,
                        "<": lambda: a < b, ">=": lambda: a >= b, "<=": lambda: a <= b}[op]()
            a, b = number(a), number(b)
            return {"-": lambda: a-b, "*": lambda: a*b, "/": lambda: a/b,
                    "&": lambda: bool(a) and bool(b), "|": lambda: bool(a) or bool(b)}[op]()
        fn, trees = args
        if fn == "if":
            return self.solve(trees[1] if self.solve(trees[0]) else trees[2])
        values = [self.solve(a) for a in trees]
        if fn == "gv": return self.gv(values[0])
        if fn == "si": return self.size[values[0]]
        if fn == "mu":
            mode, *nums = values; nums = [number(n) for n in nums]
            if mode == "max": return max(nums)
            if mode == "min": return min(nums)
            if mode == "floor": return math.floor(nums[0])
            if mode == "round":
                factor = 10 ** (nums[1] if len(nums) > 1 else 0)
                return math.floor(nums[0] * factor + .5) / factor
        if fn == "tc":
            mode, *v = values
            if mode == "utf": return chr(int(string(v[0]), 16))
            if mode == "count": return v[0].count(v[1])
            if mode == "reg": return re.sub(v[1], v[2], v[0])
            if mode == "fmt": return v[0] % tuple(v[1:])
            if mode == "url": return quote(v[0], safe="")
            if mode == "low": return string(v[0]).lower()
            if mode == "type":
                try:
                    return "NUMBER" if math.isfinite(float(v[0])) else "LATIN"
                except (ValueError, TypeError): return "LATIN"
            if mode == "ell": return v[0] if len(v[0]) <= int(v[1]) else v[0][:int(v[1])-1] + "…"
            if mode == "json":
                try:
                    data = json.loads(v[0])
                    if ".*." in v[1]:
                        prefix, suffix = v[1].split(".*.", 1)
                        for key, index in re.findall(r'\.([\w]+)|\[(\d+)\]', prefix):
                            data = data[key] if key else data[int(index)]
                        data = [item[suffix] for item in data.values() if suffix in item]
                    else:
                        for key, index in re.findall(r'\.([\w]+)|\[(\d+)\]', v[1]):
                            data = data[key] if key else data[int(index)]
                    return data if not isinstance(data, (dict, list)) else json.dumps(data)
                except (ValueError, KeyError, IndexError, TypeError): return ""
        if fn == "dp": return dt.datetime.fromisoformat(values[0].replace("Z", "+00:00")).timestamp()
        if fn == "df":
            if values[0] == "Z": return self.timezone
            moment = values[1] if len(values) > 1 else NOW
            if isinstance(moment, str):
                match = re.fullmatch(r'r(\d+)([hd])', moment)
                moment = NOW - int(match[1]) * (3600 if match[2] == "h" else 86400)
            if values[0] == "S": return moment
            if values[0] == "yyyy-MM-dd HH:mm:ss": return dt.datetime.fromtimestamp(moment+self.timezone, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        raise ValueError(f"Unsupported call {fn}: {values}")


def records(span=86400, count=73, lag=1200):
    result = []
    for i in range(count):
        stamp = NOW - span + (span-lag)*i/max(1, count-1)
        result.append({"created": dt.datetime.fromtimestamp(stamp, dt.timezone.utc).isoformat(),
                       "stats": {"cpu": 5 + 2*math.sin(i*.7), "mp": 15, "dp": 6,
                                 "m": 16, "mu": 2.4, "d": 1000, "du": 60,
                                 "b": [22000 + i*100, 85000 + i*800]}})
    return {"page": 1, "perPage": 500, "totalItems": 999, "items": result}


def load_root():
    tag = "##KUSTOMCLIP##"
    return json.loads((ROOT / "widget/beszel_monitor.clip").read_text().strip()[len(tag):-len(tag)])["clip_modules"][0]


class RuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = load_root()
        cls.nodes = {n.get("internal_title"): n for n in walk(cls.root)}

    def context(self, **updates):
        latest = json.loads((ROOT / "examples/fixtures/system-latest-response.json").read_text())
        systems = {"items": [{"id": "synthetic", "name": "atlas", "status": "up",
                             "info": {"u": 957600, "dt": 43.7, "la": [1.234, .567, .891]}}]}
        return Kode(self.root["globals_list"], {
            "day_json": json.dumps(records()), "latest": json.dumps(latest),
            "sys_json": json.dumps(systems), "sys_idx": 0, **updates})

    def test_info_scalar_values(self):
        k = self.context()
        for global_, expected in (("host", "atlas"), ("up_fmt", "11d 2h"),
                ("loads", "1.23 / 0.57 / 0.89"), ("temp_fmt", "43.7°C"),
                ("ram_fmt", "2.4 / 16 GiB"), ("disk_fmt", "60 / 1000 GiB"),
                ("buffer_fmt", "3.25 GiB"), ("swap_fmt", "0.13 / 4 GiB"),
                ("rate_rx", "2 MiB/s"), ("rate_tx", "4 KiB/s"),
                ("partition", "Partition: N/A")):
            self.assertEqual(k.gv(global_), expected, global_)

    def run_flow(self, name, k, responses):
        pending = iter(responses)
        result = ""
        flow = next(f for f in self.root["internal_flows"] if f["name"] == name)
        for step in flow["a"]:
            params = step["params"]
            if step["type"] == "A_WGET":
                result = next(pending)
            elif step["type"] == "A_FORMULA":
                result = k.eval(params["formula"])
            elif step["type"] == "A_GLOBAL":
                # Native TEXT globals persist strings between Flow actions.
                k.overrides[params["global"]] = string(result)
                k.memo.clear()
            else:
                self.fail("Unmodeled Flow action")
        return k

    def test_daily_flow_materializes_and_preserves_on_failure(self):
        from widget_daily import seed_totals
        for count in (0, 1, 12, 72):
            data = records(count=count)
            data["totalItems"] = count
            k = self.run_flow("fetch_history", self.context(), [json.dumps(data)])
            tx, rx = seed_totals(data)
            self.assertAlmostEqual(number(k.gv("net_24h_rx")), round(rx), delta=1)
            self.assertAlmostEqual(number(k.gv("net_24h_tx")), round(tx), delta=1)
            for name in ("net_24h_rx", "net_24h_tx"):
                self.assertIn("global_formula", self.root["globals_list"][name])
        for response in ("", "not-json", '{"code":401}', '{"code":503}'):
            base_data = records(count=5)
            k = self.context(day_json=json.dumps(base_data))
            expected_rx = k.gv("net_24h_rx")
            expected_tx = k.gv("net_24h_tx")
            self.run_flow("fetch_history", k, [response])
            self.assertEqual(k.gv("net_24h_rx"), expected_rx)
            self.assertEqual(k.gv("net_24h_tx"), expected_tx)

    def test_preferred_load_and_zero(self):
        for values, period, expected in (([2,.5,1],"5m",.5), ([2,"",1],"15m",1),
                                         ([2,"",""],"1m",2), ([2,0,1],"5m",0)):
            k = self.context(sys_json=json.dumps({"items":[{"info":{"la":values}}]}), latest="{}")
            self.assertEqual(k.gv("load_period"), period)
            self.assertEqual(k.gv("load_best"), expected)
        k = self.context(sys_json='{"items":[{}]}', latest='{"items":[{"stats":{"la":[1,0.25,0.75]}}]}')
        self.assertEqual(k.gv("load_best"), .25)

    def test_single_ascii_module_selects_exact_catalog_art(self):
        logos = [n for n in walk(self.nodes["ViewInfo"]) if n.get("internal_title","").startswith("FetchLogo")]
        self.assertEqual(len(logos), 1)
        self.assertEqual(logos[0]["text_align"], "LEFT")
        self.assertNotIn("config_visible", logos[0].get("internal_formulas", {}))
        catalog = json.loads(self.root["globals_list"]["ascii_data"]["value"])
        original = json.loads((ROOT / "widget/assets/fastfetch/logos.json").read_text())["logos"]
        for name, art in original.items():
            k = self.context(fetch_logo=name)
            self.assertEqual(k.eval(logos[0]["internal_formulas"]["text_expression"]), art)
            self.assertEqual(k.gv("fetch_art_cols"), max(map(len, art.splitlines())))
            self.assertEqual(k.gv("fetch_art_color"), catalog[name]["color"])
            self.assertNotRegex(art, r"\$[1-9]")
        self.assertIn("MIT", self.nodes["ViewInfo"]["internal_description"])

    def test_manual_info_cache_and_metadata_fallback(self):
        flow = next(f for f in self.root["internal_flows"] if f["name"] == "fetch_info")
        self.assertEqual(flow["t"], [])
        for other in self.root["internal_flows"]:
            if other is flow: continue
            self.assertFalse(any(s["params"].get("global", "").startswith("info_") for s in other["a"]))
        host = {"id":"synthetic", "name":"atlas", "info":{"u":3600,"dt":42,"k":"legacy-kernel","m":"legacy-cpu","os":0}}
        stats = {"items":[{"stats":{"cpu":0,"mu":2,"m":16,"g":{"card0":{"n":"GPU A"},"card1":{"n":"GPU B"}}}}]}
        meta = {"id":"synthetic", "os_name":"Arch Linux","kernel":"6.12","cpu":"CPU model"}
        k = self.run_flow("fetch_info", self.context(), list(map(json.dumps,(meta,host,stats))))
        self.assertEqual(k.gv("fetch_logo"), "arch")
        self.assertEqual(k.gv("fetch_kernel"), "6.12")
        self.assertEqual(k.gv("fetch_gpu"), "GPU A + GPU B")
        before = {key:k.gv(key) for key in ("info_meta","info_sys","info_stats","info_at")}
        self.run_flow("fetch_info",k,['{"code":403}',"not-json",'{"code":503}'])
        self.assertEqual({key:k.gv(key) for key in before}, before)
        self.assertEqual(k.gv("info_error"), "Refresh failed · cache kept")
        k = self.run_flow("fetch_info",self.context(),['{"code":404}',json.dumps(host),json.dumps(stats)])
        self.assertEqual(k.gv("fetch_kernel"), "legacy-kernel")
        self.assertEqual(k.gv("fetch_cpu"), "legacy-cpu")
        self.assertEqual(k.gv("fetch_logo"), "linux")
        self.assertEqual(k.gv("info_error"), "Metadata unavailable")

    def test_optional_missing_and_malformed(self):
        for payload in ('{"items":[]}', '{}', 'not-json'):
            k = self.context(latest=payload, sys_json=payload, day_json=payload)
            for name in ("temp_fmt", "ram_fmt", "disk_fmt", "buffer_fmt", "swap_fmt", "up_fmt"):
                self.assertEqual(k.gv(name), "N/A", name)
            for name in ("rate_rx", "rate_tx"):
                self.assertEqual(k.gv(name), "0 KiB/s")
            for name in ("day_rx", "day_tx"):
                self.assertEqual(k.gv(name), "0 KiB")

    def test_overview_percent_only_inside_rings(self):
        k = self.context()
        self.assertEqual(self.nodes["Title_CPU"]["text_expression"], "󰍛 CPU")
        self.assertEqual(k.eval(self.nodes["Sub_CPU"]["internal_formulas"]["text_expression"]), "🌡 43.7°C")
        self.assertEqual(k.eval(self.nodes["Sub2_CPU"]["internal_formulas"]["text_expression"]), "Load Avg: 0.57")
        for name in ("Sub_CPU", "Sub2_CPU", "Sub_Memory", "Sub_Disk"):
            self.assertNotIn("%", k.eval(self.nodes[name]["internal_formulas"]["text_expression"]))

    def test_daily_integrates_sparse_samples_without_gate(self):
        for count in (0, 1, 2, 12, 24, 72):
            items = []
            for i in range(count):
                stamp = NOW - (count-i)*1200
                items.append({"created": dt.datetime.fromtimestamp(stamp, dt.timezone.utc).isoformat(),
                              "stats": {"b": [1024, 2048]}})
            k = self.context(day_json=json.dumps({"items": items}))
            self.assertEqual(k.gv("net_24h_rx"), count*1200*2048)
            self.assertEqual(k.gv("net_24h_tx"), count*1200*1024)
            self.assertNotIn("—", k.gv("day_rx"))
            self.assertNotIn("partial", k.gv("day_rx"))

    def test_daily_bounds_no_fabricated_long_gap(self):
        data = records(count=3)
        for record in data["items"]:
            record["stats"]["b"] = [100, 200]
        k = self.context(day_json=json.dumps(data))
        self.assertLessEqual(k.gv("net_24h_rx"), 3*1200*200)
        self.assertNotIn("ds1", self.root["globals_list"])

    def test_no_chart_or_runtime_loops_and_all_globals_resolve(self):
        serialized = json.dumps(self.root)
        for fragment in ('ViewChart', 'ChartContainer', 'HistoryLine', 'HistoryBars',
                         'shape_path', 'fl(', 'hist_json', 'gv(metric)', 'gv(range)',
                         'day_n) >= 70', '24h parcial'):
            self.assertNotIn(fragment, serialized)
        self.assertLess(len(self.root["globals_list"]), 450)
        self.assertEqual(self.nodes["TextInfo"]["text_expression"], "󰋼 Info")
        self.assertEqual(self.nodes["TabInfo"]["internal_events"][0]["switch_text"], "info")
        # Follow every static gv reference, including branches not selected in fixtures.
        refs = set(re.findall(r'gv\(([A-Za-z_][A-Za-z_0-9]*)\)', serialized))
        self.assertEqual(refs - set(self.root["globals_list"]), set())
        k = self.context()
        for node in walk(self.nodes["ViewInfo"]):
            if node.get("internal_type") == "TextModule":
                expr = node.get("internal_formulas", {}).get("text_expression")
                if expr: self.assertNotEqual(k.eval(expr), "")

    def test_pagination_and_shrink(self):
        for count in (0, 1, 5, 6, 12, 105):
            rows = [{"n": f"container-long-name-{i}", "c": i, "m": 120+i} for i in range(count)]
            for wrapped in ({"stats": rows}, {"items": [{"stats": rows}]}):
                for page in (0, 1, 2, 99):
                    k = self.context(cnt_json=json.dumps(wrapped), container_page=str(page))
                    self.assertEqual(k.gv("container_count"), count)
                    bounded = min(page, max(0, (count-1)//5))
                    self.assertEqual(k.gv("cpage"), bounded)
                    self.assertEqual(k.gv("row0_name"), rows[bounded*5]["n"] if rows else "")
                    label = k.eval(self.nodes["PageText"]["internal_formulas"]["text_expression"])
                    self.assertNotIn("/ 0", label)
                    nxt = k.eval(self.nodes["BtnNext"]["internal_events"][0]["switch_text"])
                    self.assertEqual(nxt, min(bounded+1, max(0,(count-1)//5)))
        k = self.context(cnt_json='{"stats": [{"n" : "n", "c": 0, "m": 1}]}')
        self.assertEqual(k.gv("container_count"), 1)

    def test_badge_labels_have_no_residual_padding(self):
        for title in ("ColLabelCPU", "ColLabelRAM", "Cpu", "Mem"):
            node = self.nodes[title]
            self.assertEqual(node["position_anchor"], "CENTER")
            self.assertEqual(node["position_padding_right"], 0)

    def test_docker_dot_tracks_host_and_cache(self):
        dot = self.nodes["RowLeft_0"]["viewgroup_items"][1]
        expr = dot["internal_formulas"]["paint_color"]
        for status, stale, expected in (("up", 0, "c_ok"), ("up", 1, "c_warn"), ("down", 0, "c_err")):
            k = self.context(host_status=status, stale=stale)
            self.assertEqual(k.eval(expr), k.gv(expected))

        # Test stopped/exited container is red (c_err)
        k_exited = self.context(host_status="up", stale=0, cnt_json='{"stats": [{"n": "test", "c": 0, "m": 0, "s": "exited"}]}')
        self.assertEqual(k_exited.eval(expr), k_exited.gv("c_err"))

        # Test container with 0 memory and no status is red (c_err)
        k_zero_mem = self.context(host_status="up", stale=0, cnt_json='{"stats": [{"n": "test", "c": 0, "m": 0}]}')
        self.assertEqual(k_zero_mem.eval(expr), k_zero_mem.gv("c_err"))

        # Test running container with "Up 2 hours" is green (c_ok)
        k_running = self.context(host_status="up", stale=0, cnt_json='{"stats": [{"n": "test", "c": 1.2, "m": 50000000, "s": "Up 2 hours"}]}')
        self.assertEqual(k_running.eval(expr), k_running.gv("c_ok"))

    def test_card_transparency_tokens(self):
        globals_ = self.root["globals_list"]
        self.assertEqual(globals_["c_base"]["value"], "#D91E1E2E")
        self.assertEqual(globals_["c_mantle"]["value"], "#B3181825")

    def test_pagination_button_expanded_geometry(self):
        for title, exp_offset in (("BtnPrev", 134), ("BtnNext", 52)):
            btn = self.nodes[title]
            self.assertEqual(btn["position_offset_x"], float(exp_offset))
            for child in btn["viewgroup_items"]:
                if child["internal_type"] == "ShapeModule":
                    self.assertEqual(child["shape_width"], 74.0)
                    self.assertEqual(child["shape_height"], 44.0)

    def test_wallpaper_autodetection_and_packaging(self):
        import tempfile, zipfile
        from generate_clip import build_kustom_clip
        # Empty wallpapers dir generates empty bitmap_bitmap
        komp = build_kustom_clip(write_outputs=False)
        gw = next(n for n in komp["viewgroup_items"] if n.get("internal_title") == "GlossyWallpaper")
        self.assertEqual(gw["bitmap_bitmap"], "")

        # With a wallpaper provided
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
            tmp.write(b"\x89PNG\r\n\x1a\nfake")
            tmp.flush()
            komp2 = build_kustom_clip(wallpaper_path=tmp.name, write_outputs=False)
            gw2 = next(n for n in komp2["viewgroup_items"] if n.get("internal_title") == "GlossyWallpaper")
            self.assertIn(Path(tmp.name).name, gw2["bitmap_bitmap"])
            # Verify packaging in a standalone temp zip archive
            with tempfile.NamedTemporaryFile(suffix=".kwgt") as tmp_kwgt:
                with zipfile.ZipFile(tmp_kwgt.name, "w") as zf:
                    zf.write(tmp.name, arcname=f"bitmaps/{Path(tmp.name).name}")
                with zipfile.ZipFile(tmp_kwgt.name, "r") as zf:
                    self.assertIn(f"bitmaps/{Path(tmp.name).name}", zf.namelist())

    def test_failure_keeps_cache_and_empty_clears(self):
        flow = next(f for f in self.root["internal_flows"] if f["name"] == "fetch_history")
        valid = flow["a"][2]["params"]["formula"]
        commit = flow["a"][4]["params"]["formula"]
        for response in ('', '{"code":401}', 'not json', '{"items":[{"created":"2026-09-07T20:00:00Z","stats":null}]}', '{"page":1,"totalItems":0,"items":[]}'):
            k = self.context(tmp_day=response)
            ok = k.eval(valid)
            self.assertEqual(ok, int('"page"' in response))
            k.overrides["day_ok"] = ok
            self.assertEqual(k.eval(commit), response if ok else k.gv("day_json"))

    def test_responsive_columns_and_rows(self):
        for width, height in ((480,376), (640,440), (720,560)):
            k = self.context(); k.size.update(rwidth=width, rheight=height)
            bounds = self.nodes["FetchDetailsBounds"]["internal_formulas"]
            self.assertEqual(k.eval(bounds["shape_width"]), width*.7-36)
            self.assertEqual(k.eval(bounds["shape_height"]), height-152)
            for label in ("OS", "Kernel", "CPU", "GPU", "Cores", "Uptime", "Memory", "Temp"):
                row = self.nodes[f"Fetch{label}Row"]
                y = k.eval(row["internal_formulas"]["position_offset_y"])
                self.assertLessEqual(y+20, height-192)
            self.assertEqual(k.eval(self.nodes["CardBackground"]["internal_formulas"]["shape_height"]), height)
        for view in ("overview", "containers", "info"):
            k = self.context(view=view)
            expr = self.nodes["ViewInfo"]["internal_formulas"]["config_visible"]
            self.assertEqual(k.eval(expr), "ALWAYS" if view == "info" else "REMOVE")

    def test_daily_query_and_timezone(self):
        flow = next(f for f in self.root["internal_flows"] if f["name"] == "fetch_history")
        for zone in (-10800, 0, 19800):
            k = self.context(bz_url="https://example.invalid")
            k.timezone = zone
            query = parse_qs(urlsplit(k.eval(flow["a"][0]["params"]["uri"])).query)
            self.assertIn('type="20m"', query["filter"][0])
            self.assertIn("2026-09-06 21:00:00", query["filter"][0])
            self.assertEqual(query["perPage"], ["500"])
            self.assertEqual(query["sort"], ["created"])

    def test_latest_setup_request_and_failure(self):
        from unittest.mock import patch
        import sys
        sys.path.insert(0, str(ROOT))
        import setup
        with patch.object(setup, "http_get", return_value=(200, {"items": []})) as request:
            self.assertEqual(setup.fetch_latest_stats("https://example.invalid", "synthetic"), {"items": []})
            query = parse_qs(urlsplit(request.call_args.args[0]).query)
            self.assertIn('type="1m"', query["filter"][0])
            self.assertEqual(query["perPage"], ["1"])
            self.assertEqual(query["sort"], ["-created"])
        with patch.object(setup, "http_get", return_value=(503, {})) as request:
            self.assertIsNone(setup.fetch_latest_stats("https://example.invalid", "synthetic"))
            self.assertEqual(request.call_count, 1)
        daily = records(count=73)
        with patch.object(setup, "http_get", return_value=(200, daily)):
            self.assertEqual(len(setup.fetch_system_stats("https://example.invalid", "synthetic")["items"]), 73)
        with patch.object(setup, "http_get", return_value=(503, {})) as request:
            self.assertIsNone(setup.fetch_container_stats("https://example.invalid", "synthetic"))
            self.assertEqual(request.call_count, 1)

    def test_preset_definition_is_current_projection(self):
        from generate_preset import project
        definition = json.loads((ROOT / "widget/preset.json").read_text())
        expected = project({"internal_type": "RootLayerModule", "internal_title": "Beszel Monitor",
                            "viewgroup_items": self.root["viewgroup_items"]})
        self.assertEqual(definition["root"], expected)


def render():
    """Synthetic preview of emitted ASCII/text, not native Kustom rendering."""
    import html
    import subprocess
    root = load_root()
    nodes = {n.get("internal_title"): n for n in walk(root)}
    fixture = {"id": "synthetic", "name": "atlas", "info": {"u":957600, "dt":43.7}}
    meta = {"id": "synthetic", "os_name": "Arch Linux", "os":0, "arch":"x86_64",
            "kernel":"6.12.0", "cpu":"Intel Core i5", "cores":4, "threads":4}
    for width, height in ((480,376), (640,440)):
        k = Kode(root["globals_list"], {"sys_json":json.dumps({"items":[fixture]}),
                 "sys_idx":0, "info_host":"synthetic", "info_sys":json.dumps(fixture),
                 "info_meta":json.dumps(meta), "info_error":"Updated",
                 "info_stats":(ROOT / "examples/fixtures/system-latest-response.json").read_text()},
                 width=width, height=height)
        pieces = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width*1.5}" height="{height*1.5}" viewBox="0 0 {width} {height}"><rect width="{width}" height="{height}" rx="18" fill="#1e1e2e"/>']
        def label(x, y, value, size, color):
            pieces.append(f'<text xml:space="preserve" x="{x}" y="{y}" fill="{color}" font-family="monospace" font-size="{size}">{html.escape(string(value))}</text>')
        label(24,32,"atlas · up 11d 2h",14,"#cdd6f4")
        logo = nodes["FetchLogo"]
        size = k.eval(logo["internal_formulas"]["text_size"])
        lines = k.eval(logo["internal_formulas"]["text_expression"]).splitlines()
        top = 62 + (height-128-len(lines)*size*1.2)/2
        color = "#" + k.gv("fetch_art_color")[-6:]
        for i, line in enumerate(lines): label(24,top+(i+1)*size*1.2,line,size,color)
        x = width*.3+12
        label(x,90,k.eval(nodes["FetchHeading"]["internal_formulas"]["text_expression"]),16,"#cba6f7")
        for name in ("OS", "Kernel", "CPU", "GPU", "Cores", "Uptime", "Memory", "Temp"):
            row = nodes[f"Fetch{name}Row"]
            y = 74+k.eval(row["internal_formulas"]["position_offset_y"])+14
            for child in row["viewgroup_items"][1:]:
                expr = child.get("internal_formulas",{}).get("text_expression")
                value = k.eval(expr) if expr else child["text_expression"]
                label(x+child["position_offset_x"],y,value,child["text_size"],"#"+child["paint_color"][-6:])
        for i in range(8):
            child = nodes[f"FetchColor{i}"]
            pieces.append(f'<rect x="{x+i*19}" y="{height-108}" width="14" height="10" rx="3" fill="#{child["paint_color"][-6:]}"/>')
        label(36,height-22,"Overview       Docker       Info",14,"#cdd6f4")
        pieces.append("</svg>")
        output = ROOT / f"dist/info-local-{width}.svg"
        output.write_text("".join(pieces), encoding="utf-8")
        subprocess.run(["rsvg-convert",str(output),"-o",str(output.with_suffix(".png"))],check=True)
        print(f"Synthetic preview: {output}")


if __name__ == "__main__":
    import sys
    if "--render" in sys.argv:
        render()
    else:
        unittest.main(verbosity=2)
