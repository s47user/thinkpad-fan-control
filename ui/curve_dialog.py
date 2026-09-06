import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from typing import Callable, Optional
from backend import SmartCurveEngine

CURVE_CSS = b"""
.curve-window {
    background-color: #16181f;
    color: #f1f3f7;
    border-radius: 12px;
}

.curve-card {
    background-color: #1d202b;
    border: 1px solid #2d3344;
    border-radius: 10px;
    padding: 14px;
}

.curve-title {
    font-size: 15px;
    font-weight: 700;
    color: #ffffff;
}

.curve-sub {
    font-size: 11px;
    color: #9aa1b3;
}

.profile-radio {
    font-size: 12px;
    font-weight: 600;
    color: #e5e7eb;
}

.btn-primary {
    background-color: #e2231a;
    color: #ffffff;
    border-radius: 6px;
    font-weight: 700;
    padding: 6px 16px;
}

.btn-primary:hover {
    background-color: #ff3b30;
}
"""

class CurveConfigDialog(Gtk.Dialog):
    """
    Dialog for configuring thermal curves, anti-hunting hysteresis,
    and automatic AC/battery profile switching.
    """

    def __init__(self, parent_window: Gtk.Window, curve_engine: SmartCurveEngine, on_apply: Optional[Callable[[], None]] = None):
        super().__init__(title="Smart Thermal Curve & Profiles", transient_for=parent_window, modal=True, destroy_with_parent=True)
        self.curve_engine = curve_engine
        self.on_apply = on_apply

        self.set_default_size(460, 480)
        self.set_resizable(False)
        self.get_style_context().add_class("curve-window")

        self._apply_css()
        self._build_ui()

    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_data(CURVE_CSS)
        self.get_style_context().add_provider(provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def _build_ui(self):
        content_area = self.get_content_area()
        content_area.set_spacing(12)
        content_area.set_margin_top(16)
        content_area.set_margin_bottom(16)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)

        # Header
        title = Gtk.Label(label="Smart Thermal Curves & Automation")
        title.get_style_context().add_class("curve-title")
        content_area.pack_start(title, False, False, 0)

        sub = Gtk.Label(label="Select an automated thermal response curve with anti-hunting hysteresis.")
        sub.get_style_context().add_class("curve-sub")
        content_area.pack_start(sub, False, False, 0)

        # Profile selection card
        card_profile = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card_profile.get_style_context().add_class("curve-card")

        lbl_p = Gtk.Label(label="ACTIVE COOLING PROFILE")
        lbl_p.get_style_context().add_class("curve-sub")
        card_profile.pack_start(lbl_p, False, False, 0)

        self.radio_auto = Gtk.RadioButton.new_with_label(None, "BIOS Default (Hardware Auto Control)")
        self.radio_silent = Gtk.RadioButton.new_with_label_from_widget(self.radio_auto, "Silent / Whisper (Passive bias, 0 RPM < 50°C)")
        self.radio_balanced = Gtk.RadioButton.new_with_label_from_widget(self.radio_auto, "Balanced (Daily standard, steady acoustics)")
        self.radio_turbo = Gtk.RadioButton.new_with_label_from_widget(self.radio_auto, "Turbo / High Performance (Aggressive cooling)")
        self.radio_custom = Gtk.RadioButton.new_with_label_from_widget(self.radio_auto, "Custom User Curve")

        active = self.curve_engine.active_profile
        if not self.curve_engine.is_curve_active or active == "auto":
            self.radio_auto.set_active(True)
        elif active == "silent":
            self.radio_silent.set_active(True)
        elif active == "balanced":
            self.radio_balanced.set_active(True)
        elif active == "turbo":
            self.radio_turbo.set_active(True)
        elif active == "custom":
            self.radio_custom.set_active(True)

        for r in [self.radio_auto, self.radio_silent, self.radio_balanced, self.radio_turbo, self.radio_custom]:
            r.get_style_context().add_class("profile-radio")
            card_profile.pack_start(r, False, False, 0)

        content_area.pack_start(card_profile, False, False, 0)

        # Automation settings card (Hysteresis & Battery sync)
        card_settings = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card_settings.get_style_context().add_class("curve-card")

        lbl_s = Gtk.Label(label="HYSTERESIS & ANTI-HUNTING")
        lbl_s.get_style_context().add_class("curve-sub")
        card_settings.pack_start(lbl_s, False, False, 0)

        # Hysteresis deadband scale
        row_h = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl_h_name = Gtk.Label(label="Deadband Delta:")
        lbl_h_name.get_style_context().add_class("curve-sub")
        row_h.pack_start(lbl_h_name, False, False, 0)

        self.scale_h = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1.0, 6.0, 0.5)
        self.scale_h.set_value(self.curve_engine.hysteresis_c)
        self.scale_h.set_draw_value(True)
        self.scale_h.set_value_pos(Gtk.PositionType.RIGHT)
        row_h.pack_start(self.scale_h, True, True, 0)
        card_settings.pack_start(row_h, False, False, 0)

        # Auto power profile switch toggle
        self.chk_battery = Gtk.CheckButton.new_with_label("Auto-switch to Silent profile on battery power")
        self.chk_battery.set_active(self.curve_engine.auto_power_switching)
        card_settings.pack_start(self.chk_battery, False, False, 0)

        content_area.pack_start(card_settings, False, False, 0)

        # Button Box
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_area.pack_start(btn_box, False, False, 0)

        btn_save = Gtk.Button(label="Apply & Save Profile")
        btn_save.get_style_context().add_class("btn-primary")
        btn_save.connect("clicked", self._on_save_clicked)
        btn_box.pack_start(btn_save, True, True, 0)

        btn_cancel = Gtk.Button(label="Cancel")
        btn_cancel.connect("clicked", lambda b: self.destroy())
        btn_box.pack_end(btn_cancel, False, False, 0)

        self.show_all()

    def _on_save_clicked(self, btn):
        if self.radio_auto.get_active():
            self.curve_engine.set_profile("auto")
        elif self.radio_silent.get_active():
            self.curve_engine.set_profile("silent")
        elif self.radio_balanced.get_active():
            self.curve_engine.set_profile("balanced")
        elif self.radio_turbo.get_active():
            self.curve_engine.set_profile("turbo")
        elif self.radio_custom.get_active():
            self.curve_engine.set_profile("custom")

        self.curve_engine.hysteresis_c = self.scale_h.get_value()
        self.curve_engine.auto_power_switching = self.chk_battery.get_active()
        self.curve_engine.save_config()

        if self.on_apply:
            self.on_apply()

        self.destroy()
