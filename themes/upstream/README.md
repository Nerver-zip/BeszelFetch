# Pinned upstream palette sources

`manifest.json` records public repository commits, exact files, extractors,
variants, SHA-256 checksums, support sources and license evidence. Raw files are
stored with `.txt` extensions; their original paths remain in the manifest.
These files are development inputs, never fetched by the Android widget.

```sh
# Offline reproducibility and checksum check
python3 scripts/theme_sources.py

# Verify the exact public commit URLs and refresh identical snapshots
python3 scripts/theme_sources.py --fetch

# Reproduce catalog colors/source metadata; semantic assignments stay intact
python3 scripts/theme_sources.py --write
```

Keep license evidence when updating a source. Ayu's pinned repository declares
MIT in `package.json` and has no root license file; its declaration is stored in
`licenses/ayu-theme--ayu-colors.txt`. Other license snapshots contain the
upstream license texts. Support sources document Kanagawa's variant choices
and Oxocarbon's HSLuv blend implementation.

See [source variants and readable colors](../../docs/THEMES.md#accessibility-and-contrast)
for extraction boundaries, application extensions and contrast policy.
