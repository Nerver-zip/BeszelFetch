"""Fastfetch-inspired view backed only by button-triggered Beszel snapshots."""
from copy import deepcopy
import json
from pathlib import Path

if __package__:
    from .widget_layout import anchor, formula, frame, walk
else:
    from widget_layout import anchor, formula, frame, walk


def build_fetch(root):
    globals_ = root["globals_list"]
    nodes = {n.get("internal_title"): n for n in walk(root)}
    font = nodes["HostnameText"]["text_family"]

    def derived(name, expression):
        globals_[name] = {"index": len(globals_), "type": "TEXT", "title": name,
                          "value": "", "toggles": 10, "global_formula": f"${expression}$"}

    selected = 'tc(json, gv(sys_json), ".items[" + gv(sys_idx) + "].id")'
    derived("info_ready", f'if(gv(info_host) = {selected} & gv(info_host) != "", 1, 0)')

    def value(cache, path):
        return f'tc(json, gv({cache}), "{path}")'

    def fallback(*values, default='"N/A"'):
        expr = default
        for v in reversed(values):
            expr = f'if({v} != "", {v}, {expr})'
        return expr

    for name, paths in (
        ("fetch_host", [value("info_meta", ".hostname"), value("info_sys", ".name")]),
        ("fetch_kernel", [value("info_meta", ".kernel"), value("info_sys", ".info.k")]),
        ("fetch_cpu", [value("info_meta", ".cpu"), value("info_sys", ".info.m")]),
        ("fetch_os_name", [value("info_meta", ".os_name"), value("info_sys", ".info.o")]),
        ("fetch_os_id", [value("info_meta", ".os"), value("info_sys", ".info.os")]),
        ("fetch_arch", [value("info_meta", ".arch")]),
    ):
        derived(name, f'if(gv(info_ready) = 1, {fallback(*paths)}, "N/A")')
    enum = 'if(gv(fetch_os_id) = 0, "Linux", if(gv(fetch_os_id) = 1, "macOS", if(gv(fetch_os_id) = 2, "Windows", if(gv(fetch_os_id) = 3, "FreeBSD", "Unknown OS"))))'
    derived("fetch_os", f'if(gv(fetch_os_name) != "N/A", gv(fetch_os_name), {enum})')
    derived("fetch_os_lower", 'tc(low, gv(fetch_os))')
    derived("fetch_os_line", 'gv(fetch_os) + if(gv(fetch_arch) != "N/A", " · " + gv(fetch_arch), "")')
    for name, path in (("fetch_u", ".info.u"), ("fetch_temp", ".info.dt")):
        derived(name, f'if(gv(info_ready) = 1, {value("info_sys", path)}, "")')
    derived("fetch_uptime", 'if(gv(fetch_u) != "", mu(floor, gv(fetch_u) / 86400) + "d " + (mu(floor, gv(fetch_u) / 3600) - mu(floor, gv(fetch_u) / 86400) * 24) + "h", "N/A")')
    derived("fetch_temperature", 'if(gv(fetch_temp) != "", mu(round, gv(fetch_temp), 1) + "°C", "N/A")')
    used, total = value("info_stats", ".items[0].stats.mu"), value("info_stats", ".items[0].stats.m")
    derived("fetch_memory", f'if(gv(info_ready) = 1 & {used} != "" & {total} != "", mu(round, {used}, 1) + " / " + mu(round, {total}, 1) + " GiB", "N/A")')
    cores = fallback(value("info_meta", ".cores"), value("info_sys", ".info.c"), default='0')
    threads = fallback(value("info_meta", ".threads"), value("info_sys", ".info.t"), default='0')
    derived("fetch_cores", f'if(gv(info_ready) = 1 & ({cores}) > 0, ({cores}) + " cores / " + ({threads}) + " threads", "N/A")')
    # GPU IDs are dynamic map keys; a JSONPath wildcard gets their names.
    derived("fetch_gpus", f'if(gv(info_ready) = 1, {value("info_stats", ".items[0].stats.g.*.n")}, "")')
    gpu0, gpu1 = value("fetch_gpus", "$[0]"), value("fetch_gpus", "$[1]")
    derived("fetch_gpu", f'if({gpu0} != "", {gpu0} + if({gpu1} != "", " + " + {gpu1}, ""), "Not reported")')

    # Match names before the OS enum; don't mislabel an unknown OS as Linux.
    aliases = [("debian", "debian"), ("ubuntu", "ubuntu"), ("arch", "arch"),
               ("fedora", "fedora"), ("alpine", "alpine"), ("nixos", "nixos"),
               ("mint", "linuxmint"), ("manjaro", "manjaro"), ("rasp", "raspbian"),
               ("red hat", "rhel"), ("rocky", "rocky"), ("centos", "centos"),
               ("suse", "opensuse"), ("gentoo", "gentoo"), ("void", "void"),
               ("freebsd", "freebsd"), ("openbsd", "openbsd"), ("netbsd", "netbsd"),
               ("android", "android")]
    expr = 'if(gv(fetch_os_id) = 0, "linux", if(gv(fetch_os_id) = 1, "macos", if(gv(fetch_os_id) = 2, "windows_11", if(gv(fetch_os_id) = 3, "freebsd", "unknown"))))'
    for needle, logo in reversed(aliases):
        expr = f'if(tc(count, gv(fetch_os_lower), "{needle}") > 0, "{logo}", {expr})'
    derived("fetch_logo", expr)

    def text(name, expression, size=12, color="c_text"):
        node = {"internal_type": "TextModule", "internal_title": name,
                "text_expression": expression, "text_family": font, "text_size": float(size),
                "paint_color": globals_[color]["value"], "internal_globals": {"paint_color": color}}
        # Set an explicit literal fallback AND native formula binding. The old
        # Info only wrote internal_globals; native rendering defaulted to white.
        formula(node, "paint_color", f'$gv({color})$')
        if expression.startswith("$"):
            formula(node, "text_expression", expression)
        return node

    info = nodes["ViewInfo"]
    formula(info, "config_visible", '$if(gv(view) = "info", ALWAYS, REMOVE)$')
    bounds = frame("InfoBounds", "$si(rwidth) - 24$", 248)
    formula(bounds, "shape_height", "$gv(frameh) - 128$")
    info["viewgroup_items"] = [bounds]
    assets = json.loads((Path(__file__).resolve().parents[1] / "widget/assets/fastfetch/logos.json").read_text())["logos"]
    assets["unknown"] = "  .--------.\n  |  HOST  |\n  |   ??   |\n  |________|\n     |__|"
    # A TextModule does not reliably support layer config_visible in KWGT.
    # ONE text module eliminates overlapping hidden distro variants entirely.
    catalog = {}
    for name, art in assets.items():
        color = "c_cpu"
        if name in ("debian", "rhel", "freebsd", "openbsd"): color = "c_err"
        elif name in ("ubuntu", "linux", "raspbian"): color = "c_peach"
        elif name in ("linuxmint", "manjaro", "opensuse", "void", "android"): color = "c_ok"
        elif name in ("gentoo", "nixos"): color = "c_ram"
        catalog[name] = {"art": art, "cols": max(map(len, art.splitlines())),
                         "color": globals_[color]["value"]}
    globals_["ascii_data"] = {"index": len(globals_), "type": "TEXT",
                              "title": "Fastfetch ASCII catalog", "value": json.dumps(catalog)}
    derived("fetch_art", 'tc(json, gv(ascii_data), "." + gv(fetch_logo) + ".art")')
    derived("fetch_art_cols", 'tc(json, gv(ascii_data), "." + gv(fetch_logo) + ".cols")')
    derived("fetch_art_color", 'tc(json, gv(ascii_data), "." + gv(fetch_logo) + ".color")')
    logo = text("FetchLogo", "$gv(fetch_art)$", 16, "c_cpu")
    logo["text_align"] = "LEFT"
    anchor(logo, "CENTERLEFT", 12)
    formula(logo, "text_size", '$mu(min, 18, (si(rwidth) * 0.27 - 24) / (gv(fetch_art_cols) * 0.62))$')
    formula(logo, "paint_color", "$gv(fetch_art_color)$")
    info["viewgroup_items"].append(logo)
    license_text = (Path(__file__).resolve().parents[1] / "widget/assets/fastfetch/LICENSE.fastfetch").read_text()
    info["internal_description"] = "ASCII logos adapted from Fastfetch.\n" + license_text
    content = {"internal_type": "OverlapLayerModule", "internal_title": "FetchDetails", "viewgroup_items": []}
    anchor(content, "TOPRIGHT", 12, 12)
    cb = frame("FetchDetailsBounds", "$si(rwidth) * 0.7 - 36$", 224)
    formula(cb, "shape_height", "$gv(frameh) - 152$")
    content["viewgroup_items"].append(cb)
    heading = text("FetchHeading", '$if(gv(info_ready) = 1, tc(ell, gv(fetch_host), 24) + "@beszel", "~/homelab")$', 18, "c_ram")
    anchor(heading, "TOPLEFT")
    content["viewgroup_items"].append(heading)
    specs = [("OS", "fetch_os_line", "c_cpu"), ("Kernel", "fetch_kernel", "c_net"),
             ("CPU", "fetch_cpu", "c_peach"), ("GPU", "fetch_gpu", "c_ok"),
             ("Cores", "fetch_cores", "c_warn"), ("Uptime", "fetch_uptime", "c_disk"),
             ("Memory", "fetch_memory", "c_ram"), ("Temp", "fetch_temperature", "c_err")]
    for i, (label, global_, color) in enumerate(specs):
        row = {"internal_type": "OverlapLayerModule", "internal_title": f"Fetch{label}Row", "viewgroup_items": [frame(f"Fetch{label}Bounds", "$si(rwidth) * 0.7 - 36$", 20)]}
        anchor(row, "TOPLEFT")
        formula(row, "position_offset_y", f'$28 + {i} * (gv(frameh) - 224) / 8$')
        label_node = text(f"Fetch{label}Label", "├ " + label, 14, color)
        colon = text(f"Fetch{label}Colon", ":", 14, "c_subtext")
        value_node = text(f"Fetch{label}Value", f'$tc(ell, gv({global_}), mu(max, 12, mu(floor, (si(rwidth) * 0.7 - 130) / 7.2)))$', 14)
        anchor(label_node, "CENTERLEFT")
        anchor(colon, "CENTERLEFT", 76)
        anchor(value_node, "CENTERLEFT", 90)
        row["viewgroup_items"].extend([label_node, colon, value_node])
        content["viewgroup_items"].append(row)
    for i, color in enumerate(("c_err", "c_peach", "c_warn", "c_ok", "c_disk", "c_net", "c_cpu", "c_ram")):
        chip = frame(f"FetchColor{i}", "$14$", 10)
        chip.update(shape_corners=3.0, paint_color=globals_[color]["value"])
        formula(chip, "paint_color", f'$gv({color})$')
        anchor(chip, "BOTTOMLEFT", i*19, 20)
        content["viewgroup_items"].append(chip)
    # The Info card is intentionally free of a persistent status legend. Errors
    # remain in the cache global for diagnostics, but do not consume visual
    # space below the Fastfetch details.
    info["viewgroup_items"].append(content)

    # Tapping Info and its refresh button are the ONLY triggers of bzinfo.
    nodes["TabInfo"]["internal_events"].append({"type": "SINGLE_TAP", "action": "TRIGGER_FLOW", "flow_id": "bzinfo"})
    refresh = nodes["RefreshTouchTarget"]
    manual = deepcopy(refresh)
    manual["internal_title"] = "InfoRefreshTouchTarget"
    for node in walk(manual):
        if node is not manual and "internal_title" in node:
            node["internal_title"] = "Info" + node["internal_title"]
    manual["internal_events"] = [{"type": "SINGLE_TAP", "action": "TRIGGER_FLOW", "flow_id": "bzinfo"}]
    formula(manual, "config_visible", '$if(gv(view) = "info", ALWAYS, REMOVE)$')
    formula(refresh, "config_visible", '$if(gv(view) != "info", ALWAYS, REMOVE)$')
    nodes["Header"]["viewgroup_items"].append(manual)
