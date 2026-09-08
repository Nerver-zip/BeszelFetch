# Local validation — Fastfetch Info, 2026-09-08

The user-supplied screenshot showed multiple distro logos overlapping. The
generator now emits exactly one ASCII TextModule; its text, size and color
come from the OS-selected catalog. Source spaces/newlines are preserved.
No ADB, phone connection or native debugging was used.

## Verified locally

- 60 tests: serialized contracts plus evaluated formulas and mocked Flow actions.
- One ASCII module; all 22 bundled logos match the source catalog exactly.
- Colored labels, aligned colons and responsive rows at 480/640/720 widths.
- Info has no scheduled trigger; other flows do not write its snapshots.
- Metadata failure uses legacy fields; network/auth failures preserve Info cache.
- GPU names from dynamic keys, missing fields, load preference 5m → 15m → 1m,
  valid zero and fallback to latest stats.
- Daily totals are plain TEXT cache values, calculated by staged Flow actions.
  Empty/sparse/full histories and failed responses are tested without live HTTP.
- Docker pagination, raw Overview quantities, shared clip/preset tree and
  empty credential defaults retain regression coverage.

## Reproduce

```sh
python3 scripts/generate_clip.py
python3 scripts/generate_preset.py
python3 scripts/test_contracts.py
python3 -m unittest discover -s scripts -p 'test*.py' -q
python3 scripts/test_widget_runtime.py --render
git diff --check
```

Rendering requires `rsvg-convert` and creates `dist/info-local-480.png` and
`dist/info-local-640.png`. These previews evaluate emitted ASCII/text and row
positions; they do not emulate native Kustom layout, typography or Flow timing.

## Handoff and limits

Import `widget/beszel_monitor.clip` manually. The generated KWGT archive is a
development package, not a native export. Final Android appearance, button
execution and daily Flow runtime remain for the user's manual test.

The old blank daily number is consistent with the removed recursive formula
chain; its exact native failure was not instrumented. The replacement stores
numeric totals during refresh, keeping display formulas shallow. Totals remain
approximate integrals of available 20m rates, not exact counter deltas. Missing
history cannot recover a full day's unobserved traffic.

Info uses Beszel metadata fields verified against upstream v0.18.8, not a live
private Hub. GPU inventory is not fabricated when Beszel does not report it.

## Sources

- [Beszel types](https://github.com/henrygd/beszel/blob/v0.18.8/internal/site/src/types.d.ts)
- [Fastfetch attribution and pinned assets](assets/fastfetch/README.md)
- [Kustom text conversions](https://docs.kustom.rocks/tags/Function/page/3/)
