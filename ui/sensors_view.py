import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from typing import Dict, Any, List, Optional
from .adw_clamp import AdwClamp

class SensorsView(Gtk.Box):
    """
    Modern Libadwaita Multi-Sensor Hardware Diagnostics view.
    Categorizes sensors into clear preference groups: CPU, Storage, EC Zones, and Power.
    """

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.clamp = AdwClamp(maximum_size=560)
        self.pack_start(self.clamp, True, True, 0)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.content_box.set_margin_top(12)
        self.content_box.set_margin_bottom(16)
        self.content_box.set_margin_start(16)
        self.content_box.set_margin_end(16)
        self.clamp.add(self.content_box)

        self.sensor_labels: Dict[str, Any] = {}
        self._build_ui()

    def _build_ui(self):
        # 1. CPU & COMPUTE CORES CARD
        cpu_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cpu_card.get_style_context().add_class("adw-card")

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_title = Gtk.Label(label="CPU THERMAL TELEMETRY (CORETEMP / K10TEMP)")
        lbl_title.get_style_context().add_class("adw-section-title")
        header.pack_start(lbl_title, False, False, 0)

        self.cpu_pkg_badge = Gtk.Label(label="COOL")
        self.cpu_pkg_badge.get_style_context().add_class("badge-cool")
        header.pack_end(self.cpu_pkg_badge, False, False, 0)
        cpu_card.pack_start(header, False, False, 0)

        # CPU Package Row
        row_pkg = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row_pkg.get_style_context().add_class("adw-row")

        icon_box_cpu = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        icon_box_cpu.get_style_context().add_class("row-icon-plate")
        icon_cpu = Gtk.Image.new_from_icon_name("utilities-system-monitor-symbolic", Gtk.IconSize.MENU)
        icon_cpu.set_pixel_size(16)
        icon_box_cpu.pack_start(icon_cpu, True, True, 0)
        row_pkg.pack_start(icon_box_cpu, False, False, 0)

        lbl_pkg = Gtk.Label(label="CPU Package (Die Core)")
        lbl_pkg.get_style_context().add_class("control-label")
        row_pkg.pack_start(lbl_pkg, False, False, 0)

        self.val_cpu_pkg = Gtk.Label(label="--.-°C")
        self.val_cpu_pkg.get_style_context().add_class("font-mono-num")
        row_pkg.pack_end(self.val_cpu_pkg, False, False, 0)
        cpu_card.pack_start(row_pkg, False, False, 0)

        # Individual Cores Container
        self.cores_box = Gtk.Grid()
        self.cores_box.set_column_spacing(8)
        self.cores_box.set_row_spacing(6)
        self.cores_box.set_column_homogeneous(True)
        cpu_card.pack_start(self.cores_box, False, False, 0)

        self.content_box.pack_start(cpu_card, False, False, 0)

        # 2. STORAGE & PERIPHERALS CARD
        storage_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        storage_card.get_style_context().add_class("adw-card")

        s_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_s_title = Gtk.Label(label="STORAGE & PERIPHERAL CONTROLLERS")
        lbl_s_title.get_style_context().add_class("adw-section-title")
        s_header.pack_start(lbl_s_title, False, False, 0)
        storage_card.pack_start(s_header, False, False, 0)

        self.storage_rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        storage_card.pack_start(self.storage_rows_box, False, False, 0)

        self.content_box.pack_start(storage_card, False, False, 0)

        # 3. CHASSIS & THINKPAD EC ZONES CARD
        ec_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        ec_card.get_style_context().add_class("adw-card")

        ec_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_ec_title = Gtk.Label(label="THINKPAD EC CHASSIS THERMAL ZONES")
        lbl_ec_title.get_style_context().add_class("adw-section-title")
        ec_header.pack_start(lbl_ec_title, False, False, 0)
        ec_card.pack_start(ec_header, False, False, 0)

        self.ec_rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        ec_card.pack_start(self.ec_rows_box, False, False, 0)

        self.content_box.pack_start(ec_card, False, False, 0)

        # 4. POWER & BATTERY SUBSYSTEM CARD
        pwr_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        pwr_card.get_style_context().add_class("adw-card")

        p_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        lbl_p_title = Gtk.Label(label="POWER SUBSYSTEM & BATTERY TELEMETRY")
        lbl_p_title.get_style_context().add_class("adw-section-title")
        p_header.pack_start(lbl_p_title, False, False, 0)
        pwr_card.pack_start(p_header, False, False, 0)

        pwr_grid = Gtk.Grid()
        pwr_grid.set_column_spacing(8)
        pwr_grid.set_row_spacing(6)
        pwr_grid.set_column_homogeneous(True)

        self.card_pwr_src = self._create_info_cell("POWER SOURCE", "AC Connected", "ac-adapter-symbolic")
        self.card_pwr_pct = self._create_info_cell("BATTERY LEVEL", "100% [Full]", "battery-symbolic")
        self.card_pwr_flow = self._create_info_cell("ENERGY FLOW", "Idle / 0.0W", "utilities-system-monitor-symbolic")
        self.card_pwr_stat = self._create_info_cell("HEALTH / STATE", "Good", "emblem-ok-symbolic")

        pwr_grid.attach(self.card_pwr_src[0], 0, 0, 1, 1)
        pwr_grid.attach(self.card_pwr_pct[0], 1, 0, 1, 1)
        pwr_grid.attach(self.card_pwr_flow[0], 0, 1, 1, 1)
        pwr_grid.attach(self.card_pwr_stat[0], 1, 1, 1, 1)
        pwr_card.pack_start(pwr_grid, False, False, 0)

        self.content_box.pack_start(pwr_card, False, False, 0)

    def _create_info_cell(self, title_str: str, val_str: str, icon_name: Optional[str] = None):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.get_style_context().add_class("adw-row")

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        icon_img = None
        if icon_name:
            icon_img = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            icon_img.set_pixel_size(14)
            top_row.pack_start(icon_img, False, False, 0)

        lbl_t = Gtk.Label(label=title_str)
        lbl_t.get_style_context().add_class("chip-title")
        lbl_t.set_xalign(0.0)
        top_row.pack_start(lbl_t, False, False, 0)
        box.pack_start(top_row, False, False, 0)

        lbl_v = Gtk.Label(label=val_str)
        lbl_v.get_style_context().add_class("control-label")
        lbl_v.set_xalign(0.0)
        box.pack_start(lbl_v, False, False, 0)
        return box, lbl_v, icon_img

    def update_telemetry(self, sensors: Dict[str, Any], power: Dict[str, Any]):
        """Called by main sensor tick with latest readings."""
        # 1. Update CPU Package
        pkg = sensors.get("cpu_package")
        if pkg is not None:
            self.val_cpu_pkg.set_text(f"{pkg:.1f}°C")
            self._set_temp_badge(self.cpu_pkg_badge, pkg)
        else:
            self.val_cpu_pkg.set_text("--.-°C")

        # 2. Update CPU Cores
        cores = sensors.get("cpu_cores", [])
        for i, core in enumerate(cores):
            key = f"core_{i}"
            lbl_name = core.get("label", f"Core {i}")
            temp_val = core.get("temp", 0.0)

            if key not in self.sensor_labels:
                col = i % 2
                row = i // 2
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                box.get_style_context().add_class("adw-row")

                lbl = Gtk.Label(label=lbl_name)
                lbl.get_style_context().add_class("chip-title")
                box.pack_start(lbl, False, False, 0)

                badge = Gtk.Label()
                self._set_temp_badge(badge, temp_val)
                box.pack_end(badge, False, False, 0)

                v_lbl = Gtk.Label(label=f"{temp_val:.1f}°C")
                v_lbl.get_style_context().add_class("font-mono-num")
                box.pack_end(v_lbl, False, False, 0)

                self.cores_box.attach(box, col, row, 1, 1)
                box.show_all()
                self.sensor_labels[key] = (v_lbl, badge)
            else:
                v_lbl, badge = self.sensor_labels[key]
                v_lbl.set_text(f"{temp_val:.1f}°C")
                self._set_temp_badge(badge, temp_val)

        # 3. Update Storage & Peripherals (NVMe + Wi-Fi)
        storage_items = []
        for i, nv in enumerate(sensors.get("nvme", [])):
            lbl = nv.get("label", f"NVMe SSD {i}")
            storage_items.append((f"nvme_{i}", f"NVMe SSD: {lbl}", nv.get("temp", 0.0)))

        wifi = sensors.get("wifi")
        if wifi is not None:
            storage_items.append(("wifi", "Wi-Fi Radio Controller", wifi))

        for key, name, temp_val in storage_items:
            if key not in self.sensor_labels:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                row.get_style_context().add_class("adw-row")

                icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                icon_box.get_style_context().add_class("row-icon-plate")
                icon_name = "network-wireless-symbolic" if "wifi" in key else "drive-harddisk-symbolic"
                s_icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
                s_icon.set_pixel_size(16)
                icon_box.pack_start(s_icon, True, True, 0)
                row.pack_start(icon_box, False, False, 0)

                lbl = Gtk.Label(label=name)
                lbl.get_style_context().add_class("control-label")
                row.pack_start(lbl, False, False, 0)

                badge = Gtk.Label()
                self._set_temp_badge(badge, temp_val)
                row.pack_end(badge, False, False, 0)

                v_lbl = Gtk.Label(label=f"{temp_val:.1f}°C")
                v_lbl.get_style_context().add_class("font-mono-num")
                row.pack_end(v_lbl, False, False, 0)

                self.storage_rows_box.pack_start(row, False, False, 0)
                row.show_all()
                self.sensor_labels[key] = (v_lbl, badge)
            else:
                v_lbl, badge = self.sensor_labels[key]
                v_lbl.set_text(f"{temp_val:.1f}°C")
                self._set_temp_badge(badge, temp_val)

        # 4. Update EC Thermal Zones
        ec_zones = sensors.get("thinkpad_zones", [])
        for i, zone in enumerate(ec_zones):
            lbl_zone = zone.get("label", f"EC Zone {i}")
            if lbl_zone.lower() == "cpu":
                continue
            key = f"tp_{i}"
            temp_val = zone.get("temp", 0.0)

            if key not in self.sensor_labels:
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                row.get_style_context().add_class("adw-row")

                icon_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                icon_box.get_style_context().add_class("row-icon-plate")
                s_icon = Gtk.Image.new_from_icon_name("computer-symbolic", Gtk.IconSize.MENU)
                s_icon.set_pixel_size(16)
                icon_box.pack_start(s_icon, True, True, 0)
                row.pack_start(icon_box, False, False, 0)

                lbl = Gtk.Label(label=f"ThinkPad EC: {lbl_zone}")
                lbl.get_style_context().add_class("control-label")
                row.pack_start(lbl, False, False, 0)

                badge = Gtk.Label()
                self._set_temp_badge(badge, temp_val)
                row.pack_end(badge, False, False, 0)

                v_lbl = Gtk.Label(label=f"{temp_val:.1f}°C")
                v_lbl.get_style_context().add_class("font-mono-num")
                row.pack_end(v_lbl, False, False, 0)

                self.ec_rows_box.pack_start(row, False, False, 0)
                row.show_all()
                self.sensor_labels[key] = (v_lbl, badge)
            else:
                v_lbl, badge = self.sensor_labels[key]
                v_lbl.set_text(f"{temp_val:.1f}°C")
                self._set_temp_badge(badge, temp_val)

        # 5. Update Power & Battery Telemetry
        ac_online = power.get("ac_online", True)
        bat_pct = power.get("battery_percent")
        bat_stat = power.get("battery_status", "Full")
        watts = power.get("power_now_w")

        if ac_online:
            self.card_pwr_src[1].set_text("AC Adapter Connected")
            if len(self.card_pwr_src) > 2 and self.card_pwr_src[2]:
                self.card_pwr_src[2].set_from_icon_name("ac-adapter-symbolic", Gtk.IconSize.MENU)
        else:
            self.card_pwr_src[1].set_text("Battery Power Active")
            if len(self.card_pwr_src) > 2 and self.card_pwr_src[2]:
                self.card_pwr_src[2].set_from_icon_name("battery-symbolic", Gtk.IconSize.MENU)

        if bat_pct is not None:
            self.card_pwr_pct[1].set_text(f"{bat_pct:.0f}% [{bat_stat}]")
        else:
            self.card_pwr_pct[1].set_text("N/A")

        if watts is not None and watts > 0:
            flow_dir = "Draw" if not ac_online else "Charging"
            self.card_pwr_flow[1].set_text(f"{flow_dir}: {watts:.1f} W")
        else:
            self.card_pwr_flow[1].set_text("Idle / Minimal Draw")

    def _set_temp_badge(self, badge: Gtk.Label, temp_val: float):
        badge.get_style_context().remove_class("badge-cool")
        badge.get_style_context().remove_class("badge-warm")
        badge.get_style_context().remove_class("badge-hot")

        if temp_val < 55.0:
            badge.get_style_context().add_class("badge-cool")
            badge.set_text("COOL")
        elif temp_val < 75.0:
            badge.get_style_context().add_class("badge-warm")
            badge.set_text("WARM")
        else:
            badge.get_style_context().add_class("badge-hot")
            badge.set_text("HOT")
