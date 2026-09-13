import math
import cairo
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf, GLib

class VisualGauge(Gtk.Image):
    """
    Futuristic Machined Concentric Turbine Tachometer.
    Inspired by ThinkPad's 11-blade aerodynamic impeller and TrackPoint core.
    Dynamically responds to container resizing.
    """

    def __init__(self, min_width: int = 175, min_height: int = 145, max_rpm: int = 5500):
        super().__init__()
        self.min_width = min_width
        self.min_height = min_height
        self.width = min_width
        self.height = min_height
        self.max_rpm = max_rpm
        self.current_rpm = 0.0
        self.target_rpm = 0.0
        self.level_label = "Auto (BIOS)"
        self._is_animating = False

        self.set_size_request(min_width, min_height)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.connect("size-allocate", self._on_size_allocate)
        self.redraw()

    def do_get_preferred_width(self):
        return (self.min_width, self.min_width)

    def do_get_preferred_height(self):
        return (self.min_height, self.min_height)

    def _on_size_allocate(self, widget, alloc):
        w = max(self.min_width, alloc.width)
        h = max(self.min_height, alloc.height)
        if abs(w - self.width) > 2 or abs(h - self.height) > 2:
            self.width = w
            self.height = h
            self.redraw()

    def is_animating(self) -> bool:
        return self._is_animating

    def set_target_rpm(self, rpm: float, level_str: str = ""):
        new_target = float(max(0, min(6500, rpm)))
        if level_str:
            self.level_label = level_str
        if abs(new_target - self.target_rpm) > 1.0:
            self.target_rpm = new_target
            self._is_animating = True
            self.redraw()

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
        w = self.width
        h = self.height

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surf)

        # Transparent background
        cr.set_source_rgba(0, 0, 0, 0)
        cr.paint()

        cx = w / 2.0
        cy = h / 2.0 + 2.0
        radius = min(w * 0.38, h * 0.36, 125.0)
        scale = max(0.55, min(1.30, radius / 95.0))

        start_angle = math.pi * 0.75
        end_angle = math.pi * 2.25
        total_angle = end_angle - start_angle

        # 1. Outer Concentric Turbine Shroud (Logo Inspired)
        chamber_r = radius + (14.0 * scale)
        cr.set_source_rgba(0.05, 0.06, 0.08, 1.0)
        cr.arc(cx, cy, chamber_r + (4.0 * scale), 0, 2 * math.pi)
        cr.fill()

        # Outer Machined Chamfer Rim
        cr.set_line_width(1.5 * scale)
        cr.set_source_rgba(0.18, 0.20, 0.26, 0.7)
        cr.arc(cx, cy, chamber_r + (4.0 * scale), 0, 2 * math.pi)
        cr.stroke()

        # 2. Perimeter Stator Ticks (36 Ticks around full circumference)
        fraction = max(0.0, min(1.0, self.current_rpm / float(self.max_rpm)))
        num_stator_ticks = 36
        for i in range(num_stator_ticks):
            tick_angle = (2 * math.pi / num_stator_ticks) * i
            tick_pct = i / float(num_stator_ticks)

            t_inner = chamber_r + 1.0
            t_outer = chamber_r + ((4.5 if i % 3 == 0 else 3.0) * scale)

            x1 = cx + math.cos(tick_angle) * t_inner
            y1 = cy + math.sin(tick_angle) * t_inner
            x2 = cx + math.cos(tick_angle) * t_outer
            y2 = cy + math.sin(tick_angle) * t_outer

            cr.set_line_width((1.2 if i % 3 == 0 else 0.8) * scale)
            # Stator illumination follows current RPM fraction
            if tick_pct <= fraction and fraction > 0.05:
                if tick_pct < 0.45:
                    cr.set_source_rgba(0.0, 0.82, 1.0, 0.9)   # Cyan
                elif tick_pct < 0.8:
                    cr.set_source_rgba(0.06, 0.73, 0.50, 0.9)  # Emerald
                else:
                    cr.set_source_rgba(0.89, 0.14, 0.10, 0.95) # Crimson
            else:
                cr.set_source_rgba(0.20, 0.23, 0.30, 0.35)

            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()

        # 3. Background Gauge Arc Track
        cr.set_line_width(10.0 * scale)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_source_rgba(0.10, 0.11, 0.15, 1.0)
        cr.arc(cx, cy, radius, start_angle, end_angle)
        cr.stroke()

        # 4. Active Airflow Velocity Sweep (with Neon Bloom Pass)
        if fraction > 0.01:
            active_angle = start_angle + (total_angle * fraction)
            if fraction < 0.38:
                r, g, b = 0.0, 0.82, 1.0  # Cyan
            elif fraction < 0.72:
                r, g, b = 0.06, 0.73, 0.50 # Emerald
            elif fraction < 0.88:
                r, g, b = 0.96, 0.62, 0.04 # Amber
            else:
                r, g, b = 0.89, 0.14, 0.10 # Crimson

            # Translucent Neon Bloom Pass
            cr.set_line_width(16.0 * scale)
            cr.set_source_rgba(r, g, b, 0.22)
            cr.arc(cx, cy, radius, start_angle, active_angle)
            cr.stroke()

            # Crisp Core Trace Pass
            cr.set_line_width(9.0 * scale)
            cr.set_source_rgba(r, g, b, 0.98)
            cr.arc(cx, cy, radius, start_angle, active_angle)
            cr.stroke()

        # 5. Radial Scale Markings (Internal Ticks)
        num_ticks = 10
        for i in range(num_ticks + 1):
            t_pct = i / float(num_ticks)
            angle = start_angle + (total_angle * t_pct)
            is_major = (i % 2 == 0)

            inner_r = radius - ((12.0 if is_major else 6.0) * scale)
            outer_r = radius - (4.0 * scale)

            x1 = cx + math.cos(angle) * inner_r
            y1 = cy + math.sin(angle) * inner_r
            x2 = cx + math.cos(angle) * outer_r
            y2 = cy + math.sin(angle) * outer_r

            cr.set_line_width((1.4 if is_major else 0.8) * scale)
            if is_major:
                cr.set_source_rgba(0.42, 0.46, 0.54, 0.75)
            else:
                cr.set_source_rgba(0.22, 0.25, 0.32, 0.45)
            cr.move_to(x1, y1)
            cr.line_to(x2, y2)
            cr.stroke()

        # 6. Center Metallic Hub with Ruby Core Dome
        hub_r = radius - (16.0 * scale)
        # Bezel rim
        cr.set_source_rgba(0.12, 0.14, 0.19, 1.0)
        cr.arc(cx, cy, hub_r, 0, 2 * math.pi)
        cr.fill()

        cr.set_line_width(1.2 * scale)
        cr.set_source_rgba(0.24, 0.27, 0.35, 0.8)
        cr.arc(cx, cy, hub_r, 0, 2 * math.pi)
        cr.stroke()

        # Inner dark core plate
        cr.set_source_rgba(0.06, 0.07, 0.10, 1.0)
        cr.arc(cx, cy, hub_r - (2.5 * scale), 0, 2 * math.pi)
        cr.fill()

        # Center Ruby TrackPoint Core Indicator Dome
        ruby_y = cy - (22.0 * scale)
        # Subtle glow
        cr.set_source_rgba(0.89, 0.14, 0.10, 0.35)
        cr.arc(cx, ruby_y, 5.0 * scale, 0, 2 * math.pi)
        cr.fill()
        # Solid dome
        cr.set_source_rgba(0.89, 0.14, 0.10, 1.0)
        cr.arc(cx, ruby_y, 3.0 * scale, 0, 2 * math.pi)
        cr.fill()

        # Digital Numerical RPM Readout
        rpm_val = int(round(self.current_rpm))
        rpm_str = f"{rpm_val:,}"

        cr.select_font_face("Ubuntu Sans Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(int(21 * scale))
        extents = cr.text_extents(rpm_str)
        cr.set_source_rgba(0.98, 0.98, 0.98, 1.0)
        cr.move_to(cx - extents.width / 2.0 - extents.x_bearing, cy - (3.0 * scale))
        cr.show_text(rpm_str)

        # "RPM" Label
        cr.select_font_face("Ubuntu Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(int(9 * scale))
        extents_lbl = cr.text_extents("RPM")
        cr.set_source_rgba(0.48, 0.50, 0.56, 1.0)
        cr.move_to(cx - extents_lbl.width / 2.0 - extents_lbl.x_bearing, cy + (12.0 * scale))
        cr.show_text("RPM")

        # Percentage readout
        pct_val = int(round(fraction * 100))
        pct_str = f"{pct_val}% OF PEAK"
        cr.select_font_face("Ubuntu Sans Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(int(8.5 * scale))
        extents_pct = cr.text_extents(pct_str)
        if fraction < 0.4:
            cr.set_source_rgba(0.0, 0.82, 1.0, 0.9)  # Cyan
        elif fraction < 0.75:
            cr.set_source_rgba(0.06, 0.73, 0.50, 0.9) # Emerald
        else:
            cr.set_source_rgba(0.89, 0.14, 0.10, 0.95) # Red
        cr.move_to(cx - extents_pct.width / 2.0 - extents_pct.x_bearing, cy + (24.0 * scale))
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
