"""Fixed Kustom geometry, using native serialized anchor/offset names.

The visual frame is 376 Kustom units high; changing tabs never changes its
bounds. Children use transparent shapes to reserve their geometry.
"""

from copy import deepcopy


def walk(node):
    yield node
    for child in node.get("viewgroup_items", []):
        yield from walk(child)


def formula(node, prop, expression):
    node.setdefault("internal_formulas", {})[prop] = expression
    node.setdefault("internal_toggles", {})[prop] = 10
    if prop == "position_offset_x":
        anchor_val = node.get("position_anchor", "")
        pad_prop = "position_padding_right" if "RIGHT" in anchor_val else "position_padding_left"
        node.setdefault("internal_formulas", {})[pad_prop] = expression
        node.setdefault("internal_toggles", {})[pad_prop] = 10
    elif prop == "position_offset_y":
        anchor_val = node.get("position_anchor", "")
        pad_prop = "position_padding_bottom" if "BOTTOM" in anchor_val else "position_padding_top"
        node.setdefault("internal_formulas", {})[pad_prop] = expression
        node.setdefault("internal_toggles", {})[pad_prop] = 10


def frame(title, width, height):
    node = {"internal_type": "ShapeModule", "internal_title": title,
            "shape_type": "RECT", "shape_width": 640.0,
            "shape_height": float(height), "paint_color": "#00000000"}
    formula(node, "shape_width", width)
    return node


def anchor(node, value, x=0, y=0):
    val = value.replace("_", "")
    # Re-anchoring a former right-aligned label must not retain its old padding
    # when it is centered inside a badge (the CPU/RAM misalignment).
    for side in ("left", "right", "top", "bottom"):
        prop = f"position_padding_{side}"
        node[prop] = 0.0
        node.get("internal_formulas", {}).pop(prop, None)
        node.get("internal_toggles", {}).pop(prop, None)
    node.update(position_anchor=val, position_offset_x=float(x),
                position_offset_y=float(y))
    # Native KWGT padding fields
    if "LEFT" in val:
        node["position_padding_left"] = float(x)
    elif "RIGHT" in val:
        node["position_padding_right"] = float(x)
    elif x != 0:
        node["position_padding_left"] = float(x)

    if "TOP" in val:
        node["position_padding_top"] = float(y)
    elif "BOTTOM" in val:
        node["position_padding_bottom"] = float(y)
    elif y != 0:
        node["position_padding_top"] = float(y)


