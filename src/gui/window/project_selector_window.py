import math
import os.path
import platform
import tkinter as tk
from functools import partial
from tkinter import ttk, filedialog, messagebox

from PIL import ImageTk, Image
from tkinter_autoscrollbar import AutoScrollbar

from src.backend.service.metadata_service import MetadataService
from src.backend.service.project_service import ProjectService
from src.const.colors import PRIMARY_COLOR, TEXT_EDITOR_FRAME_BG, PANEL_TEXT_COLOR, GREY, TEXT_EDITOR_BG, \
    EDITOR_TEXT_COLOR
from src.const.font_awesome_icons import FontAwesomeIcons
from src.const.fonts import HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER, FA_SOLID
from src.const.paths import METADATA_FILE_PATH
from src.const.values import VERSION
from src.domain.metadata import RecentProject
from src.domain.project import Project
from src.gui.gui_utils import GuiUtils
from src.gui.widgets.hector_button import HectorButton
from src.gui.navigator import Navigator
from src.utils import Utils


class ProjectSelectorWindow:
    def __init__(self, r):
        # SHOW 600x400 CENTERED WINDOW, NOT RESIZABLE, WITHOUT ANY ICONS
        self.root = r
        width = 800
        height = 600
        self.selector_window = tk.Toplevel(self.root)
        self.selector_window.geometry(f"{width}x{height}")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width / 2 - (width / 2)
        y = screen_height / 2 - (height / 2)
        self.selector_window.geometry("+%d+%d" % (x, y))
        self.root.update()
        self.root.withdraw()
        self.selector_window.protocol("WM_DELETE_WINDOW", self.on_close)
        # MAIN FRAME
        self.main_frame = tk.Frame(self.selector_window, background=TEXT_EDITOR_FRAME_BG)
        self.main_frame.pack(expand=1, fill=tk.BOTH, side=tk.LEFT)
        # LEFT SCROLLABLE PANEL
        left_side_panel = tk.Frame(self.main_frame, width=300, relief=tk.FLAT, borderwidth=1, background=PRIMARY_COLOR)
        left_side_panel.pack(fill=tk.BOTH, side=tk.LEFT, expand=0)
        header_frame = tk.Frame(left_side_panel, width=300, relief=tk.FLAT, borderwidth=1, background=PRIMARY_COLOR)
        header_frame.pack(fill=tk.X)
        # SHOW HECTOR LOGO
        image = Image.open(Utils.resource_path("images/hector-logo-white-text-small.png"))
        logo_width = 30
        logo_height_ratio = 0.81
        logo = ImageTk.PhotoImage(image.resize((logo_width, math.floor(logo_width / logo_height_ratio))))
        logo_holder = ttk.Label(header_frame, image=logo, background=PRIMARY_COLOR, padding=(20, 10))
        logo_holder.image = logo
        logo_holder.pack(side=tk.LEFT)
        ttk.Label(header_frame, background=PRIMARY_COLOR, foreground=GREY, padding=(20, 10),
                  text=f"{VERSION}").pack(side=tk.RIGHT)
        HectorButton(left_side_panel, text="Nový projekt", command=self.open_new_project_form, width=15, cursor="hand2",
                     padx=10, pady=5,
                     background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0).pack(
            pady=5
        )
        HectorButton(left_side_panel, text="Otvoriť projekt", command=self.open_project_from_file, width=15,
                     cursor="hand2",  padx=10, pady=5,
                     background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0).pack(
            pady=5
        )
        # MIDDLE PANE
        # MIDDLE TEXT EDITOR WINDOW
        midlle_frame = tk.Frame(self.main_frame, background=TEXT_EDITOR_FRAME_BG, borderwidth=0)
        midlle_frame.pack(expand=1, fill=tk.BOTH)
        midlle_scroll_frame = tk.Frame(midlle_frame, width=10, relief=tk.FLAT, background=PRIMARY_COLOR)
        midlle_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        midlle_scroll = AutoScrollbar(midlle_scroll_frame, orient='vertical',
                                      style='arrowless.Vertical.TScrollbar', takefocus=False)
        midlle_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.recent_projects_frame = tk.Frame(midlle_frame, background=TEXT_EDITOR_FRAME_BG, borderwidth=0)
        self.recent_projects_frame.pack(expand=1, fill=tk.BOTH)
        metadata = MetadataService.load(METADATA_FILE_PATH)
        tk.Label(self.recent_projects_frame, pady=10, padx=10, background=TEXT_EDITOR_FRAME_BG,
                 foreground=PANEL_TEXT_COLOR,
                 text="Nedávne projekty",
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='nw',
                 justify='left').pack(fill=tk.X)
        for recent_project in metadata.recent_projects:
            project_frame = tk.Frame(self.recent_projects_frame, background=TEXT_EDITOR_FRAME_BG, padx=10, pady=5,
                                     cursor="hand2")
            project_frame.pack(fill=tk.X)
            project_name = ttk.Label(project_frame, foreground=PANEL_TEXT_COLOR, background=TEXT_EDITOR_FRAME_BG,
                                     text=recent_project.name)
            project_name.pack(fill=tk.X)
            project_path = ttk.Label(project_frame, foreground=PANEL_TEXT_COLOR, background=TEXT_EDITOR_FRAME_BG,
                                     text=recent_project.path)
            project_path.pack(fill=tk.X)
            project_frame.bind("<Button-1>", partial(self.open_recent_project, recent_project))
            project_name.bind("<Button-1>", partial(self.open_recent_project, recent_project))
            project_path.bind("<Button-1>", partial(self.open_recent_project, recent_project))
            ttk.Separator(project_frame, style='Grey.TSeparator').pack(fill=tk.X)
        # NEW PROJECT FORM
        self.new_project_frame = tk.Frame(midlle_frame, background=TEXT_EDITOR_FRAME_BG, borderwidth=0)
        tk.Label(self.new_project_frame, pady=10, padx=10, background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR,
                 text="Nový projekt",
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='nw',
                 justify='left').pack(fill=tk.X)
        tk.Label(self.new_project_frame, text="Názov", anchor='w', background=TEXT_EDITOR_FRAME_BG,
                 foreground=PANEL_TEXT_COLOR).pack(
            fill=tk.X, padx=10, pady=5,
        )
        self.project_name_entry_var = tk.StringVar()
        self.project_name_entry_var.trace("w", self.on_project_name_change)
        self.project_location_entry_var = tk.StringVar()
        tk.Entry(self.new_project_frame, width=6, justify=tk.LEFT,
                 insertbackground=EDITOR_TEXT_COLOR,
                 textvariable=self.project_name_entry_var,
                 background=TEXT_EDITOR_BG, foreground=EDITOR_TEXT_COLOR,
                 highlightthickness=0, relief=tk.RAISED, borderwidth=0).pack(fill=tk.X, padx=10, pady=2)

        tk.Label(self.new_project_frame, text="Umiestnenie", anchor='w', background=TEXT_EDITOR_FRAME_BG,
                 foreground=PANEL_TEXT_COLOR).pack(
            fill=tk.X, padx=10, pady=5,
        )
        project_location_frame = tk.Frame(self.new_project_frame, background=TEXT_EDITOR_FRAME_BG)
        project_location_frame.pack(fill='x', padx=10, pady=2)
        self.browse_image = GuiUtils.fa_image(FA_SOLID, TEXT_EDITOR_BG, PANEL_TEXT_COLOR, FontAwesomeIcons.folder, 19,
                                              padding=4)
        project_location_browse_btn = HectorButton(project_location_frame, command=self.select_new_project_location,
                                                   width=19,
                                                   cursor="hand2",
                                                   image=self.browse_image,
                                                   highlightthickness=0,
                                                   background=TEXT_EDITOR_BG, foreground=PANEL_TEXT_COLOR,
                                                   relief=tk.FLAT,
                                                   borderwidth=0)
        project_location_browse_btn.pack(side=tk.RIGHT, padx=(0, 0))

        tk.Entry(project_location_frame, width=6, justify=tk.LEFT,
                 textvariable=self.project_location_entry_var,
                 insertbackground=EDITOR_TEXT_COLOR,
                 background=TEXT_EDITOR_BG, foreground=EDITOR_TEXT_COLOR,
                 highlightthickness=0, relief=tk.RAISED, borderwidth=0).pack(fill=tk.X, )

        tk.Label(self.new_project_frame, text="Popis", anchor='w', background=TEXT_EDITOR_FRAME_BG,
                 foreground=PANEL_TEXT_COLOR).pack(
            fill=tk.X, padx=10, pady=2,
        )

        self.project_description_entry = tk.Text(self.new_project_frame, wrap=tk.WORD, relief=tk.RAISED,
                                                 highlightthickness=0,
                                                 background=TEXT_EDITOR_BG,
                                                 foreground=EDITOR_TEXT_COLOR, borderwidth=0,
                                                 height=6,
                                                 spacing1=1.2, spacing2=1.2, spacing3=1.2, undo=True,
                                                 autoseparators=True, maxundo=-1,
                                                 insertbackground=PANEL_TEXT_COLOR)
        self.project_description_entry.pack(fill=tk.X, padx=10, pady=2)

        button_frame = tk.Frame(self.new_project_frame, background=TEXT_EDITOR_FRAME_BG)
        button_frame.pack(fill='x', padx=10, pady=10)
        # SAVE BUTTON
        buttons = [
            HectorButton(button_frame, text="Vytvoriť projekt", command=self.create_project, width=15, cursor="hand2",
                         padx=10, pady=5,
                         background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0),
            HectorButton(button_frame, text="Zrušiť", command=self.close_new_project_form, width=15, cursor="hand2",
                         padx=10, pady=5,
                         background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0)
        ]
        if platform.system() == 'Windows':
            buttons[0].pack(side=tk.LEFT, padx=(0, 5))
            buttons[1].pack(side=tk.LEFT, padx=5)
        else:
            buttons[1].pack(side=tk.LEFT, padx=(0, 5))
            buttons[0].pack(side=tk.LEFT, padx=5)

    def open_project_from_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Hector projekt", "*.hproj")
            ]
        )
        if file_path:
            project = ProjectService.load(file_path)
            self.open_project(project)

    def open_recent_project(self, project: RecentProject, e=None):
        if GuiUtils.open_recent_project(project):
            self.close()
            Navigator().navigate(Navigator.MAIN_WINDOW)

    def open_project(self, project: Project):
        if GuiUtils.open_project(project):
            self.close()
            Navigator().navigate(Navigator.MAIN_WINDOW)

    def open_new_project_form(self):
        self.recent_projects_frame.pack_forget()
        self.new_project_frame.pack(expand=1, fill=tk.BOTH)

    def create_project(self):
        folder_selected = self.project_location_entry_var.get()
        if len(folder_selected) == 0:
            messagebox.showerror("Umiestnenie je povinné.")
            return
        name = self.project_name_entry_var.get()
        if len(name) == 0:
            messagebox.showerror("Názov je povinný.")
            return
        description = self.project_description_entry.get(1.0, tk.END)
        project = ProjectService.create_project(name, description, folder_selected)
        self.open_project(project)

    def close_new_project_form(self):
        self.recent_projects_frame.pack(expand=1, fill=tk.BOTH)
        self.new_project_frame.pack_forget()

    def select_new_project_location(self):
        folder_selected = filedialog.askdirectory(mustexist=False)
        if folder_selected:
            self.project_location_entry_var.set(os.path.join(
                folder_selected,
                Utils.normalize_file_name(self.project_name_entry_var.get())
            ))

    def on_project_name_change(self, a, b, c):
        folder_selected = self.project_location_entry_var.get()
        if len(folder_selected) > 0:
            path_parts = list(os.path.split(folder_selected))
            path_parts[-1] = self.project_name_entry_var.get().replace(' ', '_')
            self.project_location_entry_var.set(os.path.join(*path_parts))

    # PROPAGATE CLOSE TO ENTIE APP IF USER CLOSES THIS WINDOW
    def on_close(self):
        self.root.destroy()

    # CLOSE SPLASH WINDOW
    def close(self):
        self.selector_window.destroy()
        self.root.after(10, self.root.deiconify)
