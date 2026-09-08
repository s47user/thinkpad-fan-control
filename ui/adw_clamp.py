import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk

class AdwClamp(Gtk.Bin):
    """
    GTK 3 implementation of Libadwaita's AdwClamp / HdyClamp.
    Constrains child content to a maximum width (e.g. 560px) and centers it,
    preventing awkward over-stretching on wide windows or tiling monitors.
    """

    def __init__(self, maximum_size: int = 560):
        super().__init__()
        self.maximum_size = maximum_size

    def do_get_preferred_width(self):
        child = self.get_child()
        if child:
            min_w, nat_w = child.get_preferred_width()
            return min_w, min(nat_w, self.maximum_size)
        return 0, self.maximum_size

    def do_get_preferred_height(self):
        child = self.get_child()
        if child:
            return child.get_preferred_height()
        return 0, 0

    def do_get_preferred_height_for_width(self, width):
        child = self.get_child()
        if child:
            clamped_width = min(width, self.maximum_size)
            return child.get_preferred_height_for_width(clamped_width)
        return 0, 0

    def do_get_preferred_width_for_height(self, height):
        child = self.get_child()
        if child:
            min_w, nat_w = child.get_preferred_width_for_height(height)
            return min_w, min(nat_w, self.maximum_size)
        return 0, self.maximum_size

    def do_size_allocate(self, allocation):
        self.set_allocation(allocation)
        child = self.get_child()
        if not child:
            return
        child_alloc = Gdk.Rectangle()
        if allocation.width > self.maximum_size:
            child_alloc.width = self.maximum_size
            child_alloc.x = allocation.x + (allocation.width - self.maximum_size) // 2
        else:
            child_alloc.width = allocation.width
            child_alloc.x = allocation.x
        child_alloc.y = allocation.y
        child_alloc.height = allocation.height
        child.size_allocate(child_alloc)
