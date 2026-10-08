#!/usr/bin/env python3
"""
Automated validation suite for BeszelFetch themes.

Checks:
1. JSON syntax and structure against schema_version 1.
2. Lowercase kebab-case naming and filename matching.
3. Source provenance metadata and pinned commit revisions.
4. Upstream palette hex formats.
5. All 16 required semantic role mappings.
6. Active native bindings and rendered contrast across cached-data states.
   Text >= 4.5:1; metric graphics/decorative art >= 3.0:1.
"""

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.theme_catalog import THEMES_DIR, resolve_theme, validate_theme
from scripts.theme_sources import check_palette
from scripts.generate_clip import build_kustom_clip
from scripts.theme_audit import contrast_failures, binding_failures


def validate_all_themes(themes_dir: Path = THEMES_DIR, target_theme: str = None) -> Tuple[int, int, List[str]]:
    """Check pinned imports and actual module colors; count failed themes once."""
    files = [p for p in sorted(themes_dir.glob("*.json")) if not target_theme or p.stem == target_theme]
    if not files:
        return 0, 1, [f"No matching themes found in {themes_dir}"]
    passed, failed, errors = 0, 0, []
    for path in files:
        try:
            data = json.loads(path.read_text())
            validate_theme(data, file_path=path)
            if not re.fullmatch(r"[0-9a-fA-F]{40}", data["source"]["revision"]):
                raise ValueError("Source revision must be a full pinned commit SHA")
            check_palette(data)
            root = build_kustom_clip(write_outputs=False, theme=resolve_theme(data))
            bindings = binding_failures(root)
            if bindings:
                raise ValueError("Inactive color bindings: " + ", ".join(bindings))
            failures = contrast_failures(root, states=("normal", "stale", "empty", "missing", "alert"))
            if failures:
                example = failures[0]
                raise ValueError(f"{len(failures)} rendered contrast failures; {example}")
            passed += 1
        except Exception as error:
            failed += 1
            errors.append(f"[{path.stem}] {error}")
    return passed, failed, errors


def main():
    parser = argparse.ArgumentParser(description="Validate BeszelFetch themes for schema and contrast compliance.")
    parser.add_argument("--theme", help="Specific theme ID to validate")
    parser.add_argument("--dir", type=Path, default=THEMES_DIR, help="Path to themes directory")
    args = parser.parse_args()

    print(f"\033[1;34mValidating themes in {args.dir}...\033[0m")
    passed, failed, errors = validate_all_themes(themes_dir=args.dir, target_theme=args.theme)

    if errors:
        print(f"\n\033[1;31m✖ Encountered {len(errors)} validation failure(s):\033[0m")
        for err in errors:
            print(f"  • {err}")
        sys.exit(1)

    print(f"\033[1;32m✓ All {passed} theme(s) passed pinned-source, binding and rendered contrast checks!\033[0m")
    sys.exit(0)


if __name__ == "__main__":
    main()
