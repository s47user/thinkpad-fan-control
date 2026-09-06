import cairo
import collections
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gtk, GdkPixbuf, GLib

HISTORY_SECONDS = 60

class LiveGraph(Gtk.Image):
    """
    Real-time 60-second scrolling telemetry graph.
    Plots CPU Temperature (°C) and Fan Speed (RPM) with 85°C safety trip line.
    """

    def __init__(self, width: int = 420, height: int = 180, history_len: int = HISTORY_SECONDS):
        super().__init__()
        self.width = width
        self.height = height
        self.history_len = history_len
        self.temp_history = collections.deque([48.0] * history_len, maxlen=history_len)
        self.rpm_history = collections.deque([3400] * history_len, maxlen=history_len)

        self.min_temp = 30.0
        self.max_temp = 95.0
        self.max_rpm = 5500.0

        self.set_size_request(width, height)
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

        margin_left = 34.0
        margin_right = 14.0
        margin_top = 16.0
        margin_bottom = 20.0

        plot_w = max(10.0, w - margin_left - margin_right)
        plot_h = max(10.0, h - margin_top - margin_bottom)

        # Plot interior background
        cr.set_source_rgba(0.04, 0.05, 0.07, 1.0)
        cr.rectangle(margin_left, margin_top, plot_w, plot_h)
        cr.fill()

        # 2. Horizontal Reference Lines & Labels
        cr.select_font_face("Ubuntu Sans Mono", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(9)

        for temp_ref in [40.0, 60.0, 85.0]:
            y_norm = 1.0 - ((temp_ref - self.min_temp) / (self.max_temp - self.min_temp))
            y_pos = margin_top + y_norm * plot_h

            if temp_ref == 85.0:
                cr.set_dash([4.0, 3.0])
                cr.set_source_rgba(0.95, 0.25, 0.25, 0.75)
            else:
                cr.set_dash([])
                cr.set_source_rgba(0.20, 0.22, 0.28, 0.4)

            cr.move_to(margin_left, y_pos)
            cr.line_to(margin_left + plot_w, y_pos)
            cr.stroke()

            # Axis Label
            lbl_text = f"{int(temp_ref)}°"
            extents = cr.text_extents(lbl_text)
            if temp_ref == 85.0:
                cr.set_source_rgba(0.95, 0.35, 0.35, 0.9)
            else:
                cr.set_source_rgba(0.45, 0.47, 0.53, 0.9)
            cr.move_to(margin_left - extents.width - 6, y_pos + extents.height / 2.0)
            cr.show_text(lbl_text)

        cr.set_dash([])

        # 3. Draw Fan Speed Curve (Emerald Line)
        step_x = plot_w / float(self.history_len - 1)
        cr.set_line_width(1.8)
        cr.set_source_rgba(0.06, 0.73, 0.50, 0.85)

        for i, rpm in enumerate(self.rpm_history):
            x = margin_left + i * step_x
            rpm_fraction = max(0.0, min(1.0, rpm / self.max_rpm))
            y = margin_top + plot_h - (rpm_fraction * plot_h)
            if i == 0:
                cr.move_to(x, y)
            else:
                cr.line_to(x, y)
        cr.stroke()

        # 4. Draw CPU Temperature Curve (Cyan Line + Area Fill)
        cr.move_to(margin_left, margin_top + plot_h)

        for i, temp in enumerate(self.temp_history):
            x = margin_left + i * step_x
            t_fraction = max(0.0, min(1.0, (temp - self.min_temp) / (self.max_temp - self.min_temp)))
            y = margin_top + plot_h - (t_fraction * plot_h)
            cr.line_to(x, y)

        cr.line_to(margin_left + plot_w, margin_top + plot_h)
        cr.close_path()

        # Gradient area fill
        gradient = cairo.LinearGradient(0, margin_top, 0, margin_top + plot_h)
        gradient.add_color_stop_rgba(0.0, 0.0, 0.82, 1.0, 0.25)
        gradient.add_color_stop_rgba(1.0, 0.0, 0.82, 1.0, 0.01)
        cr.set_source(gradient)
        cr.fill_preserve()

        # Stroke line
        cr.set_line_width(2.0)
        cr.set_source_rgba(0.0, 0.82, 1.0, 0.95)
        cr.stroke()

        # Border around plot
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.18, 0.20, 0.26, 0.6)
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
