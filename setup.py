#!/usr/bin/env python3
"""
Interactive Setup & Widget Generator for Beszel Homelab Monitoring KWGT Widget.
Prompts for Beszel Hub URL and credentials, authenticates with PocketBase,
validates systems access, and compiles a ready-to-paste Kustom Clip with
credentials pre-configured.
"""

import argparse
import getpass
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DIST_DIR = REPO_ROOT / "dist"
PALETTE_FILE = REPO_ROOT / "examples" / "palette.json"


def print_banner():
    banner = r"""
╔══════════════════════════════════════════════════════════════════╗
║         Beszel Homelab Monitor — KWGT Widget Setup               ║
║    Direct Hub-to-Client · Linux Ricing · Catppuccin Mocha        ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print("\033[1;34m" + banner + "\033[0m")


def http_post(url, data_dict, headers=None):
    if headers is None:
        headers = {}
    headers.setdefault("Content-Type", "application/json")
    headers.setdefault("User-Agent", "Beszel-KWGT-Setup/1.0")

    payload = json.dumps(data_dict).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}
    except Exception as e:
        return 0, {"error": str(e)}


def http_get(url, headers=None):
    if headers is None:
        headers = {}
    headers.setdefault("User-Agent", "Beszel-KWGT-Setup/1.0")

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, {"error": body}
    except Exception as e:
        return 0, {"error": str(e)}


def authenticate(hub_url, identity, password):
    hub_url = hub_url.rstrip("/")

    # 1. Try _superusers (PocketBase v0.23+ admin)
    url_super = f"{hub_url}/api/collections/_superusers/auth-with-password"
    status, res = http_post(url_super, {"identity": identity, "password": password})
    if status == 200 and "token" in res:
        return res["token"], "superuser", res.get("record", {})

    # 2. Try users collection (standard Beszel user)
    url_users = f"{hub_url}/api/collections/users/auth-with-password"
    status, res = http_post(url_users, {"identity": identity, "password": password})
    if status == 200 and "token" in res:
        return res["token"], "user", res.get("record", {})

    # 3. Try legacy admins endpoint (PocketBase < v0.23)
    url_admin = f"{hub_url}/api/admins/auth-with-password"
    status, res = http_post(url_admin, {"identity": identity, "password": password})
    if status == 200 and "token" in res:
        return res["token"], "admin", res.get("admin", {})

    return None, None, res


def fetch_systems(hub_url, token):
    hub_url = hub_url.rstrip("/")
    url = f"{hub_url}/api/collections/systems/records?perPage=100&fields=id,name,status,info&sort=name"
    status, res = http_get(url, headers={"Authorization": token})
    if status == 200:
        return res
    return None


def copy_to_clipboard(text):
    for cmd in ["wl-copy", "xclip -selection clipboard", "xsel --clipboard --input", "pbcopy"]:
        prog = cmd.split()[0]
        if shutil.which(prog):
            try:
                p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
                p.communicate(input=text.encode("utf-8"))
                if p.returncode == 0:
                    return prog
            except Exception:
                continue
    return None


def build_custom_clip(hub_url, token, email, pass_secret, systems_payload, output_file):
    # Load palette tokens
    with open(PALETTE_FILE, "r", encoding="utf-8") as f:
        palette_data = json.load(f)
    tokens = palette_data.get("tokens", {})

    def to_kustom_color(hex_str):
        hex_clean = hex_str.lstrip("#")
        if len(hex_clean) == 6:
            return f"#FF{hex_clean.upper()}"
        elif len(hex_clean) == 8:
            return f"#{hex_clean.upper()}"
        return "#FFFFFFFF"

    items = systems_payload.get("items", []) if systems_payload else []
    default_sys_id = items[0].get("id", "") if items else ""
    sys_json_cached = json.dumps(systems_payload) if systems_payload else "{}"

    # Import generator structure
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from scripts.generate_clip import build_kustom_clip

    # Generate base structure then inject pre-configured values
    build_kustom_clip()
    clip_src = REPO_ROOT / "widget" / "beszel_monitor.clip"
    with open(clip_src, "r", encoding="utf-8") as f:
        content = f.read()

    header = "##KUSTOMCLIP##\n"
    json_str = content[len(header):]
    clip_data = json.loads(json_str)

    komponent = clip_data["clip_modules"][0]
    g = komponent["globals_list"]

    # Inject authenticated credentials & cached systems
    g["bz_url"]["value"] = hub_url
    g["bz_token"]["value"] = token
    g["bz_email"]["value"] = email
    g["bz_pass"]["value"] = pass_secret
    g["sys_id"]["value"] = default_sys_id
    g["sys_json"]["value"] = sys_json_cached

    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    new_clip_content = f"{header}{json.dumps(clip_data, indent=2, ensure_ascii=False)}\n"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_clip_content)

    return new_clip_content


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Configure and compile ready-to-use Beszel KWGT widget.")
    parser.add_argument("--url", help="Beszel Hub base URL (default: http://localhost:8090)")
    parser.add_argument("--identity", help="Beszel/PocketBase user email or username")
    parser.add_argument("--password", help="Password for authentication")
    parser.add_argument("--output-dir", default=str(DIST_DIR), help="Output directory for generated widget files")
    args = parser.parse_args()

    # 1. Prompt for Hub URL
    default_url = os.environ.get("BESZEL_HUB_URL", "http://localhost:8090")
    if args.url:
        hub_url = args.url.strip().rstrip("/")
    else:
        prompt_str = f"\033[1;32m? Beszel Hub URL\033[0m [\033[36m{default_url}\033[0m]: "
        val = input(prompt_str).strip()
        hub_url = (val if val else default_url).rstrip("/")

    # Check connection
    print(f"\n⏳ Checking connection to \033[36m{hub_url}\033[0m...")
    health_status, health_res = http_get(f"{hub_url}/api/health")
    if health_status != 200:
        # Try root
        r_status, _ = http_get(f"{hub_url}/")
        if r_status == 0:
            print(f"\033[1;31m✖ Error:\033[0m Cannot reach {hub_url}. Please verify IP/domain and network.")
            sys.exit(1)

    print("\033[1;32m✓ Hub is online and reachable!\033[0m")

    # 2. Prompt for Credentials
    default_user = os.environ.get("BESZEL_USER", "")
    if args.identity:
        identity = args.identity.strip()
    else:
        if default_user:
            prompt_user = f"\033[1;32m? Email / Identity\033[0m [\033[36m{default_user}\033[0m]: "
        else:
            prompt_user = "\033[1;32m? Email / Identity\033[0m (e.g. admin@example.com): "
        val = input(prompt_user).strip()
        identity = val if val else default_user
        if not identity:
            print("\033[1;31m✖ Error:\033[0m Email / Identity cannot be empty.")
            sys.exit(1)

    if args.password:
        password = args.password
    else:
        password = getpass.getpass("\033[1;32m? Password\033[0m: ")
        if not password:
            print("\033[1;31m✖ Error:\033[0m Password cannot be empty.")
            sys.exit(1)

    # 3. Authenticate
    print("\n⏳ Authenticating with Beszel Hub...")
    token, role, auth_res = authenticate(hub_url, identity, password)
    if not token:
        print(f"\033[1;31m✖ Authentication failed!\033[0m Details: {auth_res.get('message', 'Invalid credentials')}")
        sys.exit(1)

    print(f"\033[1;32m✓ Authentication successful!\033[0m (Logged in as \033[36m{role}\033[0m)")
    print(f"  Token: \033[33m{token[:18]}...{token[-8:]}\033[0m")

    # 4. Fetch Systems
    print("\n⏳ Fetching systems data...")
    systems_data = fetch_systems(hub_url, token)
    items = systems_data.get("items", []) if systems_data else []

    if not items:
        print("\033[33m⚠ Warning:\033[0m Connected, but no systems found in Beszel yet.")
    else:
        print(f"\033[1;32m✓ Found {len(items)} system(s):\033[0m")
        for sys_item in items:
            name = sys_item.get("name", "unknown")
            status = sys_item.get("status", "unknown")
            info = sys_item.get("info", {}) or {}
            cpu = info.get("cpu", 0)
            mem = info.get("mp", 0)
            temp = info.get("dt")
            temp_str = f"{temp}°C" if temp is not None else "—"
            stat_color = "\033[32m" if status == "up" else "\033[31m"
            print(f"  • \033[1m{name}\033[0m — Status: {stat_color}{status}\033[0m | CPU: {cpu}% | RAM: {mem}% | Temp: {temp_str}")

    # 5. Compile Widget with Credentials Pre-loaded
    out_dir = Path(args.output_dir)
    out_clip = out_dir / "beszel_monitor.clip"
    out_preset = out_dir / "preset.json"

    print("\n⏳ Compiling pre-configured Kustom widget...")
    clip_text = build_custom_clip(
        hub_url=hub_url,
        token=token,
        email=identity,
        pass_secret=password,
        systems_payload=systems_data,
        output_file=out_clip
    )

    # Also save preset JSON
    with open(REPO_ROOT / "widget" / "preset.json", "r", encoding="utf-8") as f:
        preset_data = json.load(f)
    for g in preset_data.get("globals", []):
        if g["name"] == "bz_url":
            g["value"] = hub_url
        elif g["name"] == "bz_token":
            g["value"] = token
        elif g["name"] == "bz_email":
            g["value"] = identity
        elif g["name"] == "bz_pass":
            g["value"] = password
        elif g["name"] == "sys_json" and systems_data:
            g["value"] = json.dumps(systems_data)
    with open(out_preset, "w", encoding="utf-8") as f:
        json.dump(preset_data, f, indent=2)

    print(f"\033[1;32m✓ Widget generated successfully!\033[0m")
    print(f"  📁 Output clip:   \033[36m{out_clip}\033[0m")
    print(f"  📁 Output preset: \033[36m{out_preset}\033[0m")

    # 6. Copy to Clipboard
    clip_tool = copy_to_clipboard(clip_text)
    if clip_tool:
        print(f"\n\033[1;32m📋 COPIED TO SYSTEM CLIPBOARD via {clip_tool}!\033[0m")
    else:
        print(f"\n\033[33mℹ File saved at: {out_clip}\033[0m")

    # 7. Next steps summary
    print("\n" + "═" * 66)
    print("\033[1;37mNEXT STEPS TO USE ON YOUR PHONE:\033[0m")
    print(" 1. On your phone: Add a blank KWGT widget (4x2 or 4x3) to your home screen.")
    print(" 2. Tap the widget to open KWGT.")
    print(" 3. Tap the \033[1;32mPaste (Clipboard) icon\033[0m on the top right toolbar.")
    print(" 4. Tap \033[1;32mSave (Floppy icon)\033[0m at the top right.")
    print(" 5. Return to your home screen — your server metrics appear live!")
    print("═" * 66 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
