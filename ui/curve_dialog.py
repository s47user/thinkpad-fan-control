import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk
from typing import Callable, Optional, List, Tuple
from backend import SmartCurveEngine
from backend.curve_engine import DEFAULT_PROFILES

CURVE_CSS = b"""
.curve-window {
    background-color: #0b0c10;
    color: #e4e4e7;
    font-family: "Ubuntu Sans", "Inter", -apple-system, sans-serif;
    border-radius: 12px;
}

.curve-card {
    background-color: #14161f;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
}

.curve-title {
    font-size: 15px;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.2px;
}

.curve-sub {
    font-size: 11px;
    color: #71717a;
}

.profile-radio {
    font-size: 12px;
    font-weight: 600;
    color: #e4e4e7;
    letter-spacing: -0.1px;
}

.breakpoint-row {
    background-color: #0c0e15;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 6px 10px;
}

.breakpoint-ceil-row {
    background-color: rgba(226, 35, 26, 0.08);
    border: 1px dashed rgba(226, 35, 26, 0.30);
    border-radius: 6px;
    padding: 6px 10px;
}

button.btn-mini {
    background-image: none;
    background-color: #1a1d29;
    color: #e4e4e7;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 5px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 600;
}

button.btn-mini:hover {
    background-image: none;
    background-color: #282d3f;
    color: #ffffff;
}

button.btn-del {
    background-image: none;
    background-color: rgba(226, 35, 26, 0.12);
    color: #fca5a5;
    border: 1px solid rgba(226, 35, 26, 0.30);
    border-radius: 5px;
    padding: 2px 7px;
    font-size: 11px;
}

button.btn-del:hover {
    background-image: none;
    background-color: rgba(226, 35, 26, 0.30);
    color: #ffffff;
}

button.btn-primary {
    background-image: none;
    background-color: #e2231a;
    color: #ffffff;
    border: 1px solid #e2231a;
    border-radius: 6px;
    font-weight: 700;
    padding: 7px 18px;
    letter-spacing: 0.2px;
}

button.btn-primary:hover {
    background-image: none;
    background-color: #f03e3e;
}
"""

FAN_LEVEL_OPTIONS = [
    ("0", "0 (Off / 0 RPM)"),
    ("1", "Level 1 (~1900 RPM)"),
    ("2", "Level 2 (~2400 RPM)"),
    ("3", "Level 3 (~2900 RPM)"),
    ("4", "Level 4 (~3300 RPM)"),
    ("5", "Level 5 (~3800 RPM)"),
    ("6", "Level 6 (~4200 RPM)"),
    ("7", "Level 7 (~4500 RPM)"),
    ("disengaged", "Disengaged (Turbo / 5200+ RPM)")
]

