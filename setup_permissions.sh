#!/usr/bin/env bash
# ThinkPad Fan Control - One-Time Setup Script
# Configures kernel module options, tray packages, and direct permissions.

set -e

echo "=== ThinkPad Fan Control Setup ==="

# 1. Ensure kernel module parameter fan_control=1
echo "[1/3] Checking thinkpad_acpi fan_control configuration..."
if [ ! -f /etc/modprobe.d/thinkpad_fan.conf ]; then
    echo "Creating /etc/modprobe.d/thinkpad_fan.conf..."
    echo "options thinkpad_acpi fan_control=1" | sudo tee /etc/modprobe.d/thinkpad_fan.conf
else
    echo "  -> /etc/modprobe.d/thinkpad_fan.conf already exists."
fi

# 2. Install Ayatana AppIndicator for Top Panel System Tray support
echo "[2/3] Installing Ayatana AppIndicator libraries for Ubuntu GNOME top-bar tray..."
sudo apt update && sudo apt install -y gir1.2-ayatanaappindicator3-0.1 || true

# 3. Grant direct write permissions and configure persistent boot access
echo "[3/4] Setting write permissions on /proc/acpi/ibm/fan..."
sudo chmod 666 /proc/acpi/ibm/fan

# 4. Install systemd tmpfiles & polkit rules for permanent persistent access across reboots
echo "[4/4] Installing systemd tmpfiles rule and Polkit policy for persistent access..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/setup/thinkpad-fan.tmpfiles.conf" ]; then
    echo "  -> Installing /etc/tmpfiles.d/thinkpad-fan.conf..."
    sudo cp "$SCRIPT_DIR/setup/thinkpad-fan.tmpfiles.conf" /etc/tmpfiles.d/thinkpad-fan.conf
    sudo systemd-tmpfiles --create /etc/tmpfiles.d/thinkpad-fan.conf 2>/dev/null || true
fi

if [ -f "$SCRIPT_DIR/setup/org.thinkpad.fancontrol.policy" ]; then
    echo "  -> Installing /usr/share/polkit-1/actions/org.thinkpad.fancontrol.policy..."
    sudo cp "$SCRIPT_DIR/setup/org.thinkpad.fancontrol.policy" /usr/share/polkit-1/actions/
fi

echo ""
echo "Setup complete! Persistent permissions configured across reboots."
echo "Launch ThinkPad Fan Control from your application menu or run:"
echo "python3 $SCRIPT_DIR/main.py"
