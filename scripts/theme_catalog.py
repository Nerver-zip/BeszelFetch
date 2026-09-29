#!/usr/bin/env python3
"""
Theme catalog and resolver for BeszelFetch.

Provides standard library parsing, schema validation, semantic mapping resolution,
and color conversion utilities for Linux/Unix ricing themes.
"""

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

REPO_ROOT = Path(__file__).resolve().parent.parent
THEMES_DIR = REPO_ROOT / "themes"
DEFAULT_THEME_ID = "catppuccin-mocha"

REQUIRED_SEMANTIC_ROLES = (
    "background",
    "background_alt",
    "surface",
    "border",
    "text_primary",
    "text_secondary",
    "text_muted",
    "accent",
    "cpu",
    "memory",
    "disk",
    "network",
    "success",
    "warning",
    "high",
    "error",
)

SEMANTIC_TO_GLOBAL = {
    "background": "c_base",
    "background_alt": "c_mantle",
    "surface": "c_surface0",
    "border": "c_surface1",
    "text_primary": "c_text",
    "text_secondary": "c_subtext",
    "text_muted": "c_muted",
    "accent": "c_accent",
    "cpu": "c_cpu",
    "memory": "c_ram",
    "disk": "c_disk",
    "network": "c_net",
    "success": "c_ok",
    "warning": "c_warn",
    "high": "c_peach",
    "error": "c_err",
}

# Opacity policy for Kustom ARGB:
# Dark themes: 85% base (#D9), 70% mantle (#B3), 15% tab inactive (#25)
# Light themes: 95% base (#F2), 90% mantle (#E6), 15% tab inactive (#25)
DARK_OPACITY = {
    "base": 0xD9,
    "mantle": 0xB3,
    "tab_inactive": 0x25,
}

LIGHT_OPACITY = {
    "base": 0xF2,
    "mantle": 0xE6,
    "tab_inactive": 0x25,
}


