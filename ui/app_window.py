import os
from typing import Optional
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from backend import FanController, SafetyGuard, SmartCurveEngine, NotificationManager
from .visual_gauge import VisualGauge
from .live_graph import LiveGraph
from .control_panel import ControlPanel
from .tray_indicator import TrayIndicator
from .sensor_matrix import SensorMatrixWidget
from .dust_purge_dialog import DustPurgeDialog
from .curve_dialog import CurveConfigDialog


APP_CSS = b"""
* {
    font-family: "Ubuntu Sans", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

window.fan-window {
    background-color: #06070a;
    color: #e4e4e7;
}

headerbar.fan-header {
    background-color: #0d0f15;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    min-height: 48px;
    padding: 0 14px;
}

.quickbar {
    background-color: #090a0f;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    padding: 8px 16px;
}

.telemetry-capsule {
    background-color: #11131b;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 6px;
    padding: 3px 8px;
}

.panel-card {
    background-color: #11131b;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
}

.sub-metric-box {
    background-color: #08090e;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 8px 12px;
}

.section-title {
    font-size: 10px;
    font-weight: 700;
    color: #71717a;
    letter-spacing: 1.2px;
}

.control-label {
    font-size: 12px;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.1px;
}

.text-muted {
    font-size: 10px;
    font-weight: 500;
    color: #71717a;
}

.font-mono-num {
    font-family: "Ubuntu Sans Mono", "Ubuntu Mono", monospace;
    font-size: 14px;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.3px;
}

.badge-cool {
    background-color: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.badge-warm {
    background-color: rgba(245, 158, 11, 0.12);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.35);
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.badge-hot {
    background-color: rgba(226, 35, 26, 0.15);
    color: #f87171;
    border: 1px solid rgba(226, 35, 26, 0.45);
    border-radius: 4px;
    padding: 1px 6px;
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 0.5px;
}

.badge-active {
    background-color: #191c26;
    color: #fafafa;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    padding: 1px 7px;
    font-family: "Ubuntu Sans Mono", "Ubuntu Mono", monospace;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: -0.2px;
}

.badge-profile {
    background-color: rgba(56, 189, 248, 0.10);
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.30);
    border-radius: 4px;
    padding: 1px 7px;
    font-family: "Ubuntu Sans Mono", "Ubuntu Mono", monospace;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.4px;
}

.preset-btn {
    background-color: #11131b;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px 12px;
}

.preset-btn:hover {
    background-color: #181b26;
    border-color: rgba(255, 255, 255, 0.16);
}

.preset-active {
    border-color: #e2231a;
    background-color: rgba(226, 35, 26, 0.15);
}

.preset-title {
    font-size: 12px;
    font-weight: 700;
    color: #fafafa;
    letter-spacing: -0.1px;
}

.preset-sub {
    font-size: 10px;
    color: #71717a;
}

.emerald-dot { color: #10b981; font-size: 11px; }
.cyan-dot { color: #00d2ff; font-size: 11px; }
.amber-dot { color: #f59e0b; font-size: 11px; }
.red-dot { color: #e2231a; font-size: 11px; }

.slider-card {
    background-color: #11131b;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px 16px;
}

scale trough {
    background-color: #08090e;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 4px;
    min-height: 6px;
}

scale highlight {
    background-color: #e2231a;
    border-radius: 4px;
    min-height: 6px;
}

scale slider {
    background-image: none;
    background-color: #ffffff;
    border: 2px solid #e2231a;
    border-radius: 50%;
    min-width: 16px;
    min-height: 16px;
}

.perm-banner {
    background-color: #241105;
    border-bottom: 1px solid #78350f;
    color: #fef3c7;
    padding: 7px 18px;
    font-size: 11px;
    font-weight: 500;
}

.btn-unlock {
    background-color: #d97706;
    color: #ffffff;
    border-radius: 5px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
}

.btn-unlock:hover {
    background-color: #b45309;
}

button.btn-purge-action {
    background-image: none;
    background-color: rgba(226, 35, 26, 0.12);
    color: #fca5a5;
    border: 1px solid rgba(226, 35, 26, 0.35);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.2px;
}

button.btn-purge-action:hover {
    background-image: none;
    background-color: rgba(226, 35, 26, 0.25);
    border-color: #e2231a;
    color: #ffffff;
}

button.btn-curve-action {
    background-image: none;
    background-color: rgba(59, 130, 246, 0.10);
    color: #93c5fd;
    border: 1px solid rgba(59, 130, 246, 0.30);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.2px;
}

button.btn-curve-action:hover {
    background-image: none;
    background-color: rgba(59, 130, 246, 0.22);
    border-color: #3b82f6;
    color: #ffffff;
}

button.btn-toggle-sensors {
    background-image: none;
    background-color: #11131b;
    color: #a1a1aa;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 600;
}

button.btn-toggle-sensors:hover {
    background-image: none;
    background-color: #1a1c27;
    border-color: rgba(255, 255, 255, 0.20);
    color: #ffffff;
}

.status-pill {
    background-color: #10121a;
    color: #71717a;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 5px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.3px;
}

button.btn-header-action {
    background-image: none;
    background-color: transparent;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    padding: 3px 8px;
    color: #a1a1aa;
    font-size: 12px;
}

button.btn-header-action:hover {
    background-image: none;
    background-color: #1a1c27;
    border-color: rgba(255, 255, 255, 0.20);
    color: #fafafa;
}

scrolledwindow {
    background-color: transparent;
    border: none;
}

scrolledwindow overshoot.top,
scrolledwindow overshoot.bottom {
    background: none;
}

scrollbar {
    background-color: transparent;
    border: none;
}

scrollbar slider {
    background-color: rgba(255, 255, 255, 0.14);
    border-radius: 4px;
    min-width: 6px;
    min-height: 24px;
}

scrollbar slider:hover {
    background-color: rgba(255, 255, 255, 0.30);
}
"""

