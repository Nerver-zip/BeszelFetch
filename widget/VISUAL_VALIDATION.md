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
python3 scripts/validate_themes.py
python3 scripts/theme_preview.py
python3 -m unittest discover -s scripts -p 'test_*.py' -v
python3 scripts/test_widget_runtime.py --render
git diff --check
```

The theme preview generator creates `dist/theme-preview.html`, an offline
gallery of all 32 curated themes, each with separate Overview, Docker and Info
views. See the [preview contract and options](../docs/THEMES.md#visual-preview-gallery).
Rendering with `--render` requires `rsvg-convert` and creates `dist/info-local-480.png` and `dist/info-local-640.png`. These previews evaluate emitted ASCII/text and row positions; they do not emulate native Kustom layout, typography or Flow timing.

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

## Theme preview revision — 2026-10-07

The earlier local Info checks above describe the September work. This revision
used ADB captures of the installed Latte widget's three views as a visual
reference. Captures contain real telemetry and remain outside the repository.
The widget's known Network/Docker white-text defects were not changed.

- `scripts/kustom_preview.py` now renders the canonical generated module tree;
  `scripts/kustom_eval.py` shares the existing offline evaluator with runtime
  tests. `scripts/theme_preview.py` builds the full offline gallery.
- `examples/fixtures/theme-preview.json` supplies synthetic host, metrics,
  containers and Info caches. Normal, stale, empty and missing-field states are
  available; stale retains the normal cached measurements.
- Nine preview regressions pass: all-theme geometry invariance, separate views,
  clipping masks without painted badge boxes, serialized white defaults, native
  text visibility, source-driven changes, fallback states at three frame sizes,
  Docker pages, unsupported-feature failures and embedded gallery assets.
- Chrome checks pass with network disabled: 32 themes, 96 view panels, 160
  rendered pages; theme selection/arrows, light filtering, comparison mode,
  widget tabs, Docker buttons and keyboard activation, bounded pages, backdrop
  changes and local image/clear controls. Twelve screenshots across Mocha,
  Latte, Nord and Ayu Light were captured; representative outputs were inspected.
- Catalog validation passes for all 32 themes. Full unittest discovery runs
  91 tests with one existing artifact mismatch in
  `test_archive_and_dist_match_clip`: the widget archive differs from its copy
  in `dist`. Preview generation does not modify either archive.

The mock follows serialized geometry and the bundled font, with native captures
informing ring stroke bounds and ignored TextModule layer visibility. It is
still not a pixel-identical native renderer: typography, launcher scaling and
wallpaper effects remain device checks. No live API or Flow behavior is newly
validated by the gallery.


## Theme colors revision — 2026-10-08

This revision implements the approved palette/binding/uniqueness work. The
October 7 white-text defects described above are fixed in the generated tree.
No revised widget has been imported or exported through native KWGT yet.

### Changed

- All 32 catalog entries reproduce named colors from checksum-pinned upstream
  snapshots with explicit variants. Atom One palettes now come from Atom;
  Tokyo Night uses official generated exports; Kanagawa Lotus, Palenight,
  Everforest and other imports have corrected colors/backgrounds. License
  evidence and source checks are vendored for offline reproducibility.
- Every TextModule and ProgressModule has an active native color binding.
  Network details and Docker headings no longer use missing white defaults.
- Readable accent text companions are separate from metric graphics. Minimal
  contrast corrections leave the canonical upstream colors unchanged.
- Header, refresh/pagination actions and active navigation use the main accent.
  Family-specific metric mappings diversify unrelated palettes while sibling
  variants retain intentional similarity.
- `alert` adds synthetic offline/high-load data alongside normal, stale, empty
  and missing-field preview states. This changes mock data only.
- Default clips, inspectable preset definition and development archives were
  regenerated. Archives are not native KWGT exports.

### Verification

- 102 tests pass, including exact upstream extraction/checksums, source mutation
  rejection, active bindings, separate readable text, primary-accent states,
  family mappings and cross-theme structural invariance.
- All 32 themes pass `validate_themes.py`: three views, five data states, black
  and white backdrops. Tests repeat the rendered contrast checks at 480 × 376
  and 660 × 424 (1,920 view/state/backdrop/frame combinations).
- Text-center samples meet 4.5:1; rings, status dots, active/action outlines and
  decorative distro art meet 3:1 in the evaluated contexts. The renderer models
  filled-shape compositing, not antialiasing or arbitrary wallpaper effects.
- A comparison against the pre-change generated tree confirms identical
  geometry, data expressions, visibility and touch actions; non-color globals
  (excluding ordering indices and the theme-colored art catalog) and Flows are
  unchanged. Cross-theme rendered positions remain identical.
- Chrome offline checks pass: 32 themes, 96 view panels, 160 pages, theme/mode
  controls, widget navigation, Docker keyboard/pagination, backdrops and local
  image controls. Contact sheets of all 32 Overview views and detailed light
  Docker/Info views were inspected; 48 comparison screenshots remain in `/tmp`
  with synthetic data only. They are not README assets.
- `theme_sources.py --fetch` verified exact public commit URLs and checksums;
  normal source checks require no network. `git diff --check` passes.

### Remaining native confirmation

Import the regenerated clip on the device and inspect all three views over the
actual wallpaper. Confirm text baselines, launcher scaling, touch behavior and
native color formula evaluation. Final release presets must be exported by KWGT
itself. Existing runtime tests cover cache/failure behavior; this revision makes
no new claim of live Beszel or Android Flow execution.
