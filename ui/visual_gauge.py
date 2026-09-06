import math
import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf, GLib

class VisualGauge(Gtk.Image):
    """
    Precision circular speedometer gauge drawn with Cairo.
    Displays fan speed from 0 to 5,500 RPM with dynamic color transitions.
    """

    def __init__(self, width: int = 240, height: int = 240, max_rpm: int = 5500):
        super().__init__()
        self.width = width
        self.height = height
        self.max_rpm = max_rpm
        self.current_rpm = 0.0
        self.target_rpm = 0.0
        self.level_label = "Auto (BIOS)"

        self.set_size_request(width, height)
        self.redraw()

    def set_target_rpm(self, rpm: float, level_str: str = ""):
        self.target_rpm = float(max(0, min(6500, rpm)))
        if level_str:
            self.level_label = level_str
        self.redraw()

    def update_animation_step(self) -> bool:
        """Smoothly lerps current_rpm towards target_rpm."""
        diff = self.target_rpm - self.current_rpm
        if abs(diff) > 1.0:
            self.current_rpm += diff * 0.18
            self.redraw()
            return True
        else:
            if self.current_rpm != self.target_rpm:
                self.current_rpm = self.target_rpm
                self.redraw()
            return False

    def redraw(self):
        w = self.width
        h = self.height

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surf)

        # Transparent background
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        cx = w / 2.0
        cy = h / 2.0 + 8.0
        radius = min(w, h) * 0.38

        start_angle = math.pi * 0.75
        end_angle = math.pi * 2.25
        total_angle = end_angle - start_angle

        # 1. Background Arc Track
        cr.set_line_width(12.0)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_source_rgba(0.11, 0.12, 0.16, 1.0) # refined dark zinc track
        cr.arc(cx, cy, radius, start_angle, end_angle)
        cr.stroke()

        # 2. Active RPM Arc
        fraction = max(0.0, min(1.0, self.current_rpm / float(self.max_rpm)))
        if fraction > 0.01:
            active_angle = start_angle + (total_angle * fraction)
            if fraction < 0.4:
                r, g, b = 0.0, 0.82, 1.0 # Cyan
            elif fraction < 0.7:
                r, g, b = 0.06, 0.73, 0.50 # Emerald
            elif fraction < 0.88:
                r, g, b = 0.96, 0.62, 0.04 # Amber
            else:
                r, g, b = 0.89, 0.14, 0.10 # ThinkPad Red

            cr.set_source_rgba(r, g, b, 0.95)
            cr.set_line_width(12.0)
            cr.arc(cx, cy, radius, start_angle, active_angle)
            cr.stroke()

        # 3. Radial Tick Marks
        num_ticks = 10
        for i in range(num_ticks + 1):
            t_pct = i / float(num_ticks)
            angle = start_angle + (total_angle * t_pct)
            is_major = (i % 2 == 0)

            inner_r = radius - (13 if is_major else 7)
            outer_r = radius - 5

            x1 = cx + math.cos(angle) * inner_r
            y1 = cy + math.sin(angle) * inner_r
            x2 = cx + math.cos(angle) * outer_r
            y2 = cy + math.sin(angle) * outer_r

            cr.set_line_width(1.5 if is_major else 0.8)
            if is_major:
                cr.set_source_rgba(0.45, 0.47, 0.53, 0.7)
            else:
                cr.set_source_rgba(0.24, 0.26, 0.32, 0.4)
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()

        # 4. Center Digital RPM Readout
        rpm_val = int(round(self.current_rpm))
        rpm_str = f"{rpm_val:,}"

        cr.select_font_face("Ubuntu Sans Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(24)
        extents = cr.text_extents(rpm_str)
        cr.set_source_rgba(0.98, 0.98, 0.98, 1.0)
        cr.move_to(cx - extents.width / 2.0 - extents.x_bearing, cy - 8)
        cr.show_text(rpm_str)

        # "RPM" Label
        cr.select_font_face("Ubuntu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(10)
        extents_lbl = cr.text_extents("RPM")
        cr.set_source_rgba(0.48, 0.50, 0.56, 1.0)
        cr.move_to(cx - extents_lbl.width / 2.0 - extents_lbl.x_bearing, cy + 10)
        cr.show_text("RPM")

        # Percentage
        pct_val = int(round(fraction * 100))
        pct_str = f"{pct_val}% of Max"
        cr.select_font_face("Ubuntu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(9)
        extents_pct = cr.text_extents(pct_str)
        cr.set_source_rgba(0.38, 0.40, 0.46, 1.0)
        cr.move_to(cx - extents_pct.width / 2.0 - extents_pct.x_bearing, cy + 25)
        cr.show_text(pct_str)

        # Convert Cairo ARGB32 (BGRA in memory) to RGBA for GdkPixbuf
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
