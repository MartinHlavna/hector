import platform
import tkinter as tk
from tkinter import ttk, messagebox

from src.backend.service.config_service import ConfigService
from src.const.colors import TEXT_EDITOR_FRAME_BG, PANEL_TEXT_COLOR, PRIMARY_COLOR
from src.const.fonts import HELVETICA_FONT_NAME, BOLD_FONT
from src.const.paths import CONFIG_FILE_PATH
from src.domain.config import AppearanceSettings
from src.gui.widgets.hector_button import HectorButton


class AppearanceSettingsModal:
    def __init__(self, root, config, on_config_change):
        self.root = root
        self.config = config
        self.on_config_change = on_config_change
        self.toplevel = tk.Toplevel(self.root, background=TEXT_EDITOR_FRAME_BG)
        self.toplevel.title("Nastavenia vzhľadu")
        row = 0
        tk.Label(self.toplevel, text="Odsek", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )

        row += 1

        tk.Label(self.toplevel, text="Odsadenie prvého riadku", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.paragraph_lmargin1_entry = ttk.Spinbox(self.toplevel, from_=1, to=100, width=6, justify=tk.LEFT, style='hector.TSpinbox')
        self.paragraph_lmargin1_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.paragraph_lmargin1_entry.set(self.config.appearance_settings.paragraph_lmargin1)
        tk.Label(self.toplevel, text="milimetrov", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(self.toplevel, text="Medzera za odsekom", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.paragraph_spacing3_entry = ttk.Spinbox(self.toplevel, from_=1, to=100, width=6, style='hector.TSpinbox')
        self.paragraph_spacing3_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.paragraph_spacing3_entry.set(self.config.appearance_settings.paragraph_spacing3)
        tk.Label(self.toplevel, text="milimetrov", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        # SAVE BUTTON
        row += 1

        save_btn_col = 2
        revert_btn_col = 1
        if platform.system() == 'Windows':
            save_btn_col = 1
            revert_btn_col = 2
        HectorButton(self.toplevel, text="Uložiť", command=self.save_settings, cursor="hand2",
                     background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0,
                     highlightbackground=PANEL_TEXT_COLOR,
                     padx=10, pady=5).grid(
            row=row, column=save_btn_col, columnspan=1, padx=10, pady=10, sticky='w'
        )
        HectorButton(self.toplevel, text="Obnoviť pôvodné", command=self.reset_settings, cursor="hand2",
                     padx=10, pady=5,
                     background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0).grid(
            row=row, column=revert_btn_col, columnspan=1, padx=10, pady=10, sticky='w'
        )

    # SAVE SETTINGS
    def save_settings(self):
        self.config.appearance_settings.paragraph_lmargin1 = int(self.paragraph_lmargin1_entry.get())
        self.config.appearance_settings.paragraph_spacing3 = int(self.paragraph_spacing3_entry.get())
        ConfigService.save(self.config, CONFIG_FILE_PATH)
        self.on_config_change()
        self.toplevel.destroy()

    # RESET SETTINGS
    def reset_settings(self):
        should_reset = messagebox.askyesno("Obnoviť pôvodné",
                                           "Pokračovaním obnovíte pôvodné nastavenia programu. Skutočne chcete "
                                           "pokračovať?")
        if should_reset:
            self.config.appearance_settings = AppearanceSettings({})
            ConfigService.save(self.config, CONFIG_FILE_PATH)
            self.on_config_change()
            self.toplevel.destroy()
