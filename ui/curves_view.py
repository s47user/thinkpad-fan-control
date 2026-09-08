import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from typing import Callable, Optional, Dict, Any, List
from backend import SmartCurveEngine
from backend.curve_engine import DEFAULT_PROFILES
from .adw_clamp import AdwClamp

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

        self.radio_auto = Gtk.RadioButton.new_with_label_from_widget(self.radio_balanced, "Auto (Disable Curve / BIOS)")
        self.radio_auto.get_style_context().add_class("adw-radio-btn")
        self.radio_auto.connect("toggled", lambda b: self._on_radio_toggled("auto", b))

        grid.attach(self.radio_balanced, 0, 0, 1, 1)
        grid.attach(self.radio_silent, 1, 0, 1, 1)
        grid.attach(self.radio_turbo, 0, 1, 1, 1)
        grid.attach(self.radio_auto, 1, 1, 1, 1)

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
        if active == "silent":
            self.radio_silent.set_active(True)
        elif active == "turbo":
            self.radio_turbo.set_active(True)
        elif active == "auto":
            self.radio_auto.set_active(True)
        else:
            self.radio_balanced.set_active(True)

        self.scale_deadband.set_value(self.curve_engine.hysteresis_c)
        self.val_deadband.set_text(f"{self.curve_engine.hysteresis_c:.1f}°C")

        self.scale_dwell.set_value(self.curve_engine.min_dwell_seconds)
        self.val_dwell.set_text(f"{self.curve_engine.min_dwell_seconds:.0f}s")

        self._refresh_thresholds(active)
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
            "auto": "Bypasses smart curves. Hardware fan speed is managed solely by Lenovo BIOS EC firmware."
        }
        self.lbl_prof_desc.set_text(descs.get(profile_name, ""))

        if profile_name == "auto":
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            row.get_style_context().add_class("adw-row")
            lbl = Gtk.Label(label="Hardware BIOS Curve Active — No manual software curve applied.")
            lbl.get_style_context().add_class("chip-title")
            row.pack_start(lbl, False, False, 0)
            self.table_box.pack_start(row, False, False, 0)
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

        self.table_box.show_all()

    def _on_apply_clicked(self, btn: Gtk.Button):
        self.curve_engine.save_config()
        self.lbl_active_status.set_text("APPLIED & SAVED")
        self.lbl_active_status.get_style_context().remove_class("badge-cool")
        self.lbl_active_status.get_style_context().add_class("badge-active")
