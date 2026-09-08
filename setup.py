#!/usr/bin/env python3
"""
Interactive Setup & Widget Generator for Beszel Homelab Monitoring KWGT Widget.
Prompts for Beszel Hub URL, server display name, and credentials, authenticates with PocketBase,
validates systems access, and compiles a ready-to-use KWGT package and clipboard clips.
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
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DIST_DIR = REPO_ROOT / "dist"
PALETTE_FILE = REPO_ROOT / "examples" / "palette.json"


def print_banner():
    banner = r"""
╔══════════════════════════════════════════════════════════════════╗
║                         Beszel Monitor                           ║
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


def fetch_systems(hub_url, token=None):
    hub_url = hub_url.rstrip("/")
    url = f"{hub_url}/api/collections/systems/records?perPage=100&fields=id,name,status,info&sort=name"
    headers = {}
    if token:
        headers["Authorization"] = token
    status, res = http_get(url, headers=headers)
    if status == 200:
        return res
    return None


def fetch_container_stats(hub_url, system_id=None, token=None):
    hub_url = hub_url.rstrip("/")
    headers = {}
    if token:
        headers["Authorization"] = token
    if not system_id:
        return None
    query = urllib.parse.urlencode({"filter": f'system="{system_id}" && type="1m"',
                                  "sort": "-created", "perPage": 1})
    status, res = http_get(f"{hub_url}/api/collections/container_stats/records?{query}", headers=headers)
    if status == 200 and res.get("items"):
        return res["items"][0]
    return None


def fetch_system_stats(hub_url, system_id=None, token=None):
    hub_url = hub_url.rstrip("/")
    headers = {}
    if token:
        headers["Authorization"] = token
    if not system_id:
        return None
    start = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    query = urllib.parse.urlencode({
        "filter": f'system="{system_id}" && created>"{start}" && type="20m"',
        "sort": "created", "perPage": 500, "fields": "created,stats",
    })
    status, res = http_get(f"{hub_url}/api/collections/system_stats/records?{query}", headers=headers)
    if status == 200 and isinstance(res.get("items"), list):
        return res
    return None


