"""
ThinkPad Fan Control - Backend Package
Interfaces with thinkpad_acpi driver, hwmon sensors, and hardware safety mechanisms.
"""

from .fan_controller import FanController
from .safety_guard import SafetyGuard
from .curve_engine import SmartCurveEngine
from .notifier import NotificationManager

__version__ = "1.1.5"
__all__ = ["FanController", "SafetyGuard", "SmartCurveEngine", "NotificationManager", "__version__"]
