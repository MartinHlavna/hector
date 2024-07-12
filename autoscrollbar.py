from tkinter import ttk

# TODO Move to separate package?
class AutoScrollbar(ttk.Scrollbar):
    GEOMETRY_GRID = "GRID"
    GEOMETRY_PACK = "PACK"
    GEOMETRY_PLACE = "PLACE"
    """Create a scrollbar that hides itself if it's not needed.
    Works with pack, grid, and place geometry managers from tkinter.
    """

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.geometry = None
        self.original_config = None

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # SCROLLBAR IS NOT NEEDED, HIDE
            if self.geometry == AutoScrollbar.GEOMETRY_PACK:
                self.pack_forget()
            elif self.geometry == AutoScrollbar.GEOMETRY_GRID:
                self.grid_forget()
            elif self.geometry == AutoScrollbar.GEOMETRY_PLACE:
                self.place_forget()
        else:
            if self.geometry == AutoScrollbar.GEOMETRY_PACK:
                self.pack(**self.original_config)
            elif self.geometry == AutoScrollbar.GEOMETRY_GRID:
                self.grid(**self.original_config)
            elif self.geometry == AutoScrollbar.GEOMETRY_PLACE:
                self.place(**self.original_config)
        ttk.Scrollbar.set(self, lo, hi)

    def pack(self, **kwargs):
        self.geometry = AutoScrollbar.GEOMETRY_PACK
        self.original_config = kwargs
        super().pack(**kwargs)

    def grid(self, **kwargs):
        self.geometry = AutoScrollbar.GEOMETRY_GRID
        self.original_config = kwargs
        super().grid(**kwargs)

    def place(self, **kwargs):
        self.geometry = AutoScrollbar.GEOMETRY_PLACE
        self.original_config = kwargs
        super().place(**kwargs)