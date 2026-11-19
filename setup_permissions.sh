#!/usr/bin/env bash
# ThinkPad Fan Control - One-Time Setup Script
# Configures kernel module options, persistent permissions, and polkit policy.

set -e

SCRIPT_PATH="$(realpath "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# Elevate via pkexec if not running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Administrative privileges required. Requesting authentication via pkexec..."
    exec pkexec bash "$SCRIPT_PATH" "$@"
fi

echo "=== ThinkPad Fan Control - System Configuration ==="

# 1. Ensure kernel module parameter fan_control=1
echo "[1/4] Configuring kernel module options (/etc/modprobe.d/thinkpad_fan.conf)..."
cat << 'EOF' > /etc/modprobe.d/thinkpad_fan.conf
options thinkpad_acpi fan_control=1
EOF

# 2. Install systemd tmpfiles rule for persistent boot permissions
echo "[2/4] Configuring persistent boot permissions (/etc/tmpfiles.d/thinkpad-fan.conf)..."
if [ -f "$SCRIPT_DIR/setup/thinkpad-fan.tmpfiles.conf" ]; then
    cp "$SCRIPT_DIR/setup/thinkpad-fan.tmpfiles.conf" /etc/tmpfiles.d/thinkpad-fan.conf
else
    cat << 'EOF' > /etc/tmpfiles.d/thinkpad-fan.conf
z /proc/acpi/ibm/fan 0666 - - -
EOF
fi
systemd-tmpfiles --create /etc/tmpfiles.d/thinkpad-fan.conf 2>/dev/null || true

# 3. Install Polkit elevation policy
echo "[3/4] Installing Polkit elevation policy..."
if [ -f "$SCRIPT_DIR/setup/org.thinkpad.fancontrol.policy" ]; then
    cp "$SCRIPT_DIR/setup/org.thinkpad.fancontrol.policy" /usr/share/polkit-1/actions/
fi

# 4. Activate fan_control in kernel driver
echo "[4/4] Activating thinkpad_acpi fan_control in kernel..."
chmod 666 /proc/acpi/ibm/fan 2>/dev/null || true

if modprobe -r thinkpad_acpi 2>/dev/null && modprobe thinkpad_acpi; then
    chmod 666 /proc/acpi/ibm/fan 2>/dev/null || true
    echo "  -> thinkpad_acpi reloaded with fan_control=1 active!"
else
    echo "  -> Note: thinkpad_acpi is in use. Persistent permissions will apply on next reboot."
fi

# Optional: Install Ayatana AppIndicator for top-bar tray support
if ! dpkg -s gir1.2-ayatanaappindicator3-0.1 >/dev/null 2>&1; then
    echo "Installing optional system tray support (gir1.2-ayatanaappindicator3-0.1)..."
    DEBIAN_FRONTEND=noninteractive apt install -y -q gir1.2-ayatanaappindicator3-0.1 2>/dev/null || true
fi

echo ""
echo "=== Configuration Complete ==="
echo "Fan control is now permanently enabled with persistent write access across reboots."
