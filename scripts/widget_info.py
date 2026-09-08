"""Overview scalar adapter and manual Fastfetch-style Info view.

Only the daily network accumulator visits history records. No vector paths,
chart samples, metric selectors or runtime fl() loops are emitted.
"""
if __package__:
    from .widget_layout import anchor, formula, frame, walk
else:
    from widget_layout import anchor, formula, frame, walk


def build_info(root):
    globals_ = root["globals_list"]

    def derived(name, expression):
        globals_[name] = {"index": len(globals_), "type": "TEXT", "title": name,
                          "value": "", "toggles": 10, "global_formula": f"${expression}$"}

    def system(field):
        return f'tc(json, gv(sys_json), ".items[" + gv(sys_idx) + "].{field}")'

    def stats(field):
        return f'tc(json, gv(latest), ".items[0].stats.{field}")'

    derived("host", f'if({system("name")} != "", {system("name")}, gv(server_name))')
    derived("host_status", system("status"))
    for name, field in (("uptime", "u"), ("temp", "dt"), ("load1", "la[0]"), ("load5", "la[1]"), ("load15", "la[2]")):
        derived(name, f'if({system("info." + field)} != "", {system("info." + field)}, {stats(field)})')
    for name, field in (("ramused", "mu"), ("ramtotal", "m"), ("diskused", "du"), ("disktotal", "d"),
                        ("buffer", "mb"), ("swap", "s"), ("swapused", "su")):
        derived(name, stats(field))
    for direction, idx, legacy in (("tx", 0, "ns"), ("rx", 1, "nr")):
        raw, old, info = stats(f"b[{idx}]"), stats(legacy), system(f"info.bb[{idx}]")
        derived(f"net_{direction}", f'if({raw} != "", mu(max, 0, {raw}), if({old} != "", mu(max, 0, {old}) * 1048576, if({info} != "", mu(max, 0, {info}), 0)))')
        derived(f"rate_{direction}", f'if(gv(net_{direction}) >= 1048576, mu(round, gv(net_{direction}) / 1048576, 1) + " MiB/s", mu(round, gv(net_{direction}) / 1024, 1) + " KiB/s")')

    for prefix in ("ram", "disk"):
        derived(f"{prefix}_fmt", f'if(gv({prefix}used) != "" & gv({prefix}total) != "", mu(round, gv({prefix}used), 1) + " / " + mu(round, gv({prefix}total), 1) + " GiB", "N/A")')
    derived("temp_fmt", 'if(gv(temp) != "", mu(round, gv(temp), 1) + "°C", "N/A")')
    derived("up_days", 'mu(floor, (gv(uptime) + 0) / 86400)')
    derived("up_hours", 'mu(floor, (gv(uptime) + 0) / 3600) - gv(up_days) * 24')
    derived("up_fmt", 'if(gv(uptime) != "", gv(up_days) + "d " + gv(up_hours) + "h", "N/A")')
    for name in ("load1", "load5", "load15"):
        derived(f"{name}_fmt", f'if(gv({name}) != "", mu(round, gv({name}), 2), "N/A")')
    derived("loads", 'gv(load1_fmt) + " / " + gv(load5_fmt) + " / " + gv(load15_fmt)')
    derived("buffer_fmt", 'if(gv(buffer) != "", mu(round, gv(buffer), 2) + " GiB", "N/A")')
    derived("swap_fmt", 'if(gv(swap) != "", mu(round, gv(swapused) + 0, 2) + " / " + mu(round, gv(swap), 2) + " GiB", "N/A")')
    # Beszel v0.18.8 explicitly excludes the primary mountpoint from Stats JSON.
    # Do not invent a root device/partition from percentage or capacity fields.
    derived("partition", '"Partition: N/A"')

    derived("load_period", 'if(gv(load5) != "", "5m", if(gv(load15) != "", "15m", "1m"))')
    derived("load_best", 'if(gv(load5) != "", gv(load5_fmt), if(gv(load15) != "", gv(load15_fmt), gv(load1_fmt)))')
    # Totals are materialized by the refresh Flow, never recursively summed by UI.
    for direction in ("rx", "tx"):
        v = f"gv(net_24h_{direction})"
        derived(f"day_{direction}", f'if({v} >= 1073741824, "≈ " + mu(round, {v} / 1073741824, 1) + " GiB", if({v} >= 1048576, "≈ " + mu(round, {v} / 1048576, 1) + " MiB", if({v} > 0, "≈ " + mu(round, {v} / 1024, 1) + " KiB", "0 KiB")))')

    nodes = {n.get("internal_title"): n for n in walk(root)}
    font = nodes["HostnameText"]["text_family"]
    # Overview percentages occur only in the rings.
    nodes["Title_CPU"]["text_expression"] = "󰍛 CPU"
    formula(nodes["Sub_CPU"], "text_expression", '$" " + gv(temp_fmt)$')
    formula(nodes["Sub2_CPU"], "text_expression", '$"Load Avg: " + if(gv(load_best) != "", gv(load_best), "N/A")$')
    for title, global_ in (("Memory", "ram_fmt"), ("Disk", "disk_fmt")):
        formula(nodes[f"Sub_{title}"], "text_expression", f'$gv({global_})$')
        nodes[f"Sub_{title}"]["text_size"] = 14.0
    for title, global_ in (("NetDownVal", "rate_rx"), ("NetUpVal", "rate_tx"),
                           ("NetVolVal", "day_rx"), ("NetVolUpVal", "day_tx")):
        formula(nodes[title], "text_expression", f'$gv({global_})$')
    for i in range(5):
        dot = nodes[f"RowLeft_{i}"]["viewgroup_items"][1]
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

    if __package__:
        from .widget_fetch import build_fetch
    else:
        from widget_fetch import build_fetch
    build_fetch(root)