class CurveConfigDialog(Gtk.Dialog):
    """
    Dialog for configuring thermal curves, anti-hunting hysteresis,
    custom breakpoint tables, and automatic AC/battery profile switching.
    """

    def __init__(self, parent_window: Gtk.Window, curve_engine: SmartCurveEngine, on_apply: Optional[Callable[[], None]] = None):
        super().__init__(title="Smart Thermal Curve & Profiles", transient_for=parent_window, modal=True, destroy_with_parent=True)
        self.curve_engine = curve_engine
        self.on_apply = on_apply

        self.set_default_size(500, 640)
        self.set_resizable(True)
        self.get_style_context().add_class("curve-window")

        # Load custom curve points
        raw_custom = self.curve_engine.profiles.get("custom", DEFAULT_PROFILES["custom"])
        self.custom_points: List[Tuple[float, str]] = [
            (float(t), str(l)) for t, l in raw_custom if t < 900.0
        ]
        if not self.custom_points:
            self.custom_points = [(45.0, "1"), (55.0, "3"), (68.0, "5"), (80.0, "7")]
        self.row_widgets = []

        self._apply_css()
        self._build_ui()

    def _apply_css(self):
        screen = Gdk.Screen.get_default()
        if screen:
            provider = Gtk.CssProvider()
            provider.load_from_data(CURVE_CSS)
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _build_ui(self):
        content_area = self.get_content_area()
        content_area.set_spacing(10)

        # Scrolled container for entire dialog body
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_propagate_natural_height(True)
        content_area.pack_start(scrolled, True, True, 0)

        main_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_vbox.set_margin_top(16)
        main_vbox.set_margin_bottom(12)
        main_vbox.set_margin_left(20)
        main_vbox.set_margin_right(20)
        scrolled.add(main_vbox)

        # Header
        title = Gtk.Label(label="Smart Thermal Curves & Automation")
        title.get_style_context().add_class("curve-title")
        main_vbox.pack_start(title, False, False, 0)

        sub = Gtk.Label(label="Select an automated thermal response curve with anti-hunting hysteresis.")
        sub.get_style_context().add_class("curve-sub")
        main_vbox.pack_start(sub, False, False, 0)

        # 1. Profile selection card
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

        main_vbox.pack_start(card_profile, False, False, 0)

        # 2. Custom Curve Breakpoint Editor Card (Interactive Table)
        self.card_custom = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.card_custom.get_style_context().add_class("curve-card")

        custom_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl_c = Gtk.Label(label="CUSTOM THERMAL BREAKPOINTS")
        lbl_c.get_style_context().add_class("curve-sub")
        custom_header.pack_start(lbl_c, False, False, 0)

        btn_reset = Gtk.Button(label="Reset Defaults")
        btn_reset.get_style_context().add_class("btn-mini")
        btn_reset.connect("clicked", self._on_reset_defaults)
        custom_header.pack_end(btn_reset, False, False, 0)

        btn_add = Gtk.Button(label="+ Add Step")
        btn_add.get_style_context().add_class("btn-mini")
        btn_add.connect("clicked", self._on_add_step)
        custom_header.pack_end(btn_add, False, False, 0)

        self.card_custom.pack_start(custom_header, False, False, 0)

        # Breakpoint rows container
        self.rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.card_custom.pack_start(self.rows_box, False, False, 0)

        # Rebuild table rows
        self._rebuild_breakpoint_rows()

        main_vbox.pack_start(self.card_custom, False, False, 0)

        # Connect radio change to show/hide custom editor
        self.radio_custom.connect("toggled", self._on_custom_radio_toggled)
        self.card_custom.set_visible(self.radio_custom.get_active())

        # 3. Automation settings card (Hysteresis & Battery sync)
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

        main_vbox.pack_start(card_settings, False, False, 0)

        # Pinned Bottom Action Buttons (Outside scrollable area)
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_margin_left(20)
        btn_box.set_margin_right(20)
        btn_box.set_margin_top(6)
        btn_box.set_margin_bottom(16)
        content_area.pack_end(btn_box, False, False, 0)

        btn_save = Gtk.Button(label="Apply & Save Profile")
        btn_save.get_style_context().add_class("btn-primary")
        btn_save.connect("clicked", self._on_save_clicked)
        btn_box.pack_start(btn_save, True, True, 0)

        btn_cancel = Gtk.Button(label="Cancel")
        btn_cancel.connect("clicked", lambda b: self.destroy())
        btn_box.pack_end(btn_cancel, False, False, 0)

        self.show_all()
        # Ensure custom card matches initial radio state
        self.card_custom.set_visible(self.radio_custom.get_active())

    def _on_custom_radio_toggled(self, radio):
        self.card_custom.set_visible(radio.get_active())

    def _rebuild_breakpoint_rows(self):
        # Clear existing children
        for child in self.rows_box.get_children():
            self.rows_box.remove(child)
        self.row_widgets = []

        num_points = len(self.custom_points)
        for idx, (temp_val, level_val) in enumerate(self.custom_points):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.get_style_context().add_class("breakpoint-row")

            lbl_below = Gtk.Label(label="Below")
            lbl_below.get_style_context().add_class("curve-sub")
            row.pack_start(lbl_below, False, False, 0)

            spin = Gtk.SpinButton.new_with_range(30.0, 95.0, 1.0)
            spin.set_digits(0)
            spin.set_value(temp_val)
            row.pack_start(spin, False, False, 0)

            lbl_arrow = Gtk.Label(label="°C  →  Fan:")
            lbl_arrow.get_style_context().add_class("curve-sub")
            row.pack_start(lbl_arrow, False, False, 0)

            combo = Gtk.ComboBoxText()
            for opt_id, opt_label in FAN_LEVEL_OPTIONS:
                combo.append(opt_id, opt_label)
            combo.set_active_id(level_val if level_val in [o[0] for o in FAN_LEVEL_OPTIONS] else "1")
            row.pack_start(combo, True, True, 0)

            btn_del = Gtk.Button()
            del_img = Gtk.Image.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
            del_img.set_pixel_size(12)
            btn_del.set_image(del_img)
            btn_del.set_tooltip_text("Delete threshold")
            btn_del.get_style_context().add_class("btn-del")
            btn_del.set_sensitive(num_points > 2)
            btn_del.connect("clicked", self._make_delete_handler(idx))
            row.pack_end(btn_del, False, False, 0)

            self.rows_box.pack_start(row, False, False, 0)
            self.row_widgets.append((spin, combo))

        # Always append the fail-safe ceiling info row
        ceil_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ceil_row.get_style_context().add_class("breakpoint-ceil-row")
        lbl_ceil = Gtk.Label(label="Above highest threshold  →  Disengaged / Full-Speed (Fail-Safe Ceiling)")
        lbl_ceil.get_style_context().add_class("curve-sub")
        ceil_row.pack_start(lbl_ceil, False, False, 0)
        self.rows_box.pack_start(ceil_row, False, False, 0)

        self.rows_box.show_all()

    def _sync_custom_points_from_ui(self):
        new_points = []
        for spin, combo in self.row_widgets:
            t = float(spin.get_value())
            lvl = combo.get_active_id() or "1"
            new_points.append((t, lvl))
        self.custom_points = sorted(new_points, key=lambda x: x[0])

    def _make_delete_handler(self, index: int):
        def _handler(btn):
            self._sync_custom_points_from_ui()
            if len(self.custom_points) > 2 and 0 <= index < len(self.custom_points):
                self.custom_points.pop(index)
                self._rebuild_breakpoint_rows()
        return _handler

    def _on_add_step(self, btn):
        self._sync_custom_points_from_ui()
        highest = max([t for t, _ in self.custom_points], default=75.0)
        new_temp = min(90.0, highest + 6.0)
        self.custom_points.append((new_temp, "7"))
        self.custom_points = sorted(self.custom_points, key=lambda x: x[0])
        self._rebuild_breakpoint_rows()

    def _on_reset_defaults(self, btn):
        self.custom_points = [(45.0, "1"), (55.0, "3"), (68.0, "5"), (80.0, "7")]
        self._rebuild_breakpoint_rows()

    def _on_save_clicked(self, btn):
        # 1. Update Profile Selection
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

        # 2. Save Custom Breakpoints
        self._sync_custom_points_from_ui()
        final_custom = list(self.custom_points)
        final_custom.append((999.0, "disengaged"))
        self.curve_engine.set_custom_curve(final_custom)

        # 3. Save Hysteresis and Battery Policy
        self.curve_engine.hysteresis_c = self.scale_h.get_value()
        self.curve_engine.auto_power_switching = self.chk_battery.get_active()
        self.curve_engine.save_config()

        if self.on_apply:
            self.on_apply()

        self.destroy()
