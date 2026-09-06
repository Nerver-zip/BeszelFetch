---
name: docs-release
description: Maintains documentation, sanitized test fixtures, changelogs, and preset release packaging checklists.
---

# Docs & Release

## Update Documentation Whenever

- An API endpoint changes;
- A JSON path mapping changes;
- A global variable is added, renamed, or deprecated;
- A new Flow is implemented;
- A new view or component is introduced;
- Compatibility changes;
- Failure/fallback behaviors change.

## Fixture Integrity Rules

Every test fixture must be:
- Compact and well-formatted;
- Syntactically valid JSON;
- Synthetic or thoroughly sanitized;
- Devoid of real tokens;
- Devoid of real passwords;
- Free of private IP addresses or internal domain names.

## Release Packaging Checklist

- [ ] `README.md` reflects current setup and features;
- [ ] `DATA_CONTRACT.md` matches verified API schema;
- [ ] Document tested Beszel version;
- [ ] Document tested KWGT version;
- [ ] Credentials stripped from all preset globals;
- [ ] Temporary debug caches flushed;
- [ ] `debug = 0`;
- [ ] Screenshots audited for private data;
- [ ] `.kwgt` file exported directly via KWGT app;
- [ ] Release bundle contains zero credentials.

## Suggested Changelog Format

```markdown
## [version] - YYYY-MM-DD
### Added
### Changed
### Fixed
### Compatibility
```

## Compatibility Assertions

Never claim compatibility with a Beszel or KWGT version without:
- Active verification against that version;
- Or explicitly denoting it as "untested".
