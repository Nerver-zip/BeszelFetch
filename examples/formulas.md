# Formulas — Patterns & Examples

> Exact path concatenation syntax should be validated against your installed Kustom version. These examples represent standard implementation patterns.

## Parsing JSON with `wg()`

Kustom JSON extraction pattern:

```text
$wg(gv(sys_json), json, ".items[0].name")$
```

CPU of the first system:

```text
$wg(gv(sys_json), json, ".items[0].info.cpu")$
```

RAM %:

```text
$wg(gv(sys_json), json, ".items[0].info.mp")$
```

Disk %:

```text
$wg(gv(sys_json), json, ".items[0].info.dp")$
```

Status (`up` / `down`):

```text
$wg(gv(sys_json), json, ".items[0].status")$
```

## Dynamic Indexing

Concept:

```text
".items[" + gv(sys_idx) + "].info.cpu"
```

If dynamic string concatenation becomes complex or fragile in your Kustom release, normalize the active system fields into separate globals (`sel_cpu`, `sel_ram`, `sel_disk`, etc.) inside the Flow. This is preferred over deeply nested runtime formulas.

## Visibility Logic

Concept:

```text
$if(gv(view) = overview, ALWAYS, REMOVE)$
```

Use the visibility enumeration (`ALWAYS`, `REMOVE`, `NEVER`) supported by your Kustom layer.

## Color Threshold Logic

Concept:

```text
$if(gv(cpu_val) >= 95, gv(c_red), if(gv(cpu_val) >= 85, gv(c_peach), if(gv(cpu_val) >= 70, gv(c_yellow), gv(c_blue))))$
```

Centralize threshold evaluation inside reusable component globals or global formulas.

## Container Row Indexing

For row `r` (`0..4`):

```text
index = gv(container_page) * 5 + r
```

The row component:
- Reads `stats[index]`;
- Hides (`visibility: REMOVE`) if no record exists at that index.

## Network Unit Formatting

Logic:

```text
< 1 MiB/s -> format as KiB/s
< 1 GiB/s -> format as MiB/s
>= 1 GiB/s -> format as GiB/s
```

## Uptime Formatting

Input in seconds:

```text
days = floor(uptime / 86400)
hours = floor((uptime % 86400) / 3600)
```

Output:
```text
12d 04h
```

## Architectural Design Note

If a single formula attempts to simultaneously:
- Parse raw JSON;
- Resolve dynamic indices;
- Convert units;
- Handle missing fallbacks;
- Calculate threshold colors;

It should be decomposed. Keep normalization inside the Flow or adapter globals, and use UI formulas purely for presentation.
