import os
import json
import time
from typing import Dict, Any, List, Tuple, Optional

CONFIG_DIR = os.path.expanduser("~/.config/thinkpad-fan-control")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# Default Profiles: list of (max_temp_c, fan_level)
DEFAULT_PROFILES = {
    "silent": [
        (48.0, "0"),
        (56.0, "1"),
        (66.0, "2"),
        (76.0, "4"),
        (84.0, "7"),
        (999.0, "disengaged")
    ],
    "balanced": [
        (45.0, "1"),
        (54.0, "2"),
        (64.0, "3"),
        (74.0, "5"),
        (82.0, "7"),
        (999.0, "disengaged")
    ],
    "turbo": [
        (40.0, "2"),
        (50.0, "4"),
        (62.0, "6"),
        (74.0, "7"),
        (999.0, "disengaged")
    ],
    "custom": [
        (45.0, "1"),
        (55.0, "3"),
        (68.0, "5"),
        (80.0, "7"),
        (999.0, "disengaged")
    ]
}

class SmartCurveEngine:
    """
    Automates fan speed based on thermal curves with hysteresis anti-hunting.
    Prevents fan oscillation and synchronizes with AC/battery power states.
    """

    def __init__(self):
        self.active_profile: str = "balanced"   # 'auto', 'silent', 'balanced', 'turbo', 'custom'
        self.is_curve_active: bool = False       # True when smart curve overrides manual / BIOS
        self.hysteresis_c: float = 3.0           # 3.0°C deadband for step-down
        self.min_dwell_seconds: float = 5.0      # Minimum seconds before stepping down

        # Power profile automation
        self.auto_power_switching: bool = True
        self.ac_profile: str = "balanced"
        self.battery_profile: str = "silent"

        # Internal state tracking
        self.current_level: str = "auto"
        self.last_step_down_time: float = 0.0
        self.last_temp: float = 45.0
        self.profiles = dict(DEFAULT_PROFILES)

        self.load_config()

    def evaluate_temp(self, current_temp: Optional[float]) -> Optional[str]:
        """
        Determines the target fan level for a given temperature.
        Applies hysteresis: step-up is immediate; step-down requires temp <= (threshold - hysteresis)
        and enforces minimum dwell time.
        Returns target level string, or None if in BIOS 'auto' mode or unchanged.
        """
        if current_temp is None or not self.is_curve_active or self.active_profile == "auto":
            return None

        curve = self.profiles.get(self.active_profile, self.profiles["balanced"])
        now = time.time()

        # Find nominal target level
        nominal_level = "disengaged"
        current_threshold = 999.0
        for max_temp, lvl in curve:
            if current_temp < max_temp:
                nominal_level = lvl
                current_threshold = max_temp
                break

        # Level weight hierarchy for comparison
        def level_rank(l: str) -> int:
            ranks = {"auto": -1, "0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "disengaged": 8, "full-speed": 8}
            return ranks.get(l, 0)

        curr_rank = level_rank(self.current_level)
        nom_rank = level_rank(nominal_level)

        # 1. Immediate Step-Up on rising temperatures (Safety First)
        if nom_rank > curr_rank:
            self.current_level = nominal_level
            self.last_temp = current_temp
            self.last_step_down_time = now
            return nominal_level

        # 2. Step-Down check with Hysteresis Deadband and Dwell Timer
        elif nom_rank < curr_rank:
            # Check dwell time
            if (now - self.last_step_down_time) < self.min_dwell_seconds:
                return None  # Hold speed, haven't dwelled long enough

            # Check deadband: temperature must have cooled at least hysteresis_c below previous band
            lower_target = None
            for max_temp, lvl in curve:
                if lvl == nominal_level:
                    lower_target = max_temp
                    break

            if lower_target and current_temp <= (lower_target - self.hysteresis_c):
                self.current_level = nominal_level
                self.last_temp = current_temp
                self.last_step_down_time = now
                return nominal_level
            else:
                return None  # In deadband, maintain current speed

        return None

    def handle_power_transition(self, ac_online: bool) -> Optional[str]:
        """
        Switches profile when AC adapter is plugged or unplugged.
        Returns the newly activated profile name if changed, else None.
        """
        if not self.auto_power_switching or not self.is_curve_active:
            return None

        target = self.ac_profile if ac_online else self.battery_profile
        if target != self.active_profile:
            self.set_profile(target)
            return target
        return None

    def set_profile(self, profile_name: str):
        profile_name = profile_name.lower().strip()
        if profile_name in ["auto", "silent", "balanced", "turbo", "custom"]:
            self.active_profile = profile_name
            self.is_curve_active = (profile_name != "auto")
            self.save_config()

    def set_custom_curve(self, curve: List[Tuple[float, str]]):
        """Sets custom user breakpoints: list of (max_temp, level)."""
        sorted_curve = sorted(curve, key=lambda x: x[0])
        self.profiles["custom"] = sorted_curve
        self.save_config()

    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.active_profile = data.get("active_profile", "balanced")
                    self.is_curve_active = data.get("is_curve_active", False)
                    self.hysteresis_c = float(data.get("hysteresis_c", 3.0))
                    self.min_dwell_seconds = float(data.get("min_dwell_seconds", 5.0))
                    self.auto_power_switching = data.get("auto_power_switching", True)
                    self.ac_profile = data.get("ac_profile", "balanced")
                    self.battery_profile = data.get("battery_profile", "silent")
                    if "custom_curve" in data:
                        self.profiles["custom"] = [(float(t), str(l)) for t, l in data["custom_curve"]]
        except Exception as e:
            print(f"Note: Using default curve settings ({e})")

    def save_config(self):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            data = {
                "active_profile": self.active_profile,
                "is_curve_active": self.is_curve_active,
                "hysteresis_c": self.hysteresis_c,
                "min_dwell_seconds": self.min_dwell_seconds,
                "auto_power_switching": self.auto_power_switching,
                "ac_profile": self.ac_profile,
                "battery_profile": self.battery_profile,
                "custom_curve": self.profiles.get("custom", DEFAULT_PROFILES["custom"])
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving curve config: {e}")
