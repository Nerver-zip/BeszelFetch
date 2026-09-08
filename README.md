# 🖥️ Beszel Homelab Monitor for Android (KWGT)

<p align="center">
  <img src="docs/screenshots/homescreen.png" alt="Beszel Monitor Android Homescreen" width="380"/>
</p>

<p align="center">
  <strong>A modern, Unix-riced homelab monitoring widget for Android/KWGT, consuming the Beszel Hub REST API directly with zero middleman or proxy services.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Style-Catppuccin%20Mocha-cba6f7?style=flat-square" alt="Catppuccin Mocha"/>
  <img src="https://img.shields.io/badge/Client-KWGT%20%2F%20Kustom-89b4fa?style=flat-square" alt="KWGT"/>
  <img src="https://img.shields.io/badge/Backend-Beszel%20Hub-a6e3a1?style=flat-square" alt="Beszel"/>
  <img src="https://img.shields.io/badge/Security-Gitleaks-brightgreen?style=flat-square" alt="Gitleaks"/>
  <img src="https://img.shields.io/badge/CI-GitHub%20Actions-blue?style=flat-square" alt="CI"/>
  <img src="https://img.shields.io/badge/License-MIT-fab387?style=flat-square" alt="MIT License"/>
</p>

---

## ✨ Highlights & Features

- **Direct Hub-to-Client**: Your Android phone communicates directly with your Beszel Hub (PocketBase REST API). No third-party servers, cloud bridges, or proxy microservices.
- **Catppuccin Mocha Palette**: High-contrast, OLED-friendly colors with deep translucent cards and frosted-glass depth.
- **Three Interactive Tabbed Views**:
  - **Overview**: Circular gauges for CPU, RAM, Disk, Load Average, Temperature, and Network I/O rates + 24-hour total traffic.
  - **Docker Containers**: Live container list with real-time status dots (🟢 running / 🔴 stopped or unhealthy), CPU %, RAM usage, and ◀ Prev / Next ▶ pagination.
  - **System Info (Fastfetch)**: Distro-specific ASCII art (Arch, Debian, Ubuntu, Fedora, Alpine, etc.), Kernel, CPU model, Core/Thread counts, Uptime, and terminal ANSI color blocks.
- **Multi-Host Switching**: Tap the hostname in the header bar to cycle seamlessly through all registered homelab servers.
- **Zero-Loss Caching**: Temporary network dropouts never blank your screen; last-known metrics are preserved with a visual status indicator.
- **Works with KWGT Free & Pro**: Fully importable via clipboard without purchasing KWGT Pro.

---

## 📸 Widget Views

<table align="center">
  <tr>
    <th align="center">📊 System Overview</th>
    <th align="center">🐳 Docker Containers</th>
    <th align="center">🐧 Host Info (Fastfetch)</th>
  </tr>
  <tr>
    <td align="center">
      <img src="docs/screenshots/overview.png" alt="Overview Tab" width="280"/>
      <br/>
      <em>CPU, RAM, Disk, Temps & Network I/O</em>
    </td>
    <td align="center">
      <img src="docs/screenshots/docker.png" alt="Docker Containers Tab" width="280"/>
      <br/>
      <em>Container state, usage & pagination</em>
    </td>
    <td align="center">
      <img src="docs/screenshots/info.png" alt="System Info Tab" width="280"/>
      <br/>
      <em>Fastfetch-style ASCII distro art & hardware specs</em>
    </td>
  </tr>
</table>

---

## 📋 Prerequisites & Beszel API Setup

