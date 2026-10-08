"""Offline evaluator for the emitted Kode subset. Unknown calls fail closed.

This evaluates cached, synthetic inputs only; it never runs Kustom Flows or HTTP.
"""
import datetime as dt
import json
import math
import re
from urllib.parse import quote

NOW = dt.datetime(2026, 9, 7, 21, tzinfo=dt.timezone.utc).timestamp()


def number(value):
    return float(value or 0)


def string(value):
    return str(int(value)) if isinstance(value, (int, float)) and value == int(value) else str(value)


class Kode:
    token = re.compile(r'\s*(#[0-9A-Fa-f]{6,8}|"(?:\\.|[^"\\])*"|\d+(?:\.\d+)?|[A-Za-z_][\w]*|!=|>=|<=|[()+*/%=<>|&,\-])')
    precedence = {"|": 1, "&": 2, "=": 3, "!=": 3, ">": 3, "<": 3, ">=": 3, "<=": 3, "+": 4, "-": 4, "*": 5, "/": 5, "%": 5}

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
            return {"-": lambda: a-b, "*": lambda: a*b, "/": lambda: a/b, "%": lambda: a%b,
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