def fetch_latest_stats(hub_url, system_id=None, token=None):
    """Seed scalar Info/Sensors independently from daily network aggregates."""
    if not system_id:
        return None
    query = urllib.parse.urlencode({"filter": f'system="{system_id}" && type="1m"',
                                  "sort": "-created", "perPage": 1, "fields": "created,stats"})
    headers = {"Authorization": token} if token else {}
    status, res = http_get(f"{hub_url.rstrip('/')}/api/collections/system_stats/records?{query}", headers=headers)
    return res if status == 200 and isinstance(res.get("items"), list) else None


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


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="Configure and compile ready-to-use Beszel KWGT widget.")
    parser.add_argument("--url", help="Beszel Hub base URL (default: http://localhost:8090)")
    parser.add_argument("--name", help="Server display name (default: localhost or auto-detected)")
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
        r_status, _ = http_get(f"{hub_url}/")
        if r_status == 0:
            print(f"\033[1;31m✖ Error:\033[0m Cannot reach {hub_url}. Please verify IP/domain and network.")
            sys.exit(1)

    print("\033[1;32m✓ Hub is online and reachable!\033[0m")

    # 2. Prompt for Credentials (optional if Hub allows public read)
    default_user = os.environ.get("BESZEL_USER", "")
    token = None
    role = None
    identity = ""
    password = ""

    if args.identity is not None:
        identity = args.identity.strip()
    else:
        prompt_user = f"\033[1;32m? Email / Identity\033[0m (press Enter if no auth required) [\033[36m{default_user}\033[0m]: "
        val = input(prompt_user).strip()
        identity = val if val else default_user

    if identity:
        if args.password:
            password = args.password
        else:
            password = getpass.getpass("\033[1;32m? Password\033[0m: ")

        print("\n⏳ Authenticating with Beszel Hub...")
        token, role, auth_res = authenticate(hub_url, identity, password)
        if not token:
            print(f"\033[1;31m✖ Authentication failed!\033[0m Details: {auth_res.get('message', 'Invalid credentials')}")
            sys.exit(1)

        print(f"\033[1;32m✓ Authentication successful!\033[0m (Logged in as \033[36m{role}\033[0m)")
        print(f"  Token: \033[33m{token[:18]}...{token[-8:]}\033[0m")
    else:
        print("\nℹ Skipping authentication (no identity provided).")

    # 3. Fetch Systems
    print("\n⏳ Fetching systems data...")
    systems_data = fetch_systems(hub_url, token)
    items = systems_data.get("items", []) if systems_data else []

    if not items:
        if not identity:
            print("\033[33m⚠ No systems visible without authentication. Your Beszel instance requires login.\033[0m")
            prompt_user = f"\033[1;32m? Email / Identity\033[0m: "
            identity = input(prompt_user).strip()
            if identity:
                password = getpass.getpass("\033[1;32m? Password\033[0m: ")
                print("\n⏳ Authenticating with Beszel Hub...")
                token, role, auth_res = authenticate(hub_url, identity, password)
                if token:
                    print(f"\033[1;32m✓ Authentication successful!\033[0m (Logged in as \033[36m{role}\033[0m)")
                    systems_data = fetch_systems(hub_url, token)
                    items = systems_data.get("items", []) if systems_data else []
        if not items:
            print("\033[33m⚠ Warning:\033[0m Connected, but no systems found in Beszel yet.")
    if items:
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

    # 4. Fetch Live Containers & Telemetry History for Active System
    active_sys_id = items[0].get("id", "") if items else ""
    containers_data = None
    history_data = None
    latest_data = None
    if active_sys_id:
        print(f"\n⏳ Fetching live Docker containers for primary system...")
        containers_data = fetch_container_stats(hub_url, active_sys_id, token)
        if containers_data and "stats" in containers_data:
            c_list = containers_data.get("stats", [])
            print(f"\033[1;32m✓ Found {len(c_list)} running container(s):\033[0m")
            for c in c_list[:5]:
                m_val = c.get('m', 0)
                m_mb = round(m_val, 1)
                print(f"  • \033[1m{c.get('n', 'unknown')}\033[0m | CPU: {c.get('c', 0)}% | RAM: {m_mb} MiB")
        else:
            print("\033[33mℹ No container stats in hub yet (using standard template).\033[0m")

        print(f"\n⏳ Fetching 24h history telemetry...")
        history_data = fetch_system_stats(hub_url, active_sys_id, token)
        if history_data and history_data.get("items"):
            items_raw = history_data["items"]
            n = len(items_raw)
            print(f"\033[1;32m✓ Retrieved {n} history points.\033[0m")
            # Preserve every 20m aggregate for the daily traffic integral.
            # Info/Sensors does not need any chart downsampling.
        latest_data = fetch_latest_stats(hub_url, active_sys_id, token)

    # 5. Prompt for Server Display Name (suggesting detected system name if available)
    detected_name = items[0].get("name", "localhost") if items else "localhost"
    default_name = os.environ.get("BESZEL_SERVER_NAME", detected_name)
    if args.name:
        server_name = args.name.strip()
    else:
        prompt_name = f"\n\033[1;32m? Server Display Name\033[0m [\033[36m{default_name}\033[0m]: "
        val_name = input(prompt_name).strip()
        server_name = val_name if val_name else default_name

    # 6. Compile Widget
    print(f"\n⏳ Compiling widget with server name: \033[1;36m{server_name}\033[0m...")
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from scripts.generate_clip import build_kustom_clip

    build_kustom_clip(
        hub_url=hub_url,
        token=token,
        email=identity,
        password=password,
        server_name=server_name,
        systems_data=systems_data,
        containers_data=containers_data if containers_data is not None else {"stats": []},
        history_data=history_data if history_data is not None else {"items": []},
        latest_data=latest_data if latest_data is not None else {"items": []}
    )

    kwgt_file = REPO_ROOT / "widget" / "beszel_monitor.kwgt"
    clip_file = REPO_ROOT / "widget" / "beszel_monitor.clip"

    print(f"\n\033[1;32m✓ Widget generated successfully!\033[0m")
    print(f"  📁 Standalone KWGT package: \033[36m{kwgt_file}\033[0m")
    print(f"  📁 Kustom Clip (Komponent): \033[36m{clip_file}\033[0m")

    # 6. Copy Clip to Clipboard
    try:
        with open(clip_file, "r", encoding="utf-8") as f:
            clip_content = f.read()
        clip_tool = copy_to_clipboard(clip_content)
        if clip_tool:
            print(f"\n\033[1;32m📋 COPIED TO SYSTEM CLIPBOARD via {clip_tool}!\033[0m")
    except Exception:
        pass

    # 7. Next steps summary
    print("\n" + "═" * 66)
    print("\033[1;37mHOW TO INSTALL ON YOUR PHONE:\033[0m")
    print(" Option A (Standalone Preset - Recommended):")
    print(f"   1. Transfer the .kwgt file to your phone's Kustom widgets directory:")
    print(f"      \033[33mscp {kwgt_file} <phone_user>@<phone_ip>:/sdcard/Kustom/widgets/\033[0m")
    print("   2. Add a blank KWGT widget (4x2 or 4x3) on your home screen.")
    print("   3. Tap it, go to Library / Explore, and select 'Beszel Monitor'.")
    print("   4. Tap Save (Floppy icon). Done!")
    print()
    print(" Option B (Clipboard Paste):")
    print("   1. Open any blank KWGT widget on your phone.")
    print("   2. Tap the Clipboard / Paste icon on the top right toolbar.")
    print("   3. Tap Save. Done!")
    print("═" * 66 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
