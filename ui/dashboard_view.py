import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from typing import Callable, Optional, Dict, Any

from .circular_gauge import CircularGauge
from .adw_clamp import AdwClamp

class DashboardView(Gtk.Box):
    """
    Main Controls / Overview view for ThinkPad Fan Control.
    Matches the Modern Libadwaita layout chosen by user:
    - Cooling State hero card with CircularGauge
    - System Telemetry preference rows
    - 2x2 Preset Profiles grid
    - Automated Dust Cleaning Routine quick-action card
    - Collapsible Manual Speed Stepper
    """

    def __init__(
        self,
        on_level_selected: Callable[[str], None],
        on_open_cleaning: Optional[Callable[[], None]] = None,
        on_open_sensors: Optional[Callable[[], None]] = None
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.on_level_selected = on_level_selected
        self.on_open_cleaning = on_open_cleaning
        self.on_open_sensors = on_open_sensors
        self._updating_internally = False

        self.clamp = AdwClamp(maximum_size=560)
        self.pack_start(self.clamp, True, True, 0)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(16)
        self.content_box.set_margin_start(16)
        self.content_box.set_margin_end(16)
        self.clamp.add(self.content_box)

        self._build_ui()

    def _build_ui(self):
        # =========================================================================
        # 1. HERO COOLING STATE CARD
        # =========================================================================
        hero_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        hero_card.get_style_context().add_class("adw-card")
        self.hero_card = hero_card

        left_hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        left_hero.set_hexpand(True)

        lbl_section = Gtk.Label(label="COOLING STATE")
        lbl_section.get_style_context().add_class("adw-section-title")
        lbl_section.set_xalign(0.0)
        left_hero.pack_start(lbl_section, False, False, 0)

        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.val_mode_title = Gtk.Label(label="Balanced")
        self.val_mode_title.get_style_context().add_class("hero-mode-title")
        title_row.pack_start(self.val_mode_title, False, False, 0)

        self.badge_mode = Gtk.Label(label="Auto Mode")
        self.badge_mode.get_style_context().add_class("badge-pill-emerald")
        title_row.pack_start(self.badge_mode, False, False, 0)
        left_hero.pack_start(title_row, False, False, 2)

        self.lbl_mode_desc = Gtk.Label(label="Targeting low acoustics with dynamic 48°C zero-RPM threshold.")
        self.lbl_mode_desc.get_style_context().add_class("adw-subtitle")
        self.lbl_mode_desc.set_xalign(0.0)
        self.lbl_mode_desc.set_line_wrap(True)
        left_hero.pack_start(self.lbl_mode_desc, False, False, 0)

        hero_card.pack_start(left_hero, True, True, 0)

        # Right: Circular Gauge
        self.gauge = CircularGauge(size=84, max_rpm=5500)
        hero_card.pack_end(self.gauge, False, False, 0)

        self.content_box.pack_start(hero_card, False, False, 0)

        # =========================================================================
        # 2. SYSTEM TELEMETRY GROUP
        # =========================================================================
        telem_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        lbl_telem_header = Gtk.Label(label="SYSTEM TELEMETRY")
        lbl_telem_header.get_style_context().add_class("adw-section-title")
        lbl_telem_header.set_xalign(0.0)
        telem_box.pack_start(lbl_telem_header, False, False, 0)

        telem_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        telem_card.get_style_context().add_class("adw-card")
        telem_card.get_style_context().add_class("adw-card-flat-inner")

        # Row 1: CPU Package Temperature
        row_cpu = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_cpu.get_style_context().add_class("adw-list-row")

        icon_box_cpu = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        icon_box_cpu.get_style_context().add_class("row-icon-plate")
        icon_cpu = Gtk.Image.new_from_icon_name("utilities-system-monitor-symbolic", Gtk.IconSize.MENU)
        icon_cpu.set_pixel_size(16)
        icon_box_cpu.pack_start(icon_cpu, True, True, 0)
        row_cpu.pack_start(icon_box_cpu, False, False, 0)

        meta_cpu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        lbl_cpu_t = Gtk.Label(label="CPU Package Temperature")
        lbl_cpu_t.get_style_context().add_class("control-label")
        lbl_cpu_t.set_xalign(0.0)
        meta_cpu.pack_start(lbl_cpu_t, False, False, 0)

        lbl_cpu_s = Gtk.Label(label="Intel/AMD Coretemp thermal sensor")
        lbl_cpu_s.get_style_context().add_class("adw-subtitle")
        lbl_cpu_s.set_xalign(0.0)
        meta_cpu.pack_start(lbl_cpu_s, False, False, 0)
        row_cpu.pack_start(meta_cpu, True, True, 0)

        self.val_temp = Gtk.Label(label="54.2°C")
        self.val_temp.get_style_context().add_class("font-mono-temp")
        row_cpu.pack_end(self.val_temp, False, False, 0)
        telem_card.pack_start(row_cpu, False, False, 0)

        # Separator line
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.get_style_context().add_class("adw-row-separator")
        telem_card.pack_start(sep, False, False, 0)

        # Row 2: Power Supply Status
        row_pwr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_pwr.get_style_context().add_class("adw-list-row")

        icon_box_pwr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        icon_box_pwr.get_style_context().add_class("row-icon-plate")
        self.icon_pwr = Gtk.Image.new_from_icon_name("ac-adapter-symbolic", Gtk.IconSize.MENU)
        self.icon_pwr.set_pixel_size(16)
        icon_box_pwr.pack_start(self.icon_pwr, True, True, 0)
        row_pwr.pack_start(icon_box_pwr, False, False, 0)

        meta_pwr = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        lbl_pwr_t = Gtk.Label(label="Power Supply Status")
        lbl_pwr_t.get_style_context().add_class("control-label")
        lbl_pwr_t.set_xalign(0.0)
        meta_pwr.pack_start(lbl_pwr_t, False, False, 0)

        self.lbl_pwr_desc = Gtk.Label(label="AC connected (65W ThinkPad adapter)")
        self.lbl_pwr_desc.get_style_context().add_class("adw-subtitle")
        self.lbl_pwr_desc.set_xalign(0.0)
        meta_pwr.pack_start(self.lbl_pwr_desc, False, False, 0)
        row_pwr.pack_start(meta_pwr, True, True, 0)

        self.badge_power = Gtk.Label(label="AC Power")
        self.badge_power.get_style_context().add_class("badge-pill-blue")
        row_pwr.pack_end(self.badge_power, False, False, 0)
        telem_card.pack_start(row_pwr, False, False, 0)

        telem_box.pack_start(telem_card, False, False, 0)
        self.content_box.pack_start(telem_box, False, False, 0)

        # =========================================================================
        # 3. PRESET PROFILES GRID (2x2)
        # =========================================================================
        presets_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        lbl_prof_header = Gtk.Label(label="PRESET PROFILES")
        lbl_prof_header.get_style_context().add_class("adw-section-title")
        lbl_prof_header.set_xalign(0.0)
        presets_box.pack_start(lbl_prof_header, False, False, 0)

        grid = Gtk.Grid()
        grid.set_column_spacing(8)
        grid.set_row_spacing(8)
        grid.set_column_homogeneous(True)

        self.card_auto = self._create_profile_card("Auto (BIOS)", "Firmware controlled curve", "auto", True)
        self.card_silent = self._create_profile_card("Silent", "Level 1 (~1,900 RPM)", "1", False)
        self.card_balanced = self._create_profile_card("Balanced", "Level 4 (~3,300 RPM)", "4", False)
        self.card_turbo = self._create_profile_card("Max Turbo", "Disengaged (5,400 RPM)", "disengaged", False)

        grid.attach(self.card_auto[0], 0, 0, 1, 1)
        grid.attach(self.card_silent[0], 1, 0, 1, 1)
        grid.attach(self.card_balanced[0], 0, 1, 1, 1)
        grid.attach(self.card_turbo[0], 1, 1, 1, 1)

        presets_box.pack_start(grid, False, False, 0)
        self.content_box.pack_start(presets_box, False, False, 0)

        # =========================================================================
        # 4. AUTOMATED DUST CLEANING ACTION ROW
        # =========================================================================
        purge_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        purge_card.get_style_context().add_class("adw-card")

        icon_box_purge = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        icon_box_purge.get_style_context().add_class("row-icon-plate")
        icon_purge = Gtk.Image.new_from_icon_name("weather-windy-symbolic", Gtk.IconSize.MENU)
        icon_purge.set_pixel_size(16)
        icon_box_purge.pack_start(icon_purge, True, True, 0)
        purge_card.pack_start(icon_box_purge, False, False, 0)

        meta_purge = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        meta_purge.set_hexpand(True)
        lbl_purge_t = Gtk.Label(label="Automated Dust Cleaning Routine")
        lbl_purge_t.get_style_context().add_class("control-label")
        lbl_purge_t.set_xalign(0.0)
        meta_purge.pack_start(lbl_purge_t, False, False, 0)

        lbl_purge_s = Gtk.Label(label="4-cycle high acceleration shockwave purge")
        lbl_purge_s.get_style_context().add_class("adw-subtitle")
        lbl_purge_s.set_xalign(0.0)
        meta_purge.pack_start(lbl_purge_s, False, False, 0)
        purge_card.pack_start(meta_purge, True, True, 0)

        self.btn_quick_purge = Gtk.Button(label="Start (40s)")
        self.btn_quick_purge.get_style_context().add_class("btn-purge-outline")
        self.btn_quick_purge.connect("clicked", self._on_quick_purge_clicked)
        purge_card.pack_end(self.btn_quick_purge, False, False, 0)

        self.content_box.pack_start(purge_card, False, False, 0)

        # =========================================================================
        # 5. EXPANDABLE MANUAL SPEED STEPPER (Fine Control)
        # =========================================================================
        self.expander = Gtk.Expander(label="Manual Speed Stepper (Levels 0–7)")
        self.expander.get_style_context().add_class("adw-expander")

        stepper_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        stepper_box.set_margin_top(6)
        stepper_box.set_margin_bottom(4)

        stepper_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_s_info = Gtk.Label(label="Direct EC Register Override:")
        lbl_s_info.get_style_context().add_class("adw-subtitle")
        stepper_header.pack_start(lbl_s_info, False, False, 0)

        self.stepper_val_lbl = Gtk.Label(label="Auto (BIOS)")
        self.stepper_val_lbl.get_style_context().add_class("badge-active")
        stepper_header.pack_end(self.stepper_val_lbl, False, False, 0)
        stepper_box.pack_start(stepper_header, False, False, 0)

        self.adjustment = Gtk.Adjustment(value=-1, lower=-1, upper=8, step_increment=1, page_increment=1)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adjustment)
        self.scale.set_digits(0)
        self.scale.set_draw_value(False)
        self.scale.add_mark(-1, Gtk.PositionType.BOTTOM, "Auto")
        self.scale.add_mark(0, Gtk.PositionType.BOTTOM, "0")
        self.scale.add_mark(1, Gtk.PositionType.BOTTOM, "1")
        self.scale.add_mark(2, Gtk.PositionType.BOTTOM, "2")
        self.scale.add_mark(3, Gtk.PositionType.BOTTOM, "3")
        self.scale.add_mark(4, Gtk.PositionType.BOTTOM, "4")
        self.scale.add_mark(5, Gtk.PositionType.BOTTOM, "5")
        self.scale.add_mark(6, Gtk.PositionType.BOTTOM, "6")
        self.scale.add_mark(7, Gtk.PositionType.BOTTOM, "7")
        self.scale.add_mark(8, Gtk.PositionType.BOTTOM, "Max")
        self.scale.connect("value-changed", self._on_slider_changed)
        stepper_box.pack_start(self.scale, False, False, 2)

        self.expander.add(stepper_box)
        self.content_box.pack_start(self.expander, False, False, 0)

        # Legacy compatibility references
        self.btn_auto = self.card_auto[1]
        self.btn_silent = self.card_silent[1]
        self.btn_balanced = self.card_balanced[1]
        self.btn_turbo = self.card_turbo[1]
        self.active_preset_badge = self.badge_mode
        self.val_mode = self.val_mode_title

    def _create_profile_card(self, title: str, subtitle: str, level_val: str, is_active: bool):
        btn = Gtk.Button()
        btn.get_style_context().add_class("adw-profile-card")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        lbl_t = Gtk.Label(label=title)
        lbl_t.get_style_context().add_class("control-label")
        top_row.pack_start(lbl_t, False, False, 0)

        dot = Gtk.Image.new_from_icon_name("emblem-ok-symbolic", Gtk.IconSize.MENU)
        dot.set_pixel_size(14)
        dot.get_style_context().add_class("blue-dot")
        dot.get_style_context().add_class("profile-active-check")
        dot.set_no_show_all(True)
        dot.set_visible(is_active)
        top_row.pack_end(dot, False, False, 0)
        box.pack_start(top_row, False, False, 0)

        lbl_s = Gtk.Label(label=subtitle)
        lbl_s.get_style_context().add_class("adw-subtitle")
        lbl_s.set_xalign(0.0)
        box.pack_start(lbl_s, False, False, 0)

        btn.add(box)
        btn.connect("clicked", lambda w: self._on_profile_clicked(level_val))

        if is_active:
            btn.get_style_context().add_class("adw-profile-card-active")

        return (btn, btn, dot)

    def _on_profile_clicked(self, level_val: str):
        self._updating_internally = True
        self._highlight_preset(level_val)
        if level_val == "auto":
            self.adjustment.set_value(-1)
            self.stepper_val_lbl.set_text("Auto (BIOS)")
        elif level_val == "disengaged":
            self.adjustment.set_value(8)
            self.stepper_val_lbl.set_text("Disengaged (Turbo)")
        else:
            try:
                val = int(level_val)
                self.adjustment.set_value(val)
                self.stepper_val_lbl.set_text(f"Level {val}")
            except ValueError:
                pass
        self._updating_internally = False
        self.on_level_selected(level_val)

    def _on_slider_changed(self, scale):
        if self._updating_internally:
            return
        val = int(round(self.adjustment.get_value()))
        if val == -1:
            level_str = "auto"
            self.stepper_val_lbl.set_text("Auto (BIOS)")
        elif val == 8:
            level_str = "disengaged"
            self.stepper_val_lbl.set_text("Disengaged (Turbo)")
        else:
            level_str = str(val)
            self.stepper_val_lbl.set_text(f"Level {val}")

        self._highlight_preset(level_str)
        self.on_level_selected(level_str)

    def _highlight_preset(self, level_str: str):
        cards = [
            ("auto", self.card_auto),
            ("1", self.card_silent),
            ("4", self.card_balanced),
            ("disengaged", self.card_turbo),
            ("7", self.card_turbo)
        ]

        # Reset all cards
        for _, (btn, _, dot) in cards:
            btn.get_style_context().remove_class("adw-profile-card-active")
            dot.set_visible(False)

        # Update hero title and descriptions
        level_str = str(level_str).lower()
        if level_str == "auto":
            self.card_auto[0].get_style_context().add_class("adw-profile-card-active")
            self.card_auto[2].set_visible(True)
            self.val_mode_title.set_text("Auto (BIOS)")
            self.badge_mode.set_text("Auto Mode")
            self.lbl_mode_desc.set_text("Firmware controlled cooling curve managed directly by Lenovo EC.")
        elif level_str == "1":
            self.card_silent[0].get_style_context().add_class("adw-profile-card-active")
            self.card_silent[2].set_visible(True)
            self.val_mode_title.set_text("Silent")
            self.badge_mode.set_text("Silent Mode")
            self.lbl_mode_desc.set_text("Targeting low acoustics with dynamic 48°C zero-RPM threshold.")
        elif level_str == "4":
            self.card_balanced[0].get_style_context().add_class("adw-profile-card-active")
            self.card_balanced[2].set_visible(True)
            self.val_mode_title.set_text("Balanced")
            self.badge_mode.set_text("Active Curve")
            self.lbl_mode_desc.set_text("Optimal everyday thermal and acoustic balance for general multitasking.")
        elif level_str in ["7", "disengaged", "full-speed"]:
            self.card_turbo[0].get_style_context().add_class("adw-profile-card-active")
            self.card_turbo[2].set_visible(True)
            self.val_mode_title.set_text("Max Turbo")
            self.badge_mode.set_text("Maximum")
            self.lbl_mode_desc.set_text("Aggressive cooling priority bypassing thermal throttling limits.")

    def sync_hardware_level(self, level_str: str):
        """Synchronizes UI to reflect hardware fan level."""
        if self._updating_internally:
            return
        self._updating_internally = True
        level_str = str(level_str).lower()
        if level_str == "auto":
            self.adjustment.set_value(-1)
            self.stepper_val_lbl.set_text("Auto (BIOS)")
        elif level_str in ["disengaged", "full-speed"]:
            self.adjustment.set_value(8)
            self.stepper_val_lbl.set_text("Disengaged (Turbo)")
        else:
            try:
                val = int(level_str)
                self.adjustment.set_value(val)
                self.stepper_val_lbl.set_text(f"Level {val}")
            except ValueError:
                pass
        self._highlight_preset(level_str)
        self._updating_internally = False

    def update_telemetry(self, temp_c: Optional[float], rpm: int, level_str: str, power: Dict[str, Any], profile_str: str):
        """Called on every 1000ms sensor tick."""
        # 1. Update CPU Temperature
        if temp_c is not None:
            self.val_temp.set_text(f"{temp_c:.1f}°C")
        else:
            self.val_temp.set_text("--.-°C")

        # 2. Power State
        ac_online = power.get("ac_online", True)
        bat_pct = power.get("battery_percent")
        watts = power.get("power_now_w")

        if ac_online:
            self.icon_pwr.set_from_icon_name("ac-adapter-symbolic", Gtk.IconSize.MENU)
            w_str = f" ({int(round(watts))}W)" if watts is not None and watts > 0 else ""
            self.lbl_pwr_desc.set_text(f"AC connected (65W ThinkPad adapter){w_str}")
            self.badge_power.set_text("AC Power")
            self.badge_power.get_style_context().remove_class("badge-pill-emerald")
            self.badge_power.get_style_context().add_class("badge-pill-blue")
        else:
            self.icon_pwr.set_from_icon_name("battery-symbolic", Gtk.IconSize.MENU)
            pct_str = f"{int(bat_pct)}%" if bat_pct is not None else "BAT"
            w_str = f" -{watts:.1f}W" if watts is not None and watts > 0 else ""
            self.lbl_pwr_desc.set_text(f"Operating on battery power ({pct_str}){w_str}")
            self.badge_power.set_text(f"Battery: {pct_str}")
            self.badge_power.get_style_context().remove_class("badge-pill-blue")
            self.badge_power.get_style_context().add_class("badge-pill-emerald")

        # 3. Update Circular Gauge
        self.gauge.set_target_rpm(rpm)
        self.sync_hardware_level(level_str)

    def _on_quick_purge_clicked(self, btn: Gtk.Button):
        if self.on_open_cleaning:
            self.on_open_cleaning()
