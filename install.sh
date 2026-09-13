#!/usr/bin/env bash
# ThinkPad Fan Control - Local User Installation & Update Script
# Installs CLI binary, desktop launcher, and multi-resolution hicolor icons.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICONS_BASE="$HOME/.local/share/icons/hicolor"

echo "=== ThinkPad Fan Control - Local Installation / Update ==="
echo "Target directory: $SCRIPT_DIR"

# 1. Create directories
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICONS_BASE/scalable/apps"
mkdir -p "$ICONS_BASE/512x512/apps"
mkdir -p "$ICONS_BASE/256x256/apps"
mkdir -p "$ICONS_BASE/128x128/apps"
mkdir -p "$ICONS_BASE/64x64/apps"
mkdir -p "$ICONS_BASE/48x48/apps"

# 2. Install CLI wrapper to ~/.local/bin/thinkpad-fan-control
echo "[1/4] Installing CLI launcher to $BIN_DIR/thinkpad-fan-control..."
cat << 'EOF' > "$BIN_DIR/thinkpad-fan-control"
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec /usr/bin/python3 "PROJECT_DIR_PLACEHOLDER/main.py" "$@"
EOF
sed -i "s|PROJECT_DIR_PLACEHOLDER|$SCRIPT_DIR|g" "$BIN_DIR/thinkpad-fan-control"
chmod +x "$BIN_DIR/thinkpad-fan-control"

# 3. Install System Icons across Hicolor Theme
echo "[2/4] Installing application icons to $ICONS_BASE..."
if [ -f "$SCRIPT_DIR/assets/icons/thinkpad-fan.svg" ]; then
    cp "$SCRIPT_DIR/assets/icons/thinkpad-fan.svg" "$ICONS_BASE/scalable/apps/thinkpad-fan.svg"
fi
if [ -f "$SCRIPT_DIR/assets/icons/thinkpad-fan-512.png" ]; then
    cp "$SCRIPT_DIR/assets/icons/thinkpad-fan-512.png" "$ICONS_BASE/512x512/apps/thinkpad-fan.png"
fi
if [ -f "$SCRIPT_DIR/assets/icons/thinkpad-fan-256.png" ]; then
    cp "$SCRIPT_DIR/assets/icons/thinkpad-fan-256.png" "$ICONS_BASE/256x256/apps/thinkpad-fan.png"
fi
if [ -f "$SCRIPT_DIR/assets/icons/thinkpad-fan-128.png" ]; then
    cp "$SCRIPT_DIR/assets/icons/thinkpad-fan-128.png" "$ICONS_BASE/128x128/apps/thinkpad-fan.png"
fi
if [ -f "$SCRIPT_DIR/assets/icons/thinkpad-fan-64.png" ]; then
    cp "$SCRIPT_DIR/assets/icons/thinkpad-fan-64.png" "$ICONS_BASE/64x64/apps/thinkpad-fan.png"
fi
if [ -f "$SCRIPT_DIR/assets/icons/thinkpad-fan-48.png" ]; then
    cp "$SCRIPT_DIR/assets/icons/thinkpad-fan-48.png" "$ICONS_BASE/48x48/apps/thinkpad-fan.png"
fi

if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$ICONS_BASE" 2>/dev/null || true
fi

# 4. Install Desktop Entry
echo "[3/4] Installing desktop entry to $DESKTOP_DIR/thinkpad-fan-control.desktop..."
cat << EOF > "$DESKTOP_DIR/thinkpad-fan-control.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=ThinkPad Fan Control
GenericName=Fan Speed Controller
Comment=Hardware fan control, live RPM gauges, and thermal monitoring for ThinkPad
Exec=$BIN_DIR/thinkpad-fan-control
Icon=thinkpad-fan
Terminal=false
Categories=System;HardwareSettings;Settings;
StartupNotify=true
StartupWMClass=thinkpad-fan-control
Keywords=thinkpad;fan;thermal;cooling;speed;sensors;temperature;
EOF

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# 5. Verify Installation
echo "[4/4] Verifying installation..."
python3 -m py_compile "$SCRIPT_DIR/main.py" "$SCRIPT_DIR"/backend/*.py "$SCRIPT_DIR"/ui/*.py

echo ""
echo "=== Update Successful! ==="
echo "✔ CLI Command: $BIN_DIR/thinkpad-fan-control"
echo "✔ Desktop Shortcut: $DESKTOP_DIR/thinkpad-fan-control.desktop"
echo "✔ Icons Registered: $ICONS_BASE/scalable/apps/thinkpad-fan.svg"
echo ""
echo "You can launch the app anytime via:"
echo "  1. Desktop App Grid / GNOME Search: 'ThinkPad Fan Control'"
echo "  2. Terminal: thinkpad-fan-control"
