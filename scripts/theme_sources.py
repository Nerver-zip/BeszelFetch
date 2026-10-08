#!/usr/bin/env python3
"""Reproduce canonical palettes from vendored, checksum-pinned upstream files.

The default check is offline. --fetch retrieves only the manifest's exact public
commit URLs; --write refreshes catalog colors/source metadata, never semantics.
"""
import argparse
import colorsys
import hashlib
import json
import math
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "themes/upstream"
MANIFEST = UPSTREAM / "manifest.json"


def hex_rgb(values):
    return "#" + "".join(f"{max(0, min(255, math.floor(v * 255 + .5))):02X}" for v in values)


def extract_colors(text, kind, variant=""):
    if kind == "catppuccin":
        return {k: v["hex"].upper() for k, v in json.loads(text)[variant]["colors"].items()}
    if kind == "rose-pine":
        return {v["role"]: "#" + v["hex"].upper() for v in json.loads(text)[variant]}
    if kind == "lua":
        clean = "\n".join(line.split("--", 1)[0] for line in text.splitlines())
        return {k: v.upper() for k, v in re.findall(r'(\w+)\s*=\s*(?:Shade.new\()?"(#[0-9a-fA-F]{6})"', clean)}
    if kind == "tokyo-export":
        # Only top-level colors in the official generated default export.
        block = text.split("local highlights", 1)[0]
        return {k: v.upper() for k, v in re.findall(r'^  (\w+) = "(#[0-9a-fA-F]{6})"', block, re.M)}
    if kind == "nord":
        return {k: v.upper() for k, v in re.findall(r'--(nord\d+):\s*(#[0-9a-fA-F]{6})', text)}
    if kind == "base16":
        return {k: v.upper() for k, v in re.findall(r'(base[0-9A-Fa-f]{2}):\s*"(#[0-9a-fA-F]{6})"', text)}
    if kind == "gruvbox":
        return {k: v.upper() for k, v in re.findall(r's:gb\.(\w+)\s*=\s*\[\s*[\'"](#[0-9a-fA-F]{6})', text)}
    if kind == "everforest":
        medium = text.split("elseif a:background ==# 'medium'", 1)[1].split('  else "{{{', 1)[0]
        blocks = re.findall(r'let palette1 = \{(.*?)\}', medium, re.S)
        common = text.split('let palette2 = {')[1:]
        block = blocks[0 if variant == "dark-medium" else 1] + common[0 if variant == "dark-medium" else 1].split('}', 1)[0]
        return {k: v.upper() for k, v in re.findall(r"'(\w+)':\s*\['(#[0-9a-fA-F]{6})'", block)}
    if kind == "solarized":
        return {k: v.upper() for k, v in re.findall(r'\$(\w+):\s*(#[0-9a-fA-F]{6});', text)}
    if kind == "tomorrow":
        text = text.split('" Console 256 Colours', 1)[0]
        return {k: "#" + v.upper() for k, v in re.findall(r'let s:(\w+) = "([0-9a-fA-F]{6})"', text)}
    if kind == "dracula":
        text = text.split('### Alucard', 1)[0]
        return {k.strip().lower().replace(' ', '_'): v.upper() for k, v in re.findall(r'\| ([A-Za-z ]+)\| `(#[0-9a-fA-F]{6})`', text)}
    if kind == "ayu-seeds":
        # Literal RGB seeds only, deliberately excluding references/OKLCH ramps.
        colors, parents = {}, []
        for line in text.splitlines():
            match = re.match(r'^( *)([\w]+):\s*(.*?)\s*$', line)
            if not match:
                continue
            indent, key, value = len(match[1]), match[2], match[3]
            while parents and parents[-1][0] >= indent:
                parents.pop()
            if not value:
                parents.append((indent, key))
            else:
                seed = value.split()[0].strip('"\'')
                if re.fullmatch(r'[0-9a-fA-F]{6}', seed):
                    colors['.'.join([p[1] for p in parents] + [key])] = '#' + seed.upper()
        return colors
    if kind == "atom-less":
        expressions = dict(re.findall(r'@([\w-]+):\s*([^;]+);', text))
        resolved = {}
        def value(name):
            if name in resolved:
                return resolved[name]
            expression = expressions[name].strip()
            if expression.startswith('@'):
                result = value(expression[1:])
            elif expression.startswith('hsl('):
                parts = expression[4:-1].split(',')
                nums = [value(p.strip()[1:]) if p.strip().startswith('@') else float(p.strip().rstrip('%')) for p in parts]
                result = colorsys.hls_to_rgb(nums[0] / 360, nums[2] / 100, nums[1] / 100)
            elif expression.startswith('darken('):
                reference, amount = expression[7:-1].split(',')
                rgb = value(reference.strip()[1:])
                h, l, s = colorsys.rgb_to_hls(*rgb)
                result = colorsys.hls_to_rgb(h, max(0, l-float(amount.strip().rstrip('%'))/100), s)
            else:
                result = float(expression.rstrip('%'))
            resolved[name] = result
            return result
        for name, expression in expressions.items():
            if not expression.strip().startswith('fade('):
                value(name)
        return {k: hex_rgb(v) for k, v in resolved.items() if isinstance(v, tuple)}
    if kind == "oxocarbon":
        # Native dark branch: base01..05 are channel blends, not literals.
        block = text.split('and {', 1)[1].split('}) or {', 1)[0]
        base = {k: v.upper() for k, v in re.findall(r'local (base\d+) = "(#[0-9a-fA-F]{6})"', text)}
        base.update({k: v.upper() for k, v in re.findall(r'(base\d+|blend) = "(#[0-9a-fA-F]{6})"', block)})
        for key, amount in re.findall(r'(base\d+) = blend_hex\(base00, base06, ([\d.]+)\)', block):
            a, b = base['base00'], base['base06']
            # Upstream blends in HSLuv. Both endpoints are neutral, so this is
            # an L* interpolation followed by neutral sRGB encoding.
            levels = []
            for color in (a, b):
                channel = int(color[1:3], 16) / 255
                y = channel / 12.92 if channel <= .04045 else ((channel + .055) / 1.055) ** 2.4
                levels.append(903.2962962 * y if y <= .0088564516 else 116 * y ** (1/3) - 16)
            lightness = levels[0] * (1-float(amount)) + levels[1] * float(amount)
            y = lightness / 903.2962962 if lightness <= 8 else ((lightness+16)/116)**3
            channel = 12.92*y if y <= .0031308 else 1.055*y**(1/2.4)-.055
            base[key] = hex_rgb((channel, channel, channel))
        return base
    raise ValueError(f"Unknown upstream extractor: {kind}")


