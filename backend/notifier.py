import os
import time
import subprocess
from typing import Dict, Optional

_HAS_NOTIFY = False
try:
    import gi
    gi.require_version("Notify", "0.7")
    from gi.repository import Notify
    _HAS_NOTIFY = True
except Exception:
    _HAS_NOTIFY = False

class NotificationManager:
    """
    Manages desktop notifications with debouncing and rate limiting.
    Emits alerts for high thermal spikes, emergency fail-safe trips,
    power profile transitions, and dust purge routines.
    """

    def __init__(self, app_name: str = "ThinkPad Fan Control"):
        self.app_name = app_name
        self.is_initialized = False
        self.cooldown_sec = 60.0  # Min seconds between recurring alerts of same type
        self.last_sent_times: Dict[str, float] = {}

        # Locate app icon for notifications
        self.icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "icons", "thinkpad-fan.svg"
        )
        if not os.path.exists(self.icon_path):
            self.icon_path = "preferences-system-performance"

        if _HAS_NOTIFY:
            try:
                Notify.init(self.app_name)
                self.is_initialized = True
            except Exception as e:
                print(f"Failed to initialize libnotify: {e}")
                self.is_initialized = False

    def send(self, title: str, body: str, urgency: str = "normal", alert_type: str = "general") -> bool:
        """
        Sends a desktop notification with debouncing.
        Urgency can be 'low', 'normal', or 'critical'.
        """
        now = time.time()
        last_time = self.last_sent_times.get(alert_type, 0.0)

        # Critical alerts bypass cooldown; others respect 60s debounce
        if urgency != "critical" and (now - last_time) < self.cooldown_sec:
            return False

        self.last_sent_times[alert_type] = now

        if self.is_initialized:
            try:
                urgency_map = {
                    "low": Notify.Urgency.LOW,
                    "normal": Notify.Urgency.NORMAL,
                    "critical": Notify.Urgency.CRITICAL
                }
                notif = Notify.Notification.new(title, body, self.icon_path)
                notif.set_urgency(urgency_map.get(urgency, Notify.Urgency.NORMAL))
                notif.show()
                return True
            except Exception as e:
                print(f"libnotify error: {e}, falling back to notify-send")

        # Fallback to notify-send
        try:
            cmd = ["notify-send", "-a", self.app_name, "-u", urgency, "-i", self.icon_path, title, body]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False
