import platform
import tkinter as tk
from tkinter import ttk, messagebox, StringVar

from src.backend.run_context import RunContext
from src.backend.service.project_service import ProjectService
from src.const.colors import TEXT_EDITOR_FRAME_BG, PANEL_TEXT_COLOR, TEXT_EDITOR_BG, EDITOR_TEXT_COLOR, PRIMARY_COLOR
from src.domain.project import ProjectItemType
from src.gui.widgets.hector_button import HectorButton


class NewProjectItemModal:
    def __init__(self, root, parent_item, type_options, on_new_file):
        self.root = root
        self.parent_item = parent_item
        self.on_new_file = on_new_file
        self.toplevel = tk.Toplevel(self.root, background=TEXT_EDITOR_FRAME_BG)
        self.toplevel.title("Nový súbor")
        row = 0
        tk.Label(self.toplevel, text="Názov", anchor='w', background=TEXT_EDITOR_FRAME_BG,
                 foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=(10, 2), sticky='w'
        )
        self.name_entry_variable = StringVar()
        name_entry = tk.Entry(self.toplevel, width=30, justify=tk.LEFT,
                              insertbackground=EDITOR_TEXT_COLOR,
                              textvariable=self.name_entry_variable,
                              background=TEXT_EDITOR_BG, foreground=EDITOR_TEXT_COLOR,
                              highlightthickness=0, relief=tk.RAISED, borderwidth=0)
        name_entry.grid(row=row, column=1,
                        columnspan=3, padx=10,
                        pady=(10, 2), sticky='w')
        row += 1
        self.type_combo_variable = StringVar()
        type_combo = ttk.Combobox(self.toplevel, width=27, state="readonly",
                                  textvariable=self.type_combo_variable)
        if type_options is not None:
            type_combo['values'] = list(type_options)
        else:
            type_combo['values'] = list(ProjectItemType.get_selectable_values().keys())
        type_combo.current(0)
        type_combo.grid(row=row, column=1, columnspan=3, padx=10,
                        pady=(10, 2), sticky='w')
        self.toplevel.after(100, lambda: name_entry.focus_set())

        # SAVE BUTTON
        row += 1

        save_btn_col = 1
        revert_btn_col = 0
        if platform.system() == 'Windows':
            save_btn_col = 0
            revert_btn_col = 1
        HectorButton(self.toplevel, text="Uložiť", command=self.create_item, cursor="hand2",
                     background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0,
                     highlightbackground=PANEL_TEXT_COLOR,
                     padx=10, pady=5).grid(
            row=row, column=save_btn_col, columnspan=1, padx=10, pady=10, sticky='w'
        )
        HectorButton(self.toplevel, text="Zrušiť", command=self.close, cursor="hand2",
                     padx=10, pady=5,
                     background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0).grid(
            row=row, column=revert_btn_col, columnspan=1, padx=10, pady=10, sticky='w'
        )

    # SAVE SETTINGS
    def create_item(self):
        ctx = RunContext()
        name = self.name_entry_variable.get()
        item_type = ProjectItemType.get_selectable_values()[self.type_combo_variable.get()]
        if len(name) == 0:
            messagebox.showerror("Chyba", "Názov je povinný.")
            return
        item = ProjectService.new_item(ctx.project, name, self.parent_item, item_type)
        if item is None:
            messagebox.showerror("Chyba", "Nie je možné vytvoriť súbor, súbor už existuje.")
            return
        if self.on_new_file:
            self.on_new_file(item)
        self.close()

    # RESET SETTINGS
    def close(self):
        self.toplevel.destroy()