def hex_to_rgb(hex_str: str) -> Tuple[int, int, int]:
    """Convert hex string (#RGB, #RRGGBB, #AARRGGBB) to (r, g, b) tuple."""
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    elif len(clean) == 8:
        # Strip alpha prefix if ARGB
        clean = clean[2:]
    elif len(clean) != 6:
        raise ValueError(f"Invalid hex color format: {hex_str!r}")
    return tuple(int(clean[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert (r, g, b) to #RRGGBB."""
    return f"#{max(0, min(255, round(r))):02X}{max(0, min(255, round(g))):02X}{max(0, min(255, round(b))):02X}"


def normalize_hex(hex_str: str) -> str:
    """Normalize hex color string to uppercase #RRGGBB."""
    r, g, b = hex_to_rgb(hex_str)
    return rgb_to_hex(r, g, b)


def to_kustom_argb(hex_str: str, alpha: Optional[Union[int, float]] = None) -> str:
    """
    Convert a canonical #RRGGBB hex color into a Kustom #AARRGGBB color string.
    
    If alpha is None and hex_str has 8 characters, returns standardized #AARRGGBB.
    If alpha is None and hex_str has 6 characters, defaults to fully opaque (0xFF).
    If alpha is an int (0..255) or float (0.0..1.0), formats with specified alpha.
    """
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 8 and alpha is None:
        return f"#{clean.upper()}"
    
    r, g, b = hex_to_rgb(hex_str)
    if alpha is None:
        a_int = 255
    elif isinstance(alpha, float):
        a_int = max(0, min(255, round(alpha * 255)))
    else:
        a_int = max(0, min(255, int(alpha)))
    return f"#{a_int:02X}{r:02X}{g:02X}{b:02X}"


def composite_color(fg_hex: str, bg_hex: str, alpha: Union[int, float]) -> str:
    """
    Alpha composite fg_hex over bg_hex.
    alpha: int (0..255) or float (0.0..1.0)
    Returns #RRGGBB of effective color.
    """
    a = (alpha / 255.0) if isinstance(alpha, int) else float(alpha)
    a = max(0.0, min(1.0, a))
    r1, g1, b1 = hex_to_rgb(fg_hex)
    r2, g2, b2 = hex_to_rgb(bg_hex)
    r = round(r1 * a + r2 * (1.0 - a))
    g = round(g1 * a + r2 * (1.0 - a))
    b = round(b1 * a + r2 * (1.0 - a))
    return rgb_to_hex(r, g, b)


def relative_luminance(hex_str: str) -> float:
    """Calculate WCAG 2.1 relative luminance for a given hex color."""
    r, g, b = hex_to_rgb(hex_str)
    s_rgb = [c / 255.0 for c in (r, g, b)]
    lum = []
    for c in s_rgb:
        if c <= 0.03928:
            lum.append(c / 12.92)
        else:
            lum.append(((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lum[0] + 0.7152 * lum[1] + 0.0722 * lum[2]


def contrast_ratio(hex1: str, hex2: str) -> float:
    """Calculate WCAG contrast ratio between two colors."""
    l1 = relative_luminance(hex1)
    l2 = relative_luminance(hex2)
    bright = max(l1, l2)
    dark = min(l1, l2)
    return (bright + 0.05) / (dark + 0.05)


@dataclass(frozen=True)
class ResolvedTheme:
    """Resolved, validated theme ready for Kustom generation and UI consumption."""
    id: str
    name: str
    mode: str  # "dark" or "light"
    source: Dict[str, Any]
    raw_colors: Dict[str, str]  # normalized uppercase #RRGGBB
    semantic: Dict[str, str]  # role -> #RRGGBB
    kustom_colors: Dict[str, str]  # global_name -> #AARRGGBB
    inactive_tab_bg: str  # #AARRGGBB for inactive nav tabs

    @property
    def is_dark(self) -> bool:
        return self.mode == "dark"

    @property
    def is_light(self) -> bool:
        return self.mode == "light"


def validate_theme(data: Dict[str, Any], file_path: Optional[Path] = None) -> None:
    """Validate a theme dictionary against schema requirements. Raises ValueError on error."""
    origin = f" in {file_path.name}" if file_path else ""

    if not isinstance(data, dict):
        raise ValueError(f"Theme data must be a JSON object{origin}")

    if data.get("schema_version") != 1:
        raise ValueError(f"Unsupported or missing schema_version{origin}: expected 1, got {data.get('schema_version')}")

    theme_id = data.get("id")
    if not theme_id or not isinstance(theme_id, str) or not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", theme_id):
        raise ValueError(f"Invalid theme id{origin}: must be lowercase kebab-case (e.g. 'tokyo-night-storm')")

    if file_path and file_path.stem != theme_id:
        raise ValueError(f"Theme id '{theme_id}' does not match filename '{file_path.name}'")

    name = data.get("name")
    if not name or not isinstance(name, str):
        raise ValueError(f"Missing or invalid name for theme '{theme_id}'{origin}")

    mode = data.get("mode")
    if mode not in ("dark", "light"):
        raise ValueError(f"Invalid mode '{mode}' for theme '{theme_id}'{origin}: must be 'dark' or 'light'")

    source = data.get("source")
    if not isinstance(source, dict):
        raise ValueError(f"Missing 'source' metadata object for theme '{theme_id}'{origin}")

    required_source_fields = ("project", "repository", "revision", "license")
    for field in required_source_fields:
        val = source.get(field)
        if not val or not isinstance(val, str) or val.strip() == "":
            raise ValueError(f"Missing required source field '{field}' for theme '{theme_id}'{origin}")

    colors = data.get("colors")
    if not isinstance(colors, dict) or len(colors) == 0:
        raise ValueError(f"Missing or empty 'colors' object for theme '{theme_id}'{origin}")

    for color_name, hex_val in colors.items():
        if not isinstance(hex_val, str):
            raise ValueError(f"Color '{color_name}' in theme '{theme_id}' must be a hex string{origin}")
        try:
            hex_to_rgb(hex_val)
        except Exception as e:
            raise ValueError(f"Invalid hex color '{hex_val}' for '{color_name}' in theme '{theme_id}'{origin}: {e}")

    semantic = data.get("semantic")
    if not isinstance(semantic, dict):
        raise ValueError(f"Missing 'semantic' object for theme '{theme_id}'{origin}")

    for role in REQUIRED_SEMANTIC_ROLES:
        if role not in semantic:
            raise ValueError(f"Missing required semantic role '{role}' in theme '{theme_id}'{origin}")
        ref = semantic[role]
        if not isinstance(ref, str):
            raise ValueError(f"Semantic role '{role}' in theme '{theme_id}' must be a string{origin}")
        if ref not in colors and not (ref.startswith("#") and len(ref) in (4, 7, 9)):
            raise ValueError(f"Semantic role '{role}' in theme '{theme_id}' references unknown color '{ref}'{origin}")


def load_theme(theme_id_or_path: Union[str, Path]) -> Dict[str, Any]:
    """Load raw theme data from themes directory by id or path."""
    if isinstance(theme_id_or_path, Path):
        path = theme_id_or_path
    else:
        path = THEMES_DIR / f"{theme_id_or_path}.json"

    if not path.is_file():
        available = [p.stem for p in sorted(THEMES_DIR.glob("*.json"))]
        msg = f"Theme '{theme_id_or_path}' not found at {path}."
        if available:
            msg += f" Available themes: {', '.join(available)}"
        raise FileNotFoundError(msg)

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    validate_theme(data, file_path=path)
    return data


def resolve_theme(theme_id_or_data: Union[str, Dict[str, Any], ResolvedTheme]) -> ResolvedTheme:
    """Resolve raw theme data into a ResolvedTheme instance."""
    if isinstance(theme_id_or_data, ResolvedTheme):
        return theme_id_or_data

    if isinstance(theme_id_or_data, str):
        data = load_theme(theme_id_or_data)
    else:
        data = theme_id_or_data
        validate_theme(data)

    theme_id = data["id"]
    name = data["name"]
    mode = data["mode"]
    source = dict(data["source"])

    raw_colors = {k: normalize_hex(v) for k, v in data["colors"].items()}

    semantic: Dict[str, str] = {}
    for role in REQUIRED_SEMANTIC_ROLES:
        ref = data["semantic"][role]
        if ref in raw_colors:
            semantic[role] = raw_colors[ref]
        elif ref.startswith("#"):
            semantic[role] = normalize_hex(ref)
        else:
            raise ValueError(f"Cannot resolve semantic role '{role}' with target '{ref}' in theme '{theme_id}'")

    opacity = DARK_OPACITY if mode == "dark" else LIGHT_OPACITY

    kustom_colors: Dict[str, str] = {}
    for role, global_name in SEMANTIC_TO_GLOBAL.items():
        color_hex = semantic[role]
        if role == "background":
            kustom_colors[global_name] = to_kustom_argb(color_hex, alpha=opacity["base"])
        elif role == "background_alt":
            kustom_colors[global_name] = to_kustom_argb(color_hex, alpha=opacity["mantle"])
        else:
            kustom_colors[global_name] = to_kustom_argb(color_hex, alpha=0xFF)

    inactive_tab_bg = to_kustom_argb(semantic["background_alt"], alpha=opacity["tab_inactive"])

    return ResolvedTheme(
        id=theme_id,
        name=name,
        mode=mode,
        source=source,
        raw_colors=raw_colors,
        semantic=semantic,
        kustom_colors=kustom_colors,
        inactive_tab_bg=inactive_tab_bg,
    )


def list_themes(themes_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """List all available themes with id, name, mode, and source metadata, sorted alphabetically by id."""
    target_dir = themes_dir or THEMES_DIR
    if not target_dir.is_dir():
        return []

    themes = []
    for file_path in sorted(target_dir.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            validate_theme(data, file_path=file_path)
            themes.append({
                "id": data["id"],
                "name": data["name"],
                "mode": data["mode"],
                "source": data.get("source", {}),
                "path": str(file_path),
            })
        except Exception:
            continue

    return sorted(themes, key=lambda t: t["id"])


if __name__ == "__main__":
    import sys
    themes = list_themes()
    print(f"Discovered {len(themes)} themes:")
    for t in themes:
        print(f"  - {t['id']:<26} [{t['mode']:<5}] {t['name']}")
