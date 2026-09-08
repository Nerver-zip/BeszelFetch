"""Native Flow construction: stage responses before updating valid caches.

Uses A_WGET, A_GLOBAL/TEXT and A_FORMULA, never a remote UI formula.
Android execution is a separate validation gate from serialized contract tests.
"""

def build_flows(globals_, latest_data=None):
    import json
    history_seed = globals_["day_json"]["value"]
    records = json.loads(history_seed).get("items", [])
    seed = latest_data if latest_data is not None else {"items": records[-1:]}
    globals_["latest"] = {"index": len(globals_), "type": "TEXT", "title": "Latest scalar stats", "value": json.dumps(seed)}
    for name in ("tmp_sys", "tmp_cnt", "sys_ok", "cnt_ok", "tmp_day", "tmp_now", "day_ok", "now_ok"):
        globals_[name] = {"index": len(globals_), "type": "TEXT", "title": name, "value": ""}

    def action(kind, **params):
        action.count += 1
        return {"id": f"bz{action.count:06d}", "type": kind, "params": params}
    action.count = 0

    def evaluate(expression):
        return action("A_FORMULA", formula=f"${expression}$")

    def save(name):
        return action("A_GLOBAL", store_mode="TEXT", global_=name)

    # Python's global keyword cannot be passed directly as a keyword argument.
    def store(name):
        node = save(name)
        node["params"]["global"] = node["params"].pop("global_")
        return node

    def request(cache, temporary, valid, uri, ok):
        return [
            action("A_WGET", uri=uri, headers='$"Authorization: " + gv(bz_token)$'),
            store(temporary),
            evaluate(f'if({valid}, 1, 0)'), store(ok),
            evaluate(f'if(gv({ok}) = 1, gv({temporary}), gv({cache}))'), store(cache),
        ]

    sys_uri = '$gv(bz_url) + "/api/collections/systems/records?perPage=100&fields=id,name,status,info&sort=name"$'
    system_actions = [evaluate('1'), store("stale")]
    system_actions += request("sys_json", "tmp_sys",
                              'tc(json, gv(tmp_sys), ".items[0].id") != ""', sys_uri, "sys_ok")
    system_actions += [evaluate('if(gv(sys_ok) = 1, df(S), gv(last_ok))'), store("last_ok"),
                       evaluate('if(gv(sys_ok) = 1, 0, 1)'), store("stale")]

    # Filter punctuation is URL encoded, so formulas use no single quotes/&&.
    selected = 'tc(json, gv(sys_json), ".items[" + gv(sys_idx) + "].id")'
    latest_uri = ('$gv(bz_url) + "/api/collections/system_stats/records?perPage=1&fields=created,stats&sort=-created&filter=system%3D%22" + '
                  + selected + ' + "%22%26%26type%3D%221m%22"$')
    latest_actions = request("latest", "tmp_now", 'tc(json, gv(tmp_now), ".items[0].created") != "" & tc(json, gv(tmp_now), ".items[0].stats.cpu") != ""', latest_uri, "now_ok")
    daily_uri = ('$gv(bz_url) + "/api/collections/system_stats/records?perPage=500&fields=created,stats&sort=created&filter=system%3D%22" + '
                 + selected + ' + "%22%26%26type%3D%2220m%22%26%26created%3E%22" + tc(url, df("yyyy-MM-dd HH:mm:ss", df(S) - 86400 - df(Z))) + "%22"$')
    history_actions = request("day_json", "tmp_day", '(tc(json, gv(tmp_day), ".items[0].created") != "" & tc(json, gv(tmp_day), ".items[0].stats.cpu") != "") | (tc(json, gv(tmp_day), ".page") > 0 & tc(json, gv(tmp_day), ".totalItems") = 0)', daily_uri, "day_ok")
    if __package__:
        from .widget_daily import add_daily_actions
    else:
        from widget_daily import add_daily_actions
    history_actions += add_daily_actions(globals_, evaluate, store)
    cnt_uri = ('$gv(bz_url) + "/api/collections/container_stats/records?perPage=1&sort=-created&filter=system%3D%22" + '
               + selected + ' + "%22%26%26type%3D%221m%22"$')
    container_actions = request("cnt_json", "tmp_cnt",
                                'tc(json, gv(tmp_cnt), ".items[0].created") != "" | (tc(json, gv(tmp_cnt), ".page") > 0 & tc(json, gv(tmp_cnt), ".totalItems") = 0)', cnt_uri, "cnt_ok")
    # Info has its own snapshots; no scheduled flow reads/writes these caches.
    # Capture host identity before requests so a tab/host switch cannot mix data.
    for name, value in (("info_meta", "{}"), ("info_stats", "{}"), ("info_sys", "{}"),
                        ("info_host", ""), ("info_req", ""), ("info_at", "0"),
                        ("info_error", "Tap refresh"), ("tmp_meta", "{}"),
                        ("tmp_isys", "{}"), ("tmp_istat", "{}"), ("meta_ok", "0")):
        globals_[name] = {"index": len(globals_), "type": "TEXT", "title": name, "value": value}
    info_actions = [evaluate(selected), store("info_req")]
    meta_uri = '$gv(bz_url) + "/api/collections/system_details/records/" + gv(info_req) + "?fields=id,system,hostname,kernel,cores,threads,cpu,os,os_name,arch,memory"$'
    isys_uri = '$gv(bz_url) + "/api/collections/systems/records/" + gv(info_req) + "?fields=id,name,status,info"$'
    istat_uri = latest_uri.replace(selected, "gv(info_req)")
    for temporary, uri in (("tmp_meta", meta_uri), ("tmp_isys", isys_uri), ("tmp_istat", istat_uri)):
        info_actions += [action("A_WGET", uri=uri, headers='$"Authorization: " + gv(bz_token)$'), store(temporary)]
    core_ok = 'tc(json, gv(tmp_isys), ".id") = gv(info_req) & tc(json, gv(tmp_istat), ".items[0].stats.cpu") != "" & gv(info_req) != ""'
    # Only publish a matching pair of host/runtime snapshots. A metadata 404
    # still permits legacy info.h/k/m/os fallbacks without discarding good data.
    globals_["info_ok"] = {"index": len(globals_), "type": "TEXT", "title": "info_ok", "value": "0"}
    info_actions += [evaluate(f'if({core_ok}, 1, 0)'), store("info_ok")]
    for cache, temporary in (("info_sys", "tmp_isys"), ("info_stats", "tmp_istat")):
        info_actions += [evaluate(f'if(gv(info_ok) = 1, gv({temporary}), gv({cache}))'), store(cache)]
    info_actions += [evaluate('if(tc(json, gv(tmp_meta), ".id") = gv(info_req) & gv(info_req) != "", 1, 0)'), store("meta_ok"),
                     evaluate('if(gv(info_ok) = 1, if(gv(meta_ok) = 1, gv(tmp_meta), if(gv(info_host) = gv(info_req), gv(info_meta), "{}")), gv(info_meta))'), store("info_meta"),
                     evaluate('if(gv(info_ok) = 1, gv(info_req), gv(info_host))'), store("info_host"),
                     evaluate('if(gv(info_ok) = 1, df(S), gv(info_at))'), store("info_at"),
                     evaluate('if(gv(info_ok) = 1, if(gv(meta_ok) = 1, "Updated", "Metadata unavailable"), "Refresh failed · cache kept")'), store("info_error")]
    flows = [
        {"id": "FvLj5OVJ", "name": "refresh_beszel", "t": [{"id": "bzonce", "type": "T_ONCE"}],
         "a": system_actions + container_actions + latest_actions + history_actions},
        {"id": "bzsys", "name": "fetch_systems", "t": [{"id": "bzsyscron", "type": "T_CRON", "params": {"cron_string": "*/5 * * * *"}}],
         "a": system_actions + latest_actions},
        {"id": "bzhist", "name": "fetch_history", "t": [
            {"id": "bzhistcron", "type": "T_CRON", "params": {"cron_string": "*/15 * * * *"}}
        ],
         "a": history_actions},
        {"id": "bzcnt", "name": "fetch_containers", "t": [{"id": "bzcntcron", "type": "T_CRON", "params": {"cron_string": "*/5 * * * *"}}],
         "a": container_actions},
        {"id": "bzinfo", "name": "fetch_info", "t": [], "a": info_actions},
    ]
    from copy import deepcopy
    flows = deepcopy(flows)
    for flow in flows:
        for i, step in enumerate(flow["a"]):
            step["id"] = f'{flow["id"]}_{i}'
    return flows
