import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image

from src.const.colors import PRIMARY_COLOR
from src.const.fonts import HELVETICA_FONT_NAME
from src.utils import Utils


# SPLASH SCREEN TO SHOW WHILE INITIALIZING MAIN APP,
# OR WHEN GUI IS NOT ALLOWED TO PREVENT USER TRYING TO DO SOMETHING DURING LONG ACTION
# E.G. DICTIONARY UPGRADE
class SplashWindow:
    def __init__(self, r):
        # SHOW 600x400 CENTERED WINDOW, NOT RESIZABLE, WITHOUT ANY ICONS
        self.root = r
        self.root.withdraw()
        self.splash = tk.Toplevel(self.root)
        self.splash.geometry("600x400")
        self.splash.overrideredirect(True)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width / 2 - 300
        y = screen_height / 2 - 200
        self.splash.geometry("+%d+%d" % (x, y))
        # MAIN FRAME
        self.main_frame = tk.Frame(self.splash, background=PRIMARY_COLOR)
        self.main_frame.pack(expand=1, fill=tk.BOTH, side=tk.LEFT)
        # SHOW HECTOR LOGO
        image = Image.open(Utils.resource_path("images/hector-logo-white-text.png"))
        logo = ImageTk.PhotoImage(image.resize((300, 300)))
        logo_holder = ttk.Label(self.main_frame, image=logo, background=PRIMARY_COLOR)
        logo_holder.image = logo
        logo_holder.pack()
        # SHOW VERSION INFORMATION UNDER LOGO
        tk.Label(self.main_frame, text=f"Verzia {Utils.get_version_info()}", background=PRIMARY_COLOR,
                 font=(HELVETICA_FONT_NAME, 10), foreground="#ffffff").pack()
        self.status = tk.Label(self.main_frame, text="inicializujem...", background=PRIMARY_COLOR,
                               font=(HELVETICA_FONT_NAME, 10), foreground="#ffffff")
        self.status.pack()
        # required to make window show before the program gets to the mainloop
        self.root.update()

    # CLOSE SPLASH WINDOW
    def close(self):
        self.splash.destroy()

    # UPDATE STATUS LINE TO CUSTOM TEXT AND FORCE GUI TO UPDATE
    def update_status(self, text):
        self.status.config(text=text)
        self.root.update()
