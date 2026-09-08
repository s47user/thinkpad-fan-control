import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, GLib
import unittest
from unittest.mock import MagicMock

from backend import FanController, SafetyGuard
from ui.app_window import AppWindow

class TestModernLibadwaitaUI(unittest.TestCase):
    """
    Automated regression and integration tests for the Option 2 Libadwaita UI revamp.
    """

    def setUp(self):
        self.controller = FanController()
        # Mock low-level hardware file writes and status so tests run cleanly in user-space
        self.current_level = "auto"
        def mock_set_level(level, *args, **kwargs):
            self.current_level = str(level)
            return True

        self.controller.is_writable = MagicMock(return_value=True)
        self.controller.set_level = MagicMock(side_effect=mock_set_level)
        self.controller.get_cpu_temp = MagicMock(return_value=52.5)
        self.controller.get_fan_status = MagicMock(side_effect=lambda: {
            "status": "enabled", "speed": 2850, "level": self.current_level
        })
        self.controller.get_power_state = MagicMock(return_value={
            "ac_online": True, "battery_percent": 90.0, "power_now_w": 22.0, "battery_status": "Charging"
        })
        self.controller.get_all_sensors = MagicMock(return_value={
            "cpu_package": 52.5,
            "cpu_cores": [{"label": "Core 0", "temp": 50.0}, {"label": "Core 1", "temp": 51.5}],
            "nvme": [{"label": "Composite", "temp": 44.0}],
            "wifi": 38.0,
            "thinkpad_zones": [{"label": "Motherboard", "temp": 41.0}]
        })

        self.safety = SafetyGuard(self.controller)
        self.window = AppWindow(self.controller, self.safety)
        self.window.show_all()

    def tearDown(self):
        try:
            self.safety.cleanup()
        except Exception:
            pass
        if hasattr(self, "window") and self.window:
            self.window.destroy()

    def test_window_and_stack_initialization(self):
        """Verify window created with 4 stack pages and proper titles."""
        self.assertTrue(self.window.get_resizable())
        self.assertEqual(self.window.get_title(), "ThinkPad Fan Control")

        stack = self.window.stack
        children = stack.get_children()
        self.assertEqual(len(children), 4)

        page_names = ["controls", "curves", "cleaning", "sensors"]
        for name in page_names:
            child = stack.get_child_by_name(name)
            self.assertIsNotNone(child, f"Stack child '{name}' should exist")

    def test_tab_switching(self):
        """Verify switching between stack pages without errors."""
        for name in ["curves", "cleaning", "sensors", "controls"]:
            self.window.stack.set_visible_child_name(name)
            self.assertEqual(self.window.stack.get_visible_child_name(), name)

    def test_bottom_navigation_bar(self):
        """Verify Libadwaita bottom navigation bar switches pages and updates button styles."""
        self.assertIsNotNone(self.window.bottom_bar)
        self.assertEqual(len(self.window.nav_buttons), 4)

        for page_name in ["curves", "cleaning", "sensors", "controls"]:
            btn, _, lbl = self.window.nav_buttons[page_name]
            btn.clicked()
            self.assertEqual(self.window.stack.get_visible_child_name(), page_name)
            self.assertTrue(btn.get_style_context().has_class("bottom-tab-btn-active"))
            self.assertTrue(lbl.get_style_context().has_class("bottom-tab-label-active"))

            # Other buttons should not be active
            for other_name, (o_btn, _, o_lbl) in self.window.nav_buttons.items():
                if other_name != page_name:
                    self.assertFalse(o_btn.get_style_context().has_class("bottom-tab-btn-active"))
                    self.assertFalse(o_lbl.get_style_context().has_class("bottom-tab-label-active"))

    def test_header_menu_button(self):
        """Verify clean HeaderBar with hamburger menu and popover."""
        self.assertIsNotNone(self.window.header_menu_btn)
        popover = self.window.header_menu_btn.get_popover()
        self.assertIsNotNone(popover)
        self.assertEqual(self.window.get_title(), "ThinkPad Fan Control")

    def test_sensor_tick_updates_dashboard(self):
        """Verify sensor tick propagates values into dashboard view."""
        self.window._on_sensor_tick()

        # Check CPU Temp label
        self.assertEqual(self.window.dashboard_view.val_temp.get_text(), "52.5°C")

        # Check temperature updates
        self.controller.get_cpu_temp = MagicMock(return_value=68.0)
        self.window._on_sensor_tick()
        self.assertEqual(self.window.dashboard_view.val_temp.get_text(), "68.0°C")

        self.controller.get_cpu_temp = MagicMock(return_value=82.0)
        self.window._on_sensor_tick()
        self.assertEqual(self.window.dashboard_view.val_temp.get_text(), "82.0°C")

    def test_preset_profile_selection(self):
        """Verify preset buttons trigger fan level commands and update UI states."""
        # Deactivate curve auto-evaluation during manual preset testing
        self.window.curve_engine.set_profile("auto")

        # Silent (Level 1)
        self.window.dashboard_view.btn_silent.clicked()
        self.controller.set_level.assert_called_with("1")
        self.assertEqual(self.window.dashboard_view.val_mode_title.get_text(), "Silent")
        self.assertEqual(self.window.dashboard_view.badge_mode.get_text(), "Silent Mode")

        # Balanced (Level 4)
        self.window.dashboard_view.btn_balanced.clicked()
        self.controller.set_level.assert_called_with("4")
        self.assertEqual(self.window.dashboard_view.val_mode_title.get_text(), "Balanced")

        # Turbo (Disengaged)
        self.window.dashboard_view.btn_turbo.clicked()
        self.controller.set_level.assert_called_with("disengaged")
        self.assertEqual(self.window.dashboard_view.val_mode_title.get_text(), "Max Turbo")

        # Auto (BIOS)
        self.window.dashboard_view.btn_auto.clicked()
        self.controller.set_level.assert_called_with("auto")
        self.assertEqual(self.window.dashboard_view.val_mode_title.get_text(), "Auto (BIOS)")

    def test_manual_slider_sync(self):
        """Verify manual slider interaction."""
        self.window.curve_engine.set_profile("auto")

        self.window.dashboard_view.adjustment.set_value(5)
        self.assertEqual(self.window.dashboard_view.stepper_val_lbl.get_text(), "Level 5")
        self.controller.set_level.assert_called_with("5")

        self.window.dashboard_view.adjustment.set_value(8)
        self.assertEqual(self.window.dashboard_view.stepper_val_lbl.get_text(), "Disengaged (Turbo)")
        self.controller.set_level.assert_called_with("disengaged")

    def test_curves_view_interactions(self):
        """Verify curve profile changes and hysteresis sliders."""
        curves = self.window.curves_view

        # Switch to silent
        curves.radio_silent.set_active(True)
        self.assertEqual(self.window.curve_engine.active_profile, "silent")

        # Adjust deadband slider
        curves.scale_deadband.set_value(4.5)
        self.assertEqual(self.window.curve_engine.hysteresis_c, 4.5)
        self.assertEqual(curves.val_deadband.get_text(), "4.5°C")

        # Adjust dwell filter slider
        curves.scale_dwell.set_value(8.0)
        self.assertEqual(self.window.curve_engine.min_dwell_seconds, 8.0)
        self.assertEqual(curves.val_dwell.get_text(), "8s")

    def test_dust_purge_routine_lifecycle(self):
        """Verify dust purge start, pulse sequence, and emergency abort."""
        self.window.curve_engine.set_profile("auto")
        cleaning = self.window.cleaning_view

        # Initial state
        self.assertEqual(cleaning.status_badge.get_text(), "READY")
        self.assertFalse(cleaning._is_running)

        # Start routine
        cleaning.btn_start.clicked()
        self.assertTrue(cleaning._is_running)
        self.controller.set_level.assert_called_with("disengaged")

        # Simulate 7 seconds elapsed (enters Settle phase)
        cleaning._elapsed_sec = 7.0
        cleaning._execute_tick()
        self.assertEqual(cleaning.status_badge.get_text(), "SETTLING (0 RPM)")
        self.controller.set_level.assert_called_with("0")

        # Emergency Abort
        cleaning.btn_abort.clicked()
        self.assertFalse(cleaning._is_running)
        self.assertEqual(cleaning.status_badge.get_text(), "ABORTED")
        self.controller.set_level.assert_any_call("auto")

    def test_dust_purge_thermal_auto_abort(self):
        """Verify 80.0°C thermal safety trigger aborts dust purge."""
        self.window.curve_engine.set_profile("auto")
        cleaning = self.window.cleaning_view
        cleaning.btn_start.clicked()
        self.assertTrue(cleaning._is_running)

        # Simulate CPU temperature spike to 80.5°C
        cleaning.update_cpu_temp(80.5)
        self.assertFalse(cleaning._is_running)
        self.assertEqual(cleaning.status_badge.get_text(), "THERMAL TRIP")
        self.controller.set_level.assert_any_call("auto")

    def test_sensors_view_updates(self):
        """Verify multi-sensor telemetry rows."""
        sensors = self.window.sensors_view
        self.window._on_sensor_tick()

        self.assertEqual(sensors.val_cpu_pkg.get_text(), "52.5°C")
        self.assertIn("core_0", sensors.sensor_labels)
        self.assertEqual(sensors.sensor_labels["core_0"][0].get_text(), "50.0°C")

    def test_emergency_fail_safe_85c_trip(self):
        """Verify SafetyGuard callback switches view to dashboard and flags emergency."""
        self.window.stack.set_visible_child_name("sensors")
        self.window._on_emergency_thermal_trip(86.2)

        self.assertEqual(self.window.stack.get_visible_child_name(), "controls")
        self.assertEqual(self.window.dashboard_view.val_mode.get_text(), "EMERGENCY")
        self.assertEqual(self.window.dashboard_view.active_preset_badge.get_text(), "TRIP 85°C")

    def test_adw_clamp_resizing(self):
        """Verify AdwClamp restricts content width to 560px and centers on wide screens."""
        self.window.resize(900, 600)
        while Gtk.events_pending():
            Gtk.main_iteration()

        # Check clamp allocation on dashboard view
        clamp = self.window.dashboard_view.clamp
        content = self.window.dashboard_view.content_box
        content_alloc = content.get_allocation()
        self.assertLessEqual(content_alloc.width, 560)
        self.assertGreater(content_alloc.x, 0)  # Must be centered horizontally

    def test_zero_emojis_in_ui_elements(self):
        """Verify zero emoji characters used as icons in UI labels and controls."""
        import re
        emoji_pattern = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27bf]')

        # Check popover labels
        popover = self.window.header_menu_btn.get_popover()
        def check_widget_labels(widget):
            if isinstance(widget, Gtk.Label):
                text = widget.get_text() or ""
                self.assertFalse(emoji_pattern.search(text), f"Found emoji in label: {text}")
            elif isinstance(widget, Gtk.Container):
                for child in widget.get_children():
                    check_widget_labels(child)

        check_widget_labels(popover)
        check_widget_labels(self.window.dashboard_view)
        check_widget_labels(self.window.curves_view)
        check_widget_labels(self.window.cleaning_view)
        check_widget_labels(self.window.sensors_view)

if __name__ == "__main__":
    unittest.main()