def fix_layout(root):
    nodes = {n.get("internal_title"): n for n in walk(root)}
    root["globals_list"]["cnt_base"] = {
        "index": len(root["globals_list"]), "type": "TEXT", "title": "Container cache path",
        "toggles": 10, "value": ".stats",
        "global_formula": '$if(tc(json, gv(cnt_json), ".stats[0].n") != "", ".stats", if(tc(json, gv(cnt_json), ".items[0].stats[0].n") != "", ".items[0].stats", ".stats"))$'}
    root["globals_list"]["container_count"].update(
        type="TEXT", toggles=10, global_formula='$tc(count, tc(reg, gv(cnt_json), " *:", ":"), tc(utf, 22) + "n" + tc(utf, 22) + ":") + 0$')
    root["globals_list"]["container_page"].update(type="TEXT", value="0")
    root["globals_list"]["cpage"] = {
        "index": len(root["globals_list"]), "type": "TEXT", "title": "Bounded container page",
        "toggles": 10, "value": "0",
        "global_formula": '$mu(max, 0, mu(min, gv(container_page), mu(floor, (gv(container_count) - 1) / 5)))$'}

    # Normalize position fields for Kustom
    for node in walk(root):
        if "position_anchor" in node:
            node["position_anchor"] = node["position_anchor"].replace("_", "")
        for axis in ("x", "y"):
            if f"position_{axis}" in node:
                val = float(node.pop(f"position_{axis}"))
                node[f"position_offset_{axis}"] = val
                anchor_val = node.get("position_anchor", "")
                if axis == "x":
                    pad_key = "position_padding_right" if "RIGHT" in anchor_val else "position_padding_left"
                else:
                    pad_key = "position_padding_bottom" if "BOTTOM" in anchor_val else "position_padding_top"
                node[pad_key] = val
        if "position_offset_x" in node and "position_padding_left" not in node and "position_padding_right" not in node:
            anchor_val = node.get("position_anchor", "")
            pad_key = "position_padding_right" if "RIGHT" in anchor_val else "position_padding_left"
            node[pad_key] = float(node["position_offset_x"])
        if "position_offset_y" in node and "position_padding_top" not in node and "position_padding_bottom" not in node:
            anchor_val = node.get("position_anchor", "")
            pad_key = "position_padding_bottom" if "BOTTOM" in anchor_val else "position_padding_top"
            node[pad_key] = float(node["position_offset_y"])

    content = nodes["ContentFlow"]
    content["internal_type"] = "OverlapLayerModule"
    content.pop("config_stacking", None)
    content.pop("config_margin", None)
    content["viewgroup_items"].insert(0, frame("LayoutBounds", "$si(rwidth)$", 376))
    for title in ("CardBackground", "CardBorder"):
        nodes[title]["shape_height"] = 376.0
        nodes[title]["internal_formulas"].pop("shape_height", None)
        nodes[title]["internal_toggles"].pop("shape_height", None)

    header = nodes["Header"]
    header["internal_type"] = "OverlapLayerModule"
    header.pop("config_stacking", None)
    header.pop("config_margin", None)
    anchor(header, "TOP", y=10)
    header["viewgroup_items"].insert(0, frame("HeaderBounds", "$si(rwidth) - 24$", 44))
    anchor(nodes["StatusIndicator"], "CENTERLEFT", 12)
    anchor(nodes["HostSelector"], "CENTERLEFT", 26)
    nodes["HostTouchArea"].update(shape_width=100.0, shape_height=44.0)
    host = nodes["HostnameText"]
    host["text_size"] = 17.0
    font = host["text_family"]
    original = host["internal_formulas"]["text_expression"][1:-1]
    formula(host, "text_expression", f"$tc(ell, {original}, 12)$")
    anchor(nodes["DotSep"], "CENTERLEFT", 136)
    anchor(nodes["TimeText"], "CENTERLEFT", 148)
    for title in ("DotSep", "TimeText"):
        formula(nodes[title], "config_visible", '$if(gv(view) = "overview", ALWAYS, REMOVE)$')
    refresh = nodes["RefreshTouchTarget"]
    anchor(refresh, "CENTERRIGHT")
    nodes["RefreshGlyph"].update(text_size=30.0, text_expression="󰑐")
    border = deepcopy(nodes["RefreshArea"])
    border.update(internal_title="RefreshBorder", paint_style="STROKE", stroke_width=1.0)
    border["internal_globals"] = {"paint_color": "c_surface1"}
    refresh["viewgroup_items"].insert(1, border)

    # Container Prev/Next buttons in Header (84x44dp targets, right offset 140 and 50)
    for title, offset in (("BtnPrev", 140), ("BtnNext", 50)):
        button = nodes[title]
        anchor(button, "CENTERRIGHT", offset)
        formula(button, "config_visible", '$if(gv(view) = "containers", ALWAYS, REMOVE)$')
        for child in button["viewgroup_items"]:
            if child["internal_type"] == "ShapeModule":
                child.update(shape_width=84.0, shape_height=44.0)
            elif child["internal_type"] == "TextModule":
                child["text_size"] = 16.5
        header["viewgroup_items"].append(button)

    anchor(nodes["ViewArea"], "TOP", y=62)
    anchor(nodes["BottomNav"], "BOTTOM", y=10)
    for title in ("ViewOverview", "ViewContainers", "ViewInfo"):
        anchor(nodes[title], "TOP")

    # Overview Network Card: Replaces sparkline with 3 compact lines (Download, Upload, 24h volume)
    network = nodes["Inner_Network"]
    network["internal_type"] = "OverlapLayerModule"
    network.pop("config_stacking", None)
    network.pop("config_margin", None)

    net_title = nodes["NetTitle"]
    net_title["text_size"] = 19.0
    net_title["text_expression"] = "󰀂 Network"
    anchor(net_title, "TOPLEFT", 14, 12)

    def net_text(name, expr, size=12.0, color_global="c_text"):
        item = {"internal_type": "TextModule", "internal_title": name,
                "text_expression": "", "text_family": font, "text_size": float(size),
                "internal_globals": {"paint_color": color_global}}
        formula(item, "text_expression", expr)
        return item
    down_lbl = net_text("NetDownLabel", "↓ Download", 13.5, "c_subtext")
    anchor(down_lbl, "TOPLEFT", 14, 30)
    down_expr = "$gv(rate_rx)$"
    down_val = net_text("NetDownVal", down_expr, 14.0, "c_text")
    anchor(down_val, "TOPRIGHT", 14, 30)

    up_lbl = net_text("NetUpLabel", "↑ Upload", 13.5, "c_subtext")
    anchor(up_lbl, "TOPLEFT", 14, 52)
    up_expr = "$gv(rate_tx)$"
    up_val = net_text("NetUpVal", up_expr, 14.0, "c_text")
    anchor(up_val, "TOPRIGHT", 14, 52)

    vol_lbl = net_text("NetVolLabel", "↓ 24h Total", 13.0, "c_muted")
    anchor(vol_lbl, "TOPLEFT", 14, 74)
    vol_expr = "$gv(day_rx)$"
    vol_val = net_text("NetVolVal", vol_expr, 13.5, "c_net")
    anchor(vol_val, "TOPRIGHT", 14, 74)

    vol_up_lbl = net_text("NetVolUpLabel", "↑ 24h Total", 13.0, "c_muted")
    anchor(vol_up_lbl, "TOPLEFT", 14, 96)
    vol_up_expr = "$gv(day_tx)$"
    vol_up_val = net_text("NetVolUpVal", vol_up_expr, 13.5, "c_net")
    anchor(vol_up_val, "TOPRIGHT", 14, 96)

    network["viewgroup_items"] = [
        frame("NetworkBounds", '$mu(max, 150, mu(round, (si(rwidth) - 36) / 2))$', 120),
        net_title, down_lbl, down_val, up_lbl, up_val, vol_lbl, vol_val, vol_up_lbl, vol_up_val
    ]

    # Docker Containers View
    containers = nodes["ViewContainers"]
    containers["internal_type"] = "OverlapLayerModule"
    containers.pop("config_stacking", None)
    containers.pop("config_margin", None)

    # Column header labels: NAME, CPU, RAM
    header_row = {
        "internal_type": "OverlapLayerModule",
        "internal_title": "ContainerHeader",
        "viewgroup_items": [
            frame("ContainerHeaderBounds", "$si(rwidth) - 36$", 18),
            net_text("ColLabelName", "NAME", 12.5, "c_muted"),
            net_text("ColLabelCPU", "CPU", 12.5, "c_muted"),
            net_text("ColLabelRAM", "RAM", 12.5, "c_muted"),
        ]
    }
    anchor(header_row, "TOP", y=0)
    anchor(header_row["viewgroup_items"][1], "CENTERLEFT", 36)
    # Match badge centers exactly: outer inset 12, widths 70 / 86, gap 8.
    for index, offset, width in ((2, 106, 70), (3, 12, 86)):
        label_node = header_row["viewgroup_items"][index]
        anchor(label_node, "CENTER")
        column = {"internal_type": "OverlapLayerModule", "internal_title": label_node["internal_title"] + "Column",
                  "viewgroup_items": [frame(label_node["internal_title"] + "Bounds", f"${width}$", 18), label_node]}
        anchor(column, "CENTERRIGHT", offset)
        header_row["viewgroup_items"][index] = column

    rows = containers["viewgroup_items"][:5]
    for i, row in enumerate(rows):
        anchor(row, "TOP", y=20 + i * 41)
        formula(row, "config_visible", f'$if(gv(row{i}_name) != "", ALWAYS, REMOVE)$')
    page = nodes["PageText"]
    anchor(page, "BOTTOM", y=2)
    formula(page, "text_expression", '$if(gv(container_count) > 0, "Page " + (gv(cpage) + 1) + " / " + (mu(floor, (gv(container_count) - 1) / 5) + 1), "Page 1 / 1")$')
    containers["viewgroup_items"] = [frame("ContainerBounds", "$si(rwidth) - 36$", 248), header_row, *rows, page]
    empty = deepcopy(page)
    empty.update(internal_title="ContainersEmpty", position_anchor="CENTER", position_offset_y=0.0)
    formula(empty, "text_expression", '$if(gv(row0_name) = "" & gv(cpage) = 0, "No containers", "")$')
    containers["viewgroup_items"].append(empty)

    for i in range(5):
        left = nodes[f"RowLeft_{i}"]
        right = nodes[f"RowRight_{i}"]

        # Left group: no CLIP_ALL so status dot at x=0 is fully visible
        left["internal_type"] = "OverlapLayerModule"
        left.pop("config_stacking", None)
        left.pop("config_margin", None)
        bounds_left = frame(f"{left['internal_title']}Bounds", "$si(rwidth) - 232$", 32)
        left["viewgroup_items"].insert(0, bounds_left)

        # Right group: with CLIP_ALL for badges
        right["internal_type"] = "OverlapLayerModule"
        right.pop("config_stacking", None)
        right.pop("config_margin", None)
        bounds_right = frame(f"{right['internal_title']}Bounds", "$164$", 32)
        bounds_right["fx_mask"] = "CLIP_ALL"
        right["viewgroup_items"].insert(0, bounds_right)

        # Separate Dot, Glyph, and Name with fixed geometric gap
        dot = left["viewgroup_items"][1]
        dot.update(shape_width=7.0, shape_height=7.0)
        anchor(dot, "CENTERLEFT", 0)
        formula(
            dot,
            "paint_color",
            f'$if(gv(host_status) = "down", gv(c_err), '
            f'if(gv(row{i}_name) = "", gv(c_muted), '
            f'if(gv(row{i}_status) != "", '
            f'if(tc(count, tc(low, gv(row{i}_status)), "exit") > 0 | tc(count, tc(low, gv(row{i}_status)), "stop") > 0 | tc(count, tc(low, gv(row{i}_status)), "dead") > 0, gv(c_err), '
            f'if(gv(stale) = 1, gv(c_warn), gv(c_ok))), '
            f'if(gv(row{i}_mem) != "" & gv(row{i}_mem) > 0, if(gv(stale) = 1, gv(c_warn), gv(c_ok)), gv(c_err)))))$'
        )

        glyph = {
            "internal_type": "TextModule",
            "internal_title": f"Glyph_{i}",
            "text_expression": "",
            "text_family": font,
            "text_size": 15.5,
            "paint_color": "#FF89B4FA",
            "internal_globals": {"paint_color": "c_cpu"}
        }
        anchor(glyph, "CENTERLEFT", 14)

        name = left["viewgroup_items"][2]
        anchor(name, "CENTERLEFT", 34)
        name["text_size"] = 14.5
        formula(name, "text_expression", f'$tc(ell, gv(row{i}_name), mu(max, 8, mu(floor, (si(rwidth) - 274) / 8.6)))$')
        left["viewgroup_items"] = [left["viewgroup_items"][0], dot, glyph, name]

        cpu, mem = right["viewgroup_items"][1:]
        anchor(cpu, "CENTERLEFT")
        anchor(mem, "CENTERRIGHT")
        for key, field in (("name", "n"), ("cpu", "c"), ("mem", "m")):
            path = f'gv(cnt_base) + "[" + (gv(container_page) * 5 + {i}) + "].{field}"'
            expression = f"tc(json, gv(cnt_json), {path})"
            root["globals_list"][f"row{i}_{key}"] = {
                "index": len(root["globals_list"]), "type": "TEXT",
                "title": f"Container {i} {key}", "toggles": 10,
                "global_formula": f'${expression}$', "value": ""}
        path_s = f'gv(cnt_base) + "[" + (gv(container_page) * 5 + {i}) + "].s"'
        path_status = f'gv(cnt_base) + "[" + (gv(container_page) * 5 + {i}) + "].status"'
        expr_status = f'if(tc(json, gv(cnt_json), {path_s}) != "", tc(json, gv(cnt_json), {path_s}), tc(json, gv(cnt_json), {path_status}))'
        root["globals_list"][f"row{i}_status"] = {
            "index": len(root["globals_list"]), "type": "TEXT",
            "title": f"Container {i} status", "toggles": 10,
            "global_formula": f'${expr_status}$', "value": ""}
        formula(cpu, "text_expression", f'$if(gv(row{i}_cpu) != "", mu(round, gv(row{i}_cpu), 1) + "%", "—")$')
        formula(mem, "text_expression", f'$if(gv(row{i}_mem) != "", mu(round, gv(row{i}_mem), 1) + " MiB", "—")$')
        badges = []
        for text, width, side in ((cpu, 70, "CENTERLEFT"), (mem, 86, "CENTERRIGHT")):
            box = frame(f'BadgeBounds_{i}_{side}', f'${width}$', 28)
            box.update(paint_color="#FF313244", shape_corners=6.0, fx_mask="CLIP_ALL")
            anchor(text, "CENTER")
            badge = {"internal_type": "OverlapLayerModule", "internal_title": f'Badge_{i}_{side}',
                     "viewgroup_items": [box, text]}
            anchor(badge, side)
            badges.append(badge)
        right["viewgroup_items"] = [right["viewgroup_items"][0], *badges]

    # Cache shrinkage must immediately clamp both labels and data lookups
    for node in walk(root):
        for prop, expression in node.get("internal_formulas", {}).items():
            node["internal_formulas"][prop] = expression.replace("gv(container_page)", "gv(cpage)")
        for event in node.get("internal_events", []):
            if "switch_text" in event:
                event["switch_text"] = event["switch_text"].replace("gv(container_page)", "gv(cpage)")
    for key, value in root["globals_list"].items():
        if key.startswith("row"):
            value["global_formula"] = value["global_formula"].replace("gv(container_page)", "gv(cpage)")

    # Fill the launcher's available height, preserving a 376-unit minimum for
    # legibility. Header/navigation remain fixed; cards and plot share the gain.
    globals_ = root["globals_list"]
    globals_["frameh"] = {"index": len(globals_), "type": "TEXT", "value": "376", "toggles": 10,
                         "global_formula": "$mu(max, 376, si(rheight))$"}
    for title in ("LayoutBounds", "CardBackground", "CardBorder"):
        target = next(n for n in walk(root) if n.get("internal_title") == title)
        formula(target, "shape_height", "$gv(frameh)$")
    formula(nodes["ViewAreaSpacer"], "shape_height", "$gv(frameh) - 128$")
    for title in ("CPU", "Memory", "Disk", "Network"):
        for item in walk(nodes[f"Card_{title}"]):
            if item.get("shape_height") == 120:
                formula(item, "shape_height", "$(gv(frameh) - 136) / 2$")
    for title in ("ContainerBounds",):
        target = next(n for n in walk(root) if n.get("internal_title") == title)
        formula(target, "shape_height", "$gv(frameh) - 128$")
    for i, row in enumerate(rows):
        formula(row, "position_offset_y", f'$20 + {i} * (gv(frameh) - 171) / 5$')
