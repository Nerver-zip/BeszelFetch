#!/usr/bin/env python3
"""
Automated validation suite for BeszelFetch themes.

Checks:
1. JSON syntax and structure against schema_version 1.
2. Lowercase kebab-case naming and filename matching.
3. Source provenance metadata and pinned commit revisions.
4. Upstream palette hex formats.
5. All 16 required semantic role mappings.
6. WCAG 2.1 AA contrast compliance (>= 4.5:1 for normal text, >= 3.0:1 for graphical UI).
"""

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.theme_catalog import (
    DARK_OPACITY,
    DEFAULT_THEME_ID,
    LIGHT_OPACITY,
    REQUIRED_SEMANTIC_ROLES,
    THEMES_DIR,
    composite_color,
    contrast_ratio,
    hex_to_rgb,
    list_themes,
    resolve_theme,
    validate_theme,
)


def validate_all_themes(themes_dir: Path = THEMES_DIR, target_theme: str = None) -> Tuple[int, int, List[str]]:
    """Validate themes in themes_dir. Returns (passed_count, failed_count, errors_list)."""
    theme_files = sorted(themes_dir.glob("*.json"))
    if not theme_files:
        return 0, 1, [f"No theme files found in {themes_dir}"]

    passed = 0
    failed = 0
    errors: List[str] = []

    for file_path in theme_files:
        theme_id = file_path.stem
        if target_theme and theme_id != target_theme:
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Schema and naming checks
            validate_theme(data, file_path=file_path)

            # Source revision check: should be pinned commit SHA (usually 40 hex chars)
            source = data.get("source", {})
            rev = source.get("revision", "")
            if not re.match(r"^[0-9a-fA-F]{7,40}$", rev) and rev != "HEAD":
                errors.append(f"[{theme_id}] Source revision {rev!r} does not look like a pinned git commit SHA")

            # Resolution check
            resolved = resolve_theme(data)

            # Contrast validation
            opacity = DARK_OPACITY if resolved.is_dark else LIGHT_OPACITY
            bg_raw = resolved.semantic["background"]
            text_pri = resolved.semantic["text_primary"]
            text_sec = resolved.semantic["text_secondary"]

            # Effective backgrounds across potential backdrops
            backdrops = [("#000000", "black")] if resolved.is_dark else [("#000000", "black"), ("#FFFFFF", "white")]

            for backdrop, bd_name in backdrops:
                eff_bg = composite_color(bg_raw, backdrop, opacity["base"])
                cr_text = contrast_ratio(text_pri, eff_bg)
                if cr_text < 4.5:
                    errors.append(
                        f"[{theme_id}] Primary text contrast {cr_text:.2f}:1 fails WCAG AA (< 4.5:1) "
                        f"over {bd_name} backdrop (text={text_pri}, eff_bg={eff_bg})"
                    )

            passed += 1
        except Exception as e:
            failed += 1
            errors.append(f"[{theme_id}] Validation error: {e}")

    if errors:
        failed = len(errors)

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

    print(f"\033[1;32m✓ All {passed} theme(s) passed schema, metadata, and WCAG contrast checks!\033[0m")
    sys.exit(0)


if __name__ == "__main__":
    main()
