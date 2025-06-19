import platform
import tkinter as tk
from tkinter import ttk, messagebox

from src.backend.service.metadata_service import MetadataService
from src.backend.service.project_service import ProjectService
from src.const.colors import TEXT_EDITOR_FRAME_BG, PANEL_TEXT_COLOR, PRIMARY_COLOR, TEXT_EDITOR_BG, EDITOR_TEXT_COLOR
from src.const.fonts import HELVETICA_FONT_NAME, BOLD_FONT
from src.const.paths import METADATA_FILE_PATH
from src.domain.project import Project
from src.gui.widgets.hector_button import HectorButton


class EditProjectModal:
    def __init__(self, root, project: Project, on_project_change):
        self.root = root
        self.project = project
        self.on_project_change = on_project_change

        self.toplevel = tk.Toplevel(self.root, background=TEXT_EDITOR_FRAME_BG)
        self.toplevel.title("Upraviť projekt")

        row = 0
        # Project Name
        tk.Label(
            self.toplevel,
            text="Názov",
            anchor='w',
            background=TEXT_EDITOR_FRAME_BG,
            foreground=PANEL_TEXT_COLOR
        ).grid(row=row, column=0, padx=10, pady=(2, 2), sticky='w')

        self.name_entry = tk.Entry(
            self.toplevel,
            width=40,
            background=TEXT_EDITOR_BG,
            foreground=EDITOR_TEXT_COLOR,
            insertbackground=EDITOR_TEXT_COLOR,
            highlightthickness=0,
            borderwidth=0
        )
        self.name_entry.grid(row=row, column=1, columnspan=1, padx=10, pady=2, sticky='we')
        # pre-fill
        if self.project.name:
            self.name_entry.insert(0, self.project.name)

        # Project Description
        row += 1
        tk.Label(
            self.toplevel,
            text="Popis",
            anchor='w',
            background=TEXT_EDITOR_FRAME_BG,
            foreground=PANEL_TEXT_COLOR
        ).grid(row=row, column=0, padx=10, pady=(2, 2), sticky='w')

        self.desc_text = tk.Text(
            self.toplevel,
            width=50,
            height=4,
            wrap='word',
            background=TEXT_EDITOR_BG,
            foreground=EDITOR_TEXT_COLOR,
            insertbackground=EDITOR_TEXT_COLOR,
            highlightthickness=0,
            borderwidth=0
        )
        self.desc_text.grid(row=row, column=1, columnspan=1, padx=10, pady=2, sticky='we')
        if self.project.description:
            self.desc_text.insert('1.0', self.project.description)

        # BUTTONS
        row += 1
        save_col = 0
        cancel_col = 1
        if platform.system() == 'Windows':
            save_col, cancel_col = 1, 0

        HectorButton(
            self.toplevel,
            text="Uložiť",
            command=self.save_project,
            cursor="hand2",
            background=PRIMARY_COLOR,
            foreground=PANEL_TEXT_COLOR,
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=5
        ).grid(row=row, column=save_col, padx=10, pady=10, sticky='e')

        HectorButton(
            self.toplevel,
            text="Zrušiť",
            command=self.cancel,
            cursor="hand2",
            background=PRIMARY_COLOR,
            foreground=PANEL_TEXT_COLOR,
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=5
        ).grid(row=row, column=cancel_col, padx=10, pady=10, sticky='w')

    def save_project(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Chyba", "Názov projektu nesmie byť prázdny.")
            return

        description = self.desc_text.get("1.0", "end").strip()
        self.project.name = name
        self.project.description = description if description else None

        ProjectService.save(self.project, self.project.path)
        metadata = MetadataService.load(METADATA_FILE_PATH)
        for recent_project in metadata.recent_projects:
            if recent_project.path == self.project.path:
                recent_project.name = name
        MetadataService.save(metadata, METADATA_FILE_PATH)
        self.on_project_change()
        self.toplevel.destroy()

    def cancel(self):
        self.toplevel.destroy()
