---
name: kwgt-kustom
description: Develops layout trees, global variables, formulas, touch actions, and Flows for KWGT/Kustom.
---

# KWGT / Kustom

## Scope

Use this skill for:
- Preset hierarchy tree;
- Stack and overlap groups;
- Global variables;
- Kustom formulas;
- Layer visibility logic;
- Touch actions and hot spots;
- Kustom Flows;
- Local JSON caching;
- Widget resizing behavior.

## Core Principles

1. The UI reads exclusively from local cache globals, never from remote endpoints directly.
2. Procedural logic belongs in Flows, not in monolithic UI formulas.
3. Formulas must remain short, readable, and observable.
4. Repetition uses mirrored, structured component groups.
5. Every optional field must have a fallback.
6. Main view visibility is driven by `gv(view)`.

## Standard Globals

State:
- `view`: Active tab
- `sys_idx`: Active system index
- `sys_id`: Active system UUID
- `metric`: Active chart metric
- `range`: Active time range
- `container_page`: Active pagination index
- `debug`: Diagnostics toggle

Data Caches:
- `systems_json` (or `sys_json`)
- `containers_json` (or `cnt_json`)
- `history_json` (or `hist_json`)

Operational State:
- `last_ok`: Sync timestamp
- `last_code`: HTTP status code
- `last_error`: Error category
- `is_stale`: Stale flag

## Required Flows

- `auth_beszel`
- `fetch_systems`
- `fetch_containers`
- `fetch_history`
- `refresh_current_view`

## WebGet Standards

Headers:
- `Authorization: <token>`
- `Content-Type: application/json` (on auth).

Never display credentials or tokens in text elements.

## Layer Visibility

Standard matrix:
- Overview renders only when `view = overview`;
- Containers renders only when `view = containers`;
- Chart renders only when `view = chart`.

Components without data should collapse or hide (`visibility: REMOVE`).

## Touch Interactions

Touch target hot spots must be larger than visual icons (minimum 44x44 dp).
Provide visual feedback for active states.
Bottom navigation switches view state and dispatches fetches conditionally.

## Performance Guidelines

- Default background refresh: 5 minutes;
- History chart retains cache longer (15 minutes);
- Avoid multiple independent WebGet actions per view;
- Consolidate domain requests into a single cached JSON payload.

## Formula Delivery Standards

When documenting formulas, specify:
- Target component layer and property;
- Referenced globals;
- Output unit;
- Fallback value;
- Behavior when cached JSON is absent or malformed.
