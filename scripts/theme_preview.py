#!/usr/bin/env python3
"""Generate an offline gallery of the three actual generated widget views."""
import argparse
import html
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.theme_catalog import DEFAULT_THEME_ID, list_themes, resolve_theme
from scripts.generate_clip import build_kustom_clip
from scripts.kustom_preview import (
    DEFAULT_WIDTH, DEFAULT_HEIGHT, STATES, VIEWS, KustomRenderer,
    fixture_globals, font_css, render_widget,
)


def render_widget_svg(theme, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, view="overview", state="normal", page=0, embed_font=False):
    """Render serialized native modules, including their missing-property defaults."""
    return render_widget(theme, view, width, height, state, page, embed_font)


def generate_html_gallery(themes, target_path, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, state="normal", view="all", page=0):
    if not themes:
        raise ValueError("No themes selected")
    if view not in (*VIEWS, "all"):
        raise ValueError(f"Unknown view: {view}")
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    cards, options = [], []
    count = len(json.loads(fixture_globals(state)["cnt_json"])["stats"])
    pages = max(1, (count + 4) // 5)
    for theme in themes:
        root = build_kustom_clip(write_outputs=False, theme=theme)
        panels, notes = [], set()
        for widget_view in VIEWS:
            svgs = []
            for p in range(pages if widget_view == "containers" else 1):
                renderer = KustomRenderer(root, width, height, widget_view, state, p)
                svg = renderer.render()
                notes.update(renderer.warnings)
                svgs.append(f'<div class="page" data-page="{p}">{svg}</div>')
            label = {"overview": "Overview", "containers": "Docker", "info": "Info"}[widget_view]
            panels.append(f'<section class="view-panel" data-view="{widget_view}"><h3>{label}</h3><div class="stage">{"".join(svgs)}</div></section>')
        swatches = ''.join(f'<span style="background:{theme.semantic[role]}" title="{role}: {theme.semantic[role]}"></span>' for role in ("cpu", "memory", "disk", "network", "success", "warning", "high", "error", "accent"))
        source = theme.source
        source_label = html.escape(source.get("repository", "") + "@" + source.get("revision", "")[:8])
        source_url = html.escape(f"https://github.com/{source['repository']}/blob/{source['revision']}/{source['path']}", quote=True)
        render_notes = '<details><summary>Serialized color defaults</summary><p>The white fallback is preserved where no active color property is serialized. This reproduces the current device issue.</p><ul>' + ''.join('<li>' + html.escape(note) + '</li>' for note in sorted(notes)) + '</ul></details>' if notes else ''
        cards.append(f'''<article class="theme-card" data-mode="{theme.mode}" data-theme="{theme.id}" id="theme-{theme.id}">
          <div class="theme-heading"><h2>{html.escape(theme.name)}</h2><code>{theme.id}</code><span>{theme.mode}</span></div>
          {''.join(panels)}
          <footer><div class="swatches" aria-label="Upstream semantic colors">{swatches}</div><a href="{source_url}" target="_blank" rel="noopener">{source_label}</a></footer>
          <details><summary>Palette and readable colors · {html.escape(source['variant'])}</summary><p>Swatches show the selected palette colors. The widget uses separate readable text companions and contrast-adjusted rings where needed. Canonical upstream colors stay intact.</p><ul>{''.join('<li>' + html.escape(key + ': ' + value['source'] + ' → ' + value['rendered']) + '</li>' for key, value in theme.adjustments.items())}</ul></details>
          {render_notes}</article>''')
        options.append(f'<option value="{theme.id}" data-mode="{theme.mode}">{html.escape(theme.name)}</option>')
    initial = DEFAULT_THEME_ID if any(t.id == DEFAULT_THEME_ID for t in themes) else themes[0].id
    # Script config contains identifiers only; private caches are never embedded.
    config = json.dumps({"theme": initial, "view": view, "page": min(max(page, 0), pages - 1)})
    template = '''<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BeszelFetch — Theme Gallery</title><style>
__FONT__
:root{color-scheme:dark;--backdrop:#000000;--backdrop-image:none}
*{box-sizing:border-box}body{margin:0;background:#111318;color:#e5e7ed;font:15px system-ui,sans-serif}
header{max-width:1100px;margin:auto;padding:28px 24px 12px}h1{font-size:24px;margin:0 0 10px}h2{font-size:19px;margin:0}h3{font-size:13px;font-weight:500;color:#c2c6d0;margin:12px 0 8px}
p{line-height:1.55;color:#b8bfcd;margin:10px 0}a{color:#b8bfcd;text-decoration:none}code{font:12px monospace;color:#a9b2c5}
.controls{max-width:1100px;margin:auto;padding:16px 24px;display:flex;flex-wrap:wrap;align-items:center;gap:14px;position:sticky;top:0;background:#111318f5;z-index:2;border-block:1px solid #30343e}
.control{display:flex;align-items:center;gap:8px;flex-wrap:wrap}button,select,input[type=file]{font:inherit}button,select{background:#232833;color:inherit;border:1px solid #444b59;border-radius:7px;padding:8px 11px}button{cursor:pointer}button[aria-pressed=true]{border-color:#c1a5fc;background:#393046}button:disabled{opacity:.35;cursor:default}label{font-size:13px}input[type=color]{width:38px;height:34px;border:1px solid #444b59;background:none}input[type=file]{max-width:225px;font-size:12px}
main{max-width:1100px;margin:0 auto;padding:16px 24px 40px}.theme-card{border:1px solid #30343e;border-radius:12px;padding:18px 22px;margin:0 0 24px}.theme-heading{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap}.theme-heading>span{font-size:12px;color:#a9b2c5;text-transform:uppercase}
.stage{background-color:var(--backdrop);background-image:var(--backdrop-image);background-size:cover;background-position:center;padding:18px;border-radius:8px;max-width:__STAGE_WIDTH__px}.widget-preview-svg{width:100%;height:auto;display:block;font-family:WidgetMono}.widget-preview-svg text{font-kerning:none;font-variant-ligatures:none}.widget-preview-svg g[data-node^="Tab"],.widget-preview-svg g[data-node="BtnPrev"],.widget-preview-svg g[data-node="BtnNext"]{cursor:pointer}
[hidden]{display:none!important}footer{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-top:18px;font-size:12px}.swatches{display:flex;gap:6px}.swatches span{width:16px;height:16px;border-radius:3px}details{font-size:12px;color:#a9b2c5;margin-top:14px}details p{max-width:650px}details ul{line-height:1.6}
.caption{font-size:12px}.notice{border-left:3px solid #ac91db;padding-left:12px;max-width:960px}@media(max-width:700px){header,.controls,main{padding-inline:12px}.theme-card{padding:12px}.stage{padding:10px}.controls{position:static}}
</style></head><body>
<header><h1>BeszelFetch Theme Gallery</h1><p>Three views from the generated widget: Overview, Docker and Info. Synthetic data, bundled JetBrains Mono Nerd Font, native geometry and serialized color defaults.</p>
<p class="caption">__COUNT__ themes · __WIDTH__ × __HEIGHT__ Kustom units · __STATE__ data state. Generate another size/state with the CLI.</p>
<p class="notice">Compare layouts and colors here, then confirm on KWGT. Native text rasterization, launcher scaling and wallpaper effects can still differ. Text and metric graphics are checked over black and white backdrops.</p></header>
<div class="controls">
<div class="control"><label for="mode">Mode</label><select id="mode"><option value="all">All</option><option value="dark">Dark</option><option value="light">Light</option></select><button id="previous" aria-label="Previous theme">←</button><label for="theme">Theme</label><select id="theme">__OPTIONS__</select><button id="next" aria-label="Next theme">→</button></div>
<div class="control" id="view-controls"><button data-view="overview">Overview</button><button data-view="containers">Docker</button><button data-view="info">Info</button><button data-view="all">All three</button></div>
<div class="control"><label><input id="compare" type="checkbox"> Show all themes</label></div>
<div class="control"><label for="backdrop">Backdrop</label><input id="backdrop" type="color" value="#000000"><button data-backdrop="#000000">Black</button><button data-backdrop="#ffffff">White</button><button data-backdrop="#505463">Gray</button><label for="image">Local image</label><input id="image" type="file" accept="image/*"><button id="clear-image">Clear image</button></div>
</div><main>__CARDS__</main>
<script>
const config=__CONFIG__;
const themeSelect=document.querySelector('#theme'), modeSelect=document.querySelector('#mode');
let currentView=config.view, currentPage=config.page;
themeSelect.value=config.theme;
function options(){return Array.from(themeSelect.options).filter(o=>!o.hidden)}
function refresh(){
 const available=options();
 document.querySelectorAll('.theme-card').forEach(card=>{
  card.hidden=(modeSelect.value!=='all'&&card.dataset.mode!==modeSelect.value)||(!document.querySelector('#compare').checked&&card.dataset.theme!==themeSelect.value);
  card.querySelectorAll('.view-panel').forEach(panel=>panel.hidden=currentView!=='all'&&panel.dataset.view!==currentView);
  card.querySelectorAll('[data-view="containers"] .page').forEach(p=>p.hidden=Number(p.dataset.page)!==currentPage);
 });
 document.querySelectorAll('#view-controls button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===currentView)));
 const index=available.findIndex(o=>o.value===themeSelect.value);
 document.querySelector('#previous').disabled=index<=0;document.querySelector('#next').disabled=index<0||index>=available.length-1;
}
function setView(view){currentView=view;refresh()}
modeSelect.addEventListener('change',()=>{
 Array.from(themeSelect.options).forEach(o=>{o.hidden=modeSelect.value!=='all'&&o.dataset.mode!==modeSelect.value;o.disabled=o.hidden});
 if(themeSelect.selectedOptions[0].hidden){const first=options()[0];if(first)themeSelect.value=first.value}refresh();
});
themeSelect.addEventListener('change',refresh);
for(const [id,delta] of [['previous',-1],['next',1]])document.querySelector('#'+id).addEventListener('click',()=>{const list=options(),i=list.findIndex(o=>o.value===themeSelect.value);if(list[i+delta])themeSelect.value=list[i+delta].value;refresh()});
document.querySelector('#compare').addEventListener('change',refresh);
document.querySelectorAll('#view-controls button').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.view)));
const actions={TabOverview:'overview',TabContainers:'containers',TabInfo:'info'};
document.querySelectorAll('.widget-preview-svg [data-node]').forEach(g=>{
 const name=g.dataset.node;if(!actions[name]&&!['BtnPrev','BtnNext'].includes(name))return;
 g.setAttribute('tabindex','0');g.setAttribute('role','button');g.setAttribute('aria-label',actions[name]||name);
 function activate(){if(actions[name])setView(actions[name]);else{const pages=g.closest('.stage').querySelectorAll('.page').length;currentPage=Math.min(pages-1,Math.max(0,currentPage+(name==='BtnNext'?1:-1)));refresh()}}
 g.addEventListener('click',activate);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate()}});
});
function backdrop(color){document.documentElement.style.setProperty('--backdrop',color);document.querySelector('#backdrop').value=color}
document.querySelectorAll('[data-backdrop]').forEach(b=>b.addEventListener('click',()=>backdrop(b.dataset.backdrop)));
document.querySelector('#backdrop').addEventListener('input',e=>backdrop(e.target.value));
document.querySelector('#image').addEventListener('change',e=>{const file=e.target.files[0];if(!file)return;const reader=new FileReader();reader.onload=()=>document.documentElement.style.setProperty('--backdrop-image','url("'+reader.result+'")');reader.readAsDataURL(file)});
document.querySelector('#clear-image').addEventListener('click',()=>{document.documentElement.style.setProperty('--backdrop-image','none');document.querySelector('#image').value=''});
refresh();
</script></body></html>'''
    replacements = {"__FONT__": font_css(), "__STAGE_WIDTH__": str(width + 36), "__COUNT__": str(len(themes)),
                    "__WIDTH__": str(width), "__HEIGHT__": str(height), "__STATE__": html.escape(state),
                    "__OPTIONS__": ''.join(options), "__CARDS__": '\n'.join(cards), "__CONFIG__": config}
    for key, value in replacements.items():
        template = template.replace(key, value)
    target_path.write_text(template, encoding="utf-8")
    print(f"✓ Generated three-view theme gallery: {target_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--all", action="store_true", help="Render all themes (the default)")
    parser.add_argument("--theme", help="Render only this theme ID")
    parser.add_argument("--output", type=Path, default=REPO_ROOT / "dist/theme-preview.html")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH, help="Widget width in Kustom units")
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT, help="Widget height in Kustom units (minimum 376)")
    parser.add_argument("--view", choices=(*VIEWS, "all"), default="all")
    parser.add_argument("--state", choices=STATES, default="normal")
    parser.add_argument("--page", type=int, default=0, help="Initial Docker page, zero based")
    parser.add_argument("--svg-dir", type=Path, help="Also export three standalone SVGs per theme with embedded font")
    args = parser.parse_args()
    if args.width < 1 or args.height < 376:
        parser.error("width must be positive and height must be at least 376 Kustom units")
    themes = [resolve_theme(args.theme)] if args.theme else [resolve_theme(t["id"]) for t in list_themes()]
    generate_html_gallery(themes, args.output, args.width, args.height, args.state, args.view, args.page)
    if args.svg_dir:
        args.svg_dir.mkdir(parents=True, exist_ok=True)
        for theme in themes:
            for view in VIEWS:
                svg = render_widget_svg(theme, args.width, args.height, view, args.state, args.page, embed_font=True)
                (args.svg_dir / f"{theme.id}-{view}.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
