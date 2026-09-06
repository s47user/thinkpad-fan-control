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


class TestNotificationManager(unittest.TestCase):
    def test_debouncing(self):
        nm = NotificationManager()
        nm.cooldown_sec = 10.0
        
        # First send of 'thermal_high' should succeed
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