def canonical_palette(theme_id, manifest=None):
    manifest = manifest or json.loads(MANIFEST.read_text())
    entry = manifest['themes'][theme_id]
    source = manifest['sources'][entry['source']]
    payload = (UPSTREAM / source['file']).read_bytes()
    if hashlib.sha256(payload).hexdigest() != source['sha256']:
        raise ValueError(f"Upstream checksum mismatch: {source['file']}")
    colors = extract_colors(payload.decode(), source['extractor'], entry.get('variant', ''))
    if not colors:
        raise ValueError(f"Empty upstream palette for {theme_id}")
    metadata = {k: source[k] for k in ('project', 'repository', 'revision', 'path', 'license')}
    metadata.update(snapshot=source['file'], sha256=source['sha256'], variant=entry['variant'])
    return colors, metadata


def check_palette(data):
    colors, source = canonical_palette(data['id'])
    if data['colors'] != colors:
        raise ValueError(f"{data['id']}: colors differ from pinned upstream extraction")
    if data['source'] != source:
        raise ValueError(f"{data['id']}: source metadata differs from pinned manifest")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    manifest = json.loads(MANIFEST.read_text())
    artifacts = {**manifest['sources'], **manifest.get('support_sources', {}), **manifest.get('licenses', {})}
    if args.fetch:
        for source in artifacts.values():
            url = f"https://raw.githubusercontent.com/{source['repository']}/{source['revision']}/{source['path']}"
            payload = urllib.request.urlopen(url, timeout=30).read()
            if hashlib.sha256(payload).hexdigest() != source['sha256']:
                raise ValueError(f"Fetched content differs from pinned checksum: {url}")
            (UPSTREAM / source['file']).write_bytes(payload)
    for source in artifacts.values():
        if hashlib.sha256((UPSTREAM / source['file']).read_bytes()).hexdigest() != source['sha256']:
            raise ValueError(f"Vendored artifact checksum mismatch: {source['file']}")
    for theme_id in manifest['themes']:
        path = ROOT / 'themes' / f'{theme_id}.json'
        data = json.loads(path.read_text())
        if args.write:
            data['colors'], data['source'] = canonical_palette(theme_id, manifest)
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
        check_palette(data)
    print(f"Verified {len(manifest['themes'])} canonical palettes against pinned snapshots")


if __name__ == '__main__':
    main()
