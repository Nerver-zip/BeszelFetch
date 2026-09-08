"""Materialize reactive 24h traffic total globals and seed initial clip values."""
import json


def seed_totals(payload, now=None):
    """Integrate 24h byte totals directly across available 20m interval records."""
    result = [0.0, 0.0]
    items = payload.get("items", [])[:72]
    for item in items:
        try:
            stats = item.get("stats") or {}
            b = stats.get("b")
            if isinstance(b, list) and len(b) >= 2:
                tx_rate = float(b[0])
                rx_rate = float(b[1])
            else:
                tx_rate = float(stats.get("ns", 0)) * 1048576
                rx_rate = float(stats.get("nr", 0)) * 1048576
            result[0] += max(0.0, tx_rate) * 1200
            result[1] += max(0.0, rx_rate) * 1200
        except (KeyError, ValueError, TypeError, IndexError):
            continue
    return result


def make_chunk_expr(start, count, direction_idx, legacy_field):
    b_parts = "+".join(f'(tc(json, gv(day_json), ".items[{i}].stats.b[{direction_idx}]") + 0)' for i in range(start, start + count))
    legacy_parts = "+".join(f'(tc(json, gv(day_json), ".items[{i}].stats.{legacy_field}") + 0)' for i in range(start, start + count))
    return f'if(tc(json, gv(day_json), ".items[0].stats.b[0]") != "", {b_parts}, ({legacy_parts}) * 1048576)'


def add_daily_actions(globals_, evaluate=None, store=None):
    raw_history = globals_.get("day_json", {}).get("value", "{}")
    try:
        history_data = json.loads(raw_history)
    except Exception:
        history_data = {}
    tx, rx = seed_totals(history_data)

    # 6 chunks of 12 items (72 items = 24 hours of 20m intervals)
    for i in range(6):
        rx_expr = make_chunk_expr(i * 12, 12, 1, "nr")
        tx_expr = make_chunk_expr(i * 12, 12, 0, "ns")
        globals_[f"drx{i}"] = {
            "index": len(globals_), "type": "TEXT", "title": f"drx{i}",
            "value": "", "toggles": 10, "global_formula": f"${rx_expr}$"
        }
        globals_[f"dtx{i}"] = {
            "index": len(globals_), "type": "TEXT", "title": f"dtx{i}",
            "value": "", "toggles": 10, "global_formula": f"${tx_expr}$"
        }

    rx_sum = " + ".join(f"gv(drx{i})" for i in range(6))
    tx_sum = " + ".join(f"gv(dtx{i})" for i in range(6))

    globals_["net_24h_rx"] = {
        "index": len(globals_), "type": "TEXT", "title": "net_24h_rx",
        "value": str(round(rx)), "toggles": 10,
        "global_formula": f"$mu(round, ({rx_sum}) * 1200, 0)$"
    }
    globals_["net_24h_tx"] = {
        "index": len(globals_), "type": "TEXT", "title": "net_24h_tx",
        "value": str(round(tx)), "toggles": 10,
        "global_formula": f"$mu(round, ({tx_sum}) * 1200, 0)$"
    }
    return []
