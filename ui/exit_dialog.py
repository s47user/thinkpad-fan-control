import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk

RESPONSE_TRAY = 1
RESPONSE_QUIT = 2
RESPONSE_CANCEL = 3

EXIT_CSS = b"""
.exit-window {
    background-color: #242424;
    color: #ffffff;
    font-family: "Cantarell", "Inter", -apple-system, sans-serif;
    border-radius: 12px;
}

.exit-card {
    background-color: #303030;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 12px;
    padding: 14px 16px;
}

.exit-heading {
    font-size: 16px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.2px;
}

.exit-sub {
    font-size: 12px;
    color: #9a9996;
}

.exit-action-row {
    background-color: #363636;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 10px 14px;
    transition: background-color 150ms ease-in-out;
}

.exit-action-row:hover {
    background-color: #3d3d3d;
}

.exit-action-tray {
    border-color: rgba(53, 132, 228, 0.35);
}

.exit-action-tray:hover {
    background-color: rgba(53, 132, 228, 0.15);
    border-color: #3584e4;
}

.exit-action-quit {
    border-color: rgba(224, 27, 36, 0.30);
}

.exit-action-quit:hover {
    background-color: rgba(224, 27, 36, 0.15);
    border-color: #e01b24;
}

.action-title {
    font-size: 13px;
    font-weight: 700;
    color: #ffffff;
}

.action-sub {
    font-size: 11px;
    color: #9a9996;
}

.action-title-quit {
    color: #fca5a5;
}

.row-icon-plate-blue {
    background-color: rgba(53, 132, 228, 0.16);
    border-radius: 8px;
    min-width: 32px;
    min-height: 32px;
}

.row-icon-plate-red {
    background-color: rgba(224, 27, 36, 0.16);
    border-radius: 8px;
    min-width: 32px;
    min-height: 32px;
}

.chk-remember {
    font-size: 11.5px;
    color: #9a9996;
}

button.btn-cancel {
    background-image: none;
    background-color: #363636;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 6px;
    font-weight: 600;
    font-size: 12px;
    padding: 7px 18px;
}

button.btn-cancel:hover {
    background-image: none;
    background-color: #424242;
}
"""

