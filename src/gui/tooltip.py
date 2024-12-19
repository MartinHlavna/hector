import tkinter as tk

from src.const.colors import ACCENT_COLOR, PANEL_TEXT_COLOR


class Tooltip:
    def __init__(self, root):
        self.root = root
        self.toplevel = tk.Toplevel(self.root)
        self.toplevel.overrideredirect(True)
        self.toplevel.withdraw()
        self.label = tk.Label(self.toplevel, text="", background=ACCENT_COLOR, foreground=PANEL_TEXT_COLOR,
                              relief="solid", borderwidth=1,
                              wraplength=240,
                              justify="left", padx=5, pady=5)
        self.label.pack()
        self._after_id = None  # To track scheduled calls

    def show(self, text, x, y):
        # Cancel any pending tooltip show/hide operations
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

        # Store the after ID to manage cancelation
        self._after_id = self.root.after(500, lambda t=text, _x=x, _y=y: self.delayed_show(t, _x, _y))

        # Schedule showing the tooltip with a 500ms delay

    def delayed_show(self, text, x, y):
        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Estimate the tooltip size
        self.label.config(text=text)
        self.toplevel.update_idletasks()  # Ensures dimensions are accurate after setting text
        tooltip_width = self.toplevel.winfo_reqwidth()
        tooltip_height = self.toplevel.winfo_reqheight()

        # Adjust x and y if the tooltip would go off screen
        if x + 20 + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 20
        if y + 20 + tooltip_height > screen_height:
            y = screen_height - tooltip_height - 20

        # Position the tooltip slightly offset from the mouse pointer
        self.toplevel.geometry(f"+{x + 20}+{y + 20}")
        self.toplevel.deiconify()

    def hide(self):
        # Cancel any pending tooltip show/hide operations
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

        # Immediately hide the tooltip
        self.toplevel.withdraw()
