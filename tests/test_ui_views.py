import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, GLib
import unittest
from unittest.mock import MagicMock, patch

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

    def test_exit_confirmation_dialog_structure(self):
        """Verify ExitConfirmationDialog elements, buttons, and response behavior."""
        from ui.exit_dialog import ExitConfirmationDialog, RESPONSE_TRAY, RESPONSE_QUIT, RESPONSE_CANCEL
        dlg = ExitConfirmationDialog(parent_window=self.window, tray_available=True)
        self.assertTrue(dlg.btn_tray.get_sensitive())
        self.assertTrue(dlg.btn_quit.get_sensitive())
        self.assertFalse(dlg.get_remember_choice())
        dlg.chk_remember.set_active(True)
        self.assertTrue(dlg.get_remember_choice())
        dlg.destroy()

        # When tray is unavailable, minimize button is disabled
        dlg_no_tray = ExitConfirmationDialog(parent_window=self.window, tray_available=False)
        self.assertFalse(dlg_no_tray.btn_tray.get_sensitive())
        dlg_no_tray.destroy()

    def test_close_event_handling_preferences(self):
        """Verify window close event respects close_action preferences."""
        # When close_action is "tray", window hides directly
        self.window.curve_engine.close_action = "tray"
        res_tray = self.window._on_close_event(self.window, None)
        self.assertTrue(res_tray)
        self.assertFalse(self.window.is_visible())

        # When close_action is "quit", calls _on_app_quit
        self.window.curve_engine.close_action = "quit"
        with patch.object(self.window, "_on_app_quit") as mock_quit:
            res_quit = self.window._on_close_event(self.window, None)
            self.assertFalse(res_quit)
            mock_quit.assert_called_once()

        # Reset preference
        self.window._reset_exit_preference()
        self.assertEqual(self.window.curve_engine.close_action, "ask")

    def test_safety_guard_cleanup_method(self):
        """Verify safety.cleanup() alias calls restore_safe_state and stop."""
        with patch.object(self.safety, "restore_safe_state") as mock_restore, \
             patch.object(self.safety, "stop") as mock_stop:
            self.safety.cleanup()
            mock_restore.assert_called_once()
            mock_stop.assert_called_once()

    def test_auto_mode_prevents_temperature_override(self):
        """Verify setting auto deactivates curve and prevents temperature rise from overriding auto."""
        # First enable a curve
        self.window.curve_engine.set_profile("balanced")
        self.assertTrue(self.window.curve_engine.is_curve_active)

        # Now set back to auto
        self.window._on_level_command("auto")
        self.assertFalse(self.window.curve_engine.is_curve_active)
        self.assertEqual(self.window.curve_engine.active_profile, "auto")
        self.controller.set_level.assert_called_with("auto")

        # Clear mock call history
        self.controller.set_level.reset_mock()

        # Simulate temperature rise to 75°C
        self.controller.get_cpu_temp = MagicMock(return_value=75.0)
        self.controller.get_fan_status = MagicMock(return_value={"speed": 3400, "level": "auto"})

        # Sensor tick runs
        self.window._on_sensor_tick()

        # Controller set_level must NOT have been called (no curve override!)
        self.controller.set_level.assert_not_called()

    def test_manual_mode_prevents_temperature_override(self):
        """Verify setting a manual speed deactivates curve so temp rise does not override manual level."""
        self.window.curve_engine.set_profile("balanced")
        self.assertTrue(self.window.curve_engine.is_curve_active)

        # User chooses manual level 3
        self.window._on_level_command("3")
        self.assertFalse(self.window.curve_engine.is_curve_active)
        self.controller.set_level.assert_called_with("3")

        # Clear mock call history
        self.controller.set_level.reset_mock()

        # Temperature rises to 70°C
        self.controller.get_cpu_temp = MagicMock(return_value=70.0)
        self.controller.get_fan_status = MagicMock(return_value={"speed": 2900, "level": "3"})

        # Sensor tick runs
        self.window._on_sensor_tick()

        # Must not have been overridden by curve
        self.controller.set_level.assert_not_called()

    def test_custom_curve_configuration_and_presets(self):
        """Verify custom curve radio selection, customize preset, and breakpoint rows."""
        curves = self.window.curves_view

        # Switch to custom
        curves.radio_custom.set_active(True)
        self.assertEqual(self.window.curve_engine.active_profile, "custom")
        self.assertTrue(self.window.curve_engine.is_curve_active)

        # Customize preset
        curves._on_customize_preset("silent")
        self.assertEqual(self.window.curve_engine.active_profile, "custom")
        custom_points = self.window.curve_engine.profiles["custom"]
        self.assertTrue(len(custom_points) >= 3)
        self.assertEqual(custom_points[0][1], "0")  # Silent starts at level 0


if __name__ == "__main__":
    unittest.main()
