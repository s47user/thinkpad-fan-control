import cairo
import collections
import math
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf, GLib

HISTORY_SECONDS = 60

class LiveGraph(Gtk.Image):
    """
    Real-time 60-second scrolling telemetry graph.
    Plots CPU Temperature (°C) and Fan Speed (RPM) with 85°C safety trip line.
    Dynamically renders to allocated dimensions.
    """

    def __init__(self, min_width: int = 210, min_height: int = 65, history_len: int = HISTORY_SECONDS):
        super().__init__()
        self.min_width = min_width
        self.min_height = min_height
        self.width = min_width
        self.height = min_height
        self.history_len = history_len
        self.temp_history = collections.deque([48.0] * history_len, maxlen=history_len)
        self.rpm_history = collections.deque([3400] * history_len, maxlen=history_len)

        self.min_temp = 30.0
        self.max_temp = 95.0
        self.max_rpm = 5500.0

        self.set_size_request(min_width, min_height)
        self.set_hexpand(True)
        self.set_vexpand(True)
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

    def add_telemetry(self, temp_c: float, rpm: int):
        self.temp_history.append(float(temp_c))
        self.rpm_history.append(int(rpm))
        self.redraw()

    def redraw(self):
        w = self.width
        h = self.height

        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
        cr = cairo.Context(surf)

        # 1. Background Fill
        cr.set_source_rgba(0.08, 0.09, 0.12, 1.0) # #14161f
        cr.paint()

        is_compact = h < 110
        margin_left = 26.0 if is_compact else 34.0
        margin_right = 8.0 if is_compact else 14.0
        margin_top = 8.0 if is_compact else 16.0
        margin_bottom = 10.0 if is_compact else 20.0

        plot_w = max(10.0, w - margin_left - margin_right)
        plot_h = max(10.0, h - margin_top - margin_bottom)

        # Plot interior background (Deep Obsidian)
        cr.set_source_rgba(0.02, 0.03, 0.05, 1.0)
        cr.rectangle(margin_left, margin_top, plot_w, plot_h)
        cr.fill()

        # Vertical Time Grid Lines (Adaptive intervals across history)
        cr.set_line_width(0.8)
        cr.set_source_rgba(0.18, 0.22, 0.30, 0.25)
        num_v = max(4 if is_compact else 6, int(plot_w / 70.0))
        for t_step in range(1, num_v):
            vx = margin_left + (plot_w / float(num_v)) * t_step
            cr.move_to(vx, margin_top)
            cr.line_to(vx, margin_top + plot_h)
            cr.stroke()

        # 2. Horizontal Reference Lines & Labels
        axis_font_size = max(8, min(10, int(plot_h * 0.18))) if is_compact else max(9, min(12, int(plot_h * 0.024)))
        cr.select_font_face("Ubuntu Sans Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(axis_font_size)

        if plot_h > 240:
            temp_refs = [40.0, 50.0, 60.0, 70.0, 80.0, 85.0]
        elif plot_h > 100:
            temp_refs = [40.0, 55.0, 70.0, 85.0]
        elif plot_h > 50:
            temp_refs = [45.0, 65.0, 85.0]
        else:
            temp_refs = [50.0, 85.0]

        for temp_ref in temp_refs:
            y_norm = 1.0 - ((temp_ref - self.min_temp) / (self.max_temp - self.min_temp))
            y_pos = margin_top + y_norm * plot_h

            if temp_ref == 85.0:
                cr.set_dash([4.0, 3.0])
                cr.set_source_rgba(0.95, 0.25, 0.25, 0.85)
            else:
                cr.set_dash([])
                cr.set_source_rgba(0.18, 0.20, 0.26, 0.35)

            cr.move_to(margin_left, y_pos)
            cr.line_to(margin_left + plot_w, y_pos)
            cr.stroke()

            # Axis Label
            lbl_text = f"{int(temp_ref)}°"
            extents = cr.text_extents(lbl_text)
            if temp_ref == 85.0:
                cr.set_source_rgba(0.95, 0.35, 0.35, 0.95)
            else:
                cr.set_source_rgba(0.45, 0.47, 0.53, 0.9)
            cr.move_to(margin_left - extents.width - 6, y_pos + extents.height / 2.0)
            cr.show_text(lbl_text)

        cr.set_dash([])

        # 3. Draw Fan Speed Curve (Emerald Line with Dash Pattern)
        step_x = plot_w / float(self.history_len - 1)
        rpm_line_w = 1.2 if is_compact else max(1.8, min(3.0, plot_h * 0.005))
        cr.set_line_width(rpm_line_w)
        cr.set_dash([4.0, 2.0] if is_compact else [5.0, 2.5])
        cr.set_source_rgba(0.06, 0.73, 0.50, 0.90)

        last_rpm_x = margin_left
        last_rpm_y = margin_top + plot_h

        for i, rpm in enumerate(self.rpm_history):
            x = margin_left + i * step_x
            rpm_fraction = max(0.0, min(1.0, rpm / self.max_rpm))
            y = margin_top + plot_h - (rpm_fraction * plot_h)
            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
            last_rpm_x = x
            last_rpm_y = y
        cr.stroke()
        cr.set_dash([])

        # Small End-point Indicator Node on Fan Curve
        cr.set_source_rgba(0.06, 0.73, 0.50, 1.0)
        cr.arc(last_rpm_x, last_rpm_y, 2.0 if is_compact else max(2.5, min(5.0, plot_h * 0.007)), 0, 2 * math.pi)
        cr.fill()

        # 4. Draw CPU Temperature Curve (Cyan Waveform with Neon Bloom)
        cr.move_to(margin_left, margin_top + plot_h)

        last_temp_x = margin_left
        last_temp_y = margin_top + plot_h

        for i, temp in enumerate(self.temp_history):
            x = margin_left + i * step_x
            t_fraction = max(0.0, min(1.0, (temp - self.min_temp) / (self.max_temp - self.min_temp)))
            y = margin_top + plot_h - (t_fraction * plot_h)
            cr.line_to(x, y)
            last_temp_x = x
            last_temp_y = y

        cr.line_to(margin_left + plot_w, margin_top + plot_h)
        cr.close_path()

        # Gradient area fill
        gradient = cairo.LinearGradient(0, margin_top, 0, margin_top + plot_h)
        gradient.add_color_stop_rgba(0.0, 0.0, 0.88, 1.0, 0.28)
        gradient.add_color_stop_rgba(1.0, 0.0, 0.88, 1.0, 0.01)
        cr.set_source(gradient)
        cr.fill_preserve()

        # Pass 1: Neon Bloom Glow Pass
        cr.set_line_width(4.0 if is_compact else max(6.0, min(12.0, plot_h * 0.018)))
        cr.set_source_rgba(0.0, 0.88, 1.0, 0.20)
        cr.stroke_preserve()

        # Pass 2: Crisp Core Trace Line
        cr.set_line_width(1.6 if is_compact else max(2.0, min(4.0, plot_h * 0.006)))
        cr.set_source_rgba(0.0, 0.92, 1.0, 0.98)
        cr.stroke()

        # Small End-point Indicator Node on CPU Curve
        cr.set_source_rgba(0.0, 0.92, 1.0, 1.0)
        cr.arc(last_temp_x, last_temp_y, max(3.0, min(6.0, plot_h * 0.009)), 0, 2 * math.pi)
        cr.fill()

        # Border around oscilloscope frame
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.20, 0.24, 0.32, 0.7)
        cr.rectangle(margin_left, margin_top, plot_w, plot_h)
        cr.stroke()

        # Fast BGRA -> RGBA in place
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
