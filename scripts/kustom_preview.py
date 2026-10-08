"""Render the generated Kustom tree using synthetic cached data.

Geometry, visibility, strings, colors and progress come from serialized modules.
The supported native subset is deliberately explicit: unsupported modules,
bindings and formulas raise rather than quietly producing a plausible mock.
"""
import base64
from copy import deepcopy
from dataclasses import dataclass, field
from functools import lru_cache
import html
import hashlib
import json
import math
from pathlib import Path
import re
import struct

if __package__:
    from .generate_clip import build_kustom_clip, FONT_SRC
    from .kustom_eval import Kode, string
else:
    from generate_clip import build_kustom_clip, FONT_SRC
    from kustom_eval import Kode, string

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ("overview", "containers", "info")
STATES = ("normal", "stale", "empty", "missing", "alert")
# Device capture: ~1.5 physical pixels per Kustom unit, ~990 x 636 widget frame.
DEFAULT_WIDTH, DEFAULT_HEIGHT = 660, 424


class FontMetrics:
    """Read TrueType advances/vertical metrics without a second font dependency."""

    def __init__(self, path=FONT_SRC):
        self.data = d = Path(path).read_bytes()
        tables = {}
        for i in range(struct.unpack_from(">H", d, 4)[0]):
            tag, _, offset, _ = struct.unpack_from(">4sIII", d, 12 + i * 16)
            tables[tag] = offset
        self.units = struct.unpack_from(">H", d, tables[b"head"] + 18)[0]
        self.ascent, descent, gap = struct.unpack_from(">hhh", d, tables[b"hhea"] + 4)
        self.line_height = self.ascent - descent + gap
        count = struct.unpack_from(">H", d, tables[b"hhea"] + 34)[0]
        self.advances = [struct.unpack_from(">H", d, tables[b"hmtx"] + i * 4)[0] for i in range(count)]
        cmap = tables[b"cmap"]
        subtables = []
        for i in range(struct.unpack_from(">H", d, cmap + 2)[0]):
            platform, encoding, offset = struct.unpack_from(">HHI", d, cmap + 4 + i * 8)
            start = cmap + offset
            fmt = struct.unpack_from(">H", d, start)[0]
            if platform in (0, 3) and fmt in (4, 12):
                subtables.append((fmt, start))
        self.glyphs = {}
        for fmt, start in sorted(subtables):
            if fmt == 12:
                for i in range(struct.unpack_from(">I", d, start + 12)[0]):
                    first, last, glyph = struct.unpack_from(">III", d, start + 16 + i * 12)
                    self.glyphs.update({c: glyph + c - first for c in range(first, last + 1)})
            else:
                n = struct.unpack_from(">H", d, start + 6)[0] // 2
                ends, starts, deltas, offsets = start + 14, start + 16 + 2 * n, start + 16 + 4 * n, start + 16 + 6 * n
                for i in range(n):
                    end = struct.unpack_from(">H", d, ends + i * 2)[0]
                    first = struct.unpack_from(">H", d, starts + i * 2)[0]
                    delta = struct.unpack_from(">h", d, deltas + i * 2)[0]
                    offset = struct.unpack_from(">H", d, offsets + i * 2)[0]
                    for c in range(first, min(end, 65534) + 1):
                        glyph = (c + delta) & 65535
                        if offset:
                            glyph = struct.unpack_from(">H", d, offsets + i * 2 + offset + 2 * (c - first))[0]
                            if glyph:
                                glyph = (glyph + delta) & 65535
                        self.glyphs[c] = glyph

    def width(self, text, size):
        return sum(self.advances[min(self.glyphs.get(ord(c), 0), len(self.advances) - 1)] for c in text) * size / self.units


@lru_cache(maxsize=1)
def font_metrics():
    return FontMetrics()


@lru_cache(maxsize=1)
def font_css():
    encoded = base64.b64encode(FONT_SRC.read_bytes()).decode("ascii")
    return '@font-face{font-family:WidgetMono;src:url(data:font/ttf;base64,' + encoded + ') format("truetype");font-weight:400;font-style:normal;font-display:block;}'