class ExitConfirmationDialog(Gtk.Dialog):
    """
    GNOME Libadwaita modal dialog prompting whether to minimize
    to the system tray or cleanly terminate the application.
    """

    def __init__(self, parent_window: Gtk.Window, tray_available: bool = True):
        super().__init__(
            title="Exit Application",
            transient_for=parent_window,
            modal=True,
            destroy_with_parent=True
        )
        self.tray_available = tray_available
        self.remember_choice = False

        self.set_default_size(440, 360)
        self.set_resizable(False)
        self.get_style_context().add_class("exit-window")

        self._apply_css()
        self._build_ui()

    def _apply_css(self):
        screen = Gdk.Screen.get_default()
        if screen:
            provider = Gtk.CssProvider()
            provider.load_from_data(EXIT_CSS)
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _build_ui(self):
        content_area = self.get_content_area()
        content_area.set_spacing(12)
        content_area.set_margin_top(20)
        content_area.set_margin_bottom(16)
        content_area.set_margin_start(20)
        content_area.set_margin_end(20)

        # Header with app icon and title
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        icon_plate = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        icon_plate.get_style_context().add_class("row-icon-plate-blue")
        icon_plate.set_valign(Gtk.Align.CENTER)
        icon = Gtk.Image.new_from_icon_name("weather-windy-symbolic", Gtk.IconSize.LARGE_TOOLBAR)
        icon.set_pixel_size(20)
        icon_plate.pack_start(icon, True, True, 6)
        header_box.pack_start(icon_plate, False, False, 0)

        title_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        lbl_heading = Gtk.Label(label="Exit ThinkPad Fan Control?")
        lbl_heading.set_xalign(0.0)
        lbl_heading.get_style_context().add_class("exit-heading")
        title_vbox.pack_start(lbl_heading, False, False, 0)

        lbl_sub = Gtk.Label(
            label="Choose whether to keep fan automation running in the background top-bar tray, or completely exit."
        )
        lbl_sub.set_xalign(0.0)
        lbl_sub.set_line_wrap(True)
        lbl_sub.get_style_context().add_class("exit-sub")
        title_vbox.pack_start(lbl_sub, False, False, 0)

        header_box.pack_start(title_vbox, True, True, 0)
        content_area.pack_start(header_box, False, False, 0)

        # Choices Card
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("exit-card")

        # Choice 1: Minimize to Tray
        self.btn_tray = Gtk.Button()
        self.btn_tray.get_style_context().add_class("exit-action-row")
        self.btn_tray.get_style_context().add_class("exit-action-tray")

        box_t = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        plate_t = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        plate_t.get_style_context().add_class("row-icon-plate-blue")
        plate_t.set_valign(Gtk.Align.CENTER)
        icon_t = Gtk.Image.new_from_icon_name("go-down-symbolic", Gtk.IconSize.MENU)
        icon_t.set_pixel_size(16)
        plate_t.pack_start(icon_t, True, True, 6)
        box_t.pack_start(plate_t, False, False, 0)

        text_t = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_t = Gtk.Label(label="Minimize to System Tray")
        title_t.set_xalign(0.0)
        title_t.get_style_context().add_class("action-title")
        text_t.pack_start(title_t, False, False, 0)

        sub_t_text = (
            "Fan curves, telemetry, and safety watchdog remain active in your top panel."
            if self.tray_available else
            "System tray indicator is not available on this desktop session."
        )
        sub_t = Gtk.Label(label=sub_t_text)
        sub_t.set_xalign(0.0)
        sub_t.get_style_context().add_class("action-sub")
        text_t.pack_start(sub_t, False, False, 0)
        box_t.pack_start(text_t, True, True, 0)

        self.btn_tray.add(box_t)
        self.btn_tray.set_sensitive(self.tray_available)
        self.btn_tray.connect("clicked", lambda b: self.response(RESPONSE_TRAY))
        card.pack_start(self.btn_tray, False, False, 0)

        # Choice 2: Completely Quit
        self.btn_quit = Gtk.Button()
        self.btn_quit.get_style_context().add_class("exit-action-row")
        self.btn_quit.get_style_context().add_class("exit-action-quit")

        box_q = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        plate_q = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        plate_q.get_style_context().add_class("row-icon-plate-red")
        plate_q.set_valign(Gtk.Align.CENTER)
        icon_q = Gtk.Image.new_from_icon_name("application-exit-symbolic", Gtk.IconSize.MENU)
        icon_q.set_pixel_size(16)
        plate_q.pack_start(icon_q, True, True, 6)
        box_q.pack_start(plate_q, False, False, 0)

        text_q = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_q = Gtk.Label(label="Quit Application")
        title_q.set_xalign(0.0)
        title_q.get_style_context().add_class("action-title")
        title_q.get_style_context().add_class("action-title-quit")
        text_q.pack_start(title_q, False, False, 0)

        sub_q = Gtk.Label(label="Restores default BIOS auto control and terminates the process.")
        sub_q.set_xalign(0.0)
        sub_q.get_style_context().add_class("action-sub")
        text_q.pack_start(sub_q, False, False, 0)
        box_q.pack_start(text_q, True, True, 0)

        self.btn_quit.add(box_q)
        self.btn_quit.connect("clicked", lambda b: self.response(RESPONSE_QUIT))
        card.pack_start(self.btn_quit, False, False, 0)

        content_area.pack_start(card, False, False, 0)

        # Remember choice checkbox & Cancel button row
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        
        self.chk_remember = Gtk.CheckButton.new_with_label("Remember my choice and do not ask again")
        self.chk_remember.get_style_context().add_class("chk-remember")
        bottom_box.pack_start(self.chk_remember, True, True, 0)

        btn_cancel = Gtk.Button(label="Cancel")
        btn_cancel.get_style_context().add_class("btn-cancel")
        btn_cancel.connect("clicked", lambda b: self.response(RESPONSE_CANCEL))
        bottom_box.pack_end(btn_cancel, False, False, 0)

        content_area.pack_start(bottom_box, False, False, 0)

        self.show_all()

    def get_remember_choice(self) -> bool:
        return self.chk_remember.get_active()
