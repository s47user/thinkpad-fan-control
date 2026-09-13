import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
from typing import Callable, Optional
from backend import FanController
from .adw_clamp import AdwClamp

class CleaningView(Gtk.Box):
    """
    Modern Libadwaita Dust Cleaning (De-Dusting) view.
    Executes the 4-cycle aerodynamic shockwave pulse protocol (40s total).
    Includes real-time thermal watchdog protection and emergency abort.
    """

    TOTAL_DURATION_SEC = 40.0
    CYCLE_DURATION_SEC = 10.0
    PULSE_DURATION_SEC = 6.0
    SETTLE_DURATION_SEC = 4.0
    TOTAL_CYCLES = 4
    TEMP_LIMIT_C = 80.0

    def __init__(self, controller: FanController, on_purge_complete: Optional[Callable[[], None]] = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.controller = controller
        self.on_purge_complete = on_purge_complete

        self._timer_id: Optional[int] = None
        self._elapsed_sec: float = 0.0
        self._is_running: bool = False
        self._previous_level: str = "auto"

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
        # 1. HERO PURGE MONITOR CARD
        hero_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        hero_card.get_style_context().add_class("adw-card")

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_title = Gtk.Label(label="AUTOMATED FAN DUST PURGE ROUTINE")
        lbl_title.get_style_context().add_class("adw-section-title")
        header.pack_start(lbl_title, False, False, 0)

        self.status_badge = Gtk.Label(label="READY")
        self.status_badge.get_style_context().add_class("badge-cool")
        header.pack_end(self.status_badge, False, False, 0)
        hero_card.pack_start(header, False, False, 0)

        # Main Status & Countdown Row
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        status_box.get_style_context().add_class("adw-row")

        meta_left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.lbl_phase_headline = Gtk.Label(label="Ready to Purge")
        self.lbl_phase_headline.get_style_context().add_class("hero-temp-mono")
        self.lbl_phase_headline.set_xalign(0.0)
        meta_left.pack_start(self.lbl_phase_headline, False, False, 0)

        self.lbl_phase_sub = Gtk.Label(label="4-cycle alternating aerodynamic shockwave pulse protocol")
        self.lbl_phase_sub.get_style_context().add_class("chip-title")
        self.lbl_phase_sub.set_xalign(0.0)
        meta_left.pack_start(self.lbl_phase_sub, False, False, 0)
        status_box.pack_start(meta_left, True, True, 0)

        self.lbl_time_rem = Gtk.Label(label="40.0s")
        self.lbl_time_rem.get_style_context().add_class("purge-time-display")
        status_box.pack_end(self.lbl_time_rem, False, False, 0)
        hero_card.pack_start(status_box, False, False, 0)

        # Progress Bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.get_style_context().add_class("adw-purge-progress")
        hero_card.pack_start(self.progress_bar, False, False, 0)

        # Cycle Steps Indicators
        cycles_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cycles_row.set_homogeneous(True)
        self.cycle_pills = []
        for i in range(1, 5):
            pill = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            pill.get_style_context().add_class("adw-cycle-pill")
            lbl_c = Gtk.Label(label=f"CYCLE {i}")
            lbl_c.get_style_context().add_class("chip-title")
            pill.pack_start(lbl_c, False, False, 0)
            lbl_st = Gtk.Label(label="Pending")
            lbl_st.get_style_context().add_class("preset-sub")
            pill.pack_start(lbl_st, False, False, 0)
            cycles_row.pack_start(pill, True, True, 0)
            self.cycle_pills.append((pill, lbl_st))
        hero_card.pack_start(cycles_row, False, False, 0)

        # Action Buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.btn_start = Gtk.Button(label="Start 40s Dust Purge Routine")
        self.btn_start.get_style_context().add_class("adw-btn-primary")
        self.btn_start.connect("clicked", self._on_start_clicked)
        btn_box.pack_start(self.btn_start, True, True, 0)

        self.btn_abort = Gtk.Button(label="Emergency Stop / Abort")
        self.btn_abort.get_style_context().add_class("adw-btn-abort")
        self.btn_abort.set_sensitive(False)
        self.btn_abort.connect("clicked", self._on_abort_clicked)
        btn_box.pack_start(self.btn_abort, False, False, 0)

        hero_card.pack_start(btn_box, False, False, 0)
        self.content_box.pack_start(hero_card, False, False, 0)

        # 2. PRINCIPLES & THERMAL SAFETY WATCHDOG CARD
        safety_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        safety_card.get_style_context().add_class("adw-card")

        s_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_s_title = Gtk.Label(label="THERMAL SAFETY WATCHDOG & AERODYNAMICS")
        lbl_s_title.get_style_context().add_class("adw-section-title")
        s_header.pack_start(lbl_s_title, False, False, 0)
        safety_card.pack_start(s_header, False, False, 0)

        row_safety = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_safety.get_style_context().add_class("adw-row")

        icon_box_safety = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        icon_box_safety.get_style_context().add_class("row-icon-plate")
        icon_safety = Gtk.Image.new_from_icon_name("security-high-symbolic", Gtk.IconSize.MENU)
        icon_safety.set_pixel_size(16)
        icon_box_safety.pack_start(icon_safety, True, True, 0)
        row_safety.pack_start(icon_box_safety, False, False, 0)

        watch_meta = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_w_title = Gtk.Label(label="Emergency Thermal Auto-Abort Threshold: 80.0°C")
        lbl_w_title.get_style_context().add_class("control-label")
        lbl_w_title.set_xalign(0.0)
        watch_meta.pack_start(lbl_w_title, False, False, 0)

        lbl_w_sub = Gtk.Label(
            label="If CPU package exceeds 80.0°C during deceleration, the routine immediately aborts to BIOS cooling."
        )
        lbl_w_sub.get_style_context().add_class("chip-title")
        lbl_w_sub.set_xalign(0.0)
        lbl_w_sub.set_line_wrap(True)
        watch_meta.pack_start(lbl_w_sub, False, False, 0)
        row_safety.pack_start(watch_meta, True, True, 0)

        self.val_cur_temp = Gtk.Label(label="--.-°C")
        self.val_cur_temp.get_style_context().add_class("font-mono-num")
        row_safety.pack_end(self.val_cur_temp, False, False, 0)
        safety_card.pack_start(row_safety, False, False, 0)

        # Principles explanation row
        row_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        row_info.get_style_context().add_class("adw-row")
        lbl_inf_t = Gtk.Label(label="Aerodynamic Shockwave Cleaning Principle")
        lbl_inf_t.get_style_context().add_class("control-label")
        lbl_inf_t.set_xalign(0.0)
        row_info.pack_start(lbl_inf_t, False, False, 0)

        lbl_inf_b = Gtk.Label(
            label="Rapid acceleration to 5,200+ RPM bursts (6s) followed by quick deceleration to 0 RPM (4s) creates "
                  "fluid vortex pressure shocks that dislodge dry dust clinging to copper heatsink radiator fins and impeller blades."
        )
        lbl_inf_b.get_style_context().add_class("chip-title")
        lbl_inf_b.set_xalign(0.0)
        lbl_inf_b.set_line_wrap(True)
        row_info.pack_start(lbl_inf_b, False, False, 0)
        safety_card.pack_start(row_info, False, False, 0)

        self.content_box.pack_start(safety_card, False, False, 0)

    def update_cpu_temp(self, temp_c: Optional[float]):
        if temp_c is not None:
            self.val_cur_temp.set_text(f"{temp_c:.1f}°C")
            if self._is_running and temp_c >= self.TEMP_LIMIT_C:
                self._abort_due_to_temperature(temp_c)
        else:
            self.val_cur_temp.set_text("--.-°C")

    def _on_start_clicked(self, btn: Gtk.Button):
        if self._is_running:
            return
        if not self.controller.is_writable():
            self.lbl_phase_headline.set_text("Read-Only: Speed control requires elevation.")
            self.status_badge.set_text("PERM ERROR")
            self.status_badge.get_style_context().remove_class("badge-cool")
            self.status_badge.get_style_context().add_class("badge-hot")
            return

        status = self.controller.get_fan_status()
        self._previous_level = status.get("level", "auto")
        self._is_running = True
        self._elapsed_sec = 0.0

        self.btn_start.set_sensitive(False)
        self.btn_abort.set_sensitive(True)

        self._execute_tick()
        self._timer_id = GLib.timeout_add(250, self._on_tick)

    def _on_abort_clicked(self, btn: Gtk.Button):
        if not self._is_running:
            return
        self._stop_routine("ABORTED", "Purge aborted by user. Restored BIOS cooling.", is_error=True)

    def _abort_due_to_temperature(self, temp_c: float):
        self._stop_routine(
            "THERMAL TRIP",
            f"Emergency Abort: CPU reached {temp_c:.1f}°C (>={self.TEMP_LIMIT_C}°C).",
            is_error=True
        )

    def _stop_routine(self, badge_str: str, message: str, is_error: bool = False):
        self._is_running = False
        if self._timer_id:
            GLib.source_remove(self._timer_id)
            self._timer_id = None

        try:
            self.controller.set_level("auto")
        except Exception:
            pass

        self.btn_start.set_sensitive(True)
        self.btn_abort.set_sensitive(False)

        self.status_badge.set_text(badge_str)
        self.status_badge.get_style_context().remove_class("badge-cool")
        self.status_badge.get_style_context().remove_class("badge-warm")
        self.status_badge.get_style_context().remove_class("badge-hot")
        self.status_badge.get_style_context().add_class("badge-hot" if is_error else "badge-cool")

        self.lbl_phase_headline.set_text(message)
        self.progress_bar.set_fraction(0.0 if is_error else 1.0)
        self.lbl_time_rem.set_text("0.0s")

        if self.on_purge_complete:
            self.on_purge_complete()

    def _on_tick(self) -> bool:
        if not self._is_running:
            return False

        self._elapsed_sec += 0.25
        if self._elapsed_sec >= self.TOTAL_DURATION_SEC:
            self._stop_routine("COMPLETED", "Purge finished successfully! Fan restored to auto.", is_error=False)
            return False

        self._execute_tick()
        return True

    def _execute_tick(self):
        fraction = min(1.0, self._elapsed_sec / self.TOTAL_DURATION_SEC)
        self.progress_bar.set_fraction(fraction)

        rem_sec = max(0.0, self.TOTAL_DURATION_SEC - self._elapsed_sec)
        self.lbl_time_rem.set_text(f"{rem_sec:.1f}s")

        # Current cycle (0-indexed)
        cycle_idx = min(3, int(self._elapsed_sec // self.CYCLE_DURATION_SEC))
        phase_time = self._elapsed_sec % self.CYCLE_DURATION_SEC

        # Update Cycle Pills
        for i, (pill, lbl_st) in enumerate(self.cycle_pills):
            pill.get_style_context().remove_class("adw-cycle-pill-active")
            if i < cycle_idx:
                lbl_st.set_text("Done")
            elif i == cycle_idx:
                pill.get_style_context().add_class("adw-cycle-pill-active")
                lbl_st.set_text("Running...")
            else:
                lbl_st.set_text("Pending")

        # Pulse vs Settle
        if phase_time < self.PULSE_DURATION_SEC:
            # Burst pulse
            self.status_badge.set_text("BURST (FULL)")
            self.status_badge.get_style_context().remove_class("badge-cool")
            self.status_badge.get_style_context().add_class("badge-hot")

            self.lbl_phase_headline.set_text(f"Cycle {cycle_idx + 1}/4: Acceleration Burst")
            self.lbl_phase_sub.set_text("Fan set to Disengaged (~5,200+ RPM) — Shockwave air pulse active")

            try:
                self.controller.set_level("disengaged")
            except Exception:
                pass
        else:
            # Settle phase
            self.status_badge.set_text("SETTLING (0 RPM)")
            self.status_badge.get_style_context().remove_class("badge-hot")
            self.status_badge.get_style_context().add_class("badge-cool")

            self.lbl_phase_headline.set_text(f"Cycle {cycle_idx + 1}/4: Deceleration Settle")
            self.lbl_phase_sub.set_text("Fan set to 0 RPM — Allowing impeller to brake and reverse airflow vortex")

            try:
                self.controller.set_level("0")
            except Exception:
                pass
