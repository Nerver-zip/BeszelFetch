#!/usr/bin/env python3
"""Generate the inspectable definition from the SAME tree as the native clip.

This is a development artifact, not a claim of native KWGT export/validation.
No second implementation of UI formulas or pretend authentication flows.
"""
import json
from pathlib import Path

if __package__:
    from .generate_clip import build_kustom_clip
else:
    from generate_clip import build_kustom_clip

REPO_ROOT = Path(__file__).resolve().parents[1]
PRESET_FILE = REPO_ROOT / "widget/preset.json"


def project(node):
    """Retain native properties while giving the documented tree readable keys."""
    result = {k: v for k, v in node.items()
              if k not in ("viewgroup_items", "internal_title", "internal_type")}
    result.update(name=node.get("internal_title", ""), type=node["internal_type"])
    children = [project(child) for child in node.get("viewgroup_items", [])]
    if children:
        result["children"] = children
    result["width"] = node.get("shape_width", max((c.get("width", 0) for c in children), default=0))
    result["height"] = node.get("shape_height", max((c.get("height", 0) for c in children), default=0))
    if node.get("internal_events"):
        result["touch_action"] = node["internal_events"][0]
    return result


def build_kustom_preset():
    komponent = build_kustom_clip(write_outputs=False)
    definition = {
        "kustom_version": 37000,
        "widget_spec": {"title": "Beszel Homelab Monitor",
                        "description": "Overview, Docker and two-column System Info & Sensors",
                        "artifact_kind": "development definition; native import tested manually"},
        "globals": [{"name": name, **value} for name, value in komponent["globals_list"].items()],
        "root": project({"internal_type": "RootLayerModule", "internal_title": "Beszel Monitor",
                         "viewgroup_items": komponent["viewgroup_items"]}),
        "flows": [{"id": f["name"], "native_id": f["id"], "triggers": f["t"], "actions": f["a"]}
                  for f in komponent["internal_flows"]],
    }
    PRESET_FILE.write_text(json.dumps(definition, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✓ Preset definition successfully generated at: {PRESET_FILE}")
    return definition


if __name__ == "__main__":
    build_kustom_preset()
