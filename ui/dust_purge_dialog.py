import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from typing import Callable, Optional
from backend import FanController

DIALOG_CSS = b"""
.purge-window {
    background-color: #0b0c10;
    color: #e4e4e7;
    font-family: "Ubuntu Sans", "Inter", -apple-system, sans-serif;
    border-radius: 12px;
}

.purge-card {
    background-color: #14161f;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
}

.purge-title {
    font-size: 15px;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.2px;
}

.purge-sub {
    font-size: 11px;
    color: #71717a;
}

.purge-badge-burst {
    background-color: rgba(226, 35, 26, 0.15);
    color: #f87171;
    border: 1px solid rgba(226, 35, 26, 0.45);
    border-radius: 5px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}

.purge-badge-settle {
    background-color: rgba(56, 189, 248, 0.12);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 5px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}

.purge-badge-ready {
    background-color: #1f222e;
    color: #d4d4d8;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 5px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}

button.purge-btn-start {
    background-image: none;
    background-color: #e2231a;
    color: #ffffff;
    border: 1px solid #e2231a;
    border-radius: 6px;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 18px;
}

button.purge-btn-start:hover {
    background-image: none;
    background-color: #f03e3e;
}

button.purge-btn-abort {
    background-image: none;
    background-color: #b91c1c;
    color: #ffffff;
    border: 1px solid #b91c1c;
    border-radius: 6px;
    font-weight: 700;
    font-size: 13px;
    padding: 8px 18px;
}

button.purge-btn-abort:hover {
    background-image: none;
    background-color: #991b1b;
}

.mono-telemetry {
    font-family: "Ubuntu Sans Mono", "Ubuntu Mono", "JetBrains Mono", monospace;
    font-size: 16px;
    font-weight: 700;
    color: #fafafa;
}
"""

