"""Inspect colors actually emitted by the generated tree on solid backdrops.

Text-center samples composite preceding filled shapes. Decorative ASCII art
uses the graphic target. This does not emulate wallpaper effects or antialiasing.
"""
from .kustom_preview import KustomRenderer, VIEWS
from .theme_catalog import composite_color, contrast_ratio
from .widget_layout import walk


def binding_failures(root):
    """Text and progress paints must use active formula bindings to theme globals."""
    failures = []
    for node in walk(root):
        props = {"TextModule": ("paint_color",), "ProgressModule": ("color_fgcolor", "color_bgcolor")}.get(node["internal_type"], ())
        for prop in props:
            if (node.get("internal_toggles", {}).get(prop) != 10
                    or not node.get("internal_formulas", {}).get(prop)
                    or node.get("internal_globals", {}).get(prop) not in root["globals_list"]):
                failures.append(f"{node.get('internal_title', '')}.{prop}")
    return failures


def composite_argb(color, background):
    alpha = int(color[1:3], 16) if len(color) == 9 else 255
    return composite_color(color, background, alpha)


def paint_order(layout, x=0, y=0):
    yield layout, x, y
    for child, cx, cy in layout.children:
        if child.node.get("fx_mask") != "CLIP_ALL":
            yield from paint_order(child, x+cx, y+cy)


def rendered_samples(root, view="overview", state="normal", backdrop="#000000", width=660, height=424, page=0):
    renderer = KustomRenderer(root, width, height, view, state, page)
    layout = renderer.measure(root)
    fills, samples = [], []
    def background_at(px, py):
        background = backdrop
        for x, y, w, h, color, shape in fills:
            if not (x <= px <= x+w and y <= py <= y+h):
                continue
            if shape == "CIRCLE" and ((px-x-w/2)/(w/2))**2 + ((py-y-h/2)/(h/2))**2 > 1:
                continue
            background = composite_argb(color, background)
        return background
    for item, x, y in paint_order(layout):
        node = item.node
        typ, title = node["internal_type"], node.get("internal_title", "")
        if typ == "ShapeModule":
            color = renderer.prop(node, "paint_color", "#FFFFFFFF")
            style = node.get("paint_style", "FILL")
            # Status dots and active/action outlines communicate state; neutral
            # card dividers and palette swatches are decorative.
            if (node.get("shape_type") == "CIRCLE"
                    or (style == "STROKE" and color == root['globals_list']['c_accent']['value'])):
                bg = background_at(x+item.width/2, y+item.height/2)
                fg = composite_argb(color, bg)
                samples.append({"node": title or "ActionOutline", "kind": "graphic",
                                "foreground": fg, "background": bg, "contrast": contrast_ratio(fg, bg),
                                "view": view, "state": state, "backdrop": backdrop})
            if style == "FILL":
                fills.append((x, y, item.width, item.height, color, node.get("shape_type", "RECT")))
        elif typ == "TextModule" and item.text.strip():
            bg = background_at(x+item.width/2, y+item.height/2)
            color = renderer.prop(node, "paint_color", "#FFFFFFFF")
            fg = composite_argb(color, bg)
            samples.append({"node": title, "kind": "graphic" if title == "FetchLogo" else "text",
                            "foreground": fg, "background": bg, "contrast": contrast_ratio(fg, bg),
                            "view": view, "state": state, "backdrop": backdrop})
        elif typ == "ProgressModule":
            fg = renderer.prop(node, "color_fgcolor")
            for bg in (background_at(x+item.width/2, y+item.height/2), renderer.prop(node, "color_bgcolor")):
                samples.append({"node": title, "kind": "graphic", "foreground": fg, "background": bg,
                                "contrast": contrast_ratio(fg, bg), "view": view, "state": state, "backdrop": backdrop})
    return samples


def contrast_failures(root, states=("normal",), sizes=((660, 424),)):
    failures = []
    for width, height in sizes:
        for state in states:
            for backdrop in ("#000000", "#FFFFFF"):
                for view in VIEWS:
                    for sample in rendered_samples(root, view, state, backdrop, width, height):
                        target = 3 if sample['kind'] == 'graphic' else 4.5
                        if sample['contrast'] < target:
                            failures.append(sample)
    return failures
