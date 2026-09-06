---
name: kustom-data
description: Designs caching, JSON parsing, adapter transformations, units normalization, fallbacks, and stale-state handling in Kustom.
---

# Kustom Data Adapter

## Goal

Transform raw Beszel API payloads into stable, validated data contracts for the UI.

## Processing Pipeline

```text
HTTP Response
 -> HTTP status verification
 -> JSON integrity check
 -> Schema adapter mapping
 -> Update local cache
 -> Populate presentation globals / UI bindings
```

## Architectural Invariants

- An invalid response or network error must never overwrite valid cache;
- Every numeric metric must have an explicit, unambiguous unit;
- Missing hardware sensors (e.g., temperature) must be treated as graceful nulls, not fatal errors;
- Empty arrays must trigger dedicated empty states;
- The adapter is the only layer authorized to decode compact Beszel keys.

## Cache Domains

### Systems
Suggested TTL: 5 minutes.

### Containers
Suggested TTL: 5 minutes or on-view.

### History
Suggested TTL: 15 minutes or on-view.

## Stale State

Mark `is_stale = 1` when:
- Network request fails;
- Cache age exceeds 2x TTL;
- JSON parsing fails validation.

Continue rendering cached data with a subtle stale badge.

## Unit Normalization

### Bytes (IEC Standards)
- `KiB` = 1,024 bytes
- `MiB` = 1,048,576 bytes
- `GiB` = 1,073,741,824 bytes

### Percentages
Clamp values between `0` and `100`.

### Temperature
Format to maximum 1 decimal place (e.g., `43.0°C`).

### Load Average
Format to 2 decimal places (e.g., `0.42`).

## Chart Downsampling

When receiving `N` datapoints and the UI renders 24 bars:
- Retain the first and last datapoints;
- Sample points at evenly spaced intervals;
- Do not introduce complex interpolation in MVP.

## Version Compatibility

Keep all paths documented in `DATA_CONTRACT.md`.
Whenever a key path changes across Beszel versions, maintain fallback handling in the adapter layer.
