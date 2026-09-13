import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk
from typing import Dict, Any
from .sensor_matrix import SensorMatrixWidget

SENSOR_DIALOG_CSS = b"""
.sensor-dialog-window {
    background-color: #0b0c10;
    color: #e4e4e7;
    font-family: "Ubuntu Sans", "Inter", -apple-system, sans-serif;
    border-radius: 12px;
}

.sensor-dialog-title {
    font-size: 15px;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.2px;
}

.sensor-dialog-sub {
    font-size: 11px;
    color: #71717a;
}

button.btn-dialog-close {
    background-image: none;
    background-color: #1a1d29;
    color: #e4e4e7;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 6px 16px;
    font-weight: 600;
    font-size: 12px;
}

button.btn-dialog-close:hover {
    background-image: none;
    background-color: #282d3f;
    color: #ffffff;
}
"""

class SensorMatrixDialog(Gtk.Dialog):
    """
    Dedicated modal dialog displaying the Hardware Thermal Matrix
    and detailed system sensors.
    """

    def __init__(self, parent: Gtk.Window):
        super().__init__(
            title="Hardware Thermal Matrix",
            transient_for=parent,
            modal=True,
            destroy_with_parent=True
        )
        self.set_default_size(520, 360)
        self.set_position(Gtk.WindowPosition.CENTER_ON_PARENT)
        self.get_style_context().add_class("sensor-dialog-window")

        self._apply_css()
        self._build_ui()

    def _apply_css(self):
        screen = Gdk.Screen.get_default()
        if screen:
            provider = Gtk.CssProvider()
            provider.load_from_data(SENSOR_DIALOG_CSS)
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _build_ui(self):
        content_area = self.get_content_area()
        content_area.set_spacing(12)
        content_area.set_margin_top(16)
        content_area.set_margin_bottom(16)
        content_area.set_margin_left(18)
        content_area.set_margin_right(18)

        # Header Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dot = Gtk.Label(label="●")
        dot.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0.06, 0.73, 0.50, 1.0))
        title_box.pack_start(dot, False, False, 0)

        title_lbl = Gtk.Label(label="Hardware Thermal Matrix & Sensors")
        title_lbl.get_style_context().add_class("sensor-dialog-title")
        title_box.pack_start(title_lbl, False, False, 0)
        content_area.pack_start(title_box, False, False, 0)

        # Subtitle
        desc_lbl = Gtk.Label(
            label="Real-time multi-sensor telemetry across CPU Package, Cores, NVMe SSDs, "
                  "ThinkPad EC thermal zones, Wi-Fi module, and Battery subsystem."
        )
        desc_lbl.set_line_wrap(True)
        desc_lbl.get_style_context().add_class("sensor-dialog-sub")
        content_area.pack_start(desc_lbl, False, False, 0)

        # Sensor Matrix Widget
        self.sensor_matrix = SensorMatrixWidget()
        content_area.pack_start(self.sensor_matrix, True, True, 0)

        # Action Buttons Area
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_area.pack_start(btn_box, False, False, 0)

        btn_close = Gtk.Button(label="Close")
        btn_close.get_style_context().add_class("btn-dialog-close")
        btn_close.connect("clicked", lambda b: self.destroy())
        btn_box.pack_end(btn_close, False, False, 0)

        self.show_all()

    def update_telemetry(self, sensors: Dict[str, Any], power: Dict[str, Any]):
        self.sensor_matrix.update_telemetry(sensors, power)
