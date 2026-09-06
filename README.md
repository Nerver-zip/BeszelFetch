# Server Monitor Widget — KWGT + Beszel

A homelab monitoring widget for Android/KWGT consuming the **Beszel Hub REST API** directly, without requiring any middleman, proxy service, or secondary backend. Features a **Linux/Unix ricing + Catppuccin Mocha** aesthetic.

---

## 🚀 Complete Step-by-Step Setup Guide (Start Here!)

> **Zero-to-Hero Assumption**: You only have Beszel Hub running on a server/NAS and an Android device with KWGT installed. Nothing else has been configured.
>
> 💡 **No KWGT Pro Key Required**: You can import this widget completely free using the **Kustom Clip (`.clip`) method** below!

```text
┌─────────────────────────┐                            ┌─────────────────────────┐
│   Android Phone / KWGT  │   Direct HTTP(S) REST      │   Beszel Hub Server     │
│   (Free or Pro)         │ ─────────────────────────▶ │   (PocketBase API)      │
│   [Beszel Monitor Clip] │ ◀───────────────────────── │   Port 8090             │
└─────────────────────────┘                            └─────────────────────────┘
```

---

### Step 1: Verify Network Reachability

Your Android phone must be able to reach your Beszel Hub over your network.

1. **Find your Beszel Hub address**:
   - **Local Wi-Fi / LAN**: `http://<SERVER_IP>:8090` (e.g. `http://192.168.1.100:8090`).
   - **Remote / VPN**: Tailscale IP (`http://100.x.y.z:8090`), WireGuard LAN IP, or Cloudflare Tunnel / reverse proxy domain (`https://beszel.yourdomain.com`).
2. **Test from your phone**:
   - Open Chrome or Firefox on your Android phone.
   - Navigate to your Beszel address (e.g. `http://192.168.1.100:8090`).
   - If the Beszel web interface loads, your phone can reach the Hub!

---

### Step 2: Configure Beszel / PocketBase API Access

Beszel stores all metrics in an embedded PocketBase instance. Choose **Path A** (recommended for local homelabs) or **Path B** (for internet-exposed servers):

#### Path A: Public Read-Only for LAN (Easiest & Recommended for KWGT Free)
*Allows KWGT to read metrics directly via standard `$wg()` web formulas with zero token expiration worries.*

1. In your desktop browser, open the PocketBase Admin UI by adding `/_/` to your Beszel URL:
   ```text
   http://<YOUR_SERVER_IP>:8090/_/
   ```
2. Log in with the admin credentials you created when first installing Beszel.
3. In the left sidebar, click **Collections**.
4. Click on the **`systems`** collection:
   - Click the **API Rules** tab (padlock icon).
   - Under **"View rule"** and **"List rule"**, clear any existing text so the fields are completely empty (`""` / unlocked for anyone).
   - Click **Save changes** at the bottom.
5. *(Optional for Containers tab)*: Click the **`container_stats`** collection -> API Rules -> set View and List rules to empty -> Save.
6. *(Optional for Chart tab)*: Click the **`system_stats`** collection -> API Rules -> set View and List rules to empty -> Save.
7. **Verify**: Open `http://<YOUR_SERVER_IP>:8090/api/collections/systems/records` in your browser. You should immediately see JSON output containing your server list!

#### Path B: Dedicated User with JWT Token (For Secure / Internet-Facing Setups)
*Restricts API queries to an authenticated user account.*

1. In the PocketBase Admin UI (`http://<YOUR_SERVER_IP>:8090/_/`):
   - Go to Collections -> `users`.
   - Click **New record**, enter an email (e.g. `kwgt@local`) and password (e.g. `MyWidgetPass123`).
2. Obtain a JWT token using terminal/curl (or PowerShell):
   ```bash
   curl -X POST "http://<YOUR_SERVER_IP>:8090/api/collections/users/auth-with-password" \
     -H "Content-Type: application/json" \
     -d '{"identity": "kwgt@local", "password": "MyWidgetPass123"}'
   ```
3. Copy the `"token"` value from the returned JSON response (e.g. `eyJhbGci...`). You will paste this into `bz_token` in KWGT.

---

### Step 3: Install the Widget into KWGT