class AppWindow(Gtk.Window):
    """
    Main ThinkPad Fan Control Desktop Window.
    """

    def __init__(self, controller: FanController, safety: SafetyGuard):
        super().__init__(title="ThinkPad Fan Control — L14 Gen 2")
        self.controller = controller
        self.safety = safety

        # Initialize Smart Curve Engine & Desktop Notifier
        self.curve_engine = SmartCurveEngine()
        self.notifier = NotificationManager()
        self.last_ac_online: Optional[bool] = None

        self.set_default_size(780, 560)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.get_style_context().add_class("fan-window")

        # Set application and window icon
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets", "icons", "thinkpad-fan.svg"
        )
        if os.path.exists(icon_path):
            try:
                self.set_icon_from_file(icon_path)
                Gtk.Window.set_default_icon_from_file(icon_path)
            except Exception as e:
                print(f"Note: Could not set window icon: {e}")

        self._apply_css()
        self._build_ui()

        # Connect safety override callback
        self.safety.on_emergency_override = self._on_emergency_thermal_trip

        # Tray Indicator
        self.tray = TrayIndicator(
            on_toggle_window=self._toggle_visibility,
            on_select_preset=self._on_level_command,
            on_quit=self._on_app_quit,
            on_open_dust_purge=self._open_dust_purge_dialog,
            on_open_curve_dialog=self._open_curve_dialog
        )

        # Polling Timers
        GLib.timeout_add(100, self._on_anim_tick)
        GLib.timeout_add(1000, self._on_sensor_tick)

        self.connect("delete-event", self._on_close_event)
        self.connect("size-allocate", self._on_window_size_allocate)
        self.connect("key-press-event", self._on_key_press_event)
        self.connect("window-state-event", self._on_window_state_event)

    def _apply_css(self):
        screen = Gdk.Screen.get_default()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(APP_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _build_ui(self):
        root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root_vbox)

        # 1. Custom HeaderBar
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.get_style_context().add_class("fan-header")

        # Direct EC Control Pill
        ec_pill = Gtk.Label(label="DIRECT EC CONTROL")
        ec_pill.get_style_context().add_class("status-pill")
        header.pack_start(ec_pill)

        # Fullscreen Toggle Button
        self.btn_fullscreen = Gtk.Button()
        self.btn_fullscreen.get_style_context().add_class("btn-header-action")
        self.btn_fullscreen.set_tooltip_text("Toggle Fullscreen (F11)")
        self.lbl_fs_icon = Gtk.Label(label="⛶")
        self.btn_fullscreen.add(self.lbl_fs_icon)
        self.btn_fullscreen.connect("clicked", self._on_toggle_fullscreen)
        header.pack_end(self.btn_fullscreen)
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        red_dot = Gtk.Label(label="●")
        red_dot.get_style_context().add_class("red-dot")
        title_box.pack_start(red_dot, False, False, 0)

        t_lbl = Gtk.Label(label="ThinkPad Fan Control")
        t_lbl.get_style_context().add_class("control-label")
        title_box.pack_start(t_lbl, False, False, 0)

        sub_model = Gtk.Label(label="L14 Gen 2 (20X2S37F00)")
        sub_model.get_style_context().add_class("text-muted")
        title_box.pack_start(sub_model, False, False, 0)
        header.set_custom_title(title_box)

        self.set_titlebar(header)

        # 2. Permission Banner (if read-only)
        self.perm_banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.perm_banner.get_style_context().add_class("perm-banner")
        
        perm_text = Gtk.Label(label="Read-Only Telemetry: Manual fan speed control requires elevation.")
        self.perm_banner.pack_start(perm_text, False, False, 0)

        btn_unlock = Gtk.Button(label="Unlock Controls")
        btn_unlock.get_style_context().add_class("btn-unlock")
        btn_unlock.connect("clicked", self._on_unlock_permissions)
        self.perm_banner.pack_end(btn_unlock, False, False, 0)

        root_vbox.pack_start(self.perm_banner, False, False, 0)
        self._update_perm_banner()

        # 3. Quick Telemetry Bar
        quickbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        quickbar.get_style_context().add_class("quickbar")
        self.quickbar = quickbar

        # CPU Temp
        box_temp = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box_temp.get_style_context().add_class("telemetry-capsule")
        lbl_temp_name = Gtk.Label(label="CPU Package:")
        lbl_temp_name.get_style_context().add_class("text-muted")
        box_temp.pack_start(lbl_temp_name, False, False, 0)

        self.val_temp = Gtk.Label(label="--.-°C")
        self.val_temp.get_style_context().add_class("font-mono-num")
        box_temp.pack_start(self.val_temp, False, False, 0)

        self.badge_temp = Gtk.Label(label="COOL")
        self.badge_temp.get_style_context().add_class("badge-cool")
        box_temp.pack_start(self.badge_temp, False, False, 0)
        quickbar.pack_start(box_temp, False, False, 0)

        # Fan RPM
        box_rpm = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box_rpm.get_style_context().add_class("telemetry-capsule")
        lbl_rpm_name = Gtk.Label(label="Tachometer:")
        lbl_rpm_name.get_style_context().add_class("text-muted")
        box_rpm.pack_start(lbl_rpm_name, False, False, 0)

        self.val_rpm = Gtk.Label(label="---- RPM")
        self.val_rpm.get_style_context().add_class("font-mono-num")
        box_rpm.pack_start(self.val_rpm, False, False, 0)
        quickbar.pack_start(box_rpm, False, False, 0)

        # Active Mode
        box_mode = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box_mode.get_style_context().add_class("telemetry-capsule")
        lbl_mode_name = Gtk.Label(label="Mode:")
        lbl_mode_name.get_style_context().add_class("text-muted")
        box_mode.pack_start(lbl_mode_name, False, False, 0)

        self.val_mode = Gtk.Label(label="auto")
        self.val_mode.get_style_context().add_class("badge-active")
        box_mode.pack_start(self.val_mode, False, False, 0)
        quickbar.pack_start(box_mode, False, False, 0)

        # Smart Curve Profile Badge
        box_prof = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box_prof.get_style_context().add_class("telemetry-capsule")
        lbl_prof_name = Gtk.Label(label="Profile:")
        lbl_prof_name.get_style_context().add_class("text-muted")
        box_prof.pack_start(lbl_prof_name, False, False, 0)

        self.badge_profile = Gtk.Label(label="AUTO (BIOS)")
        self.badge_profile.get_style_context().add_class("badge-profile")
        box_prof.pack_start(self.badge_profile, False, False, 0)
        quickbar.pack_start(box_prof, False, False, 0)

        # Toggle Sensor Matrix Button
        self.btn_sensors = Gtk.Button(label="Thermal Matrix ▾")
        self.btn_sensors.get_style_context().add_class("btn-toggle-sensors")
        self.btn_sensors.connect("clicked", self._on_toggle_sensor_matrix)
        quickbar.pack_end(self.btn_sensors, False, False, 0)

        # Watchdog status
        box_wd = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        lbl_wd = Gtk.Label(label="WATCHDOG 10s")
        lbl_wd.get_style_context().add_class("status-pill")
        box_wd.pack_end(lbl_wd, False, False, 0)
        quickbar.pack_end(box_wd, False, False, 0)

        root_vbox.pack_start(quickbar, False, False, 0)

        # 4. Central Workspace: Split Gauge and Live Graph
        workspace = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        workspace.set_margin_top(14)
        workspace.set_margin_bottom(14)
        workspace.set_margin_left(16)
        workspace.set_margin_right(16)
        self.workspace = workspace

        # Wrap workspace in a ScrolledWindow so controls never get clipped off-screen
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_propagate_natural_width(True)
        scrolled.add(workspace)
        root_vbox.pack_start(scrolled, True, True, 0)

        top_panels = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        top_panels.set_hexpand(True)
        workspace.pack_start(top_panels, False, True, 0)

        # Left Panel: Visual Speedometer Gauge Card
        gauge_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        gauge_card.get_style_context().add_class("panel-card")
        gauge_card.set_size_request(310, -1)
        self.gauge_card = gauge_card

        gauge_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_gh = Gtk.Label(label="FAN TACHOMETER")
        lbl_gh.get_style_context().add_class("section-title")
        gauge_header.pack_start(lbl_gh, False, False, 0)
        gauge_card.pack_start(gauge_header, False, False, 0)

        self.gauge = VisualGauge(max_rpm=5500)
        gauge_card.pack_start(self.gauge, True, True, 0)

        gauge_metrics = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        gauge_metrics.set_homogeneous(True)

        box_f1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box_f1.get_style_context().add_class("sub-metric-box")
        lbl_f1_t = Gtk.Label(label="FAN 1")
        lbl_f1_t.get_style_context().add_class("text-muted")
        box_f1.pack_start(lbl_f1_t, False, False, 0)
        self.lbl_f1_v = Gtk.Label(label="---- RPM")
        self.lbl_f1_v.get_style_context().add_class("font-mono-num")
        box_f1.pack_start(self.lbl_f1_v, False, False, 0)
        gauge_metrics.pack_start(box_f1, True, True, 0)

        box_ceil = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box_ceil.get_style_context().add_class("sub-metric-box")
        lbl_ceil_t = Gtk.Label(label="CEILING")
        lbl_ceil_t.get_style_context().add_class("text-muted")
        box_ceil.pack_start(lbl_ceil_t, False, False, 0)
        self.lbl_ceil_v = Gtk.Label(label="Dynamic")
        self.lbl_ceil_v.get_style_context().add_class("font-mono-num")
        box_ceil.pack_start(self.lbl_ceil_v, False, False, 0)
        gauge_metrics.pack_start(box_ceil, True, True, 0)

        gauge_card.pack_start(gauge_metrics, False, False, 0)
        top_panels.pack_start(gauge_card, False, False, 0)

        # Right Panel: 60-Second Real-Time Telemetry Graph
        graph_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        graph_card.get_style_context().add_class("panel-card")

        graph_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_gtitle = Gtk.Label(label="REAL-TIME TELEMETRY (60s)")
        lbl_gtitle.get_style_context().add_class("section-title")
        graph_header.pack_start(lbl_gtitle, False, False, 0)

        lbl_legend = Gtk.Label(label="■ Temp (°C)   ■ Fan (RPM)   ▲ 85°C Trip Limit")
        lbl_legend.get_style_context().add_class("text-muted")
        graph_header.pack_end(lbl_legend, False, False, 0)
        graph_card.pack_start(graph_header, False, False, 0)

        self.graph = LiveGraph(history_len=60)
        graph_card.pack_start(self.graph, True, True, 0)

        # Stats summary row
        stats_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        stats_row.set_homogeneous(True)

        self.stat_cur = self._create_stat_box("CUR TEMP", "--.-°C")
        self.stat_peak = self._create_stat_box("PEAK TEMP", "--.-°C")
        self.stat_avg = self._create_stat_box("AVG TEMP", "--.-°C")
        self.stat_trip = self._create_stat_box("FAIL-SAFE", "85.0°C")

        stats_row.pack_start(self.stat_cur[0], True, True, 0)
        stats_row.pack_start(self.stat_peak[0], True, True, 0)
        stats_row.pack_start(self.stat_avg[0], True, True, 0)
        stats_row.pack_start(self.stat_trip[0], True, True, 0)
        graph_card.pack_start(stats_row, False, False, 0)

        top_panels.pack_start(graph_card, True, True, 0)

        # 5. Middle Panel: Multi-Sensor Hardware Thermal Matrix (Collapsible)
        self.sensor_matrix = SensorMatrixWidget()
        self.sensor_matrix.show_all()
        self.sensor_matrix.set_no_show_all(True)
        self.sensor_matrix.hide()
        workspace.pack_start(self.sensor_matrix, False, False, 0)

        # 6. Bottom Controls: Presets, Custom Curves, and Granular Slider
        self.control_panel = ControlPanel(
            on_level_selected=self._on_level_command,
            on_open_curve_dialog=self._open_curve_dialog,
            on_open_dust_purge=self._open_dust_purge_dialog
        )
        workspace.pack_start(self.control_panel, False, False, 0)

        self._peak_temp = 0.0

    def _create_stat_box(self, label_str: str, val_str: str):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.get_style_context().add_class("sub-metric-box")
        lbl = Gtk.Label(label=label_str)
        lbl.get_style_context().add_class("text-muted")
        box.pack_start(lbl, False, False, 0)

        v_lbl = Gtk.Label(label=val_str)
        v_lbl.get_style_context().add_class("font-mono-num")
        box.pack_start(v_lbl, False, False, 0)
        return box, v_lbl

    def _update_perm_banner(self):
        if self.controller.is_writable():
            self.perm_banner.hide()
        else:
            self.perm_banner.show_all()

    def _on_unlock_permissions(self, btn):
        btn.set_sensitive(False)
        success = self.controller.unlock_permissions()
        if success:
            self._update_perm_banner()
        else:
            btn.set_sensitive(True)

    def _on_level_command(self, level_str: str):
        try:
            self.controller.set_level(level_str)
            self._update_perm_banner()
            self._on_sensor_tick()
        except Exception as e:
            print(f"Error setting level {level_str}: {e}")

    def _on_anim_tick(self) -> bool:
        self.gauge.update_animation_step()
        return True

    def _on_sensor_tick(self) -> bool:
        temp_c = self.controller.get_cpu_temp()
        status = self.controller.get_fan_status()
        rpm = status.get("speed", 0)
        level_str = status.get("level", "auto")

        # 1. Read Hardware Multi-Sensors & Power State
        sensors = self.controller.get_all_sensors()
        power = self.controller.get_power_state()

        if self.sensor_matrix.get_visible():
            self.sensor_matrix.update_telemetry(sensors, power)

        # 2. Power Transition Check (AC / Battery Auto-Profile Switching)
        ac_online = power.get("ac_online", True)
        if self.last_ac_online is not None and ac_online != self.last_ac_online:
            new_profile = self.curve_engine.handle_power_transition(ac_online)
            if new_profile:
                p_text = "AC Adapter Connected" if ac_online else "Operating on Battery Power"
                self.notifier.send(
                    "Thermal Profile Switched",
                    f"{p_text}: Activated '{new_profile.capitalize()}' profile.",
                    urgency="normal",
                    alert_type="power_switch"
                )
        self.last_ac_online = ac_online

        # 3. Smart Curve Automation with Hysteresis
        if self.curve_engine.is_curve_active:
            target_level = self.curve_engine.evaluate_temp(temp_c)
            if target_level is not None and target_level != level_str:
                try:
                    self.controller.set_level(target_level)
                    level_str = target_level
                except Exception as e:
                    print(f"Error applying curve target level {target_level}: {e}")
            self.badge_profile.set_text(f"CURVE: {self.curve_engine.active_profile.upper()}")
        else:
            self.badge_profile.set_text("AUTO (BIOS)")

        # 4. Thermal Warning Notification (>82°C, debounced to 60s cooldown)
        if temp_c >= 82.0:
            self.notifier.send(
                "High Temperature Alert",
                f"CPU temperature reached {temp_c:.1f}°C! Fan cooling recommended.",
                urgency="critical",
                alert_type="thermal_high"
            )

        # 5. Update Visual Gauge
        self.gauge.set_target_rpm(rpm, f"Level {level_str}")

        # 6. Update Real-Time Graph
        self.graph.add_telemetry(temp_c, rpm)

        # 7. Update Quickbar
        self.val_temp.set_text(f"{temp_c:.1f}°C")
        self.val_rpm.set_text(f"{rpm:,} RPM")
        self.val_mode.set_text(f"level {level_str}")
        self.lbl_f1_v.set_text(f"{rpm:,} RPM")

        # 8. Update Badge
        self.badge_temp.get_style_context().remove_class("badge-cool")
        self.badge_temp.get_style_context().remove_class("badge-warm")
        self.badge_temp.get_style_context().remove_class("badge-hot")
        if temp_c < 55.0:
            self.badge_temp.get_style_context().add_class("badge-cool")
            self.badge_temp.set_text("COOL")
        elif temp_c < 75.0:
            self.badge_temp.get_style_context().add_class("badge-warm")
            self.badge_temp.set_text("WARM")
        else:
            self.badge_temp.get_style_context().add_class("badge-hot")
            self.badge_temp.set_text("HOT")

        # 9. Update Stats
        if temp_c > self._peak_temp:
            self._peak_temp = temp_c
        self.stat_cur[1].set_text(f"{temp_c:.1f}°C")
        self.stat_peak[1].set_text(f"{self._peak_temp:.1f}°C")
        
        hist = list(self.graph.temp_history)
        if hist:
            avg = sum(hist) / len(hist)
            self.stat_avg[1].set_text(f"{avg:.1f}°C")

        # 10. Sync Controls & Tray
        self.control_panel.sync_hardware_level(level_str)
        self.tray.update_telemetry(temp_c, rpm, level_str)

        return True

    def _on_toggle_sensor_matrix(self, btn):
        if self.sensor_matrix.get_visible():
            self.sensor_matrix.hide()
            btn.set_label("Thermal Matrix ▾")
        else:
            self.sensor_matrix.show()
            btn.set_label("Thermal Matrix ▴")
            sensors = self.controller.get_all_sensors()
            power = self.controller.get_power_state()
            self.sensor_matrix.update_telemetry(sensors, power)

    def _open_dust_purge_dialog(self):
        dialog = DustPurgeDialog(
            parent_window=self,
            controller=self.controller,
            on_finish_callback=self._on_purge_finished
        )
        dialog.run()

    def _on_purge_finished(self):
        self.notifier.send(
            "Fan Dust Purge Completed",
            "4 aerodynamic high-velocity pulses executed successfully.",
            urgency="normal",
            alert_type="dust_purge"
        )
        self._on_sensor_tick()

    def _open_curve_dialog(self):
        dialog = CurveConfigDialog(
            parent_window=self,
            curve_engine=self.curve_engine,
            on_apply=self._on_sensor_tick
        )
        dialog.run()

    def _on_emergency_thermal_trip(self, critical_temp: float):
        print(f"UI NOTIFIED: Emergency thermal trip at {critical_temp}°C!")
        self.control_panel.sync_hardware_level("7")
        self.notifier.send(
            "Emergency Thermal Trip",
            f"CPU exceeded safe limit at {critical_temp:.1f}°C! Fan forced to maximum.",
            urgency="critical",
            alert_type="emergency_trip"
        )

    def _toggle_visibility(self):
        if self.is_visible():
            self.hide()
        else:
            self.present()

    def _on_close_event(self, widget, event):
        self._on_app_quit()
        return False

    def _on_window_size_allocate(self, widget, alloc):
        w = alloc.width
        h = alloc.height
        h_margin = max(16, min(28, int(w * 0.015)))
        v_margin = max(10, min(20, int(h * 0.015)))

        if hasattr(self, "workspace"):
            self.workspace.set_margin_left(h_margin)
            self.workspace.set_margin_right(h_margin)
            self.workspace.set_margin_top(v_margin)
            self.workspace.set_margin_bottom(v_margin)

        if hasattr(self, "quickbar"):
            self.quickbar.set_margin_left(h_margin)
            self.quickbar.set_margin_right(h_margin)

    def _on_toggle_fullscreen(self, btn=None):
        win = self.get_window()
        if win and (win.get_state() & Gdk.WindowState.FULLSCREEN):
            self.unfullscreen()
        else:
            self.fullscreen()

    def _on_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_F11:
            self._on_toggle_fullscreen()
            return True
        elif event.keyval == Gdk.KEY_Escape:
            win = self.get_window()
            if win and (win.get_state() & Gdk.WindowState.FULLSCREEN):
                self.unfullscreen()
                return True
        return False

    def _on_window_state_event(self, widget, event):
        is_fs = bool(event.new_window_state & Gdk.WindowState.FULLSCREEN)
        if hasattr(self, "lbl_fs_icon"):
            self.lbl_fs_icon.set_text("🗗" if is_fs else "⛶")
            self.btn_fullscreen.set_tooltip_text("Exit Fullscreen (Esc / F11)" if is_fs else "Toggle Fullscreen (F11)")

    def _on_app_quit(self):
        self.safety.restore_safe_state()
        self.safety.stop()
        Gtk.main_quit()


