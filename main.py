#!/usr/bin/env python3
"""
ThinkPad Fan Control - Desktop Application
Lenovo ThinkPad L14 Gen 2 (20X2S37F00) - Ubuntu 24.04 LTS
"""

import sys
import os
import signal
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from backend import FanController, SafetyGuard
from ui.app_window import AppWindow

def main():
    # Verify hardware compatibility
    controller = FanController()
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
