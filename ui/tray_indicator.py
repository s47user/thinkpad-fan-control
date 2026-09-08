import os
from typing import Callable, Optional
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

_HAS_INDICATOR = False
try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
    _HAS_INDICATOR = True
except Exception:
    try:
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3 as AppIndicator
        _HAS_INDICATOR = True
    except Exception:
        _HAS_INDICATOR = False

class TrayIndicator:
    """
    Ayatana / AppIndicator top panel tray widget.
    Gracefully falls back if gir1.2-ayatanaappindicator3-0.1 is not installed.
    """

    def __init__(
        self,
        on_toggle_window: Callable[[], None],
        on_select_preset: Callable[[str], None],
        on_quit: Callable[[], None],
        on_open_dust_purge: Optional[Callable[[], None]] = None,
        on_open_curve_dialog: Optional[Callable[[], None]] = None
    ):
        self.on_toggle_window = on_toggle_window
        self.on_select_preset = on_select_preset
        self.on_quit = on_quit
        self.on_open_dust_purge = on_open_dust_purge
        self.on_open_curve_dialog = on_open_curve_dialog
        self.indicator = None
        self.is_available = _HAS_INDICATOR

        if self.is_available:
            try:
                icon_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "assets", "icons", "thinkpad-fan.svg"
                )
                icon_name = icon_path if os.path.exists(icon_path) else "preferences-system-performance"

                self.indicator = AppIndicator.Indicator.new(
                    "thinkpad-fan-control",
                    icon_name,
                    AppIndicator.IndicatorCategory.HARDWARE
                )
                self.indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
                self._build_menu()
            except Exception as e:
                print(f"Failed to initialize AppIndicator: {e}")
                self.is_available = False

    def _build_menu(self):
        menu = Gtk.Menu()

        item_show = Gtk.MenuItem(label="Open Fan Control Window")
        item_show.connect("activate", lambda w: self.on_toggle_window())
        menu.append(item_show)

        if self.on_open_dust_purge or self.on_open_curve_dialog:
            menu.append(Gtk.SeparatorMenuItem())

            if self.on_open_dust_purge:
                item_purge = Gtk.MenuItem(label="Start Fan Dust Purge...")
                item_purge.connect("activate", lambda w: self.on_open_dust_purge())
                menu.append(item_purge)

            if self.on_open_curve_dialog:
                item_curve = Gtk.MenuItem(label="Smart Curve Profiles...")
                item_curve.connect("activate", lambda w: self.on_open_curve_dialog())
                menu.append(item_curve)

        menu.append(Gtk.SeparatorMenuItem())

        item_auto = Gtk.MenuItem(label="Auto (BIOS)")
        item_auto.connect("activate", lambda w: self.on_select_preset("auto"))
        menu.append(item_auto)

        item_silent = Gtk.MenuItem(label="Silent (Level 1)")
        item_silent.connect("activate", lambda w: self.on_select_preset("1"))
        menu.append(item_silent)

        item_balanced = Gtk.MenuItem(label="Balanced (Level 4)")
        item_balanced.connect("activate", lambda w: self.on_select_preset("4"))
        menu.append(item_balanced)

        item_turbo = Gtk.MenuItem(label="Turbo / Max (Disengaged)")
        item_turbo.connect("activate", lambda w: self.on_select_preset("disengaged"))
        menu.append(item_turbo)

        menu.append(Gtk.SeparatorMenuItem())

        item_quit = Gtk.MenuItem(label="Quit (Restore Auto)")
        item_quit.connect("activate", lambda w: self.on_quit())
        menu.append(item_quit)

        menu.show_all()
        self.indicator.set_menu(menu)

    def update_telemetry(self, temp_c: Optional[float], rpm: int, level_str: str):
        if not self.is_available or not self.indicator:
            return
        temp_str = f"{int(round(temp_c))}°C" if temp_c is not None else "--°C"
        label_text = f"{temp_str} | {rpm:,} RPM [{level_str}]"
        self.indicator.set_label(label_text, "99°C | 9999 RPM [disengaged]")
