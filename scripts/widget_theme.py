"""Bind native paint properties; retain all geometry, data logic and actions."""
if __package__:
    from .widget_layout import formula, walk
else:
    from widget_layout import formula, walk

TEXT_ACCENTS = {"c_accent", "c_cpu", "c_ram", "c_disk", "c_net", "c_ok", "c_warn", "c_peach", "c_err"}


def bind(node, globals_, name, prop="paint_color", expression=None):
    node[prop] = globals_[name]["value"]
    node.setdefault("internal_globals", {})[prop] = name
    formula(node, prop, expression or f"$gv({name})$")


def apply_theme(root):
    globals_ = root["globals_list"]
    # Parent overrides run after children have their standard bindings.
    for node in reversed(list(walk(root))):
        typ = node["internal_type"]
        title = node.get("internal_title", "")
        for prop, role in list(node.get("internal_globals", {}).items()):
            if role not in globals_ or globals_[role].get("type") != "COLOR":
                continue
            expression = node.get("internal_formulas", {}).get(prop)
            if typ == "TextModule" and prop == "paint_color" and role in TEXT_ACCENTS and title != "FetchLogo":
                role += "_text"
                if expression:
                    for accent in TEXT_ACCENTS:
                        expression = expression.replace(f"gv({accent})", f"gv({accent}_text)")
            bind(node, globals_, role, prop, expression)
        if typ == "TextModule" and title != "FetchLogo" and "paint_color" not in node.get("internal_toggles", {}):
            bind(node, globals_, "c_text")
        if typ == "ProgressModule":
            bind(node, globals_, "c_track", "color_bgcolor")
        if title in ("HostnameText", "RefreshGlyph", "InfoRefreshGlyph"):
            bind(node, globals_, "c_accent_text")
        if title in ("RefreshArea", "InfoRefreshArea"):
            bind(node, globals_, "c_selected")
        if title in ("RefreshBorder", "InfoRefreshBorder"):
            bind(node, globals_, "c_accent")
        if title in ("BtnPrev", "BtnNext"):
            for child in node.get("viewgroup_items", []):
                if child["internal_type"] == "TextModule":
                    bind(child, globals_, "c_accent_text")
                elif child["internal_type"] == "ShapeModule":
                    bind(child, globals_, "c_accent" if child.get("paint_style") == "STROKE" else "c_selected")
        if title in ("TabOverview", "TabContainers", "TabInfo"):
            view = {"TabOverview": "overview", "TabContainers": "containers", "TabInfo": "info"}[title]
            for child in node["viewgroup_items"]:
                if child["internal_type"] == "TextModule":
                    bind(child, globals_, "c_accent_text", expression=f'$if(gv(view) = "{view}", gv(c_accent_text), gv(c_muted))$')
                elif child.get("paint_style") == "STROKE":
                    bind(child, globals_, "c_accent", expression=f'$if(gv(view) = "{view}", gv(c_accent), gv(c_surface0))$')
                else:
                    bind(child, globals_, "c_selected", expression=f'$if(gv(view) = "{view}", gv(c_selected), gv(c_tab_inactive))$')
