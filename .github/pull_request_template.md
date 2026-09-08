## Description
<!-- Provide a clear, concise summary of the changes in this pull request. -->

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 🎨 UI / Visual improvement (layout, typography, aesthetic)
- [ ] 📝 Documentation update
- [ ] 🧪 Refactoring, testing, or CI enhancement

## Definition of Done Checklist
- [ ] **Direct Client-to-Hub**: Preserved direct Android/KWGT to Beszel Hub architecture (no proxy or bridge).
- [ ] **No Secret Leakage**: Zero passwords, real tokens, or private IPs introduced.
- [ ] **Gitleaks Verified**: Checked with `gitleaks detect` with zero leaks.
- [ ] **Cache Resilience**: Tested failure behavior to ensure network dropouts do not wipe valid telemetry cache.
- [ ] **Automated Tests**: Unit and contract tests pass (`python -m unittest discover -s scripts -p "test_*.py"`).
- [ ] **Preset Synchronized**: Ran `python scripts/generate_preset.py` and committed updated assets if presets changed.
- [ ] **Touch Target Accessibility**: All interactive touch targets maintain >= 48dp dimensions.