#### Method 1: The Kustom Clip Method (100% Free — No KWGT Pro Needed!)

1. On your phone or computer, open [`widget/beszel_monitor.clip`](widget/beszel_monitor.clip).
2. **Copy the ENTIRE file contents to your phone's clipboard** (make sure the first line `##KUSTOMCLIP##` is included).
   > *Tip: Send the text to your phone via Telegram "Saved Messages", WhatsApp, KDE Connect, or open GitHub on your phone browser.*
3. On your Android home screen:
   - Long-press an empty area and tap **Widgets**.
   - Scroll to **KWGT** and add a **4x2** or **4x3** blank widget to your screen.
4. Tap the blank widget on your home screen to open the KWGT editor.
5. In the top toolbar, tap the **Paste** (clipboard) icon:
   - KWGT will parse the `##KUSTOMCLIP##` from your clipboard and immediately insert the **Beszel Monitor** Komponent!
6. Tap on the newly pasted **Beszel Monitor** item in the items list to open its settings.
7. Navigate to the **Globals** tab and configure your connection:
   - **`bz_url`**: Set to your Beszel address (e.g. `http://192.168.1.100:8090` without a trailing slash).
   - If using **Path A**: Leave `bz_token` empty.
   - If using **Path B**: Paste your JWT token into **`bz_token`** (or enter `bz_email` and `bz_pass`).
8. Tap the **Save icon** (floppy disk) at the top right of KWGT.
9. Return to your home screen — your server metrics are now live!

#### Method 2: Preset Import (Requires KWGT Pro Key)

1. Copy [`widget/preset.json`](widget/preset.json) or your exported `.kwgt` file into your phone's `/sdcard/Kustom/widgets/` folder.
2. Add a KWGT widget to your home screen and tap it.
3. Go to the **Library** tab -> **Exported**, and select **Beszel Monitor**.
4. Configure globals in the **Globals** tab and tap **Save**.

---

### Step 4: Interacting with the Widget

The widget features 3 switchable views and interactive touch targets:

- **Switch Views**: Tap the bottom navigation tabs:
  - `[ overview ]`: Gauges for CPU %, RAM %, Disk %, Network I/O (sent/recv rate), Load Average, Temperature, and Uptime.
  - `[ containers ]`: Live container list with status dot, name, CPU %, and memory usage.
  - `[ chart ]`: 24-point historical sparklines. Tap `[CPU]`, `[RAM]`, `[DISK]`, or `[NET]` to toggle metrics.
- **Switch Monitored Server**: Tap the **hostname** in the top header to cycle between all registered servers.
- **Manual Refresh**: Tap the **↻** icon in the top right to force an instant telemetry sync.
- **Container Pagination**: In the Containers view, tap **◀ Prev** and **Next ▶** to page through running containers.
- **Health Indicator**:
  - 🟢 **Green Dot**: Server is `up` and telemetry is fresh.
  - 🟡 **Yellow Dot**: Stale cache (server temporarily unreachable; displays last known metrics).
  - 🔴 **Red Dot**: Server is `down` or connection/auth failed.

---

### Step 5: Troubleshooting & FAQs

| Symptom | Cause | Solution |
|---|---|---|
| **Red Dot / "beszel-host" default text** | Cannot reach Hub or 403 Forbidden | Ensure phone is on the same Wi-Fi/VPN as the server. Verify PocketBase API rules are unlocked (Path A) or token is valid (Path B). |
| **Widget content is too small or clipped** | Launcher grid scaling mismatch | In KWGT editor, go to the **Layer** tab and adjust the **Scale** slider until it fits your widget frame cleanly. |
| **Containers tab shows no rows** | Container agent not enabled or collection locked | Ensure the Beszel Agent is running Docker/Podman metrics on the server, and `container_stats` API rules are unlocked in PocketBase. |
| **No updates when on mobile data** | Server is only on local LAN IP | Connect to your home VPN (Tailscale, WireGuard) or expose Beszel Hub via a secure reverse proxy / Cloudflare Tunnel. |

---

## Architectural Principles

