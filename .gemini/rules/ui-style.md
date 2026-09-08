# GNOME Libadwaita Design System & UI Conventions

All UI development in this repository must strictly adhere to authentic GNOME / Libadwaita Human Interface Guidelines (HIG):

## 1. Palette Tokens
* **Window Background:** `#242424` (authentic GNOME dark theme background)
* **Card Surfaces (`.adw-card`):** `#303030` with `1px solid rgba(255, 255, 255, 0.07)` border and `12px` border-radius.
* **List Rows (`.adw-row`):** `#363636` with `#3d3d3d` hover state and `8px` border-radius.
* **Accent Color:** `#3584e4` (Canonical GNOME Blue) for primary actions, active profile outlines, sliders, and active checkmarks.
* **Status Badges:** `#2ec27e` (Cool/Emerald), `#e5a50a` (Warm/Amber), `#e01b24` (Hot/Destructive Red).
* **Secondary / Dim Labels:** `#9a9996` with standard font sizing.

## 2. Zero Emojis (Native Vector Symbolic Icons Only)
* **Never use emojis as icons** in labels, headers, buttons, or indicators (e.g. do not use ⚡, 🔋, 🛡️, 📍, ✓, ●).
* Always use native GTK symbolic icons inside standard `.row-icon-plate` (or native icon widgets):
  * CPU telemetry & monitor: `utilities-system-monitor-symbolic`
  * AC adapter / charger: `ac-adapter-symbolic`
  * Battery power: `battery-symbolic`
  * Active checkmark: `emblem-ok-symbolic` (styled `#3584e4`)
  * Dust purge / airflow: `weather-windy-symbolic`
  * Safety guard / watchdog: `security-high-symbolic`
  * NVMe storage: `drive-harddisk-symbolic`
  * Wi-Fi radio: `network-wireless-symbolic`
  * Motherboard / chassis zones: `computer-symbolic`
  * Hamburger menu: `open-menu-symbolic`
  * Close / Delete: `window-close-symbolic`

## 3. Typography & Hierarchy
* **Font Stack:** `Cantarell, Inter, -apple-system, sans-serif`.
* **Monospace Metrics:** Temperatures, RPM metrics, and numerical telemetry use Cantarell / monospace for alignment.
* Standard Libadwaita sizing: Section titles (11px, bold, `#9a9996`), control titles (13px, bold, `#ffffff`), subtitles (11.5px, `#9a9996`).

## 4. Window Resizability (`AdwClamp`)
* Do not allow content cards or rows to stretch infinitely across wide displays or tiling window managers.
* Always constrain view content inside `AdwClamp(maximum_size=560)` so content remains centered horizontally with equal margins (matching GNOME Settings and Blur my Shell).

## 5. Navigation Shell
* **HeaderBar (Upper Bar):** Clean title and subtitle with hamburger menu button (`open-menu-symbolic`) and native window controls.
* **Bottom Bar (Lower Bar):** Libadwaita ViewSwitcher navigation bar with stacked symbolic icon + label and rounded `#383838` active tab pill.
