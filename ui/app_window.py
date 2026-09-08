import os
from typing import Optional, Dict, Any
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib
from backend import FanController, SafetyGuard, SmartCurveEngine, NotificationManager

from .circular_gauge import CircularGauge
from .tray_indicator import TrayIndicator
from .dashboard_view import DashboardView
from .curves_view import CurvesView
from .cleaning_view import CleaningView
from .sensors_view import SensorsView
from .sensor_matrix import SensorMatrixWidget
from .dust_purge_dialog import DustPurgeDialog
from .curve_dialog import CurveConfigDialog
from .sensor_dialog import SensorMatrixDialog


APP_CSS = b"""
* {
    font-family: "Cantarell", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

/* GNOME Libadwaita Dark Window Surface */
window.fan-window {
    background-color: #242424;
    color: #ffffff;
}

scrolledwindow {
    background-color: transparent;
}

viewport {
    background-color: transparent;
}

/* HeaderBar */
headerbar.fan-header {
    background-color: #242424;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    min-height: 46px;
    padding: 0 8px;
}

headerbar.fan-header .title {
    font-weight: 700;
    font-size: 13px;
    color: #ffffff;
}

headerbar.fan-header .subtitle {
    font-size: 11px;
    color: #9a9996;
}

.header-menu-btn {
    background-image: none;
    background-color: transparent;
    color: #9a9996;
    border: none;
    border-radius: 6px;
    padding: 5px 6px;
    box-shadow: none;
    transition: all 120ms ease-in-out;
}

.header-menu-btn:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #ffffff;
}

/* Popover Menu */
.header-menu-popover {
    background-color: #2e2e2e;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 12px;
}

.popover-info-card {
    background-color: #262626;
    border-radius: 8px;
    padding: 8px 12px;
}

.popover-status-label {
    font-size: 11px;
    font-weight: 600;
    color: #2ec27e;
}

.popover-info-label {
    font-size: 10px;
    color: #9a9996;
}

.popover-action-btn {
    font-size: 12px;
    color: #ffffff;
    padding: 6px 10px;
    border-radius: 6px;
}

.popover-action-btn:hover {
    background-color: rgba(255, 255, 255, 0.08);
    color: #ffffff;
}

/* Bottom ViewSwitcher Navigation Bar (Blur my Shell style) */
.bottom-switcher-bar {
    background-color: #242424;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding: 5px 12px 6px 12px;
}

.bottom-tab-btn {
    background-image: none;
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 4px 6px;
    box-shadow: none;
    transition: all 120ms ease-in-out;
    min-height: 46px;
}

.bottom-tab-btn:hover {
    background-color: rgba(255, 255, 255, 0.06);
}

.bottom-tab-btn-active {
    background-color: #383838;
}

.bottom-tab-btn-active:hover {
    background-color: #424242;
}

.bottom-tab-btn image {
    color: #9a9996;
}

.bottom-tab-btn:hover image {
    color: #ffffff;
}

.bottom-tab-btn-active image {
    color: #ffffff;
}

.bottom-tab-label {
    font-size: 10.5px;
    font-weight: 500;
    color: #9a9996;
    margin-top: 2px;
}

.bottom-tab-btn:hover .bottom-tab-label {
    color: #ffffff;
}

.bottom-tab-label-active {
    color: #ffffff;
    font-weight: 700;
}

/* Authentic GNOME Libadwaita Cards & Boxed Lists */
.adw-card {
    background-color: #303030;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 12px 14px;
}

.adw-card-flat-inner {
    padding: 0;
}

.adw-list-row {
    padding: 10px 14px;
}

.adw-row-separator {
    background-color: rgba(255, 255, 255, 0.06);
    min-height: 1px;
    border: none;
}

/* Icon Plate in List Rows */
.row-icon-plate {
    background-color: rgba(255, 255, 255, 0.07);
    border-radius: 6px;
    min-width: 28px;
    min-height: 28px;
    padding: 4px;
}

.row-icon-plate image {
    color: #ffffff;
}

/* Nested Preferences Rows */
.adw-row {
    background-color: #363636;
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    padding: 8px 12px;
}

.adw-row:hover {
    background-color: #3d3d3d;
    border-color: rgba(255, 255, 255, 0.10);
}

/* Section Titles & Labels */
.adw-section-title {
    font-size: 11px;
    font-weight: 700;
    color: #9a9996;
    letter-spacing: 0.4px;
}

.hero-mode-title {
    font-size: 21px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.2px;
}

.adw-subtitle {
    font-size: 11.5px;
    color: #9a9996;
}

.chip-title {
    font-size: 11px;
    color: #9a9996;
}

.control-label {
    font-size: 13px;
    font-weight: 500;
    color: #ffffff;
}

.font-mono-temp {
    font-family: "Cantarell", monospace;
    font-size: 14px;
    font-weight: 700;
    color: #3584e4;
}

.font-mono-num {
    font-family: "Cantarell", monospace;
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
}

.purge-time-display {
    font-family: "Cantarell", monospace;
    font-size: 22px;
    font-weight: 700;
    color: #e01b24;
    letter-spacing: -0.5px;
}

/* Status Badges */
.badge-pill-emerald {
    background-color: rgba(46, 194, 126, 0.20);
    color: #2ec27e;
    border: 1px solid rgba(46, 194, 126, 0.40);
    border-radius: 9999px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
}

.badge-pill-blue {
    background-color: rgba(53, 132, 228, 0.20);
    color: #3584e4;
    border: 1px solid rgba(53, 132, 228, 0.40);
    border-radius: 9999px;
    padding: 2px 10px;
    font-size: 10px;
    font-weight: 600;
}

.badge-cool {
    background-color: rgba(46, 194, 126, 0.18);
    color: #2ec27e;
    border: 1px solid rgba(46, 194, 126, 0.35);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: 700;
}

.badge-warm {
    background-color: rgba(229, 165, 10, 0.18);
    color: #e5a50a;
    border: 1px solid rgba(229, 165, 10, 0.35);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: 700;
}

.badge-hot {
    background-color: rgba(224, 27, 36, 0.20);
    color: #e01b24;
    border: 1px solid rgba(224, 27, 36, 0.45);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: 700;
}

.badge-active {
    background-color: #383838;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 4px;
    padding: 2px 7px;
    font-family: "Cantarell", monospace;
    font-size: 10.5px;
    font-weight: 600;
}

.status-pill {
    background-color: #262626;
    color: #9a9996;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 9px;
    font-weight: 600;
}

/* Preset Action Cards */
.adw-profile-card {
    background-image: none;
    background-color: #303030;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 10px 12px;
    box-shadow: none;
    transition: all 120ms ease-in-out;
}

.adw-profile-card:hover {
    background-image: none;
    background-color: #383838;
    border-color: rgba(255, 255, 255, 0.14);
}

.adw-profile-card-active {
    border: 1.5px solid #3584e4;
    background-color: #383838;
}

.blue-dot {
    color: #3584e4;
}

.btn-purge-outline {
    background-image: none;
    background-color: rgba(224, 27, 36, 0.12);
    border: 1px solid rgba(224, 27, 36, 0.40);
    color: #f66151;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 14px;
    transition: all 120ms ease-in-out;
}

.btn-purge-outline:hover {
    background-image: none;
    background-color: rgba(224, 27, 36, 0.28);
    color: #ffffff;
    border-color: #e01b24;
}

.adw-expander {
    font-size: 11px;
    color: #9a9996;
    font-weight: 600;
    margin-top: 2px;
}

/* Stepper Scale */
scale trough {
    background-color: #262626;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 3px;
    min-height: 5px;
}

scale highlight {
    background-color: #3584e4;
    border-radius: 3px;
    min-height: 5px;
}

scale slider {
    background-image: none;
    background-color: #ffffff;
    border: 2px solid #3584e4;
    border-radius: 50%;
    min-width: 14px;
    min-height: 14px;
}

/* Progress bar */
progressbar.adw-purge-progress trough {
    background-color: #262626;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 4px;
    min-height: 8px;
}

progressbar.adw-purge-progress progress {
    background-color: #e01b24;
    border-radius: 4px;
    min-height: 8px;
}

/* Buttons */
button.adw-btn-primary {
    background-image: none;
    background-color: #e01b24;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 700;
    font-size: 12px;
}

button.adw-btn-primary:hover {
    background-image: none;
    background-color: #ed333b;
}

button.adw-btn-abort {
    background-image: none;
    background-color: rgba(224, 27, 36, 0.15);
    color: #f66151;
    border: 1px solid rgba(224, 27, 36, 0.35);
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 700;
    font-size: 12px;
}

button.adw-btn-abort:hover {
    background-image: none;
    background-color: rgba(224, 27, 36, 0.30);
    color: #ffffff;
}

.adw-cycle-pill {
    background-color: #363636;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 5px 8px;
}

.adw-cycle-pill-active {
    border-color: #e01b24;
    background-color: rgba(224, 27, 36, 0.20);
}

.perm-banner {
    background-color: #3d2410;
    border-bottom: 1px solid #78350f;
    color: #fef3c7;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 500;
}

.btn-unlock {
    background-color: #e5a50a;
    color: #1a1a1a;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
}

.btn-unlock:hover {
    background-color: #f6d32d;
}
"""