1. **Direct Client-to-Hub**: Android/KWGT is the sole client; Beszel Hub/PocketBase is the sole data source. No middleman proxy or cloud bridge.
2. **Dual-Mode Data Fetching**: Formulas support both cached globals populated by Kustom Flows AND direct native `$wg()` requests, making the widget work equally on KWGT Free and Pro.
3. **Graceful Degradation**: Network drops never wipe valid data. Stale cache is retained and flagged with a warning indicator.
4. **Catppuccin Mocha Palette**: High-contrast dark theme optimized for OLED screens with WCAG 2.1 AA/AAA compliance.
5. **Touch Accessibility**: All interactive touch targets (tabs, host selector, refresh button, pagination) meet or exceed the 48dp minimum standard.

---

## Repository Structure

```text
server-monitor/
├── README.md                          # Full setup guide, architecture & documentation
├── ARCHITECTURE.md                    # Core architecture & design constraints
├── WIDGET_SPEC.md                     # Screen specifications, sizing & layouts
├── KWGT_BUILD_GUIDE.md                # Layer assembly & step-by-step editor guide
├── DATA_CONTRACT.md                   # Beszel/PocketBase JSON schemas & mappings
├── SECURITY.md                        # Security model & secrets quarantine
├── widget/
│   ├── beszel_monitor.clip            # Standalone Kustom Clip (##KUSTOMCLIP## for KWGT Free)
│   ├── preset.json                    # Declarative Kustom preset schema definition
│   ├── TREE.md                        # Complete component hierarchy
│   └── COMPONENTS.md                  # Detailed element properties
├── scripts/
│   ├── generate_clip.py               # Generates widget/beszel_monitor.clip
│   ├── generate_preset.py             # Generates widget/preset.json & runs clip generator
│   └── test_contracts.py              # Automated test harness (28 unit tests)
├── examples/
│   ├── palette.json                   # Catppuccin Mocha tokens & contrast definitions
│   ├── globals.md                     # Global variable specifications
│   ├── flows.md                       # Kustom Flows recipes (auth, polling, caching)
│   ├── formulas.md                    # Ready-to-copy formula snippets
│   └── fixtures/                      # Sanitized API response mocks
└── .agents/                           # Specialized multi-agent developer skills
```

---

## Automated Contract Testing

An automated test harness validates data contracts, formulas, downsampling algorithms, and preset definitions:

```bash
python3 scripts/test_contracts.py
```

Output:
```text
test_contrast_ratios ... ok
test_touch_targets_standard ... ok
test_threshold_ranges ... ok
test_clip_header_and_valid_json ... ok
test_komponent_globals ... ok
test_komponent_views_and_touch_targets ... ok
test_preset_root_keys ... ok
test_required_globals_present ... ok
test_root_view_layers_present ... ok
test_touch_targets_dimensions_in_preset ... ok
test_401_triggers_single_reauth ... ok
test_403_forbidden_no_retry ... ok
test_network_failure_preserves_cache ... ok
test_parse_valid_systems ... ok
test_byte_formatting ... ok
test_uptime_formatting ... ok
----------------------------------------------------------------------
Ran 28 tests in 0.024s

OK
```

---

## Recommended Defaults

| Parameter | Recommended Value | Purpose |
|---|---|---|
| Background Refresh | 5 minutes | Balances battery consumption with metric freshness |
| Manual Refresh | Header button `↻` | On-demand immediate update (`FORCE_UPDATE`) |
| Container Page Size | 5 containers | Preserves legibility and 48dp minimum touch bounds |
| Chart Datapoints | 24 points | Fits standard daily/hourly buckets evenly |
| Color Theme | Catppuccin Mocha | Contrast > 10:1 on text, > 4:1 on UI elements |

---

## Documentation Index

- [ARCHITECTURE.md](ARCHITECTURE.md) — System constraints, boundary rules, and cache strategy.
- [DATA_CONTRACT.md](DATA_CONTRACT.md) — Exact JSON payload specifications for Beszel v0.7+ and v0.10+.
- [KWGT_BUILD_GUIDE.md](KWGT_BUILD_GUIDE.md) — Manual building guide for KWGT editor.
- [WIDGET_SPEC.md](WIDGET_SPEC.md) — Visual mockup definitions and grid dimensions.
- [.agents/README.md](.agents/README.md) — Multi-agent role descriptions and skill guidelines.