This widget connects directly to [Beszel](https://github.com/henrygd/beszel), a lightweight server monitoring hub powered by an embedded PocketBase database.

Before installing the widget, ensure:
1. Your phone can reach your Beszel Hub over LAN, Wi-Fi, or VPN (e.g. Tailscale / WireGuard).
2. The Hub\'s PocketBase API allows reading system data.

### Option A: Public Read-Only Access (Easiest — Recommended for Homelabs)
Allows KWGT to read metrics without managing expiring auth tokens:
1. Open the PocketBase Admin UI in your browser by appending `/_/` to your Hub URL:
   ```text
   http://<YOUR_SERVER_IP>:8090/_/
   ```
2. In the left navigation, open **Collections**.
3. Select **`systems`** → click the **API Rules** tab (padlock icon) → leave **View Rule** and **List Rule** completely blank (empty string `""`) → click **Save changes**.
4. *(For Docker tab)* Repeat for **`container_stats`** collection → set rules to empty → Save.
5. *(For 24h Network totals)* Repeat for **`system_stats`** collection → set rules to empty → Save.

### Option B: Authenticated User (For Internet-Exposed Setups)
1. In the PocketBase Admin UI, go to **Collections** → **`users`** → create a user account.
2. Generate an auth token via curl or use the interactive setup script below.

---

## ⚡ Quick Setup Wizard (`setup.py`)

We provide an interactive Python wizard that verifies connectivity with your Beszel Hub, authenticates your account, lists your available systems, and compiles custom `.kwgt` and `.clip` files with your settings pre-filled:

```bash
python3 setup.py
```

```text
╔══════════════════════════════════════════════════════════════════╗
║                         Beszel Monitor                           ║
╚══════════════════════════════════════════════════════════════════╝

Enter Beszel Hub URL [http://127.0.0.1:8090]: http://192.168.1.100:8090
Enter username/email: user@example.com
Enter password:
✓ Authenticated successfully as user!
✓ Discovered 2 systems:
  [1] homelab (up)
  [2] storage-nas (up)
Select server to monitor by default [1]: 1

✓ Built dist/beszel_monitor.kwgt
✓ Built dist/beszel_monitor.clip
```

The script outputs ready-to-import bundles into the `dist/` directory.

---

## 📲 Importing into KWGT (Step-by-Step)

### Method 1: Clipboard Import (100% Free — No KWGT Pro Key Required!)

> [!IMPORTANT]
> **The Clipboard Trick**: KWGT does not automatically display clipboard paste options on a fresh widget. Follow this exact sequence to trigger the clipboard prompt:

1. **Copy the clip content**:
   - Open `dist/beszel_monitor.clip` (or `widget/beszel_monitor.clip`).
   - Copy the entire file content to your Android device\'s clipboard (ensuring the header `##KUSTOMCLIP##` is included).
2. **Add a blank widget**:
   - Long-press an empty area on your Android home screen → tap **Widgets**.
   - Select **KWGT Kustom Widget** and drag a **4×2** or **4×3** widget onto your screen.
3. **Open the editor**:
   - Tap the empty widget on your home screen to open the KWGT editor.
4. **Trigger the Clipboard Import**:
   - In the top right toolbar, tap the **`+` (Add)** icon.
   - Tap **Komponent**.
   - **The Trick**: Now, immediately press your phone\'s **Back button** (or perform your Android back swipe gesture) to exit the Komponent file browser.
   - Upon backing out, KWGT will detect the clipboard content and display a **"Paste Komponent from Clipboard"** prompt. Tap to paste!
5. **Save**:
   - Tap the **Floppy Disk (Save)** icon in the top right.

### Method 2: Preset Import (Requires KWGT Pro)

1. Copy `dist/beszel_monitor.kwgt` to your phone\'s `/sdcard/Kustom/widgets/` directory.
2. Place a blank KWGT widget on your home screen and tap it.
3. Switch to the **Library** tab → select **Exported** → choose **Beszel Monitor**.
4. Tap the **Floppy Disk (Save)** icon.

---

## 🔧 Essential Post-Import Setup

### 1. Activating Nerd Font Glyphs
The widget uses **JetBrainsMono Nerd Font** for clean system glyphs (CPU, Docker whale, disk, network, thermometers). On a fresh import, Android may show placeholder rectangles until the font is loaded into Kustom\'s active cache.

> [!TIP]
> **One-Touch Font Activation**:
> 1. Open the widget in KWGT and expand any text element (e.g., inside `Header` or `Overview`).
> 2. Tap on the **Font** property to open the font selector.
> 3. Select `JetBrainsMonoNerdFont.ttf` (bundled inside the preset or from your fonts directory).
> 4. Once selected in any single element, KWGT registers the font globally across all modules and icons immediately!

### 2. Enabling the Frosted-Glass (Glossy) Wallpaper Effect
To achieve authentic frosted-glass translucency that matches your launcher wallpaper:

1. Inside KWGT, navigate to the root item list and locate the **`GlossyWallpaper`** layer.
2. Select **Bitmap** and pick your current phone wallpaper from your gallery.
3. Adjust the **Position** offset (X and Y offsets) or **Scale** so that the widget\'s background aligns with your home screen wallpaper framing.
4. The translucent cards will now create a realistic glassmorphism depth effect over your background!

### 3. Adjusting Scale
Depending on your screen resolution and launcher grid (e.g. Nova, Lawnchair, OneUI):
- In the KWGT editor, select the root **Layer** tab.
- Adjust the **Scale** slider until the widget cleanly fills the container boundaries without clipping.

---

## ⚙️ Global Variables Reference

If you need to customize connections, colors, or refresh frequencies manually, go to the **Globals** tab in KWGT:

| Variable | Type | Default | Description |
|---|---|---|---|
| `bz_url` | Text | `http://192.168.1.100:8090` | Beszel Hub base URL (no trailing slash). |
| `bz_host` | Text | `homelab` | Default hostname to display on load. |
| `bz_token` | Text | *(empty)* | PocketBase JWT token (leave empty if API rules are unlocked). |
| `accent` | Color | `#cba6f7` | Catppuccin Mauve accent color for active tabs and highlights. |
| `bg` | Color | `#1e1e2e` | Catppuccin Base background color. |
| `card_bg` | Color | `#181825` | Dark surface color for metric cards. |
| `pg_size` | Number | `5` | Number of Docker containers shown per page. |
| `debug` | Number | `0` | Set to `1` to output diagnostic error traces. |

---

## 🎮 Navigation & Touch Controls

- **Tab Switching**: Tap `[ Overview ]`, `[ Docker ]`, or `[ Info ]` in the bottom bar to switch views.
- **Host Cycling**: Tap the **hostname** in the top-left header to cycle across all servers registered in your Hub.
- **Manual Refresh**: Tap the **↻** icon in the top-right header to trigger an immediate metrics update.
- **Docker Pagination**: Tap **◀ Prev** and **Next ▶** to navigate through pages of containers.
- **Status Indicator**:
  - 🟢 **Green**: Connected, telemetry fresh, server is up.
  - 🟡 **Yellow**: Stale cache (hub unreachable; showing last-known metrics).
  - 🔴 **Red**: Server down or authentication failed.

---

## 🏗️ Architecture & Privacy

```text
┌────────────────────────────────────────────────────────┐
│                  Android Device (KWGT)                 │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │                 Beszel Monitor                 │   │
│   │                                                │   │
│   │  [Overview]        [Docker]        [Fastfetch] │   │
│   └────────────────────────────────────────────────┘   │
│                           │                            │
│                  Direct HTTP(S) REST                   │
│             (Local LAN / WireGuard / Tailscale)        │
└───────────────────────────┼────────────────────────────┘
                            ▼
┌────────────────────────────────────────────────────────┐
│                   Beszel Hub Server                    │
│                                                        │
│               PocketBase REST API (:8090)              │
│       /api/collections/systems/records                 │
│       /api/collections/container_stats/records         │
│       /api/collections/system_stats/records            │
└────────────────────────────────────────────────────────┘
```

- **Zero Cloud Leakage**: No telemetry, analytics, or credentials ever leave your local network or VPN tunnel.
- **Decoupled Architecture**: Raw PocketBase JSON payloads are parsed and normalized into standard Kustom structures.
- **Graceful Degradation**: If Wi-Fi drops or the server reboots, the widget retains its previous state and updates the status indicator rather than blanking out.

---

## 🧪 Development & Testing

The repository includes a comprehensive unit test suite validating formulas, data contracts, pagination, and layout trees:

```bash
# Run test suite
python3 -m unittest discover -s scripts -p "test_*.py"

# Regenerate presets and clipboard files
python3 scripts/generate_preset.py
```

---

## 📄 License

Distributed under the **MIT License**. Distro ASCII art adapted from [Fastfetch](https://github.com/fastfetch-cli/fastfetch) under MIT.
Catppuccin color palette under MIT by [Catppuccin Org](https://github.com/catppuccin/catppuccin).
