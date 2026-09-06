#!/usr/bin/env python3
"""
ThinkPad Fan Control - Desktop Application
Lenovo ThinkPad L14 Gen 2 (20X2S37F00) - Ubuntu 24.04 LTS
"""

import sys
import os
import signal
import argparse
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from backend import FanController, SafetyGuard, __version__
from ui.app_window import AppWindow

def handle_cli_args(controller: FanController) -> bool:
    """Handles command line arguments. Returns True if GUI should start, False if CLI exited."""
    parser = argparse.ArgumentParser(
        prog="thinkpad-fan-control",
        description="Hardware fan control, live RPM gauges, and thermal monitoring for ThinkPad"
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-s", "--status", action="store_true", help="Print current hardware thermal telemetry and fan status")
    parser.add_argument(
        "--set-level",
        dest="level",
        choices=["auto", "0", "1", "2", "3", "4", "5", "6", "7", "disengaged", "full-speed"],
        help="Set fan speed level directly from terminal"
    )

    args = parser.parse_args()

    if args.status:
        fan = controller.get_fan_status()
        temp = controller.get_cpu_temp()
        pwr = controller.get_power_state()
        ac_str = "AC Online" if pwr.get("ac_online", True) else "Battery Power"
        bat_pct = pwr.get("battery_percent", 0)

        print(f"ThinkPad Fan Control v{__version__}")
        print("=" * 42)
        print(f"  CPU Package Temp : {temp:.1f}°C" if temp is not None else "  CPU Package Temp : N/A")
        print(f"  Tachometer Speed : {fan['speed']:,} RPM")
        print(f"  Active Fan Level : {fan['level']}")
        print(f"  Power Source     : {ac_str} ({bat_pct}%)")
        print(f"  Writable Access  : {'Granted' if fan['writable'] else 'Requires Elevation'}")
        print(f"  Driver Enabled   : {'Yes' if fan['control_enabled'] else 'No (fan_control=1 needed)'}")
        return False

    if args.level:
        if not controller.is_writable():
            print("Error: Write access to /proc/acpi/ibm/fan required. Run 'sudo ./setup_permissions.sh' or elevate.")
            sys.exit(1)
        ok = controller.set_level(args.level)
        if ok:
            print(f"✔ Fan level set to: {args.level}")
        else:
            print(f"✘ Failed to set fan level to '{args.level}'. Check permissions.")
            sys.exit(1)
        return False

    return True

def main():
    # Verify hardware compatibility
    controller = FanController()

    # Parse CLI flags
    if not handle_cli_args(controller):
        return

    # Set application identity for desktop shell integration (Wayland / GNOME Shell)
    GLib.set_prgname("thinkpad-fan-control")
    GLib.set_application_name("ThinkPad Fan Control")

    if not os.path.exists(controller.fan_path):
        print(f"Warning: {controller.fan_path} not found. Ensure thinkpad_acpi is loaded.")

    # Initialize safety guard & watchdog
    safety = SafetyGuard(controller)
    safety.start()

    # Create & present desktop window
    app = AppWindow(controller, safety)
    app.show_all()

    # Clean exit on Ctrl+C in terminal
    def sigint_handler(sig, frame):
        print("\nCaught interrupt signal, resetting fan to auto and exiting...")
        safety.restore_safe_state()
        safety.stop()
        Gtk.main_quit()

    signal.signal(signal.SIGINT, sigint_handler)

    # Periodic GLib timeout to allow Python signals (like SIGINT) to process
    GLib.timeout_add(250, lambda: True)

    try:
        Gtk.main()
    finally:
        safety.restore_safe_state()
        safety.stop()

if __name__ == "__main__":
    main()