class DustPurgeDialog(Gtk.Dialog):
    """
    Modal dialog executing a safe, pulsed Fan Dust Purge routine
    inspired by Lenovo's hardware Dust Removal protocol.
    """

    def __init__(self, parent_window: Gtk.Window, controller: FanController, on_finish_callback: Optional[Callable[[], None]] = None):
        super().__init__(title="ThinkPad Fan Dust Purge", transient_for=parent_window, modal=True, destroy_with_parent=True)
        self.controller = controller
        self.on_finish_callback = on_finish_callback

        self.set_default_size(440, 380)
        self.set_resizable(False)
        self.get_style_context().add_class("purge-window")

        self.total_duration_sec = 40.0
        self.elapsed_time = 0.0
        self.is_running = False
        self.timer_id: Optional[int] = None
        self.original_level = "auto"

        self._apply_css()
        self._build_ui()
        self.connect("delete-event", self._on_dialog_close)

    def _apply_css(self):
        screen = Gdk.Screen.get_default()
        if screen:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(DIALOG_CSS)
            Gtk.StyleContext.add_provider_for_screen(
                screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _build_ui(self):
        content_area = self.get_content_area()
        content_area.set_spacing(14)
        content_area.set_margin_top(16)
        content_area.set_margin_bottom(16)
        content_area.set_margin_left(20)
        content_area.set_margin_right(20)

        # Header Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dot = Gtk.Label(label="●")
        dot.override_color(Gtk.StateFlags.NORMAL, gi.repository.Gdk.RGBA(0.89, 0.14, 0.1, 1.0))
        title_box.pack_start(dot, False, False, 0)

        title_lbl = Gtk.Label(label="Fan Dust Purge Routine")
        title_lbl.get_style_context().add_class("purge-title")
        title_box.pack_start(title_lbl, False, False, 0)
        content_area.pack_start(title_box, False, False, 0)

        # Explanation
        desc_lbl = Gtk.Label(
            label="Executes 4 rapid high-velocity pulses (~5,200 RPM) followed by brief settle phases. "
                  "Aerodynamic shockwaves dislodge dry dust particles from heatsink fins and exhaust channels."
        )
        desc_lbl.set_line_wrap(True)
        desc_lbl.get_style_context().add_class("purge-sub")
        content_area.pack_start(desc_lbl, False, False, 0)

        # Main Telemetry & Cycle Card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class("purge-card")

        # Top row: Cycle status badge
        row_status = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl_status_title = Gtk.Label(label="Current Phase:")
        lbl_status_title.get_style_context().add_class("purge-sub")
        row_status.pack_start(lbl_status_title, False, False, 0)

        self.phase_badge = Gtk.Label(label="READY TO START")
        self.phase_badge.get_style_context().add_class("purge-badge-ready")
        row_status.pack_end(self.phase_badge, False, False, 0)
        card.pack_start(row_status, False, False, 0)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_text("0 / 40 seconds")
        card.pack_start(self.progress_bar, False, False, 0)

        # Telemetry metrics row
        metrics_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        metrics_row.set_homogeneous(True)

        # RPM
        box_rpm = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_r = Gtk.Label(label="TACHOMETER")
        lbl_r.get_style_context().add_class("purge-sub")
        box_rpm.pack_start(lbl_r, False, False, 0)
        self.val_rpm = Gtk.Label(label="---- RPM")
        self.val_rpm.get_style_context().add_class("mono-telemetry")
        box_rpm.pack_start(self.val_rpm, False, False, 0)
        metrics_row.pack_start(box_rpm, True, True, 0)

        # Temperature
        box_temp = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        lbl_t = Gtk.Label(label="CPU TEMP")
        lbl_t.get_style_context().add_class("purge-sub")
        box_temp.pack_start(lbl_t, False, False, 0)
        self.val_temp = Gtk.Label(label="--.-°C")
        self.val_temp.get_style_context().add_class("mono-telemetry")
        box_temp.pack_start(self.val_temp, False, False, 0)
        metrics_row.pack_start(box_temp, True, True, 0)

        card.pack_start(metrics_row, False, False, 0)
        content_area.pack_start(card, True, True, 0)

        # Safety info note
        safety_lbl = Gtk.Label(label="Safety Watchdog Active: Purge auto-aborts if temperature exceeds 80°C.")
        safety_lbl.get_style_context().add_class("purge-sub")
        content_area.pack_start(safety_lbl, False, False, 0)

        # Action Buttons Area
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        content_area.pack_start(btn_box, False, False, 0)

        self.btn_action = Gtk.Button(label="Start Dust Purge (40s)")
        self.btn_action.get_style_context().add_class("purge-btn-start")
        self.btn_action.connect("clicked", self._on_toggle_purge)
        btn_box.pack_start(self.btn_action, True, True, 0)

        self.btn_close = Gtk.Button(label="Close")
        self.btn_close.connect("clicked", lambda b: self._close_dialog())
        btn_box.pack_end(self.btn_close, False, False, 0)

        self.show_all()

    def _on_toggle_purge(self, btn):
        if not self.is_running:
            self._start_purge()
        else:
            self._abort_purge(reason="Aborted by user")

    def _start_purge(self):
        # Save current level to restore upon completion
        status = self.controller.get_fan_status()
        self.original_level = status.get("level", "auto")

        self.is_running = True
        self.elapsed_time = 0.0
        self.btn_action.set_label("Abort / Emergency Stop")
        self.btn_action.get_style_context().remove_class("purge-btn-start")
        self.btn_action.get_style_context().add_class("purge-btn-abort")
        self.btn_close.set_sensitive(False)

        # Start timer tick (every 250ms)
        self.timer_id = GLib.timeout_add(250, self._on_tick)

    def _on_tick(self) -> bool:
        if not self.is_running:
            return False

        self.elapsed_time += 0.25
        frac = min(1.0, self.elapsed_time / self.total_duration_sec)
        rem_sec = max(0, int(self.total_duration_sec - self.elapsed_time))
        self.progress_bar.set_fraction(frac)
        self.progress_bar.set_text(f"{int(self.elapsed_time)}s / {int(self.total_duration_sec)}s ({rem_sec}s remaining)")

        # Read live hardware telemetry
        temp_c = self.controller.get_cpu_temp()
        status = self.controller.get_fan_status()
        rpm = status.get("speed", 0)

        self.val_rpm.set_text(f"{rpm:,} RPM")
        self.val_temp.set_text(f"{temp_c:.1f}°C")

        # Emergency Thermal Safety Check
        if temp_c >= 80.0:
            self._abort_purge(reason=f"Emergency auto-abort: CPU reached {temp_c:.1f}°C!")
            return False

        # Pulse Cycle Logic: 4 cycles of 10 seconds
        # 0s - 6s: Burst ('disengaged')
        # 6s - 10s: Settle ('0')
        cycle_idx = int(self.elapsed_time // 10) + 1
        cycle_time = self.elapsed_time % 10.0

        if cycle_time < 6.0:
            target_level = "disengaged"
            self.phase_badge.get_style_context().remove_class("purge-badge-settle")
            self.phase_badge.get_style_context().remove_class("purge-badge-ready")
            self.phase_badge.get_style_context().add_class("purge-badge-burst")
            self.phase_badge.set_text(f"PULSE {cycle_idx}/4: HIGH VELOCITY")
        else:
            target_level = "0"
            self.phase_badge.get_style_context().remove_class("purge-badge-burst")
            self.phase_badge.get_style_context().remove_class("purge-badge-ready")
            self.phase_badge.get_style_context().add_class("purge-badge-settle")
            self.phase_badge.set_text(f"PULSE {cycle_idx}/4: SETTLE & DECEL")

        current_level = status.get("level", "auto")
        if current_level != target_level:
            try:
                self.controller.set_level(target_level)
            except Exception as e:
                print(f"Purge error setting level {target_level}: {e}")

        # Check for completion
        if self.elapsed_time >= self.total_duration_sec:
            self._complete_purge()
            return False

        return True

    def _complete_purge(self):
        self.is_running = False
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

        # Restore original or auto mode
        try:
            self.controller.set_level(self.original_level)
        except Exception:
            self.controller.set_level("auto")

        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("Completed successfully!")
        self.phase_badge.get_style_context().remove_class("purge-badge-burst")
        self.phase_badge.get_style_context().remove_class("purge-badge-settle")
        self.phase_badge.get_style_context().add_class("purge-badge-ready")
        self.phase_badge.set_text("PURGE COMPLETED")

        self.btn_action.set_label("Purge Complete (Restart?)")
        self.btn_action.get_style_context().remove_class("purge-btn-abort")
        self.btn_action.get_style_context().add_class("purge-btn-start")
        self.btn_close.set_sensitive(True)

        if self.on_finish_callback:
            self.on_finish_callback()

    def _abort_purge(self, reason: str = "Purge Aborted"):
        self.is_running = False
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

        # Immediately restore safe state
        try:
            self.controller.set_level("auto")
        except Exception:
            pass

        self.phase_badge.get_style_context().remove_class("purge-badge-burst")
        self.phase_badge.get_style_context().remove_class("purge-badge-settle")
        self.phase_badge.get_style_context().add_class("purge-badge-ready")
        self.phase_badge.set_text("ABORTED")
        self.progress_bar.set_text(reason)

        self.btn_action.set_label("Start Dust Purge (40s)")
        self.btn_action.get_style_context().remove_class("purge-btn-abort")
        self.btn_action.get_style_context().add_class("purge-btn-start")
        self.btn_close.set_sensitive(True)

        if self.on_finish_callback:
            self.on_finish_callback()

    def _close_dialog(self):
        if self.is_running:
            self._abort_purge()
        self.destroy()

    def _on_dialog_close(self, widget, event):
        self._close_dialog()
        return False
