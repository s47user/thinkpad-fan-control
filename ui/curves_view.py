import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from typing import Callable, Optional, Dict, Any, List
from backend import SmartCurveEngine
from backend.curve_engine import DEFAULT_PROFILES
from .adw_clamp import AdwClamp

FAN_LEVEL_OPTIONS = [
    ("0", "Level 0 (Off / 0 RPM)"),
    ("1", "Level 1 (~1,900 RPM)"),
    ("2", "Level 2 (~2,400 RPM)"),
    ("3", "Level 3 (~2,900 RPM)"),
    ("4", "Level 4 (~3,300 RPM)"),
    ("5", "Level 5 (~3,700 RPM)"),
    ("6", "Level 6 (~4,100 RPM)"),
    ("7", "Level 7 (~4,500 RPM)"),
    ("disengaged", "Disengaged (Turbo / 5,400+ RPM)")
]

class CurvesView(Gtk.Box):
    """
    Modern Libadwaita Curves configuration view.
    Provides live hysteresis adjustments, profile management, and AC/Battery auto-switching.
    """

    def __init__(self, curve_engine: SmartCurveEngine, on_profile_applied: Optional[Callable[[str], None]] = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.curve_engine = curve_engine
        self.on_profile_applied = on_profile_applied
        self._updating = False
        self._custom_row_widgets = []

        self.clamp = AdwClamp(maximum_size=560)
        self.pack_start(self.clamp, True, True, 0)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(16)
        self.content_box.set_margin_start(16)
        self.content_box.set_margin_end(16)
        self.clamp.add(self.content_box)

        self._build_ui()
        self._load_from_engine()

    def _build_ui(self):
        # 1. PROFILE SELECTOR CARD
        prof_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        prof_card.get_style_context().add_class("adw-card")

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_title = Gtk.Label(label="SMART THERMAL CURVE PROFILES")
        lbl_title.get_style_context().add_class("adw-section-title")
        header.pack_start(lbl_title, False, False, 0)

        self.lbl_active_status = Gtk.Label(label="ACTIVE")
        self.lbl_active_status.get_style_context().add_class("badge-cool")
        header.pack_end(self.lbl_active_status, False, False, 0)
        prof_card.pack_start(header, False, False, 0)

        # Profile selection radios
        grid = Gtk.Grid()
        grid.set_column_spacing(8)
        grid.set_row_spacing(8)
        grid.set_column_homogeneous(True)

        self.radio_balanced = Gtk.RadioButton.new_with_label(None, "Balanced (Default)")
        self.radio_balanced.get_style_context().add_class("adw-radio-btn")
        self.radio_balanced.connect("toggled", lambda b: self._on_radio_toggled("balanced", b))

        self.radio_silent = Gtk.RadioButton.new_with_label_from_widget(self.radio_balanced, "Silent (0 RPM < 48°C)")
        self.radio_silent.get_style_context().add_class("adw-radio-btn")
        self.radio_silent.connect("toggled", lambda b: self._on_radio_toggled("silent", b))

        self.radio_turbo = Gtk.RadioButton.new_with_label_from_widget(self.radio_balanced, "Turbo (Maximum Cooling)")
        self.radio_turbo.get_style_context().add_class("adw-radio-btn")
        self.radio_turbo.connect("toggled", lambda b: self._on_radio_toggled("turbo", b))

        self.radio_custom = Gtk.RadioButton.new_with_label_from_widget(self.radio_balanced, "Custom (User Breakpoints)")
        self.radio_custom.get_style_context().add_class("adw-radio-btn")
        self.radio_custom.connect("toggled", lambda b: self._on_radio_toggled("custom", b))

        self.radio_auto = Gtk.RadioButton.new_with_label_from_widget(self.radio_balanced, "Auto (Disable Curve / BIOS)")
        self.radio_auto.get_style_context().add_class("adw-radio-btn")
        self.radio_auto.connect("toggled", lambda b: self._on_radio_toggled("auto", b))

        grid.attach(self.radio_balanced, 0, 0, 1, 1)
        grid.attach(self.radio_silent, 1, 0, 1, 1)
        grid.attach(self.radio_turbo, 0, 1, 1, 1)
        grid.attach(self.radio_custom, 1, 1, 1, 1)
        grid.attach(self.radio_auto, 0, 2, 2, 1)

        prof_card.pack_start(grid, False, False, 0)

        self.lbl_prof_desc = Gtk.Label()
        self.lbl_prof_desc.get_style_context().add_class("chip-title")
        self.lbl_prof_desc.set_xalign(0.0)
        self.lbl_prof_desc.set_line_wrap(True)
        prof_card.pack_start(self.lbl_prof_desc, False, False, 0)

        self.content_box.pack_start(prof_card, False, False, 0)

        # 2. HYSTERESIS & ANTI-HUNTING TUNING CARD
        hys_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        hys_card.get_style_context().add_class("adw-card")

        hys_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_h_title = Gtk.Label(label="ANTI-HUNTING HYSTERESIS CONFIGURATION")
        lbl_h_title.get_style_context().add_class("adw-section-title")
        hys_header.pack_start(lbl_h_title, False, False, 0)
        hys_card.pack_start(hys_header, False, False, 0)

        # Deadband Slider Row
        row_deadband = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_deadband.get_style_context().add_class("adw-row")
        
        db_meta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_db_name = Gtk.Label(label="Temperature Deadband Window")
        lbl_db_name.get_style_context().add_class("control-label")
        lbl_db_name.set_xalign(0.0)
        db_meta.pack_start(lbl_db_name, False, False, 0)

        lbl_db_sub = Gtk.Label(label="Required drop below step threshold to trigger step-down.")
        lbl_db_sub.get_style_context().add_class("chip-title")
        lbl_db_sub.set_xalign(0.0)
        lbl_db_sub.set_line_wrap(True)
        db_meta.pack_start(lbl_db_sub, False, False, 0)
        row_deadband.pack_start(db_meta, True, True, 0)

        self.val_deadband = Gtk.Label(label="3.0°C")
        self.val_deadband.get_style_context().add_class("badge-active")
        row_deadband.pack_end(self.val_deadband, False, False, 0)

        self.scale_deadband = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 1.0, 8.0, 0.5)
        self.scale_deadband.set_value(3.0)
        self.scale_deadband.set_size_request(130, -1)
        self.scale_deadband.set_draw_value(False)
        self.scale_deadband.connect("value-changed", self._on_deadband_changed)
        row_deadband.pack_end(self.scale_deadband, False, False, 0)
        hys_card.pack_start(row_deadband, False, False, 0)

        # Dwell Filter Row
        row_dwell = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_dwell.get_style_context().add_class("adw-row")

        dw_meta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_dw_name = Gtk.Label(label="Step-Down Dwell Timer Filter")
        lbl_dw_name.get_style_context().add_class("control-label")
        lbl_dw_name.set_xalign(0.0)
        dw_meta.pack_start(lbl_dw_name, False, False, 0)

        lbl_dw_sub = Gtk.Label(label="Minimum hold duration before fan speed can decelerate.")
        lbl_dw_sub.get_style_context().add_class("chip-title")
        lbl_dw_sub.set_xalign(0.0)
        lbl_dw_sub.set_line_wrap(True)
        dw_meta.pack_start(lbl_dw_sub, False, False, 0)
        row_dwell.pack_start(dw_meta, True, True, 0)

        self.val_dwell = Gtk.Label(label="5.0s")
        self.val_dwell.get_style_context().add_class("badge-active")
        row_dwell.pack_end(self.val_dwell, False, False, 0)

        self.scale_dwell = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 2.0, 15.0, 1.0)
        self.scale_dwell.set_value(5.0)
        self.scale_dwell.set_size_request(130, -1)
        self.scale_dwell.set_draw_value(False)
        self.scale_dwell.connect("value-changed", self._on_dwell_changed)
        row_dwell.pack_end(self.scale_dwell, False, False, 0)
        hys_card.pack_start(row_dwell, False, False, 0)

        self.content_box.pack_start(hys_card, False, False, 0)

        # 3. POWER AUTO-SWITCHING CARD
        pwr_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        pwr_card.get_style_context().add_class("adw-card")

        pwr_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_pw_title = Gtk.Label(label="HARDWARE POWER AUTO-SWITCHING")
        lbl_pw_title.get_style_context().add_class("adw-section-title")
        pwr_header.pack_start(lbl_pw_title, False, False, 0)

        self.switch_power = Gtk.Switch()
        self.switch_power.set_active(self.curve_engine.auto_power_switching)
        self.switch_power.connect("notify::active", self._on_power_switch_toggled)
        pwr_header.pack_end(self.switch_power, False, False, 0)
        pwr_card.pack_start(pwr_header, False, False, 0)

        row_pwr_profiles = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row_pwr_profiles.get_style_context().add_class("adw-row")

        box_ac = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon_ac = Gtk.Image.new_from_icon_name("ac-adapter-symbolic", Gtk.IconSize.MENU)
        icon_ac.set_pixel_size(14)
        lbl_ac_desc = Gtk.Label(label="On AC Power: Balanced")
        lbl_ac_desc.get_style_context().add_class("chip-title")
        box_ac.pack_start(icon_ac, False, False, 0)
        box_ac.pack_start(lbl_ac_desc, False, False, 0)
        row_pwr_profiles.pack_start(box_ac, True, True, 0)

        box_bat = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon_bat = Gtk.Image.new_from_icon_name("battery-symbolic", Gtk.IconSize.MENU)
        icon_bat.set_pixel_size(14)
        lbl_bat_desc = Gtk.Label(label="On Battery: Silent")
        lbl_bat_desc.get_style_context().add_class("chip-title")
        box_bat.pack_start(icon_bat, False, False, 0)
        box_bat.pack_start(lbl_bat_desc, False, False, 0)
        row_pwr_profiles.pack_start(box_bat, True, True, 0)
        pwr_card.pack_start(row_pwr_profiles, False, False, 0)

        self.content_box.pack_start(pwr_card, False, False, 0)

        # 4. ACTIVE PROFILE THRESHOLDS TABLE CARD
        thresh_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        thresh_card.get_style_context().add_class("adw-card")

        th_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_th_title = Gtk.Label(label="ACTIVE TEMPERATURE BREAKPOINTS")
        lbl_th_title.get_style_context().add_class("adw-section-title")
        th_header.pack_start(lbl_th_title, False, False, 0)
        thresh_card.pack_start(th_header, False, False, 0)

        self.table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        thresh_card.pack_start(self.table_box, False, False, 0)

        # Apply Button
        btn_apply = Gtk.Button(label="Apply Curve Profile to EC Engine")
        btn_apply.get_style_context().add_class("adw-btn-primary")
        btn_apply.connect("clicked", self._on_apply_clicked)
        thresh_card.pack_start(btn_apply, False, False, 0)

        self.content_box.pack_start(thresh_card, False, False, 0)

    def _load_from_engine(self):
        self._updating = True
        active = self.curve_engine.active_profile
        if not self.curve_engine.is_curve_active or active == "auto":
            self.radio_auto.set_active(True)
        elif active == "silent":
            self.radio_silent.set_active(True)
        elif active == "turbo":
            self.radio_turbo.set_active(True)
        elif active == "custom":
            self.radio_custom.set_active(True)
        else:
            self.radio_balanced.set_active(True)

        self.scale_deadband.set_value(self.curve_engine.hysteresis_c)
        self.val_deadband.set_text(f"{self.curve_engine.hysteresis_c:.1f}°C")

        self.scale_dwell.set_value(self.curve_engine.min_dwell_seconds)
        self.val_dwell.set_text(f"{self.curve_engine.min_dwell_seconds:.0f}s")

        self._refresh_thresholds(active)
        self._updating = False

    def sync_active_profile(self, profile_name: str):
        """Synchronizes the radio buttons when profile is changed elsewhere."""
        self._updating = True
        if profile_name == "silent":
            self.radio_silent.set_active(True)
        elif profile_name == "turbo":
            self.radio_turbo.set_active(True)
        elif profile_name == "custom":
            self.radio_custom.set_active(True)
        elif profile_name == "auto":
            self.radio_auto.set_active(True)
        else:
            self.radio_balanced.set_active(True)
        self._refresh_thresholds(profile_name)
        self._updating = False

    def _on_radio_toggled(self, profile_name: str, btn: Gtk.RadioButton):
        if not btn.get_active() or self._updating:
            return
        self.curve_engine.set_profile(profile_name)
        self._refresh_thresholds(profile_name)
        if self.on_profile_applied:
            self.on_profile_applied(profile_name)

    def _on_deadband_changed(self, scale: Gtk.Scale):
        val = scale.get_value()
        self.val_deadband.set_text(f"{val:.1f}°C")
        self.curve_engine.hysteresis_c = val

    def _on_dwell_changed(self, scale: Gtk.Scale):
        val = scale.get_value()
        self.val_dwell.set_text(f"{val:.0f}s")
        self.curve_engine.min_dwell_seconds = val

    def _on_power_switch_toggled(self, switch: Gtk.Switch, gparam):
        self.curve_engine.auto_power_switching = switch.get_active()

    def _refresh_thresholds(self, profile_name: str):
        # Clear existing rows
        for child in self.table_box.get_children():
            self.table_box.remove(child)

        descs = {
            "balanced": "Optimal daily balance between acoustics and thermals. Ideal for general engineering & web tasks.",
            "silent": "Passive cooling priority. Keeps fan at 0 RPM below 48°C for silent library/office work.",
            "turbo": "Aggressive cooling bias. Steps up fan speeds early to minimize thermal throttling under load.",
            "custom": "Fully user-configurable temperature breakpoints and fan levels with automatic step-up and hysteresis.",
            "auto": "Bypasses smart curves. Hardware fan speed is managed solely by Lenovo BIOS EC firmware."
        }
        self.lbl_prof_desc.set_text(descs.get(profile_name, ""))

        if profile_name == "auto":
            row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            row.get_style_context().add_class("adw-row")
            lbl_title = Gtk.Label(label="Hardware BIOS EC Curve Active")
            lbl_title.get_style_context().add_class("control-label")
            lbl_title.set_xalign(0.0)
            row.pack_start(lbl_title, False, False, 0)

            lbl_sub = Gtk.Label(label="Software curve automation is disengaged. Lenovo BIOS EC firmware has complete hardware control. The software will not override fan speeds as temperatures rise.")
            lbl_sub.get_style_context().add_class("chip-title")
            lbl_sub.set_xalign(0.0)
            lbl_sub.set_line_wrap(True)
            row.pack_start(lbl_sub, False, False, 0)
            self.table_box.pack_start(row, False, False, 0)
            self.table_box.show_all()
            return

        if profile_name == "custom":
            raw_custom = self.curve_engine.profiles.get("custom", DEFAULT_PROFILES["custom"])
            custom_points = [(float(t), str(l)) for t, l in raw_custom if t < 900.0]
            if not custom_points:
                custom_points = [(45.0, "1"), (55.0, "3"), (68.0, "5"), (80.0, "7")]

            # Action bar: Add step and Reset
            action_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            action_bar.set_margin_bottom(4)
            lbl_hint = Gtk.Label(label="Configure temperature thresholds and speeds:")
            lbl_hint.get_style_context().add_class("chip-title")
            action_bar.pack_start(lbl_hint, False, False, 0)

            btn_reset = Gtk.Button(label="Reset Defaults")
            btn_reset.get_style_context().add_class("btn-mini")
            btn_reset.connect("clicked", self._on_reset_custom_defaults)
            action_bar.pack_end(btn_reset, False, False, 0)

            btn_add = Gtk.Button(label="+ Add Step")
            btn_add.get_style_context().add_class("btn-mini")
            btn_add.connect("clicked", self._on_add_custom_step)
            action_bar.pack_end(btn_add, False, False, 0)
            self.table_box.pack_start(action_bar, False, False, 0)

            self._custom_row_widgets = []
            num_points = len(custom_points)
            for idx, (temp_val, level_val) in enumerate(custom_points):
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                row.get_style_context().add_class("adw-row")

                lbl_below = Gtk.Label(label="Below")
                lbl_below.get_style_context().add_class("chip-title")
                row.pack_start(lbl_below, False, False, 0)

                spin = Gtk.SpinButton.new_with_range(30.0, 95.0, 1.0)
                spin.set_digits(0)
                spin.set_value(temp_val)
                row.pack_start(spin, False, False, 0)

                lbl_arrow = Gtk.Label(label="°C  →  Fan:")
                lbl_arrow.get_style_context().add_class("chip-title")
                row.pack_start(lbl_arrow, False, False, 0)

                combo = Gtk.ComboBoxText()
                for opt_id, opt_label in FAN_LEVEL_OPTIONS:
                    combo.append(opt_id, opt_label)
                valid_ids = [o[0] for o in FAN_LEVEL_OPTIONS]
                combo.set_active_id(level_val if level_val in valid_ids else "1")
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

                self.table_box.pack_start(row, False, False, 0)
                self._custom_row_widgets.append((spin, combo))

            # Ceil row
            ceil_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            ceil_row.get_style_context().add_class("adw-row")
            lbl_ceil = Gtk.Label(label="Above highest threshold  →  Disengaged (Full-Speed / 5,400+ RPM Fail-Safe)")
            lbl_ceil.get_style_context().add_class("chip-title")
            ceil_row.pack_start(lbl_ceil, False, False, 0)
            self.table_box.pack_start(ceil_row, False, False, 0)

            self.table_box.show_all()
            return

        curve_data = self.curve_engine.profiles.get(profile_name, DEFAULT_PROFILES.get("balanced", []))
        rpm_estimates = {
            "0": "0 RPM (Silent)", "1": "~1,900 RPM", "2": "~2,400 RPM", "3": "~2,900 RPM",
            "4": "~3,300 RPM", "5": "~3,700 RPM", "6": "~4,100 RPM", "7": "~4,500 RPM",
            "disengaged": "~5,400+ RPM (Max)"
        }

        prev_temp = 0.0
        for i, (temp_thresh, level) in enumerate(curve_data):
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.get_style_context().add_class("adw-row")

            range_str = f"{prev_temp:.0f}°C – {temp_thresh:.0f}°C"
            lbl_r = Gtk.Label(label=range_str)
            lbl_r.get_style_context().add_class("font-mono-num")
            lbl_r.set_size_request(100, -1)
            lbl_r.set_xalign(0.0)
            row.pack_start(lbl_r, False, False, 0)

            lbl_lvl = Gtk.Label(label=f"Level {level.upper()}")
            lbl_lvl.get_style_context().add_class("badge-active")
            row.pack_start(lbl_lvl, False, False, 0)

            rpm_str = rpm_estimates.get(str(level).lower(), "Active")
            lbl_rpm = Gtk.Label(label=rpm_str)
            lbl_rpm.get_style_context().add_class("chip-title")
            row.pack_end(lbl_rpm, False, False, 0)

            self.table_box.pack_start(row, False, False, 0)
            prev_temp = temp_thresh

        # Ceil row
        ceil_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ceil_row.get_style_context().add_class("adw-row")
        lbl_cr = Gtk.Label(label=f"≥ {prev_temp:.0f}°C")
        lbl_cr.get_style_context().add_class("font-mono-num")
        lbl_cr.set_size_request(100, -1)
        lbl_cr.set_xalign(0.0)
        ceil_row.pack_start(lbl_cr, False, False, 0)

        lbl_clvl = Gtk.Label(label="DISENGAGED")
        lbl_clvl.get_style_context().add_class("badge-hot")
        ceil_row.pack_start(lbl_clvl, False, False, 0)

        lbl_crpm = Gtk.Label(label="~5,400+ RPM (Full Blast)")
        lbl_crpm.get_style_context().add_class("chip-title")
        ceil_row.pack_end(lbl_crpm, False, False, 0)
        self.table_box.pack_start(ceil_row, False, False, 0)

        # Action button to copy into custom
        act_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        act_row.set_margin_top(4)
        btn_cust = Gtk.Button(label=f"Customize {profile_name.capitalize()} Breakpoints as Custom Curve")
        btn_cust.get_style_context().add_class("btn-mini")
        btn_cust.connect("clicked", lambda b, p=profile_name: self._on_customize_preset(p))
        act_row.pack_start(btn_cust, True, True, 0)
        self.table_box.pack_start(act_row, False, False, 0)

        self.table_box.show_all()

    def _make_delete_handler(self, index: int):
        def handler(btn):
            raw_custom = self.curve_engine.profiles.get("custom", DEFAULT_PROFILES["custom"])
            points = [(float(t), str(l)) for t, l in raw_custom if t < 900.0]
            if len(points) > 2 and index < len(points):
                points.pop(index)
                full = sorted(points, key=lambda x: x[0]) + [(999.0, "disengaged")]
                self.curve_engine.set_custom_curve(full)
                self._refresh_thresholds("custom")
        return handler

    def _on_add_custom_step(self, btn):
        raw_custom = self.curve_engine.profiles.get("custom", DEFAULT_PROFILES["custom"])
        custom_points = [(float(t), str(l)) for t, l in raw_custom if t < 900.0]
        if custom_points:
            last_t = custom_points[-1][0]
            new_t = min(last_t + 8.0, 92.0)
            custom_points.append((new_t, "7"))
        else:
            custom_points = [(45.0, "1"), (60.0, "4"), (75.0, "7")]
        full = sorted(custom_points, key=lambda x: x[0]) + [(999.0, "disengaged")]
        self.curve_engine.set_custom_curve(full)
        self._refresh_thresholds("custom")

    def _on_reset_custom_defaults(self, btn):
        self.curve_engine.profiles["custom"] = list(DEFAULT_PROFILES["custom"])
        self.curve_engine.save_config()
        self._refresh_thresholds("custom")

    def _on_customize_preset(self, base_profile: str):
        base_curve = list(self.curve_engine.profiles.get(base_profile, DEFAULT_PROFILES.get("balanced", [])))
        self.curve_engine.profiles["custom"] = list(base_curve)
        self.curve_engine.set_profile("custom")
        self.radio_custom.set_active(True)
        self._refresh_thresholds("custom")
        if self.on_profile_applied:
            self.on_profile_applied("custom")

    def _on_apply_clicked(self, btn: Gtk.Button):
        if self.curve_engine.active_profile == "custom" and hasattr(self, "_custom_row_widgets") and self._custom_row_widgets:
            new_points = []
            for spin, combo in self._custom_row_widgets:
                t = float(spin.get_value())
                lvl = combo.get_active_id() or "1"
                new_points.append((t, lvl))
            sorted_points = sorted(new_points, key=lambda x: x[0])
            full_curve = sorted_points + [(999.0, "disengaged")]
            self.curve_engine.set_custom_curve(full_curve)
        self.curve_engine.save_config()
        self.lbl_active_status.set_text("APPLIED & SAVED")
        self.lbl_active_status.get_style_context().remove_class("badge-cool")
        self.lbl_active_status.get_style_context().add_class("badge-active")
        if self.on_profile_applied:
            self.on_profile_applied(self.curve_engine.active_profile)
