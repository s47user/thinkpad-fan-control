import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk
from typing import Dict, Any, List

SENSOR_CSS = b"""
.sensor-matrix-card {
    background-color: #14161f;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px 16px;
}

.sensor-grid-title {
    font-size: 10px;
    font-weight: 700;
    color: #71717a;
    letter-spacing: 1.2px;
}

.sensor-item-box {
    background-color: #0c0d12;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 7px;
    padding: 7px 11px;
}

.sensor-name {
    font-size: 10px;
    font-weight: 600;
    color: #a1a1aa;
    letter-spacing: -0.1px;
}

.sensor-val {
    font-family: "Ubuntu Sans Mono", "Ubuntu Mono", "JetBrains Mono", monospace;
    font-size: 13px;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.2px;
}

.sensor-badge-cool {
    background-color: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 9px;
    font-weight: 700;
}

.sensor-badge-warm {
    background-color: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 9px;
    font-weight: 700;
}

.sensor-badge-hot {
    background-color: rgba(226, 35, 26, 0.15);
    color: #f87171;
    border: 1px solid rgba(226, 35, 26, 0.45);
    border-radius: 4px;
    padding: 1px 5px;
    font-size: 9px;
    font-weight: 700;
}
"""

class SensorMatrixWidget(Gtk.Box):
    """
    Multi-Sensor Thermal Matrix widget displaying real-time telemetry
    across CPU Cores, NVMe SSD, ThinkPad EC zones, Wi-Fi, and Battery.
    """

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.get_style_context().add_class("sensor-matrix-card")

        self._apply_css()
        self._build_ui()

    def _apply_css(self):
        screen = Gdk.Screen.get_default()
        if screen:
            provider = Gtk.CssProvider()
            provider.load_from_data(SENSOR_CSS)
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _build_ui(self):
        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        title = Gtk.Label(label="HARDWARE THERMAL MATRIX & TELEMETRY")
        title.get_style_context().add_class("sensor-grid-title")
        header.pack_start(title, False, False, 0)

        self.power_badge = Gtk.Label(label="AC POWER")
        self.power_badge.get_style_context().add_class("sensor-badge-cool")
        header.pack_end(self.power_badge, False, False, 0)
        self.pack_start(header, False, False, 0)

        # Flowbox / Grid for sensor items
        self.grid = Gtk.Grid()
        self.grid.set_column_spacing(10)
        self.grid.set_row_spacing(8)
        self.grid.set_column_homogeneous(True)
        self.pack_start(self.grid, True, True, 0)

        # Static placeholder sensor boxes
        self.sensor_widgets: Dict[str, Any] = {}

    def update_telemetry(self, sensors: Dict[str, Any], power: Dict[str, Any]):
        """Refreshes the sensor matrix with live sensor readings."""
        # Update Power Badge
        ac_online = power.get("ac_online", True)
        bat_pct = power.get("battery_percent", 0)
        bat_stat = power.get("battery_status", "Full")

        if ac_online:
            self.power_badge.set_text(f"AC ONLINE ({bat_pct}%)")
            self.power_badge.get_style_context().remove_class("sensor-badge-warm")
            self.power_badge.get_style_context().add_class("sensor-badge-cool")
        else:
            self.power_badge.set_text(f"BATTERY: {bat_pct}% [{bat_stat}]")
            self.power_badge.get_style_context().remove_class("sensor-badge-cool")
            self.power_badge.get_style_context().add_class("sensor-badge-warm")

        # Compile flat list of key sensors: (key, display_name, temp_val)
        items = []

        # CPU Package
        pkg = sensors.get("cpu_package")
        if pkg is not None:
            items.append(("cpu_pkg", "CPU Package", pkg))

        # CPU Cores
        for i, core in enumerate(sensors.get("cpu_cores", [])):
            lbl = core.get("label", f"Core {i}")
            items.append((f"core_{i}", lbl, core.get("temp", 0.0)))

        # NVMe
        for i, nv in enumerate(sensors.get("nvme", [])):
            lbl = nv.get("label", f"NVMe {i}")
            items.append((f"nvme_{i}", f"SSD: {lbl}", nv.get("temp", 0.0)))

        # ThinkPad EC thermal zones
        for i, zone in enumerate(sensors.get("thinkpad_zones", [])):
            lbl = zone.get("label", f"Zone {i}")
            if lbl.lower() != "cpu":  # Avoid duplicate CPU entry
                items.append((f"tp_{i}", f"EC: {lbl}", zone.get("temp", 0.0)))

        # Wi-Fi
        wifi = sensors.get("wifi")
        if wifi is not None:
            items.append(("wifi", "Wi-Fi Module", wifi))

        # Rebuild or update grid
        for i, (key, label_str, temp_val) in enumerate(items[:8]):  # Show up to top 8 sensors cleanly
            col = i % 4
            row = i // 4

            if key not in self.sensor_widgets:
                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                box.get_style_context().add_class("sensor-item-box")

                top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                lbl_name = Gtk.Label(label=label_str)
                lbl_name.get_style_context().add_class("sensor-name")
                top_row.pack_start(lbl_name, False, False, 0)

                badge = Gtk.Label(label="COOL")
                badge.get_style_context().add_class("sensor-badge-cool")
                top_row.pack_end(badge, False, False, 0)
                box.pack_start(top_row, False, False, 0)

                val_lbl = Gtk.Label(label=f"{temp_val:.1f}°C")
                val_lbl.get_style_context().add_class("sensor-val")
                box.pack_start(val_lbl, False, False, 0)

                self.grid.attach(box, col, row, 1, 1)
                box.show_all()
                self.sensor_widgets[key] = (val_lbl, badge)
            else:
                val_lbl, badge = self.sensor_widgets[key]
                val_lbl.set_text(f"{temp_val:.1f}°C")

                badge.get_style_context().remove_class("sensor-badge-cool")
                badge.get_style_context().remove_class("sensor-badge-warm")
                badge.get_style_context().remove_class("sensor-badge-hot")

                if temp_val < 50.0:
                    badge.get_style_context().add_class("sensor-badge-cool")
                    badge.set_text("COOL")
                elif temp_val < 70.0:
                    badge.get_style_context().add_class("sensor-badge-warm")
                    badge.set_text("WARM")
                else:
                    badge.get_style_context().add_class("sensor-badge-hot")
                    badge.set_text("HOT")
