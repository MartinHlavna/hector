import platform
import tkinter as tk
from tkinter import ttk, messagebox

from src.backend.service import Service
from src.const.colors import ACCENT_COLOR, PANEL_TEXT_COLOR
from src.const.fonts import HELVETICA_FONT_NAME, BOLD_FONT
from src.const.paths import CONFIG_FILE_PATH
from src.domain.config import AnalysisSettings


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

    def show(self, text, x, y):
        self.label.config(text=text)

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # Estimate the tooltip size
        self.toplevel.update_idletasks()  # Ensures dimensions are accurate after setting text
        tooltip_width = self.toplevel.winfo_reqwidth()
        tooltip_height = self.toplevel.winfo_reqheight()

        # Adjust x and y if the tooltip would go off screen
        if x + 20 + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 20  # Position within screen bounds
        if y + 20 + tooltip_height > screen_height:
            y = screen_height - tooltip_height - 20  # Position within screen bounds

        # Position the tooltip slightly offset from the mouse pointer
        self.toplevel.geometry(f"+{x+20}+{y+20}")
        self.toplevel.deiconify()


    def hide(self):
        self.toplevel.withdraw()