def fixture_globals(state="normal", page=0):
    if state not in STATES:
        raise ValueError(f"Unsupported preview state: {state}")
    g = deepcopy(json.loads((ROOT / "examples/fixtures/theme-preview.json").read_text())["globals"])
    g["container_page"] = page
    if state == "stale":
        g.update(stale=1, info_error="Refresh failed · cache kept")
    elif state == "alert":
        g["sys_json"]["items"][0]["status"] = "down"
        for stats in (g["sys_json"]["items"][0]["info"], g["latest"]["items"][0]["stats"]):
            stats.update(cpu=88, mp=94, dp=97)
        g["cnt_json"]["stats"][0].update(c=88, s="exited")
        g["info_error"] = "Host offline · cache kept"
    elif state == "empty":
        g.update(sys_json={"items": []}, latest={"items": []}, cnt_json={"stats": []},
                 info_host="", info_sys={}, info_meta={}, info_stats={"items": []},
                 net_24h_rx=0, net_24h_tx=0)
    elif state == "missing":
        g["sys_json"]["items"][0]["info"].pop("dt")
        g["sys_json"]["items"][0]["info"].pop("la")
        g["info_sys"]["info"].pop("dt")
        for key in ("kernel", "cpu", "cores", "threads"):
            g["info_meta"].pop(key)
    return {name: json.dumps(value) if isinstance(value, (dict, list)) else value for name, value in g.items()}


def css_color(value):
    """Kustom ARGB is alpha first; SVG hex alpha is last."""
    value = str(value).upper()
    if value.startswith("#") and len(value) == 9:
        return "#" + value[3:] + value[1:3]
    if value.startswith("#") and len(value) == 7:
        return value
    raise ValueError(f"Unsupported color: {value!r}")


@dataclass
class Layout:
    node: dict
    width: float
    height: float
    children: list = field(default_factory=list)
    text: str = ""
    size: float = 0


