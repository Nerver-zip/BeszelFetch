---
name: test-debug
description: Validates network, auth, schema, cache, UI states, pagination, and regressions across the widget.
---

# Test & Debug

## Minimum Test Matrix

### Network States
- Normal online connectivity;
- Network disabled / Airplane mode;
- Beszel Hub rebooting / temporarily unreachable;
- Request timeout.

### Authentication States
- Valid JWT token;
- Expired / invalid token -> triggers automatic re-auth;
- Invalid password -> auth error badge;
- Dedicated user lacking system permissions.

### Systems
- Single host configured;
- Multiple hosts;
- Currently selected host removed from Hub;
- Host in `down` status.

### Optional Data Fields
- Temperature sensor absent;
- Bandwidth metrics absent;
- Load average absent;
- Disk metrics absent.

### Containers View
- 0 containers running (empty state);
- 1 container running;
- 5 containers running (exact full page);
- 6 containers running (multi-page transition);
- 20+ containers running;
- Extra-long container names.

### Charts View
- 0 datapoints (empty state);
- 1 datapoint;
- 12 datapoints;
- Exactly 24 datapoints;
- >24 datapoints (downsampling);
- Constant zero metrics;
- 100% saturation spikes;
- Network bandwidth auto-scaling.

## Core Verification Assertions

- Valid cached data is never wiped on error or failure;
- No credentials, passwords, or raw tokens appear in the UI;
- 401 re-auth never triggers an infinite loop;
- Bottom navigation tabs remain fully switchable when offline;
- Empty container rows collapse gracefully;
- Pagination page index is bounded: `0 <= page <= max_page`;
- Percentages are visually clamped between 0 and 100;
- Stale status badge is clearly rendered when cache is old;
- Timestamp of last sync is understandable.

## Debug Diagnostic Overlay

Displays strictly:
```text
HTTP status code
Cache age
Sanitized system ID
Item counts
Active view / metric / range
```

## Visual Regression Testing

Capture reference screenshots:
- Overview (normal healthy state);
- Containers (5 rows populated);
- Chart (24h CPU series);
- Stale cache state;
- Offline state.

Audit:
- Text overflow;
- Horizontal/vertical alignment;
- Color contrast;
- Text truncation;
- Touch target hitboxes.
