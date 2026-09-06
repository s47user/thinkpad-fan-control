import os
import glob
import subprocess
from typing import Dict, Any, Optional

FAN_PROC_PATH = "/proc/acpi/ibm/fan"
THERMAL_PROC_PATH = "/proc/acpi/ibm/thermal"
FAN_CONTROL_PARAM = "/sys/module/thinkpad_acpi/parameters/fan_control"

VALID_LEVELS = ["auto", "0", "1", "2", "3", "4", "5", "6", "7", "disengaged", "full-speed"]

class FanController:
    """
    Hardware interface to the ThinkPad ACPI driver and thermal sensors.
    """

    def __init__(self, fan_path: str = FAN_PROC_PATH):
        self.fan_path = fan_path
        self._cached_coretemp_path: Optional[str] = None

    def is_fan_control_enabled(self) -> bool:
        """Checks if thinkpad_acpi fan_control parameter is Y."""
        if os.path.exists(FAN_CONTROL_PARAM):
            try:
                with open(FAN_CONTROL_PARAM, "r") as f:
                    return f.read().strip().upper() == "Y"
            except Exception:
                pass
        return False

    def is_writable(self) -> bool:
        """Returns True if the current process has write access to /proc/acpi/ibm/fan."""
        return os.access(self.fan_path, os.W_OK)

    def unlock_permissions(self) -> bool:
        """
        Attempts to grant write access using pkexec (Polkit graphical prompt).
        Returns True if successful.
        """
        try:
            cmd = ["pkexec", "chmod", "666", self.fan_path]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return res.returncode == 0 and self.is_writable()
        except Exception as e:
            print(f"Error requesting elevation via pkexec: {e}")
            return False

    def get_fan_status(self) -> Dict[str, Any]:
        """
        Reads and parses /proc/acpi/ibm/fan.
        """
        status_info = {
            "status": "unknown",
            "speed": 0,
            "level": "auto",
            "commands": [],
            "writable": self.is_writable(),
            "control_enabled": self.is_fan_control_enabled()
        }

        if not os.path.exists(self.fan_path):
            return status_info

        try:
            with open(self.fan_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("status:"):
                        status_info["status"] = line.split(":", 1)[1].strip()
                    elif line.startswith("speed:"):
                        try:
                            status_info["speed"] = int(line.split(":", 1)[1].strip())
                        except ValueError:
                            status_info["speed"] = 0
                    elif line.startswith("level:"):
                        status_info["level"] = line.split(":", 1)[1].strip()
                    elif line.startswith("commands:"):
                        cmd = line.split(":", 1)[1].strip()
                        status_info["commands"].append(cmd)
        except Exception as e:
            print(f"Error reading fan status: {e}")

        return status_info

    def get_cpu_temp(self) -> float:
        """
        Retrieves current CPU package temperature in Celsius.
        """
        if self._cached_coretemp_path and os.path.exists(self._cached_coretemp_path):
            try:
                with open(self._cached_coretemp_path, "r") as f:
                    val = int(f.read().strip()) / 1000.0
                    if 15.0 <= val <= 115.0:
                        return round(val, 1)
            except Exception:
                self._cached_coretemp_path = None

        for name_path in glob.glob("/sys/class/hwmon/hwmon*/name"):
            try:
                with open(name_path, "r") as f:
                    if "coretemp" in f.read().strip():
                        hwmon_dir = os.path.dirname(name_path)
                        for tfile in sorted(glob.glob(f"{hwmon_dir}/temp*_input")):
                            with open(tfile, "r") as tf:
                                val = int(tf.read().strip()) / 1000.0
                                if 15.0 <= val <= 115.0:
                                    self._cached_coretemp_path = tfile
                                    return round(val, 1)
            except Exception:
                pass

        if os.path.exists(THERMAL_PROC_PATH):
            try:
                with open(THERMAL_PROC_PATH, "r") as f:
                    content = f.read().strip()
                    parts = content.split()
                    for p in parts[1:]:
                        try:
                            temp_val = float(p)
                            if 15.0 <= temp_val <= 115.0:
                                return round(temp_val, 1)
                        except ValueError:
                            pass
            except Exception:
                pass

        for tz in glob.glob("/sys/class/thermal/thermal_zone*/temp"):
            try:
                with open(tz, "r") as f:
                    val = int(f.read().strip()) / 1000.0
                    if 15.0 <= val <= 115.0:
                        return round(val, 1)
            except Exception:
                pass

        return 45.0

    def set_level(self, level: str, allow_elevation: bool = True) -> bool:
        """
        Sets the fan level.
        Valid levels: 'auto', '0' to '7', 'disengaged', 'full-speed'
        """
        level = str(level).strip().lower()
        if level not in VALID_LEVELS:
            raise ValueError(f"Invalid level '{level}'. Must be one of: {', '.join(VALID_LEVELS)}")

        cmd_str = f"level {level}\n"

        # Direct write if permitted
        if self.is_writable():
            try:
                with open(self.fan_path, "w") as f:
                    f.write(cmd_str)
                    f.flush()
                return True
            except Exception as e:
                print(f"Error direct-writing to {self.fan_path}: {e}")

        if not allow_elevation:
            return False

        # Fallback to pkexec
        try:
            res = subprocess.run(
                ["pkexec", "sh", "-c", f"echo 'level {level}' > {self.fan_path}"],
                capture_output=True, text=True, timeout=10
            )
            return res.returncode == 0
        except Exception as e:
            print(f"Elevation command failed: {e}")
            return False

    def set_watchdog(self, timeout_sec: int = 10) -> bool:
        """
        Sets the kernel ACPI watchdog timer (0 to 120 seconds).
        """
        if not self.is_writable():
            return False

        timeout_sec = max(0, min(120, int(timeout_sec)))
        cmd_str = f"watchdog {timeout_sec}\n"

        try:
            with open(self.fan_path, "w") as f:
                f.write(cmd_str)
                f.flush()
            return True
        except Exception:
            return False

    def get_power_state(self) -> Dict[str, Any]:
        """
        Detects AC adapter connection and battery status.
        """
        ac_online = False
        for ac in glob.glob("/sys/class/power_supply/AC*/online") + glob.glob("/sys/class/power_supply/ADP*/online"):
            try:
                with open(ac, "r") as f:
                    if f.read().strip() == "1":
                        ac_online = True
                        break
            except Exception:
                pass

        bat_pct = 0
        bat_status = "Unknown"
        bat_present = False
        for b in glob.glob("/sys/class/power_supply/BAT*"):
            try:
                cap_f = os.path.join(b, "capacity")
                stat_f = os.path.join(b, "status")
                if os.path.exists(cap_f):
                    with open(cap_f, "r") as f:
                        bat_pct = int(f.read().strip())
                    bat_present = True
                if os.path.exists(stat_f):
                    with open(stat_f, "r") as f:
                        bat_status = f.read().strip()
                break
            except Exception:
                pass

        return {
            "ac_online": ac_online,
            "battery_present": bat_present,
            "battery_percent": bat_pct,
            "battery_status": bat_status
        }

    def get_all_sensors(self) -> Dict[str, Any]:
        """
        Comprehensive discovery of thermal sensors:
        - CPU Package and individual Core temperatures
        - ThinkPad EC thermal zones
        - NVMe SSD temperature
        - Wi-Fi adapter temperature
        """
        sensors: Dict[str, Any] = {
            "cpu_package": self.get_cpu_temp(),
            "cpu_cores": [],
            "thinkpad_zones": [],
            "nvme": [],
            "wifi": None
        }

        for h in sorted(glob.glob("/sys/class/hwmon/hwmon*")):
            name_file = os.path.join(h, "name")
            if not os.path.exists(name_file):
                continue
            try:
                with open(name_file, "r") as f:
                    name = f.read().strip()
            except Exception:
                continue

            if name == "coretemp":
                for t in sorted(glob.glob(f"{h}/temp*_input")):
                    try:
                        with open(t, "r") as f:
                            val = round(int(f.read().strip()) / 1000.0, 1)
                        label_f = t.replace("_input", "_label")
                        lbl = "Core"
                        if os.path.exists(label_f):
                            with open(label_f, "r") as lf:
                                lbl = lf.read().strip()
                        if "Package" in lbl:
                            sensors["cpu_package"] = val
                        else:
                            sensors["cpu_cores"].append({"label": lbl, "temp": val})
                    except Exception:
                        pass

            elif name == "thinkpad":
                for t in sorted(glob.glob(f"{h}/temp*_input")):
                    try:
                        with open(t, "r") as f:
                            val = round(int(f.read().strip()) / 1000.0, 1)
                        if val <= 0 or val > 120:
                            continue
                        label_f = t.replace("_input", "_label")
                        lbl = os.path.basename(t).replace("_input", "")
                        if os.path.exists(label_f):
                            with open(label_f, "r") as lf:
                                lbl = lf.read().strip()
                        sensors["thinkpad_zones"].append({"label": lbl, "temp": val})
                    except Exception:
                        pass

            elif name == "nvme":
                for t in sorted(glob.glob(f"{h}/temp*_input")):
                    try:
                        with open(t, "r") as f:
                            val = round(int(f.read().strip()) / 1000.0, 1)
                        label_f = t.replace("_input", "_label")
                        lbl = "SSD"
                        if os.path.exists(label_f):
                            with open(label_f, "r") as lf:
                                lbl = lf.read().strip()
                        sensors["nvme"].append({"label": lbl, "temp": val})
                    except Exception:
                        pass

            elif "phy" in name:
                for t in sorted(glob.glob(f"{h}/temp*_input")):
                    try:
                        with open(t, "r") as f:
                            val = round(int(f.read().strip()) / 1000.0, 1)
                        sensors["wifi"] = val
                    except Exception:
                        pass

        return sensors

