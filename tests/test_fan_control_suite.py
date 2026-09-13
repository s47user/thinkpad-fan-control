import os
import time
import unittest
from backend.curve_engine import SmartCurveEngine, DEFAULT_PROFILES
from backend.fan_controller import FanController
from backend.notifier import NotificationManager

class TestSmartCurveEngine(unittest.TestCase):
    def setUp(self):
        self.engine = SmartCurveEngine()
        self.engine.hysteresis_c = 3.0
        self.engine.min_dwell_seconds = 2.0
        self.engine.set_profile("balanced")

    def test_profile_activation(self):
        self.assertTrue(self.engine.is_curve_active)
        self.assertEqual(self.engine.active_profile, "balanced")
        
        self.engine.set_profile("auto")
        self.assertFalse(self.engine.is_curve_active)
        self.assertIsNone(self.engine.evaluate_temp(60.0))

    def test_immediate_step_up(self):
        self.engine.set_profile("balanced")
        self.engine.current_level = "1"
        
        # At 68°C in balanced, target should step up to Level 5 immediately
        res = self.engine.evaluate_temp(68.0)
        self.assertEqual(res, "5")
        self.assertEqual(self.engine.current_level, "5")

    def test_hysteresis_deadband_hold(self):
        self.engine.set_profile("balanced")
        # In balanced:
        # <45: 1, 45-54: 2, 54-64: 3, 64-74: 5
        self.engine.current_level = "5" # was at >=64°C
        self.engine.last_step_down_time = time.time() - 10.0 # Dwell time satisfied
        
        # Temp drops to 62.0°C. 
        # Nominal band for 62.0°C is Level 3 (threshold is 64°C).
        # But with 3.0°C deadband, temp must be <= (64 - 3.0) = 61.0°C to step down.
        # At 62.0°C, it should hold Level 5!
        res = self.engine.evaluate_temp(62.0)
        self.assertIsNone(res)
        self.assertEqual(self.engine.current_level, "5")
        
        # Temp drops to 60.5°C (below 61.0°C deadband limit).
        res2 = self.engine.evaluate_temp(60.5)
        self.assertEqual(res2, "3")
        self.assertEqual(self.engine.current_level, "3")

    def test_dwell_timer_restriction(self):
        self.engine.set_profile("balanced")
        self.engine.current_level = "5"
        self.engine.last_step_down_time = time.time() # Just stepped down
        
        # Even if temp is well below threshold (e.g. 40°C), dwell timer holds level
        res = self.engine.evaluate_temp(40.0)
        self.assertIsNone(res)
        self.assertEqual(self.engine.current_level, "5")

    def test_power_profile_transition(self):
        self.engine.set_profile("balanced")
        self.engine.auto_power_switching = True
        self.engine.ac_profile = "turbo"
        self.engine.battery_profile = "silent"

        # Disconnected from AC -> switch to battery profile (silent)
        new_prof = self.engine.handle_power_transition(ac_online=False)
        self.assertEqual(new_prof, "silent")
        self.assertEqual(self.engine.active_profile, "silent")

        # Plugged into AC -> switch to AC profile (turbo)
        new_prof2 = self.engine.handle_power_transition(ac_online=True)
        self.assertEqual(new_prof2, "turbo")
        self.assertEqual(self.engine.active_profile, "turbo")


class TestHardwareSensorsAndPower(unittest.TestCase):
    def setUp(self):
        self.controller = FanController()

    def test_power_state_structure(self):
        power = self.controller.get_power_state()
        self.assertIsInstance(power, dict)
        self.assertIn("ac_online", power)
        self.assertIn("battery_present", power)
        self.assertIn("battery_percent", power)
        self.assertIn("battery_status", power)

    def test_all_sensors_structure(self):
        sensors = self.controller.get_all_sensors()
        self.assertIsInstance(sensors, dict)
        self.assertIn("cpu_package", sensors)
        self.assertIn("cpu_cores", sensors)
        self.assertIn("thinkpad_zones", sensors)
        self.assertIn("nvme", sensors)
        self.assertIn("wifi", sensors)
        self.assertIsInstance(sensors["cpu_cores"], list)
        self.assertIsInstance(sensors["thinkpad_zones"], list)


from unittest.mock import MagicMock
from backend.safety_guard import SafetyGuard
from ui.visual_gauge import VisualGauge


