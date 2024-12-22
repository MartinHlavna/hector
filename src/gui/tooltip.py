import tkinter as tk

from src.const.colors import ACCENT_COLOR, PANEL_TEXT_COLOR


# TOOLTIP THAT SHOWS IN APPLICATION
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
        self._timer_id = None  # To track scheduled calls

    # PUBLIC SHOW METHOD. SCHEDULES TOOLTIP TO SHOW AFTER 500ms
    # CANCELS ANY PREVIOUS SCHEDULED SHOWS
    def show(self, text, x, y):
        # CANCEL ANY PENDING TOOLTIP SHOW/HIDE OPERATIONS
        if self._timer_id:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None

        # STORE THE AFTER ID TO MANAGE CANCELLATION
        # SCHEDULE SHOWING THE TOOLTIP WITH A 500MS DELAY
        self._timer_id = self.root.after(500, lambda t=text, _x=x, _y=y: self._show_debounced(t, _x, _y))

    # PUBLIC HIDE METHOD. IMMEDIATELY HIDES TOOLTIP AND CANCELS ANY REQUEST SHOW CALLS
    def hide(self):
        # cancel any pending tooltip show operations
        if self._timer_id:
            self.root.after_cancel(self._timer_id)
            self._timer_id = None

        # IMMEDIATELY HIDE THE TOOLTIP
        self.toplevel.withdraw()

    # PRIVATE CALLBACK, THAT ACTUALLY SHOWS TOOLTIP
    def _show_debounced(self, text, x, y):
        # GET SCREEN DIMENSIONS
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # ESTIMATE THE TOOLTIP SIZE
        self.label.config(text=text)
        self.toplevel.update_idletasks()  # ENSURES DIMENSIONS ARE ACCURATE AFTER SETTING TEXT
        tooltip_width = self.toplevel.winfo_reqwidth()
        tooltip_height = self.toplevel.winfo_reqheight()

        # ADJUST X AND Y IF THE TOOLTIP WOULD GO OFF SCREEN
        if x + 20 + tooltip_width > screen_width:
            x = screen_width - tooltip_width - 20
        if y + 20 + tooltip_height > screen_height:
            y = screen_height - tooltip_height - 20

        # POSITION THE TOOLTIP SLIGHTLY OFFSET FROM THE MOUSE POINTER
        self.toplevel.geometry(f"+{x + 20}+{y + 20}")
        self.toplevel.deiconify()
