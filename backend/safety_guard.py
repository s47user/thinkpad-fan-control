import atexit
import signal
import threading
import time
from typing import Callable, Optional
from .fan_controller import FanController

CRITICAL_TEMP_CELSIUS = 85.0
EXTREME_TEMP_CELSIUS = 90.0
WATCHDOG_PING_INTERVAL_SEC = 4.0
MAX_SENSOR_READ_FAILURES = 3

class SafetyGuard:
    """
    Hardware fail-safe and watchdog manager.
    Protects CPU from thermal overheating and ensures clean exit states.
    """

    def __init__(self, controller: FanController, on_emergency_override: Optional[Callable[[float], None]] = None):
        self.controller = controller
        self.on_emergency_override = on_emergency_override
        self.watchdog_enabled = True
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._critical_limit = CRITICAL_TEMP_CELSIUS
        self._extreme_limit = EXTREME_TEMP_CELSIUS
        self._consecutive_sensor_failures = 0

        atexit.register(self.restore_safe_state)
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except Exception:
            pass

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._guard_loop, daemon=True, name="SafetyGuardThread")
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def restore_safe_state(self):
        """Ensures the hardware is returned to BIOS auto control."""
        try:
            if self.controller.is_writable():
                print("SafetyGuard: Restoring fan to BIOS 'auto' mode...")
                self.controller.set_level("auto", allow_elevation=False)
                self.controller.set_watchdog(0)
        except Exception as e:
            print(f"SafetyGuard cleanup error: {e}")

    def _handle_signal(self, signum, frame):
        self.restore_safe_state()
        exit(0)

    def _guard_loop(self):
        while self._running:
            try:
                # 1. ACPI Watchdog Ping
                if self.watchdog_enabled and self.controller.is_writable():
                    self.controller.set_watchdog(10)

                # 2. Thermal threshold & sensor sanity check
                cur_temp = self.controller.get_cpu_temp()
                if cur_temp is None:
                    self._consecutive_sensor_failures += 1
                    if self._consecutive_sensor_failures >= MAX_SENSOR_READ_FAILURES:
                        print(f"SafetyGuard WARNING: Sensor unreadable for {self._consecutive_sensor_failures} cycles. Restoring BIOS 'auto'.")
                        self.restore_safe_state()
                else:
                    self._consecutive_sensor_failures = 0
                    if cur_temp >= self._extreme_limit:
                        status = self.controller.get_fan_status()
                        cur_level = str(status.get("level", "auto")).lower()
                        if cur_level not in ["disengaged", "full-speed"]:
                            print(f"SafetyGuard ALERT: EXTREME temp {cur_temp}°C! Overriding level {cur_level} -> disengaged")
                            self.controller.set_level("disengaged", allow_elevation=True)
                            if self.on_emergency_override:
                                self.on_emergency_override(cur_temp)
                    elif cur_temp >= self._critical_limit:
                        status = self.controller.get_fan_status()
                        cur_level = str(status.get("level", "auto")).lower()
                        if cur_level in ["0", "1", "2", "3", "4", "5", "6", "auto"]:
                            print(f"SafetyGuard ALERT: Critical temp {cur_temp}°C! Overriding level {cur_level} -> level 7")
                            self.controller.set_level("7", allow_elevation=True)
                            if self.on_emergency_override:
                                self.on_emergency_override(cur_temp)
            except Exception as e:
                print(f"SafetyGuard loop exception: {e}")

            time.sleep(WATCHDOG_PING_INTERVAL_SEC)