class AppWindow(Gtk.Window):
    """
    Modern Libadwaita / GNOME Native ThinkPad Fan Control Desktop Window.
    Implements a resizable, deep black UI with segmented StackSwitcher navigation:
    [ Controls ] [ Curves ] [ Cleaning ] [ Sensors ].
    """

    def __init__(self, controller: FanController, safety: SafetyGuard):
        super().__init__(title="ThinkPad Fan Control")
        self.controller = controller
        self.safety = safety

        # Initialize Smart Curve Engine & Desktop Notifier
        self.curve_engine = SmartCurveEngine()
        self.notifier = NotificationManager()
        self.last_ac_online: Optional[bool] = None
        self._has_shown_tray_hint = False

        # Resizable modern window design (default 480x560, min 440x480)
        self.set_resizable(True)
        self.set_default_size(480, 560)
        hints = Gdk.Geometry()
        hints.min_width = 440
        hints.min_height = 480
        self.set_geometry_hints(None, hints, Gdk.WindowHints.MIN_SIZE)

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
        self.show_all()

    def _apply_css(self):
        screen = Gdk.Screen.get_default()
        if screen:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(APP_CSS)
            Gtk.StyleContext.add_provider_for_screen(
                screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _build_ui(self):
        root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(root_vbox)

        # 1. Libadwaita Clean HeaderBar (Upper Bar - matching GNOME Extensions / Blur my Shell)
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.get_style_context().add_class("fan-header")
        header.set_title("ThinkPad Fan Control")
        header.set_subtitle("ThinkPad L14 Gen 2")

        # Hamburger Menu Button (Open-Menu-Symbolic)
        menu_btn = Gtk.MenuButton()
        menu_btn.get_style_context().add_class("header-menu-btn")
        menu_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.MENU)
        menu_icon.set_pixel_size(16)
        menu_btn.set_image(menu_icon)
        menu_btn.set_tooltip_text("Main Menu")

        popover = Gtk.Popover.new(menu_btn)
        popover.get_style_context().add_class("header-menu-popover")
        popover.set_position(Gtk.PositionType.BOTTOM)

        pop_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        pop_box.set_margin_top(8)
        pop_box.set_margin_bottom(8)
        pop_box.set_margin_start(10)
        pop_box.set_margin_end(10)

        # Status row
        row_status = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        row_status.get_style_context().add_class("popover-info-card")

        row_guard = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon_guard = Gtk.Image.new_from_icon_name("security-high-symbolic", Gtk.IconSize.MENU)
        icon_guard.set_pixel_size(14)
        lbl_w = Gtk.Label(label="Safety Guard: 85°C Active")
        lbl_w.set_xalign(0.0)
        lbl_w.get_style_context().add_class("popover-status-label")
        row_guard.pack_start(icon_guard, False, False, 0)
        row_guard.pack_start(lbl_w, False, False, 0)
        row_status.pack_start(row_guard, False, False, 0)

        row_ec = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon_ec = Gtk.Image.new_from_icon_name("utilities-system-monitor-symbolic", Gtk.IconSize.MENU)
        icon_ec.set_pixel_size(14)
        lbl_ec = Gtk.Label(label="Direct EC: /proc/acpi/ibm/fan")
        lbl_ec.set_xalign(0.0)
        lbl_ec.get_style_context().add_class("popover-info-label")
        row_ec.pack_start(icon_ec, False, False, 0)
        row_ec.pack_start(lbl_ec, False, False, 0)
        row_status.pack_start(row_ec, False, False, 0)
        pop_box.pack_start(row_status, False, False, 4)

        sep1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep1.get_style_context().add_class("adw-row-separator")
        pop_box.pack_start(sep1, False, False, 3)

        btn_reset = Gtk.ModelButton(text="Restore BIOS Auto Control")
        btn_reset.get_style_context().add_class("popover-action-btn")
        btn_reset.connect("clicked", lambda w: (self._on_level_command("auto"), popover.popdown()))
        pop_box.pack_start(btn_reset, False, False, 0)

        btn_purge = Gtk.ModelButton(text="Start 40s Dust Purge Routine")
        btn_purge.get_style_context().add_class("popover-action-btn")
        btn_purge.connect("clicked", lambda w: (self._open_dust_purge_dialog(), popover.popdown()))
        pop_box.pack_start(btn_purge, False, False, 0)

        sep2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep2.get_style_context().add_class("adw-row-separator")
        pop_box.pack_start(sep2, False, False, 3)

        btn_about = Gtk.ModelButton(text="About ThinkPad Fan Control")
        btn_about.get_style_context().add_class("popover-action-btn")
        btn_about.connect("clicked", lambda w: (self._show_about_dialog(), popover.popdown()))
        pop_box.pack_start(btn_about, False, False, 0)

        pop_box.show_all()
        popover.add(pop_box)
        menu_btn.set_popover(popover)
        header.pack_end(menu_btn)
        self.header_menu_btn = menu_btn

        self.set_titlebar(header)
        self.set_title("ThinkPad Fan Control")
        header.set_title("ThinkPad Fan Control")
        header.set_subtitle("ThinkPad L14 Gen 2")

        # 2. Permission Banner (if read-only)
        self.perm_banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.perm_banner.get_style_context().add_class("perm-banner")
        
        perm_text = Gtk.Label(label="Read-Only: Speed control requires elevation.")
        self.perm_banner.pack_start(perm_text, False, False, 0)

        btn_unlock = Gtk.Button(label="Unlock")
        btn_unlock.get_style_context().add_class("btn-unlock")
        btn_unlock.connect("clicked", self._on_unlock_permissions)
        self.perm_banner.pack_end(btn_unlock, False, False, 0)

        root_vbox.pack_start(self.perm_banner, False, False, 0)

        # 3. ScrolledWindow Container for Stack Pages
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_overlay_scrolling(True)
        root_vbox.pack_start(scrolled, True, True, 0)

        # 4. Add Stack Pages
        self.stack = Gtk.Stack()
        self.stack.set_hhomogeneous(False)
        self.stack.set_vhomogeneous(False)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(160)
        self.stack.connect("notify::visible-child-name", self._on_stack_page_changed)

        # Page 1: Controls
        self.dashboard_view = DashboardView(
            on_level_selected=self._on_level_command,
            on_open_cleaning=self._open_dust_purge_dialog,
            on_open_sensors=self._open_sensor_dialog
        )
        self.stack.add_titled(self.dashboard_view, "controls", "Controls")

        # Page 2: Smart Curves
        self.curves_view = CurvesView(
            curve_engine=self.curve_engine,
            on_profile_applied=self._on_curve_profile_changed
        )
        self.stack.add_titled(self.curves_view, "curves", "Curves")

        # Page 3: Dust Cleaning Routine
        self.cleaning_view = CleaningView(
            controller=self.controller,
            on_purge_complete=self._on_purge_completed
        )
        self.stack.add_titled(self.cleaning_view, "cleaning", "Cleaning")

        # Page 4: Multi-Sensor Hardware Diagnostics
        self.sensors_view = SensorsView()
        self.stack.add_titled(self.sensors_view, "sensors", "Sensors")

        scrolled.add(self.stack)

        # 5. Libadwaita Bottom Navigation Bar (Lower Bar - Blur my Shell style)
        self.bottom_bar = self._build_bottom_bar()
        root_vbox.pack_start(self.bottom_bar, False, False, 0)
        self.switcher = self.bottom_bar
        self._update_nav_selection("controls")

        # Compatibility references
        self.gauge = self.dashboard_view.gauge
        self.control_panel = self.dashboard_view
        self.sensor_matrix = SensorMatrixWidget()
        self.sensor_dialog = None

        self._update_perm_banner()

    def _build_bottom_bar(self) -> Gtk.Box:
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bar.get_style_context().add_class("bottom-switcher-bar")
        bar.set_homogeneous(True)

        self.nav_buttons = {}
        tabs = [
            ("controls", "Controls", "speedometer-symbolic"),
            ("curves", "Curves", "utilities-system-monitor-symbolic"),
            ("cleaning", "Cleaning", "weather-windy-symbolic"),
            ("sensors", "Sensors", "computer-symbolic"),
        ]

        for page_name, label_text, icon_name in tabs:
            btn = Gtk.Button()
            btn.get_style_context().add_class("bottom-tab-btn")

            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            box.set_valign(Gtk.Align.CENTER)
            box.set_halign(Gtk.Align.CENTER)

            img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            img.set_pixel_size(18)

            lbl = Gtk.Label(label=label_text)
            lbl.get_style_context().add_class("bottom-tab-label")

            box.pack_start(img, False, False, 0)
            box.pack_start(lbl, False, False, 0)
            btn.add(box)

            btn.connect("clicked", lambda w, p=page_name: self.switch_to_page(p))
            bar.pack_start(btn, True, True, 0)
            self.nav_buttons[page_name] = (btn, img, lbl)

        return bar

    def switch_to_page(self, page_name: str):
        """Switches visible stack child and updates navigation selection."""
        self.stack.set_visible_child_name(page_name)
        self._update_nav_selection(page_name)

    def _on_stack_page_changed(self, stack, pspec):
        visible = stack.get_visible_child_name()
        if visible:
            self._update_nav_selection(visible)

    def _update_nav_selection(self, page_name: str):
        if not hasattr(self, "nav_buttons"):
            return
        for name, (btn, img, lbl) in self.nav_buttons.items():
            if name == page_name:
                btn.get_style_context().add_class("bottom-tab-btn-active")
                lbl.get_style_context().add_class("bottom-tab-label-active")
            else:
                btn.get_style_context().remove_class("bottom-tab-btn-active")
                lbl.get_style_context().remove_class("bottom-tab-label-active")

    def _show_about_dialog(self):
        dialog = Gtk.AboutDialog(transient_for=self, modal=True)
        dialog.set_program_name("ThinkPad Fan Control")
        dialog.set_version("2.1.0")
        dialog.set_comments("Libadwaita Thermal & Acoustic Fan Controller tailored for Lenovo ThinkPad hardware.")
        dialog.set_copyright("© 2026 ThinkPad Linux Community")
        dialog.set_license_type(Gtk.License.GPL_3_0)
        dialog.set_website("https://github.com")
        dialog.set_website_label("GitHub Repository")
        dialog.run()
        dialog.destroy()

    def _open_dust_purge_dialog(self):
        """Switches stack to Cleaning tab and presents window."""
        self.stack.set_visible_child_name("cleaning")
        self.present()

    def _open_curve_dialog(self):
        """Switches stack to Curves tab and presents window."""
        self.stack.set_visible_child_name("curves")
        self.present()

    def _open_sensor_dialog(self):
        """Switches stack to Sensors tab and presents window."""
        self.stack.set_visible_child_name("sensors")
        self.present()

    def _on_curve_profile_changed(self, profile_name: str):
        self._on_sensor_tick()

    def _on_purge_completed(self):
        self._on_sensor_tick()

    def show_all(self):
        super().show_all()
        self._update_perm_banner()

    def _update_perm_banner(self):
        is_writable = self.controller.is_writable()
        if is_writable:
            self.perm_banner.hide()
        else:
            self.perm_banner.show_all()
        self.dashboard_view.set_sensitive(is_writable)
        self.cleaning_view.btn_start.set_sensitive(is_writable)

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
        if not self.is_visible():
            return True
        if hasattr(self, "dashboard_view") and hasattr(self.dashboard_view, "gauge"):
            if self.dashboard_view.gauge.is_animating():
                self.dashboard_view.gauge.update_animation_step()
        return True

    def _on_sensor_tick(self) -> bool:
        temp_c = self.controller.get_cpu_temp()
        status = self.controller.get_fan_status()
        rpm = status.get("speed", 0)
        level_str = status.get("level", "auto")

        # 1. Read Hardware Multi-Sensors & Power State
        sensors = self.controller.get_all_sensors()
        power = self.controller.get_power_state()

        # Update Views
        if hasattr(self, "sensors_view"):
            self.sensors_view.update_telemetry(sensors, power)

        if hasattr(self, "cleaning_view"):
            self.cleaning_view.update_cpu_temp(temp_c)

        # 2. Power Transition Check
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
            profile_display = f"Curve: {self.curve_engine.active_profile.upper()}"
        else:
            profile_display = "Auto (BIOS)"

        # 4. Thermal Warning Notification (>82°C, debounced to 60s cooldown)
        if temp_c is not None and temp_c >= 82.0:
            self.notifier.send(
                "High Temperature Alert",
                f"CPU temperature reached {temp_c:.1f}°C! Fan cooling recommended.",
                urgency="critical",
                alert_type="thermal_high"
            )

        # 5. Update Dashboard View
        if hasattr(self, "dashboard_view"):
            self.dashboard_view.update_telemetry(temp_c, rpm, level_str, power, profile_display)

        # 6. Sync Tray
        if hasattr(self, "tray"):
            self.tray.update_telemetry(temp_c, rpm, level_str)

        return True

    def _on_emergency_thermal_trip(self, temp_c: float):
        """Called when SafetyGuard trips the 85°C fail-safe."""
        self.stack.set_visible_child_name("controls")
        self.dashboard_view.val_mode_title.set_text("EMERGENCY")
        self.dashboard_view.badge_mode.set_text("TRIP 85°C")
        self.dashboard_view.badge_mode.get_style_context().remove_class("badge-pill-emerald")
        self.dashboard_view.badge_mode.get_style_context().add_class("badge-hot")
        self.present()

    def _toggle_visibility(self):
        if self.is_visible():
            self.hide()
        else:
            self.present()

    def _on_close_event(self, widget, event):
        """Minimizes to system tray instead of destroying the application."""
        self.hide()
        if not self._has_shown_tray_hint:
            self._has_shown_tray_hint = True
            self.notifier.send(
                "Running in Background",
                "ThinkPad Fan Control is still active in the system tray.",
                urgency="low",
                alert_type="tray_hint"
            )
        return True

    def _on_app_quit(self):
        """Fully exits the application, restoring BIOS fan control."""
        try:
            self.safety.cleanup()
        except Exception:
            pass
        Gtk.main_quit()
