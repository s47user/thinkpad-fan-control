import math
import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf, GLib

class CircularGauge(Gtk.Image):
    """
    Modern Libadwaita Circular Fan Progress Meter.
    Renders a glowing radial progress ring with live RPM readout in the center.
    """

    def __init__(self, size: int = 88, max_rpm: int = 5500):
        super().__init__()
        self.size = size
        self.max_rpm = max_rpm
        self.current_rpm = 0.0
        self.target_rpm = 0.0
        self._is_animating = False

        self.set_size_request(size, size)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.connect("size-allocate", self._on_size_allocate)
        self.redraw()

    def _on_size_allocate(self, widget, alloc):
        new_size = min(alloc.width, alloc.height)
        if new_size > 40 and abs(new_size - self.size) > 2:
            self.size = new_size
            self.redraw()

    def set_target_rpm(self, rpm: float):
        new_target = float(max(0, min(6500, rpm)))
        if abs(new_target - self.target_rpm) > 1.0:
            self.target_rpm = new_target
            self._is_animating = True
            self.redraw()

    def is_animating(self) -> bool:
        return self._is_animating

    def update_animation_step(self) -> bool:
        """Smoothly lerps current_rpm towards target_rpm."""
        if not self._is_animating:
            return False
        diff = self.target_rpm - self.current_rpm
        if abs(diff) > 1.0:
            self.current_rpm += diff * 0.18
            self.redraw()
            return True
        else:
            self.current_rpm = self.target_rpm
            self._is_animating = False
            self.redraw()
            return False

    def redraw(self):
        w = max(60, self.size)
        h = max(60, self.size)

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surf)

        # Transparent background
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        cx = w / 2.0
        cy = h / 2.0
        radius = min(cx, cy) - 6.0
        scale = max(0.6, min(1.3, radius / 36.0))

        # 1. Background Track Ring (GNOME subtle trough)
        cr.set_line_width(6.0 * scale)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.08)
        cr.arc(cx, cy, radius, 0, 2 * math.pi)
        cr.stroke()

        # 2. Active Progress Arc
        fraction = max(0.0, min(1.0, self.current_rpm / float(self.max_rpm)))
        start_angle = -math.pi / 2.0  # 12 o'clock

        if fraction > 0.01:
            sweep_angle = fraction * (2 * math.pi)
            end_angle = start_angle + sweep_angle

            # Standard GNOME Libadwaita color tokens
            if fraction < 0.40:
                # GNOME Green (#2ec27e)
                r, g, b = 0.180, 0.761, 0.494
            elif fraction < 0.75:
                # GNOME Blue (#3584e4)
                r, g, b = 0.208, 0.518, 0.894
            elif fraction < 0.90:
                # GNOME Amber (#e5a50a)
                r, g, b = 0.898, 0.647, 0.039
            else:
                # GNOME Red (#e01b24)
                r, g, b = 0.878, 0.106, 0.141

            # Subtle Outer Glow Pass
            cr.set_line_width(9.0 * scale)
            cr.set_source_rgba(r, g, b, 0.20)
            cr.arc(cx, cy, radius, start_angle, end_angle)
            cr.stroke()

            # Crisp Core Arc Pass
            cr.set_line_width(5.0 * scale)
            cr.set_source_rgba(r, g, b, 0.95)
            cr.arc(cx, cy, radius, start_angle, end_angle)
            cr.stroke()

        # 3. Center Numeric Readout
        rpm_val = int(round(self.current_rpm))
        rpm_str = f"{rpm_val:,}"

        # Font: Cantarell / Inter / Monospace
        cr.select_font_face("Cantarell", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(int(14.5 * scale))
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        ext = cr.text_extents(rpm_str)
        cr.move_to(cx - ext.width / 2.0 - ext.x_bearing, cy - (1.0 * scale))
        cr.show_text(rpm_str)

        # "RPM" Subtitle (GNOME Dim Label #9a9996)
        cr.select_font_face("Cantarell", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(int(9.0 * scale))
        cr.set_source_rgba(0.604, 0.600, 0.588, 1.0)
        ext_lbl = cr.text_extents("RPM")
        cr.move_to(cx - ext_lbl.width / 2.0 - ext_lbl.x_bearing, cy + (12.0 * scale))
        cr.show_text("RPM")

        # Convert Cairo ARGB32 (BGRA) to RGBA for GdkPixbuf
        raw_bytes = bytearray(surf.get_data())
        raw_bytes[0::4], raw_bytes[2::4] = raw_bytes[2::4], raw_bytes[0::4]

        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
            GLib.Bytes.new(raw_bytes),
            GdkPixbuf.Colorspace.RGB,
            True,
            8,
            w,
            h,
            surf.get_stride()
        )
        self.set_from_pixbuf(pixbuf)
