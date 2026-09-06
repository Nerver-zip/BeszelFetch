---
name: orchestrator
description: Coordinates changes across the KWGT + Beszel widget, selects specialized skills, and enforces architectural constraints.
---

# Orchestrator

## Objective

Break down tasks into short, verifiable sequences aligned with the core project architecture.

## Pre-Requisites

Read:
1. `ARCHITECTURE.md`
2. `DATA_CONTRACT.md`
3. `AGENTS.md`

Categorize task:
- Kustom / UI;
- API / Auth;
- Data adapter / Cache;
- Visual / Styling;
- Chart / Historical metrics;
- Testing / Debugging;
- Documentation / Release.

## Delegated Skills

- Kustom layout & flows -> `../kwgt-kustom/SKILL.md`
- API & PocketBase -> `../beszel-pocketbase/SKILL.md`
- Data & normalization -> `../kustom-data/SKILL.md`
- Visual tokens & ricing -> `../frontend-visual/SKILL.md`
- History & charts -> `../charting/SKILL.md`
- Testing & validation -> `../test-debug/SKILL.md`
- Docs & packaging -> `../docs-release/SKILL.md`

## Inviolable Rules

- Never introduce an auxiliary backend or proxy;
- Never hardcode secrets or credentials;
- Never scatter raw Beszel JSON paths throughout UI layers;
- Never overwrite valid cache with an error or invalid payload;
- 401 triggers exactly one re-auth and one retry;
- Never configure sub-second polling;
- Never assume unverified schema fields;
- Always preserve graceful fallbacks for optional fields.

## Expected Task Output

Every change must document:
- Affected files and components;
- Input parameters;
- Successful render state;
- Failure fallback state;
- Verification instructions;
- Compatibility risks.

## Complexity Guidelines

Prefer:
1. Clear, typed global variables;
2. Kustom Flows for procedural logic and state updates;
3. Formulas strictly for UI presentation;
4. Minimized HTTP roundtrips;
5. Modular, reproducible components.

Avoid monolithic formulas when a Flow step can produce a normalized global variable.