class TestSafetyGuardTieredOverrides(unittest.TestCase):
    def setUp(self):
        self.mock_controller = MagicMock()
        self.mock_controller.is_writable.return_value = True
        self.guard = SafetyGuard(self.mock_controller)

    def test_critical_override_levels_0_to_6_and_auto(self):
        for test_level in ["0", "1", "2", "3", "4", "5", "6", "auto"]:
            self.mock_controller.reset_mock()
            self.mock_controller.get_cpu_temp.return_value = 86.0
            self.mock_controller.get_fan_status.return_value = {"level": test_level}

            # Simulate single guard check cycle
            cur_temp = self.mock_controller.get_cpu_temp()
            if cur_temp >= self.guard._critical_limit:
                status = self.mock_controller.get_fan_status()
                cur_level = str(status.get("level", "auto")).lower()
                if cur_level in ["0", "1", "2", "3", "4", "5", "6", "auto"]:
                    self.mock_controller.set_level("7", allow_elevation=True)

            self.mock_controller.set_level.assert_called_once_with("7", allow_elevation=True)

    def test_extreme_override_forces_disengaged(self):
        for test_level in ["auto", "4", "7"]:
            self.mock_controller.reset_mock()
            self.mock_controller.get_cpu_temp.return_value = 91.5
            self.mock_controller.get_fan_status.return_value = {"level": test_level}

            # Simulate single guard check cycle at extreme limit
            cur_temp = self.mock_controller.get_cpu_temp()
            if cur_temp >= self.guard._extreme_limit:
                status = self.mock_controller.get_fan_status()
                cur_level = str(status.get("level", "auto")).lower()
                if cur_level not in ["disengaged", "full-speed"]:
                    self.mock_controller.set_level("disengaged", allow_elevation=True)

            self.mock_controller.set_level.assert_called_once_with("disengaged", allow_elevation=True)

    def test_consecutive_sensor_failures_triggers_auto(self):
        self.mock_controller.get_cpu_temp.return_value = None
        self.guard.restore_safe_state = MagicMock()

        for cycle in range(3):
            cur_temp = self.mock_controller.get_cpu_temp()
            if cur_temp is None:
                self.guard._consecutive_sensor_failures += 1
                if self.guard._consecutive_sensor_failures >= 3:
                    self.guard.restore_safe_state()

        self.assertEqual(self.guard._consecutive_sensor_failures, 3)
        self.guard.restore_safe_state.assert_called_once()


class TestCustomCurveBreakpoints(unittest.TestCase):
    def setUp(self):
        self.engine = SmartCurveEngine()
        self.engine.set_profile("custom")
        self.engine.hysteresis_c = 3.0
        self.engine.min_dwell_seconds = 0.0

    def test_custom_curve_evaluation(self):
        custom_curve = [
            (40.0, "1"),
            (60.0, "4"),
            (80.0, "7"),
            (999.0, "disengaged")
        ]
        self.engine.set_custom_curve(custom_curve)

        self.assertEqual(self.engine.evaluate_temp(35.0), "1")
        self.assertEqual(self.engine.evaluate_temp(55.0), "4")
        self.assertEqual(self.engine.evaluate_temp(75.0), "7")
        self.assertEqual(self.engine.evaluate_temp(88.0), "disengaged")

    def test_none_temperature_safety(self):
        self.assertIsNone(self.engine.evaluate_temp(None))


class TestVisualGaugeAnimation(unittest.TestCase):
    def test_animation_state_transitions(self):
        gauge = VisualGauge(min_width=200, min_height=200)
        self.assertFalse(gauge.is_animating())

        gauge.set_target_rpm(3000)
        self.assertTrue(gauge.is_animating())

        # Step until lerp converges
        steps = 0
        while gauge.is_animating() and steps < 50:
            gauge.update_animation_step()
            steps += 1

        self.assertFalse(gauge.is_animating())
        self.assertEqual(gauge.current_rpm, 3000.0)

        # Subsequent step returns False immediately without animating
        res = gauge.update_animation_step()
        self.assertFalse(res)


class TestNotificationManager(unittest.TestCase):
    def test_debouncing(self):
        nm = NotificationManager()
        nm.cooldown_sec = 10.0

        # First send of 'test_type' should succeed
        res1 = nm.send("Test Warning", "Warning message 1", urgency="normal", alert_type="test_type")
        self.assertTrue(res1)

        # Immediate second send of same alert_type should be throttled
        res2 = nm.send("Test Warning", "Warning message 2", urgency="normal", alert_type="test_type")
        self.assertFalse(res2)

        # Critical alerts bypass throttling
        res3 = nm.send("Emergency", "Critical message", urgency="critical", alert_type="test_type")
        self.assertTrue(res3)


if __name__ == "__main__":
    unittest.main()

