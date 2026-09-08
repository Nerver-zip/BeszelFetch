"""Materialize traffic totals in a Flow, never a recursive render-time graph."""
from datetime import datetime, timezone
import json


def seed_totals(payload, now=None):
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    result = [0.0, 0.0]
    for item in payload.get("items", [])[:74]:
        try:
            end = datetime.fromisoformat(item["created"].replace("Z", "+00:00")).timestamp()
            duration = max(0, min(now, end) - max(now-86400, end-1200))
            stats = item.get("stats") or {}
            for idx, legacy in ((0, "ns"), (1, "nr")):
                rate = stats["b"][idx] if "b" in stats else stats.get(legacy, 0)*1048576
                result[idx] += max(0, rate)*duration
        except (KeyError, ValueError, TypeError, IndexError):
            continue
    return result


def add_daily_actions(globals_, evaluate, store):
    tx, rx = seed_totals(json.loads(globals_["day_json"]["value"]))
    for name, value in (("net_24h_rx", str(round(rx))), ("net_24h_tx", str(round(tx))),
                        ("day_time", "0"), ("sum_rx", "0"), ("sum_tx", "0")):
        globals_[name] = {"index": len(globals_), "type": "TEXT", "title": name, "value": value}
    actions = [evaluate('df(S)'), store("day_time"), evaluate('0'), store("sum_rx"), evaluate('0'), store("sum_tx")]
    # Each stage reads only plain cached values. No gv() recursion through
    # per-point dates -> durations -> partial sums -> grand totals.
    # Twenty-minute means represent their preceding bucket; clip both edges.
    for i in range(74):
        prefix = f".items[{i}]"
        stamp = f'tc(json, gv(tmp_day), "{prefix}.created")'
        # Store the parsed timestamp once and share it across both directions.
        if i == 0:
            globals_["day_stamp"] = {"index": len(globals_), "type": "TEXT", "title": "day_stamp", "value": "0"}
            globals_["day_secs"] = {"index": len(globals_), "type": "TEXT", "title": "day_secs", "value": "0"}
        actions += [evaluate(f'if({stamp} != "", df(S, dp({stamp}, auto)), 0)'), store("day_stamp"),
                    evaluate('mu(max, 0, mu(min, gv(day_time), gv(day_stamp)) - mu(max, gv(day_time) - 86400, gv(day_stamp) - 1200))'), store("day_secs")]
        for direction, idx, legacy in (("tx", 0, "ns"), ("rx", 1, "nr")):
            raw = f'tc(json, gv(tmp_day), "{prefix}.stats.b[{idx}]")'
            old = f'tc(json, gv(tmp_day), "{prefix}.stats.{legacy}")'
            rate = f'if({raw} != "", mu(max, 0, {raw}), mu(max, 0, {old} + 0) * 1048576)'
            actions += [evaluate(f'gv(sum_{direction}) + gv(day_secs) * ({rate})'), store(f"sum_{direction}")]
    for direction in ("rx", "tx"):
        actions += [evaluate(f'if(gv(day_ok) = 1 & tc(type, gv(sum_{direction})) = NUMBER, mu(round, gv(sum_{direction}), 0), gv(net_24h_{direction}))'), store(f"net_24h_{direction}")]
    return actions
