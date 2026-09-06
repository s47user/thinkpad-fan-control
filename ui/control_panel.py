import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from typing import Callable, Optional

class ControlPanel(Gtk.Box):
    """
    Control interface containing preset profile buttons and granular speed slider.
    """

    def __init__(
        self,
        on_level_selected: Callable[[str], None],
        on_open_curve_dialog: Optional[Callable[[], None]] = None,
        on_open_dust_purge: Optional[Callable[[], None]] = None
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.on_level_selected = on_level_selected
        self.on_open_curve_dialog = on_open_curve_dialog
        self.on_open_dust_purge = on_open_dust_purge
        self._updating_internally = False

        # 1. Preset Profiles Section
        preset_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl_title = Gtk.Label(label="FAN CONTROL PRESETS")
        lbl_title.get_style_context().add_class("section-title")
        preset_header.pack_start(lbl_title, False, False, 0)

        # Header Action Buttons: Smart Curve & Dust Purge
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        if self.on_open_dust_purge:
            btn_purge = Gtk.Button(label="🌪 Dust Purge")
            btn_purge.get_style_context().add_class("btn-purge-action")
            btn_purge.connect("clicked", lambda b: self.on_open_dust_purge())
            btn_box.pack_start(btn_purge, False, False, 0)

        if self.on_open_curve_dialog:
            btn_curve = Gtk.Button(label="⚙ Smart Curve")
            btn_curve.get_style_context().add_class("btn-curve-action")
            btn_curve.connect("clicked", lambda b: self.on_open_curve_dialog())
            btn_box.pack_start(btn_curve, False, False, 0)

        preset_header.pack_end(btn_box, False, False, 0)
        self.pack_start(preset_header, False, False, 0)

        # Preset Buttons Grid
        presets_grid = Gtk.Grid()
        presets_grid.set_column_spacing(10)
        presets_grid.set_row_spacing(10)
        presets_grid.set_column_homogeneous(True)

        self.btn_auto = self._create_preset_btn("Auto (BIOS)", "Default firmware curve", "auto", "emerald-dot")
        self.btn_silent = self._create_preset_btn("Silent", "Level 1 (~1900 RPM)", "1", "cyan-dot")
        self.btn_balanced = self._create_preset_btn("Balanced", "Level 4 (~3300 RPM)", "4", "amber-dot")
        self.btn_turbo = self._create_preset_btn("Turbo / Max", "Level 7 / Disengaged", "disengaged", "red-dot")

        presets_grid.attach(self.btn_auto, 0, 0, 1, 1)
        presets_grid.attach(self.btn_silent, 1, 0, 1, 1)
        presets_grid.attach(self.btn_balanced, 2, 0, 1, 1)
        presets_grid.attach(self.btn_turbo, 3, 0, 1, 1)
        self.pack_start(presets_grid, False, False, 0)

        # 2. Granular Slider Box
        slider_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        slider_card.get_style_context().add_class("slider-card")

        slider_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        slider_lbl = Gtk.Label(label="Manual Speed Stepper:")
        slider_lbl.get_style_context().add_class("control-label")
        slider_header.pack_start(slider_lbl, False, False, 0)

        self.slider_val_lbl = Gtk.Label(label="Auto (BIOS)")
        self.slider_val_lbl.get_style_context().add_class("badge-active")
        slider_header.pack_start(self.slider_val_lbl, False, False, 8)

        slider_hint = Gtk.Label(label="Levels 0 (Off) to 7 (Max) + Disengaged")
        slider_hint.get_style_context().add_class("text-muted")
        slider_header.pack_end(slider_hint, False, False, 0)
        slider_card.pack_start(slider_header, False, False, 0)

        # Slider: -1 = Auto, 0..7 = Levels, 8 = Disengaged
        self.adjustment = Gtk.Adjustment(value=-1, lower=-1, upper=8, step_increment=1, page_increment=1)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adjustment)
        self.scale.set_digits(0)
        self.scale.set_draw_value(False)
        self.scale.add_mark(-1, Gtk.PositionType.BOTTOM, "Auto")
        self.scale.add_mark(0, Gtk.PositionType.BOTTOM, "0 (Off)")
        self.scale.add_mark(1, Gtk.PositionType.BOTTOM, "1")
        self.scale.add_mark(2, Gtk.PositionType.BOTTOM, "2")
        self.scale.add_mark(3, Gtk.PositionType.BOTTOM, "3")
        self.scale.add_mark(4, Gtk.PositionType.BOTTOM, "4")
        self.scale.add_mark(5, Gtk.PositionType.BOTTOM, "5")
        self.scale.add_mark(6, Gtk.PositionType.BOTTOM, "6")
        self.scale.add_mark(7, Gtk.PositionType.BOTTOM, "7")
        self.scale.add_mark(8, Gtk.PositionType.BOTTOM, "Full")

        self.scale.connect("value-changed", self._on_slider_changed)
        slider_card.pack_start(self.scale, False, False, 4)

        self.pack_start(slider_card, False, False, 0)

    def _create_preset_btn(self, title: str, subtitle: str, level_val: str, dot_class: str) -> Gtk.Button:
        btn = Gtk.Button()
        btn.get_style_context().add_class("preset-btn")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        
        lbl_t = Gtk.Label(label=title)
        lbl_t.get_style_context().add_class("preset-title")
        top_row.pack_start(lbl_t, False, False, 0)

        dot = Gtk.Label(label="●")
        dot.get_style_context().add_class(dot_class)
        top_row.pack_end(dot, False, False, 0)
        box.pack_start(top_row, False, False, 0)

        lbl_s = Gtk.Label(label=subtitle)
        lbl_s.get_style_context().add_class("preset-sub")
        box.pack_start(lbl_s, False, False, 0)

        btn.add(box)
        btn.connect("clicked", lambda w: self._on_preset_clicked(level_val))
        return btn

    def _on_preset_clicked(self, level_val: str):
        self._updating_internally = True
        self._highlight_preset(level_val)
        if level_val == "auto":
            self.adjustment.set_value(-1)
            self.slider_val_lbl.set_text("Auto (BIOS)")
        elif level_val == "disengaged":
            self.adjustment.set_value(8)
            self.slider_val_lbl.set_text("Disengaged (Turbo)")
        else:
            try:
                val = int(level_val)
                self.adjustment.set_value(val)
                self.slider_val_lbl.set_text(f"Level {val}")
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
            self.slider_val_lbl.set_text("Auto (BIOS)")
        elif val == 8:
            level_str = "disengaged"
            self.slider_val_lbl.set_text("Disengaged (Turbo)")
        else:
            level_str = str(val)
            self.slider_val_lbl.set_text(f"Level {val}")

        self._highlight_preset(level_str)
        self.on_level_selected(level_str)

    def _highlight_preset(self, level_str: str):
        for btn in [self.btn_auto, self.btn_silent, self.btn_balanced, self.btn_turbo]:
            btn.get_style_context().remove_class("preset-active")

        if level_str == "auto":
            self.btn_auto.get_style_context().add_class("preset-active")
        elif level_str == "1":
            self.btn_silent.get_style_context().add_class("preset-active")
        elif level_str == "4":
            self.btn_balanced.get_style_context().add_class("preset-active")
        elif level_str in ["7", "disengaged"]:
            self.btn_turbo.get_style_context().add_class("preset-active")

    def sync_hardware_level(self, level_str: str):
        """Synchronizes the UI to reflect actual hardware level."""
        if self._updating_internally:
            return
        self._updating_internally = True
        level_str = str(level_str).lower()
        if level_str == "auto":
            self.adjustment.set_value(-1)
            self.slider_val_lbl.set_text("Auto (BIOS)")
        elif level_str in ["disengaged", "full-speed"]:
            self.adjustment.set_value(8)
            self.slider_val_lbl.set_text("Disengaged (Turbo)")
        else:
            try:
                val = int(level_str)
                self.adjustment.set_value(val)
                self.slider_val_lbl.set_text(f"Level {val}")
            except ValueError:
                pass
        self._highlight_preset(level_str)
        self._updating_internally = False
