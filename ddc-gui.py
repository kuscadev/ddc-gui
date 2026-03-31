#!/usr/bin/env python3
import gi
import subprocess
import os

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import Gtk, GLib, Gdk
from gi.repository import AyatanaAppIndicator3 as AppIndicator3

CSS_DARK = """
window {
    background-color: #1e1e1e;
    color: #ffffff;
    border-radius: 10px;
    border: 1px solid #333333;
}
scale trough {
    background-color: #333333;
    border-radius: 5px;
}
scale highlight {
    background-color: #ffffff;
    border-radius: 5px;
}
scale slider {
    background-color: #ffffff;
    border-radius: 10px;
    min-width: 15px;
    min-height: 15px;
}
"""

class PrecisionBar(Gtk.Window):
    def __init__(self, bus_id):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.bus_id = bus_id
        self.update_timeout = None
        
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_border_width(10)
        self.set_default_size(280, 35)
        
        self.style_context = self.get_style_context()
        self.provider = Gtk.CssProvider()
        self.provider.load_from_data(CSS_DARK.encode("utf-8"))
        self.style_context.add_provider(
            self.provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.add(self.box)

        self.label = Gtk.Label(label="🔆")
        self.box.pack_start(self.label, False, False, 0)

        self.scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 2)
        self.scale.set_value(50)
        self.scale.set_hexpand(True)
        self.scale.connect("value-changed", self.on_slider_moved)
        self.box.pack_start(self.scale, True, True, 0)

        self.connect("focus-out-event", lambda w, e: self.hide())

    def move_to_corner(self):
        screen = Gdk.Screen.get_default()
        width = screen.get_width()
        self.move(width - 320, 1000) 
        
    def on_slider_moved(self, widget):
        val = int(widget.get_value())
        if self.update_timeout:
            GLib.source_remove(self.update_timeout)
        self.update_timeout = GLib.timeout_add(100, self.apply_brightness, val)

    def apply_brightness(self, val):
        subprocess.Popen([
            "ddcutil", "--bus", self.bus_id, "setvcp", "10", str(val), "--noverify"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return False

class MonitorIndicator:
    def __init__(self):
        self.bus_id = "5" 
        self.win = PrecisionBar(self.bus_id)

        self.indicator = AppIndicator3.Indicator.new(
            "monitor-brightness",
            "display-brightness-symbolic",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.build_menu())

    def build_menu(self):
        menu = Gtk.Menu()
        
        item_control = Gtk.MenuItem(label="-- Slider --")
        item_control.connect("activate", self.show_bar)
        menu.append(item_control)

        menu.append(Gtk.SeparatorMenuItem())

        for val in [10, 30, 50, 70, 90, 100]:
            item = Gtk.MenuItem(label=f"Preset %{val}")
            item.connect("activate", lambda x, v=val: self.quick_set(v))
            menu.append(item)

        menu.append(Gtk.SeparatorMenuItem())
        item_quit = Gtk.MenuItem(label="Exit")
        item_quit.connect("activate", Gtk.main_quit)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def show_bar(self, _):
        self.win.move_to_corner()
        self.win.show_all()
        self.win.present()

    def quick_set(self, val):
        subprocess.Popen([
            "ddcutil", "--bus", self.bus_id, "setvcp", "10", str(val), "--noverify"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if __name__ == "__main__":
    app = MonitorIndicator()
    Gtk.main()
