import platform
import tkinter as tk
from tkinter import ttk, messagebox, StringVar

from src.backend.run_context import RunContext
from src.backend.service.config_service import ConfigService
from src.backend.service.project_service import ProjectService
from src.const.colors import TEXT_EDITOR_FRAME_BG, PANEL_TEXT_COLOR, TEXT_EDITOR_BG, EDITOR_TEXT_COLOR, PRIMARY_COLOR
from src.const.fonts import HELVETICA_FONT_NAME, BOLD_FONT
from src.const.paths import CONFIG_FILE_PATH
from src.domain.config import AppearanceSettings


class NewFileModal:
    def __init__(self, root, on_close):
        self.root = root
        self.on_close = on_close
        self.toplevel = tk.Toplevel(self.root, background=TEXT_EDITOR_FRAME_BG)
        self.toplevel.title("Nový súbor")
        row = 0
        tk.Label(self.toplevel, text="Názov", anchor='w', background=TEXT_EDITOR_FRAME_BG,
                 foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=(10, 2), sticky='w'
        )
        self.name_entry_variable = StringVar()
        self.name_entry = tk.Entry(self.toplevel, width=30, justify=tk.LEFT,
                                   insertbackground=EDITOR_TEXT_COLOR,
                                   textvariable=self.name_entry_variable,
                                   background=TEXT_EDITOR_BG, foreground=EDITOR_TEXT_COLOR,
                                   highlightthickness=0, relief=tk.RAISED, borderwidth=0)
        self.name_entry.grid(row=row, column=1, columnspan=3, padx=10,
                             pady=(10, 2), sticky='w')
        self.toplevel.after(100, lambda: self.name_entry.focus_set())

        # SAVE BUTTON
        row += 1

        save_btn_col = 1
        revert_btn_col = 0
        if platform.system() == 'Windows':
            save_btn_col = 0
            revert_btn_col = 1
        tk.Button(self.toplevel, text="Uložiť", command=self.create_file, cursor="hand2",
                  background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0).grid(
            row=row, column=save_btn_col, columnspan=1, padx=10, pady=10, sticky='w'
        )
        tk.Button(self.toplevel, text="Zrušiť", command=self.close, cursor="hand2",
                  background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0).grid(
            row=row, column=revert_btn_col, columnspan=1, padx=10, pady=10, sticky='w'
        )

    # SAVE SETTINGS
    def create_file(self):
        ctx = RunContext()
        name = self.name_entry_variable.get()
        if len(name) == 0:
            messagebox.showerror("Názov je povinný.")
            return
        ProjectService.new_file(ctx.project, name)
        self.close()

    # RESET SETTINGS
    def close(self):
        if self.on_close:
            self.on_close()
        self.toplevel.destroy()