class KustomRenderer:
    def __init__(self, root, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, view="overview", state="normal", page=0):
        if view not in VIEWS or width <= 0 or height < 376:
            raise ValueError("Use overview/containers/info, a positive width, and height >= 376")
        self.root, self.width, self.height = root, width, height
        self.kode = Kode(root["globals_list"], {**fixture_globals(state, page), "view": view}, width=width, height=height)
        self.font = font_metrics()
        self.view = view
        self.warnings = []
        self.positions = {}
        colors = {k: v["value"] for k, v in root["globals_list"].items() if v.get("type") == "COLOR"}
        self.prefix = hashlib.sha256(json.dumps(colors, sort_keys=True).encode()).hexdigest()[:12] + f"-{view}-{page}-{state}"
        self.mask_index = 0

    def prop(self, node, name, default=None):
        toggles = node.get("internal_toggles", {})
        toggle = toggles.get(name, 0)
        if toggle not in (0, 10):
            raise ValueError(f"Unsupported native binding {node.get('internal_title')}.{name}: {toggle}")
        if toggle == 10:
            value = node.get("internal_formulas", {}).get(name)
            if value is None:
                raise ValueError(f"Missing formula for {node.get('internal_title')}.{name}")
        else:
            # internal_globals alone is inactive in the captured preset. Preserve
            # the serialized literal/default, including white text on Latte.
            value = node.get(name, default)
        if isinstance(value, str) and "$" in value:
            if re.fullmatch(r"\$[^$]*\$", value):
                return self.kode.eval(value)
            return re.sub(r"\$([^$]*)\$", lambda m: string(self.kode.eval(m.group(1))), value)
        return value

    def offset(self, n, axis):
        anchor = n.get("position_anchor", "CENTER")
        side = ("right" if "RIGHT" in anchor else "left") if axis == "x" else ("bottom" if "BOTTOM" in anchor else "top")
        return float(self.prop(n, "position_padding_" + side, self.prop(n, "position_offset_" + axis, 0)))

    def measure(self, n):
        typ = n["internal_type"]
        # Native captures show TextModule ignores layer visibility (also noted
        # in widget_fetch.py). Its containing layer still controls visibility.
        if typ != "TextModule" and self.prop(n, "config_visible", "ALWAYS") == "REMOVE":
            return None
        if typ == "BitmapModule":
            if n.get("bitmap_bitmap"):
                raise ValueError("Bitmap effects need a native reference; use an external preview backdrop")
            return None
        if typ == "ShapeModule":
            return Layout(n, float(self.prop(n, "shape_width", 0)), float(self.prop(n, "shape_height", 0)))
        if typ == "ProgressModule":
            if self.prop(n, "style_style") != "CIRCLE":
                raise ValueError("Only emitted circular progress is supported")
            # Circle size is the stroke centerline diameter; the stroke extends
            # beyond it. The captured 72 + 8 ring occupies 80 Kustom units.
            diameter = float(self.prop(n, "style_size")) + float(self.prop(n, "style_height"))
            return Layout(n, diameter, diameter)
        if typ == "TextModule":
            if Path(n.get("text_family", "")).name != FONT_SRC.name:
                raise ValueError(f"Unbundled font on {n.get('internal_title')}")
            text, size = string(self.prop(n, "text_expression", "")), float(self.prop(n, "text_size", 12))
            lines = text.split("\n")
            return Layout(n, max(self.font.width(line, size) for line in lines),
                          len(lines) * size * self.font.line_height / self.font.units, text=text, size=size)
        if typ not in ("KomponentModule", "OverlapLayerModule", "StackLayerModule"):
            raise ValueError(f"Unsupported module: {typ}")
        children = [item for c in n.get("viewgroup_items", []) if (item := self.measure(c)) is not None]
        margin = float(self.prop(n, "config_margin", 0))
        stacking = self.prop(n, "config_stacking", "")
        if typ == "StackLayerModule":
            if stacking not in ("VERTICAL", "HORIZONTAL_CENTER"):
                raise ValueError(f"Unsupported stacking: {stacking}")
            vertical = stacking == "VERTICAL"
            widths, heights = [c.width for c in children], [c.height for c in children]
            w = max(widths, default=0) if vertical else sum(widths) + margin * max(0, len(children) - 1)
            h = sum(heights) + margin * max(0, len(children) - 1) if vertical else max(heights, default=0)
            positioned, cursor = [], 0
            for child in children:
                positioned.append((child, 0 if vertical else cursor, cursor if vertical else (h - child.height) / 2))
                cursor += (child.height if vertical else child.width) + margin
            return Layout(n, w, h, positioned)
        w = max((c.width + abs(self.offset(c.node, "x")) for c in children), default=0)
        h = max((c.height + abs(self.offset(c.node, "y")) for c in children), default=0)
        positioned = []
        for child in children:
            a = child.node.get("position_anchor", "CENTER")
            dx, dy = self.offset(child.node, "x"), self.offset(child.node, "y")
            x = dx if "LEFT" in a else w - child.width - dx if "RIGHT" in a else (w - child.width) / 2 + dx
            y = dy if "TOP" in a else h - child.height - dy if "BOTTOM" in a else (h - child.height) / 2 + dy
            positioned.append((child, x, y))
        return Layout(n, w, h, positioned)

    def color(self, n, prop="paint_color"):
        value = self.prop(n, prop, "#FFFFFFFF")
        if prop not in n and n.get("internal_toggles", {}).get(prop) != 10:
            self.warnings.append(n.get("internal_title", "unnamed") + ": missing " + prop + " → white")
        return css_color(value)

    def draw(self, layout, x=0, y=0, parent_x=0, parent_y=0):
        n = layout.node
        title = n.get("internal_title", "")
        self.positions[title] = (parent_x + x, parent_y + y, layout.width, layout.height)
        attrs = f'data-node="{html.escape(title, quote=True)}"'
        typ, w, h = n["internal_type"], layout.width, layout.height
        pieces = [f'<g {attrs} transform="translate({x:.4f} {y:.4f})">']
        if typ == "ShapeModule":
            color = self.color(n)
            stroke = self.prop(n, "paint_style", "FILL") == "STROKE"
            paint = f'fill="none" stroke="{color}" stroke-width="{self.prop(n, "stroke_width", 0)}"' if stroke else f'fill="{color}"'
            shape = self.prop(n, "shape_type", "RECT")
            if shape == "CIRCLE":
                pieces.append(f'<ellipse cx="{w/2}" cy="{h/2}" rx="{w/2}" ry="{h/2}" {paint}/>')
            elif shape == "RECT":
                pieces.append(f'<rect width="{w}" height="{h}" rx="{self.prop(n, "shape_corners", 0)}" {paint}/>')
            else:
                raise ValueError(f"Unsupported shape: {shape}")
        elif typ == "ProgressModule":
            thick = float(self.prop(n, "style_height"))
            radius = (w - thick) / 2
            length = 2 * math.pi * radius
            level = max(0, min(100, float(self.prop(n, "progress_level"))))
            pieces.append(f'<circle cx="{w/2}" cy="{w/2}" r="{radius}" fill="none" stroke="{self.color(n, "color_bgcolor")}" stroke-width="{thick}"/>')
            pieces.append(f'<circle cx="{w/2}" cy="{w/2}" r="{radius}" fill="none" stroke="{self.color(n, "color_fgcolor")}" stroke-width="{thick}" stroke-dasharray="{length*level/100} {length}" transform="rotate(-90 {w/2} {w/2})"/>')
        elif typ == "TextModule":
            color = self.color(n)
            for i, line in enumerate(layout.text.split("\n")):
                align = self.prop(n, "text_align", "LEFT")
                tx = 0 if align == "LEFT" else w if align == "RIGHT" else w/2
                anchor = "start" if align == "LEFT" else "end" if align == "RIGHT" else "middle"
                baseline = layout.size * (self.font.ascent + i * self.font.line_height) / self.font.units
                pieces.append(f'<text x="{tx}" y="{baseline}" font-family="WidgetMono" font-size="{layout.size}" font-weight="400" text-anchor="{anchor}" fill="{color}" xml:space="preserve" style="white-space:pre">{html.escape(line)}</text>')
        else:
            masks = [(child, cx, cy) for child, cx, cy in layout.children if child.node.get("fx_mask") == "CLIP_ALL"]
            if masks:
                self.mask_index += 1
                mask_id = f"mask-{self.prefix}-{self.mask_index}"
                pieces.append(f'<defs><clipPath id="{mask_id}">')
                for child, cx, cy in masks:
                    shape = child.node.get("shape_type", "RECT")
                    if shape == "RECT":
                        pieces.append(f'<rect x="{cx}" y="{cy}" width="{child.width}" height="{child.height}" rx="{self.prop(child.node, "shape_corners", 0)}"/>')
                    elif shape == "CIRCLE":
                        pieces.append(f'<ellipse cx="{cx+child.width/2}" cy="{cy+child.height/2}" rx="{child.width/2}" ry="{child.height/2}"/>')
                    else:
                        raise ValueError(f"Unsupported clipping shape: {shape}")
                pieces.append(f'</clipPath></defs><g clip-path="url(#{mask_id})">')
            for child, cx, cy in layout.children:
                if child.node.get("fx_mask") != "CLIP_ALL":
                    pieces.append(self.draw(child, cx, cy, parent_x + x, parent_y + y))
            if masks:
                pieces.append("</g>")
        pieces.append("</g>")
        return "".join(pieces)

    def render(self, embed_font=False):
        layout = self.measure(self.root)
        if abs(layout.width - self.width) > .01 or abs(layout.height - self.height) > .01:
            raise ValueError(f"Tree frame {layout.width}x{layout.height} exceeds requested {self.width}x{self.height}")
        content = self.draw(layout)
        style = "<style>" + font_css() + "</style>" if embed_font else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}" '
                f'data-view="{self.view}" class="widget-preview-svg" role="group" aria-label="{self.view} mocked widget">{style}{content}</svg>')


def render_widget(theme, view="overview", width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, state="normal", page=0, embed_font=False):
    root = build_kustom_clip(write_outputs=False, theme=theme)
    return KustomRenderer(root, width, height, view, state, page).render(embed_font=embed_font)
