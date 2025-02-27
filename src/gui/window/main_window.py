import io
import json
import math
import os
import platform
import tkinter as tk
import webbrowser
from functools import partial
from tkinter import filedialog, ttk, messagebox

from PIL import ImageTk
from reportlab.graphics import renderPM
from spacy import displacy
from spacy.tokens import Doc
from svglib.svglib import svg2rlg
from tkinter_autoscrollbar import AutoScrollbar

from src.backend.run_context import RunContext
from src.backend.service.config_service import ConfigService
from src.backend.service.export_service import ExportService
from src.backend.service.import_service import ImportService
from src.backend.service.metadata_service import MetadataService
from src.backend.service.nlp_service import NlpService
from src.backend.service.project_service import ProjectService
from src.backend.service.spellcheck_service import SpellcheckService
from src.const.colors import PRIMARY_COLOR, ACCENT_2_COLOR, TEXT_EDITOR_FRAME_BG, PANEL_TEXT_COLOR, \
    TEXT_EDITOR_BG, TRANSPARENT
from src.const.font_awesome_icons import FontAwesomeIcons
from src.const.fonts import HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER, TEXT_SIZE_BOTTOM_BAR, FA_SOLID
from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD
from src.const.paths import CONFIG_FILE_PATH, METADATA_FILE_PATH
from src.const.tags import CLOSE_WORD_PREFIX, CLOSE_WORD_TAG_NAME, \
    FREQUENT_WORD_PREFIX, FREQUENT_WORD_TAG_NAME, CLOSE_WORD_RANGE_PREFIX
from src.const.values import READABILITY_MAX_VALUE, DOCUMENTATION_LINK
from src.domain.config import Config, ConfigLevel
from src.domain.htext_file import HTextFile
from src.domain.metadata import RecentProject
from src.domain.project import ProjectItemType, ProjectItem
from src.gui.gui_utils import GuiUtils
from src.gui.modal.analysis_settings_modal import AnalysisSettingsModal
from src.gui.modal.appearance_settings_modal import AppearanceSettingsModal
from src.gui.modal.new_project_item_modal import NewProjectItemModal
from src.gui.navigator import Navigator
from src.gui.widgets.menu import MenuItem, HectorMenu, MenuSeparator, ContextMenu
from src.gui.widgets.htext_editor import HTextEditor
from src.gui.widgets.tooltip import Tooltip
from src.gui.window.splash_window import SplashWindow
from src.utils import Utils

ENABLE_DEBUG_DEP_IMAGE = False

with open(Utils.resource_path(os.path.join('data_files', 'pos_tag_translations.json')), 'r', encoding='utf-8') as file:
    POS_TAG_TRANSLATIONS = json.load(file)

with open(Utils.resource_path(os.path.join('data_files', 'dep_tag_translations.json')), 'r', encoding='utf-8') as file:
    DEP_TAG_TRANSLATION = json.load(file)


# MAIN GUI WINDOW
class MainWindow:
    def __init__(self, r):
        self.root = r
        r.overrideredirect(False)
        if platform.system() == "Windows" or platform.system() == "Darwin":
            self.root.state("zoomed")
        else:
            self.root.attributes('-zoomed', True)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        self.root.geometry("800x600")
        x = screen_width / 2 - (800 / 2)
        y = screen_height / 2 - (600 / 2)
        self.root.geometry("+%d+%d" % (x, y))
        self.ctx = RunContext()
        r.title(f"{self.ctx.project.name} | Hector")
        self.search_debounce_timer = None
        # TOOLTIP WINDOW
        self.tooltip = Tooltip(self.root)
        self.last_tags = set()
        # DEFAULT NLP DOCUMENT INITIALIZED ON EMPTY TEXT
        self.doc = self.ctx.nlp('')
        # TOKEN SELECTED IN LEFT BOTTOM INTOSPECTION WINDOW
        self.current_instrospection_token = None
        # LOAD CONFIG
        self.ctx.global_config = ConfigService.load(CONFIG_FILE_PATH)
        # LOAD METADATA
        self.metadata = MetadataService.load(METADATA_FILE_PATH)
        # PROJECT TREE ITEMS TO PROJCT ITEM INDEX
        self.project_tree_item_to_project_item = {}
        # INIT GUI
        # TOP MENU
        # Define menu items
        recent_projects = []
        for recent_project in self.metadata.recent_projects:
            if recent_project.path != self.ctx.project.path:
                recent_projects.append(MenuItem(
                    label=recent_project.name,
                    command=partial(self.open_recent_project, recent_project)
                ))
        menu_items = [
            MenuItem(label="Projekt",
                     underline_index=0,
                     submenu=[
                         MenuItem(label="Nastavenia analýzy",
                                  command=partial(
                                      self.show_analysis_settings,
                                      self.ctx.project.config,
                                      ConfigLevel.PROJECT
                                  ),
                                  ),
                         MenuItem(label="Zavrieť",
                                  command=self.close_project,
                                  ),
                         MenuItem(label="Nedávne projekty",
                                  submenu=recent_projects,
                                  )
                     ]),
            MenuSeparator(),
            MenuItem(label="Súbor",
                     underline_index=0,
                     submenu=[
                         MenuItem(label="Nový",
                                  command=self.open_new_file_dialog,
                                  icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.file, 16),
                                  highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B",
                                                                   FontAwesomeIcons.file, 16),
                                  shortcut_label="Ctrl+N", shortcut="<Control-n>"),
                         MenuItem(label="Uložiť",
                                  command=self.save_htext_file,
                                  icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.floppy_disk,
                                                         16),
                                  highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B",
                                                                   FontAwesomeIcons.floppy_disk, 16),
                                  shortcut_label="Ctrl+S", shortcut="<Control-s>"),
                         MenuSeparator(),
                         MenuItem(label="Importovať", command=self.import_file, shortcut="<Control-o>",
                                  icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.file_import,
                                                         16),
                                  highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B",
                                                                   FontAwesomeIcons.file_import, 16),
                                  shortcut_label="Ctrl+O"),
                         MenuItem(label="Reimportovať", command=self.reimport_file,
                                  shortcut="<Control-r>",
                                  icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.rotate,
                                                         16),
                                  highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B",
                                                                   FontAwesomeIcons.rotate,
                                                                   16),
                                  shortcut_label="Ctrl+R"),
                         MenuItem(label="Exportovať",
                                  command=self.export_file,
                                  shortcut="<Control-e>",
                                  icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white",
                                                         FontAwesomeIcons.file_export, 16),
                                  highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B",
                                                                   FontAwesomeIcons.file_export,
                                                                   16),
                                  shortcut_label="Ctrl+E"),
                     ]),
            MenuItem(label="Upraviť", underline_index=0, submenu=[
                MenuItem(
                    label="Vrátiť späť",
                    command=self.undo,
                    icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.rotate_left, 16),
                    highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B", FontAwesomeIcons.rotate_left, 16),
                    shortcut="<Control-z>",
                    shortcut_label="Ctrl+Z"
                ),
                MenuItem(label="Zopakovať",
                         command=self.redo,
                         icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.rotate_right, 16),
                         highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B", FontAwesomeIcons.rotate_right,
                                                          16),
                         shortcut="<Control-Shift-z>",
                         shortcut_label="Ctrl+Shift+Z"
                         ),
                MenuItem(label="Analyzovať všetko",
                         command=lambda: self.text_editor.analyze_text(force_full_analysis=True),
                         icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.rotate, 16),
                         highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B", FontAwesomeIcons.rotate, 16),
                         )
            ]),
            MenuItem(label="Nástroje", underline_index=0, submenu=[
                MenuItem(
                    label="Exportovať zoznam viet",
                    command=self.export_sentences,
                ),

            ]),
            MenuItem(label="Nastavenia", underline_index=0, submenu=[
                MenuItem(
                    label="Parametre analýzy",
                    icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.gears, 16),
                    highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B", FontAwesomeIcons.gears, 16),
                    command=partial(
                        self.show_analysis_settings,
                        self.ctx.global_config,
                        ConfigLevel.GLOBAL
                    )
                ),
                MenuItem(
                    label="Vzhľad",
                    icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.pallete, 16),
                    highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B", FontAwesomeIcons.pallete, 16),
                    command=self.show_appearance_settings
                ),
                MenuItem(
                    label="Exportovať",
                    icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.file_export, 16),
                    highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B", FontAwesomeIcons.file_export, 16),
                    command=self.export_settings
                ),
                MenuItem(
                    label="Importovať",
                    icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.file_import, 16),
                    highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B", FontAwesomeIcons.file_import, 16),
                    command=self.import_settings
                )
            ]),
            MenuItem(label="Pomoc", underline_index=1, submenu=[
                MenuItem(label="O programe",
                         icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.question_circle, 16),
                         highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B",
                                                          FontAwesomeIcons.question_circle,
                                                          16),
                         command=self.show_about
                         ),
                MenuItem(
                    label="Dokumentácia",
                    icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.book, 16),
                    highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B", FontAwesomeIcons.book, 16),
                    command=lambda: webbrowser.open(DOCUMENTATION_LINK)
                ),
                MenuItem(
                    label="Aktualizovať slovníky",
                    icon=GuiUtils.fa_image(FA_SOLID, "#3B3B3B", "white", FontAwesomeIcons.download, 16),
                    highlight_icon=GuiUtils.fa_image(FA_SOLID, "white", "#3B3B3B", FontAwesomeIcons.download, 16),
                    command=self.update_dictionaries
                )
            ])
        ]
        self.menu_bar = HectorMenu(self.root, menu_items, background="#3B3B3B", foreground="white")
        self.context_menu = ContextMenu(self.root, background="#3B3B3B", foreground="white")
        # MAIN FRAME
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=1, fill=tk.BOTH, side=tk.LEFT)
        # LEFT SCROLLABLE SIDE PANEL WITH FREQUENT WORDS
        left_side_panel = tk.Frame(self.main_frame, width=300, relief=tk.FLAT, borderwidth=1, background=PRIMARY_COLOR)
        left_side_panel.pack(fill=tk.BOTH, side=tk.LEFT, expand=0)
        # RIGHT SCROLLABLE SIDE PANEL WITH FREQUENT WORDS
        right_side_panel = tk.Frame(self.main_frame, width=200, relief=tk.FLAT, borderwidth=1, background=PRIMARY_COLOR)
        right_side_panel.pack(fill=tk.BOTH, side=tk.RIGHT)
        # MIDDLE TEXT EDITOR WINDOW
        text_editor_frame = tk.Frame(self.main_frame, background=TEXT_EDITOR_FRAME_BG, borderwidth=0)
        text_editor_frame.pack(expand=1, fill=tk.BOTH)
        # BOTTOM PANEL WITH TEXT SIZE
        bottom_panel = tk.Frame(text_editor_frame, background=ACCENT_2_COLOR, height=20)
        bottom_panel.pack(fill=tk.BOTH, side=tk.BOTTOM)
        # LEFT PANEL CONTENTS
        left_panel_notebook = ttk.Notebook(left_side_panel, style="panel.TNotebook")
        left_panel_notebook.pack(fill=tk.BOTH, expand=True)
        left_side_panel_project = tk.Frame(left_panel_notebook, width=300, relief=tk.FLAT, borderwidth=1,
                                           background=PRIMARY_COLOR)
        left_side_panel_project.pack(fill=tk.BOTH, side=tk.LEFT, expand=0)
        tk.Label(left_side_panel_project, pady=10, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                 wraplength=300,
                 text=f"{self.ctx.project.name}",
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='n',
                 padx=10,
                 justify='left').pack(fill=tk.X)
        tk.Label(left_side_panel_project, pady=10, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                 wraplength=300,
                 text=f"{self.ctx.project.description}",
                 anchor='n',
                 padx=10,
                 justify='left').pack(fill=tk.X)
        separator = ttk.Separator(left_side_panel_project, orient='horizontal')
        separator.pack(fill=tk.X, padx=10)
        self.project_tree = ttk.Treeview(left_side_panel_project, show="tree", style="panel.Treeview")
        self.project_root_image = GuiUtils.fa_image(FA_SOLID, TRANSPARENT, "white", FontAwesomeIcons.folder, 20,
                                                    padding=4)
        self.htext_image = GuiUtils.fa_image(FA_SOLID, TRANSPARENT, "white", FontAwesomeIcons.file, 20, padding=4)
        self.htext_image_with_link = ImageTk.PhotoImage(GuiUtils.merge_icons(
            GuiUtils.fa_image_raw(FA_SOLID, TRANSPARENT, "white", FontAwesomeIcons.link, 20, padding=4),
            GuiUtils.fa_image_raw(FA_SOLID, TRANSPARENT, "white", FontAwesomeIcons.file, 20, padding=4),
            space_between=0
        ))
        self.htext_image_with_broken_link = ImageTk.PhotoImage(GuiUtils.merge_icons(
            GuiUtils.fa_image_raw(FA_SOLID, TRANSPARENT, "white", FontAwesomeIcons.link_broken, 20, padding=4),
            GuiUtils.fa_image_raw(FA_SOLID, TRANSPARENT, "white", FontAwesomeIcons.file, 20, padding=4),
            space_between=0
        ))
        self.directory_image = GuiUtils.fa_image(FA_SOLID, TRANSPARENT, "white", FontAwesomeIcons.folder, 20, padding=4)
        self.project_tree_root = self.project_tree.insert(
            "", 0,
            image=self.project_root_image,
            text=self.ctx.project.name,
            open=True
        )
        self.project_tree.pack(fill=tk.BOTH, expand=1, padx=10, pady=10)
        self.project_tree.bind("<Double-1>", self._on_project_tree_double_click)
        self.project_tree.bind("<<TreeviewOpen>>", self._on_project_tree_item_open)
        self.project_tree.bind("<<TreeviewClose>>", self._on_project_tree_item_close)
        self.project_tree.bind("<FocusIn>",
                               lambda e: self.project_tree.bind("<Delete>", self._on_project_tree_item_delete))
        self.project_tree.bind("<FocusOut>", lambda e: self.project_tree.unbind("<Delete>"))

        self._show_project_files()
        left_side_panel_tools = tk.Frame(left_panel_notebook, width=300, relief=tk.FLAT, borderwidth=1,
                                         background=PRIMARY_COLOR)
        left_side_panel_tools.pack(fill=tk.BOTH, side=tk.LEFT, expand=0)
        left_panel_notebook.add(left_side_panel_project, text="Projekt")
        left_panel_notebook.add(left_side_panel_tools, text="Nástroje")
        self.introspection_text = tk.Text(left_side_panel_tools, highlightthickness=0, bd=0, wrap=tk.WORD,
                                          state=tk.DISABLED,
                                          width=30, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, height=30,
                                          font=(HELVETICA_FONT_NAME, 9), insertbackground=PANEL_TEXT_COLOR,
                                          )
        if ENABLE_DEBUG_DEP_IMAGE:
            self.dep_image_holder = ttk.Label(left_side_panel_tools, width=30)
            self.dep_image_holder.pack(pady=10, padx=10, side=tk.BOTTOM)
            self.dep_image_holder.bind("<Button-1>", self.show_dep_image)
        GuiUtils.set_text(self.introspection_text, 'Kliknite na slovo v editore')
        self.introspection_text.pack(fill=tk.X, pady=10, padx=10, side=tk.BOTTOM)
        separator = ttk.Separator(left_side_panel_tools, orient='horizontal')
        separator.pack(fill=tk.X, padx=10, side=tk.BOTTOM)
        tk.Label(left_side_panel_tools, pady=10, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                 text="Introspekcia",
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='n',
                 justify='left').pack(side=tk.BOTTOM)
        tk.Label(left_side_panel_tools, pady=10, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                 text="Často sa opakujúce slová",
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='n',
                 justify='left').pack()
        separator = ttk.Separator(left_side_panel_tools, orient='horizontal')
        separator.pack(fill=tk.X, padx=10)
        left_side_panel_scroll_frame = tk.Frame(left_side_panel_tools, width=10, relief=tk.FLAT,
                                                background=PRIMARY_COLOR)
        left_side_panel_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        left_side_frame_scroll = AutoScrollbar(left_side_panel_scroll_frame, orient='vertical',
                                               style='arrowless.Vertical.TScrollbar', takefocus=False)
        left_side_frame_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.close_words_text = tk.Text(left_side_panel_tools, highlightthickness=0, bd=0, wrap=tk.WORD,
                                        state=tk.DISABLED,
                                        width=20, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                                        yscrollcommand=left_side_frame_scroll.set, cursor="xterm")
        self.close_words_text.pack(fill=tk.BOTH, expand=1, pady=10, padx=10)
        left_side_frame_scroll.config(command=self.close_words_text.yview)
        # RIGHT PANEL CONTENTS
        tk.Label(right_side_panel, pady=10, compound=tk.LEFT, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                 text="Hľadať", font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER),
                 anchor='n', justify='left').pack(fill=tk.X)
        search_frame = tk.Frame(right_side_panel, relief=tk.FLAT, background=PRIMARY_COLOR)
        search_frame.pack(fill=tk.X, padx=0)
        prev_search_button = tk.Label(search_frame, text="⮝", background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                                      cursor="hand2")
        prev_search_button.pack(side=tk.RIGHT, padx=2)
        next_search_button = tk.Label(search_frame, text="⮟", background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                                      cursor="hand2")
        self.search_field = ttk.Entry(search_frame, width=22, background=TEXT_EDITOR_BG)
        self.search_field.bind('<KeyRelease>', self._search_debounced)
        self.search_field.pack(padx=0)
        tk.Label(right_side_panel, pady=10, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                 text="Často použité slová", font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER),
                 anchor='n', justify='left').pack()
        ttk.Separator(right_side_panel, orient='horizontal').pack(fill=tk.X, padx=10)
        right_side_panel_scroll_frame = tk.Frame(right_side_panel, width=10, relief=tk.FLAT, background=PRIMARY_COLOR)
        right_side_panel_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_side_frame_scroll = AutoScrollbar(right_side_panel_scroll_frame, orient='vertical',
                                                style='arrowless.Vertical.TScrollbar', takefocus=False)
        right_side_frame_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.word_freq_text = tk.Text(right_side_panel, highlightthickness=0, bd=0, wrap=tk.WORD, state=tk.DISABLED,
                                      width=20, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                                      yscrollcommand=right_side_frame_scroll.set, cursor="xterm")
        self.word_freq_text.pack(fill=tk.BOTH, expand=1, pady=10, padx=10)
        right_side_frame_scroll.config(command=self.word_freq_text.yview)
        # RICH TEXT EDITOR
        self.text_editor = HTextEditor(self.root, text_editor_frame, self.tooltip, self.doc,
                                       self.close_words_text, self.word_freq_text,
                                       on_word_selected=self.introspect,
                                       on_text_paste=self._on_editor_text_paste,
                                       on_text_analyzed=self._on_text_analyzed,
                                       on_formatting_changed=self._on_formatting_changed
                                       )
        # BOTTOM PANEL CONTENTS
        char_count_info_label = tk.Label(bottom_panel, text="Počet znakov s medzerami:", anchor='sw',
                                         justify='left', background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                                         font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        char_count_info_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        self.char_count_info_value = tk.Label(bottom_panel, text="0", anchor='sw', justify='left',
                                              background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                                              font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.char_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)
        tk.Label(bottom_panel, text="Počet slov:", anchor='sw', justify='left',
                 background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.LEFT, padx=(5, 0), pady=5
        )
        self.word_count_info_value = tk.Label(bottom_panel, text="0", anchor='sw', justify='left',
                                              background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                                              font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.word_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)
        tk.Label(bottom_panel, text="Počet normostrán:", anchor='sw', justify='left',
                 background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.LEFT, padx=(5, 0), pady=5
        )
        self.page_count_info_value = tk.Label(bottom_panel, text="0", anchor='sw', justify='left',
                                              background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                                              font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.page_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)
        tk.Label(bottom_panel, text="Štylistická zložitosť textu:", anchor='sw', justify='left',
                 background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.LEFT, padx=(5, 0), pady=5
        )
        self.readability_value = tk.Label(bottom_panel, text=f"0 / {READABILITY_MAX_VALUE}", anchor='sw',
                                          justify='left',
                                          background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                                          font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.readability_value.pack(side=tk.LEFT, padx=0, pady=5)
        self.editor_text_size_input = ttk.Spinbox(bottom_panel, from_=1, to=30, width=10,
                                                  font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR),
                                                  style='info.TSpinbox', takefocus=False,
                                                  command=lambda: self.set_text_size(self.editor_text_size_input.get()))
        self.editor_text_size_input.set(self.text_editor.text_size)
        self.editor_text_size_input.bind("<Return>", lambda e: self.set_text_size(self.editor_text_size_input.get()))
        self.editor_text_size_input.pack(side=tk.RIGHT)
        tk.Label(bottom_panel, text="Veľkosť textu v editore:", anchor='sw', justify='left',
                 background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.RIGHT, padx=(5, 0), pady=5
        )
        next_search_button.pack(side=tk.RIGHT, padx=2)
        prev_search_button.bind("<Button-1>", self.text_editor.prev_search)
        next_search_button.bind("<Button-1>", self.text_editor.next_search)
        self.search_field.bind('<Return>', self.text_editor.next_search)
        self.search_field.bind('<Shift-Return>', self.text_editor.prev_search)
        # MOUSE AND KEYBOARD BINDINGS
        self.text_editor.bind_events()
        self.root.bind("<Control-F>", self.focus_search)
        self.root.bind("<Control-f>", self.focus_search)
        self.root.bind("<Control-e>", self.text_editor.focus)
        self.root.bind("<Control-E>", self.text_editor.focus)
        self.root.bind("<Button-3>", self.open_context_menu)
        # WINDOWS SPECIFIC
        self.root.bind("<MouseWheel>", self.on_mouse_wheel_event)
        # LINUX SPECIFIC
        self.root.bind("<Button-4>", self.on_mouse_wheel_event)
        self.root.bind("<Button-5>", self.on_mouse_wheel_event)
        self.menu_bar.bind_events()

    # START MAIN LOOP
    def start_main_loop(self):
        # START MAIN LOOP TO SHOW ROOT WINDOW
        if self.ctx.has_available_update:
            self.root.after(1000, self.show_about)

    def set_text_size(self, text_size):
        self.text_editor.set_text_size(text_size)
        self.editor_text_size_input.set(text_size)
        self.editor_text_size_input.select_clear()

    # CHANGE TEXT SIZE WHEN USER SCROLL MOUSEWHEEL WITH CTRL PRESSED
    def on_mouse_wheel_event(self, event):
        # CHECK IF CTRL IS PRESSED
        if event.state & 0x0004:
            # ON WINDOWS IF USER SCROLLS "UP" event.delta IS POSITIVE
            # ON LINUX IF USER SCROLLS "UP" event.num IS 4
            if event.delta > 0 or event.num == 4:
                self.set_text_size(self.text_editor.text_size + 1)
            # ON WINDOWS IF USER SCROLLS "DOWN" event.delta IS NEGATIVE
            # ON LINUX IF USER SCROLLS "DOWN" event.num IS 5
            elif event.delta < 0 or event.num == 5:
                self.set_text_size(self.text_editor.text_size - 1)

    # DISPLAY INFORMATIONS ABOUT TEXT SIZE
    def display_bottom_bar_info(self, doc: Doc):
        self.char_count_info_value.config(text=f"{doc._.total_chars}")
        self.word_count_info_value.config(text=f"{doc._.total_words}")
        self.page_count_info_value.config(text=f"{doc._.total_pages}")
        readability = NlpService.compute_readability(self.doc)
        self.readability_value.configure(text=f"{readability: .0f} / {READABILITY_MAX_VALUE}")
        self.introspect()

    # CALCULATE AND DISPLAY FREQUENT WORDS
    def display_word_frequencies(self, doc: Doc, config: Config):
        if not config.analysis_settings.enable_frequent_words:
            return
        word_counts = NlpService.compute_word_frequencies(doc, config)
        # NOTE
        # In tk, there is problem with scrolling so we default to using on big text to dispaly frequencies
        # There is way of making canvas with scrollregion but this is more performant
        self.word_freq_text.config(state=tk.NORMAL)
        self.word_freq_text.delete(1.0, tk.END)
        start_char = 0
        for word in word_counts:
            word_text = f"{word.text}\t\t{len(word.occourences)}x\n"
            tag_name = f"{FREQUENT_WORD_PREFIX}{word.text}"
            # Insert the text
            self.word_freq_text.insert(tk.END, word_text)
            # Add the tag to the inserted text
            start_index = f"1.0 + {start_char} chars"
            end_index = f"1.0 + {start_char + len(word_text)} chars"
            self.word_freq_text.tag_add(tag_name, start_index, end_index)
            self.word_freq_text.tag_add(FREQUENT_WORD_TAG_NAME, start_index, end_index)
            start_char += len(word_text)
            GuiUtils.bind_tag_mouse_event(tag_name,
                                          self.word_freq_text,
                                          on_enter=lambda e: self.text_editor.highlight_same_word(
                                              e,
                                              self.word_freq_text,
                                              tag_prefix=FREQUENT_WORD_PREFIX,
                                              tooltip="Kliknutím nájsť další výskyt."
                                          ),
                                          on_leave=lambda e: self.text_editor.unhighlight_same_word(e),
                                          on_click=lambda e: self.text_editor.jump_to_next_word_occourence(
                                              e, self.word_freq_text, tag_prefix=FREQUENT_WORD_PREFIX)
                                          )
        self.word_freq_text.config(state=tk.DISABLED)
        # ADD TAG TO ALL OCCOURENCES
        for word in word_counts:
            for occourence in word.occourences:
                start_index = f"1.0 + {occourence.idx} chars"
                end_index = f"1.0 + {occourence.idx + len(occourence.lower_)} chars"
                self.text_editor.tag_add(f'{FREQUENT_WORD_PREFIX}{word.text}', start_index, end_index)

    # HIGHLIGHT WORDS THAT REPEATS CLOSE TO EACH OTHER
    def highlight_close_words(self, config: Config):
        if config.analysis_settings.enable_close_words:
            close_words = self.text_editor.close_words
            # NOTE
            # In tk, there is problem with scrolling so we default to using on big text to dispaly frequencies
            # There is way of making canvas with scrollregion but this is more performant
            self.close_words_text.config(state=tk.NORMAL)
            self.close_words_text.delete(1.0, tk.END)
            panel_start_char = 0
            for word in close_words:
                word_text = f"{word.lower()}\t\t{close_words[word]["total"]}x\n"
                tag_name = f"{CLOSE_WORD_PREFIX}{word}"
                # Insert the text
                self.close_words_text.insert(tk.END, word_text)
                # Add the tag to the inserted text
                panel_start_index = f"1.0 + {panel_start_char} chars"
                panel_end_index = f"1.0 + {panel_start_char + len(word_text)} chars"
                self.close_words_text.tag_add(tag_name, panel_start_index, panel_end_index)
                self.close_words_text.tag_add(CLOSE_WORD_TAG_NAME, panel_start_index, panel_end_index)
                panel_start_char += len(word_text)
                GuiUtils.bind_tag_mouse_event(tag_name,
                                              self.close_words_text,
                                              lambda e: self.text_editor.highlight_same_word(
                                                  e,
                                                  self.close_words_text,
                                                  tooltip="Kliknutím nájsť další výskyt."
                                              ),
                                              lambda e: self.text_editor.unhighlight_same_word(e),
                                              on_click=lambda e: self.text_editor.jump_to_next_word_occourence(
                                                  e, self.close_words_text, tag_prefix=CLOSE_WORD_PREFIX)
                                              )
                word_partitions = close_words[word]["repetition_groups"]

                for word_partition in word_partitions:
                    first_token = word_partition[0]
                    last_token = word_partition[-1]
                    first_token_index = self.text_editor.index(f"1.0+{first_token.idx} chars")
                    first_token_par = first_token_index.split(".")[0]
                    last_token_par = self.text_editor.index(f"1.0+{last_token.idx} chars").split(".")[0]
                    prefix = f"{tag_name}:{CLOSE_WORD_RANGE_PREFIX}"
                    range_tag_name = f"{prefix}{first_token_par}"
                    if len(word_partitions) > 1:
                        partition_text = f" ods.{first_token_par}-{last_token_par} \t\t{len(word_partition)}x\n"
                        panel_start_index = f"1.0 + {panel_start_char} chars"
                        panel_end_index = f"1.0 + {panel_start_char + len(partition_text)} chars"
                        self.close_words_text.insert(tk.END, partition_text)
                        self.close_words_text.tag_add(range_tag_name, panel_start_index, panel_end_index)
                        tooltip = f"Kliknutím prejsť na odsek {first_token_par}."
                        GuiUtils.bind_tag_mouse_event(range_tag_name,
                                                      self.close_words_text,
                                                      lambda e, p=prefix,
                                                             t=tooltip: self.text_editor.highlight_same_word(
                                                          e,
                                                          self.close_words_text,
                                                          tag_prefix=p,
                                                          tooltip=t
                                                      ),
                                                      lambda e: self.text_editor.unhighlight_same_word(e),
                                                      on_click=partial(
                                                          self.text_editor.move_carret,
                                                          first_token_index
                                                      )
                                                      )
                        panel_start_char += len(partition_text)
            self.close_words_text.config(state=tk.DISABLED)

    def undo(self, event=None):
        self.text_editor.edit_undo()
        if self.ctx.current_file is not None:
            self.save_htext_file()
        self.text_editor.analyze_text()
        return 'break'

    def redo(self, event=None):
        self.text_editor.edit_redo()
        if self.ctx.current_file is not None:
            self.save_htext_file()
        self.text_editor.analyze_text()
        return 'break'

    # LOAD TEXT FILE
    def import_file_contents(self, item, file_path):
        text = ImportService.import_document(file_path)
        item.contents = HTextFile(text, [])
        item.imported_path = file_path
        ProjectService.save_file_contents(self.ctx.project, item)
        ProjectService.save(self.ctx.project, self.ctx.project.path)
        self._show_project_files()
        self.open_text_file(item)

    # LOAD TEXT FILE
    def close_project(self, navigate_to_selector=True):
        self.ctx.current_file = None
        self.ctx.project = None
        self.main_frame.destroy()
        self.menu_bar.destroy()
        self.tooltip.destroy()
        if navigate_to_selector:
            Navigator().navigate(Navigator.PROJECT_SELECTOR_WINDOW)

    # noinspection PyMethodMayBeStatic
    def open_recent_project(self, project: RecentProject, e=None):
        self.close_project(navigate_to_selector=False)
        if GuiUtils.open_recent_project(project):
            Navigator().navigate(Navigator.MAIN_WINDOW)
        else:
            Navigator().navigate(Navigator.PROJECT_SELECTOR_WINDOW)

    # LOAD TEXT FILE
    def open_new_file_dialog(self, type_options=None, callback=lambda x: None):
        parent_item = None
        selection = self.project_tree.selection()
        if len(selection) > 0:
            item_id = self.project_tree.selection()[0]
            parent_item = self.project_tree_item_to_project_item.get(item_id, None)
            if parent_item is not None:
                if parent_item.type != ProjectItemType.DIRECTORY:
                    parent_item_id = self.project_tree.parent(item_id)
                    if parent_item_id:
                        parent_item = self.project_tree_item_to_project_item.get(parent_item_id, None)

        modal = NewProjectItemModal(
            self.root,
            parent_item=parent_item,
            type_options=type_options,
            on_new_file=lambda item: Utils.execute_callbacks([self._show_project_files, partial(callback, item)])
        )
        GuiUtils.configure_modal(self.root, modal.toplevel, height=120, width=400)

    def save_htext_file(self):
        if self.ctx.current_file:
            self.ctx.current_file.contents.raw_text = self.text_editor.get_text(1.0, tk.END)
            self.ctx.current_file.contents.formatting = self.text_editor.get_formatting()
            ProjectService.save_file_contents(self.ctx.project, self.ctx.current_file)
        else:
            self.open_new_file_dialog(
                # EXCLUDE DIRECTORY FROM OPTIONS
                type_options={key: val for key, val in ProjectItemType.get_selectable_values().items() if
                              val != ProjectItemType.DIRECTORY},
                callback=lambda item: Utils.execute_callbacks(
                    [partial(self.open_text_file, item), self.save_htext_file]
                ))

    def _on_project_tree_double_click(self, e=None):
        item_id = self.project_tree.selection()[0]
        if item_id:
            item = self.project_tree_item_to_project_item[item_id]
            if item.type == ProjectItemType.HTEXT:
                self.open_text_file(item)

    def _on_project_tree_item_open(self, e=None):
        item_id = self.project_tree.focus()
        if item_id:
            item = self.project_tree_item_to_project_item[item_id]
            if item.type == ProjectItemType.DIRECTORY:
                item.opened = True
                ProjectService.save(self.ctx.project, self.ctx.project.path)

    def _on_project_tree_item_delete(self, e=None):
        item_id = self.project_tree.focus()
        if item_id:
            item = self.project_tree_item_to_project_item.get(item_id, None)
            if item is None:
                return
            parent_item_id = self.project_tree.parent(item_id)
            parent_item = None
            if parent_item_id:
                parent_item = self.project_tree_item_to_project_item.get(parent_item_id, None)
            item_type_label = ProjectItemType.get_translations()[item.type]
            should_delete = messagebox.askyesno(
                f"Vymazať {item_type_label}",
                f"Naozaj chcete vymazať {item_type_label} '{item.name}'?"
            )
            if should_delete:
                ProjectService.delete_item(self.ctx.project, item, parent_item)
                if self.ctx.current_file == item:
                    self.open_text_file(None)
                self._show_project_files()

    def _on_project_tree_item_close(self, e=None):
        item_id = self.project_tree.focus()
        item = self.project_tree_item_to_project_item[item_id]
        if item.type == ProjectItemType.DIRECTORY:
            item.opened = False
            ProjectService.save(self.ctx.project, self.ctx.project.path)

    def open_text_file(self, item):
        if item is not None:
            self.ctx.current_file = item
            self.root.title(f"{item.name} | {self.ctx.project.name} | Hector")
            item.contents = ProjectService.load_file_contents(self.ctx.project, item)
            self.text_editor.set_text(item.contents.raw_text)
            self.text_editor.set_filename(item.name)
            self.text_editor.set_formatting(item.contents.formatting)
            self.text_editor.analyze_text(True)
        else:
            self.ctx.current_file = None
            self.root.title(f"{self.ctx.project.name} | Hector")
            self.text_editor.set_text("")
            self.text_editor.set_filename("(neuloźený súbor)")
            self.text_editor.analyze_text(True)

    # LOAD TEXT FILE
    def import_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Textové súbory", "*.txt"),
                ("Microsoft Word 2007+ dokumenty", "*.docx"),
                ("OpenOffice dokument", "*.odt"),
                ("RTF dokumenty", "*.rtf"),
            ]
        )
        self.open_new_file_dialog(
            # EXCLUDE DIRECTORY FROM OPTIONS
            type_options={key: val for key, val in ProjectItemType.get_selectable_values().items() if
                          val != ProjectItemType.DIRECTORY},
            callback=lambda item: Utils.execute_callbacks(
                [partial(self.import_file_contents, item, file_path)]
            ))

    # RELOAD TEXT FILE
    def reimport_file(self):
        if self.ctx.current_file is None:
            return
        if self.ctx.current_file.imported_path is None:
            return
        if len(self.ctx.current_file.imported_path) < 1:
            return
        if not os.path.exists(self.ctx.current_file.imported_path):
            messagebox.showerror("Chyba", "Previazaný súbor neexistuje.")
            self._show_project_files()
            return
        self.import_file_contents(self.ctx.current_file, self.ctx.current_file.imported_path)

    # SAVE TEXT FILE
    def export_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Textové súbory", "*.txt")])
        text = self.text_editor.get_text(1.0, tk.END)
        ExportService.export_text_file(file_path, text)

    # SAVE SETTINGS TO FILE
    def export_settings(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".hector.conf",
                                                 confirmoverwrite=True,
                                                 filetypes=[("Nastavenia programu Hector", "*.hector.conf")])
        if file_path:
            ConfigService.save(self.ctx.global_config, file_path)

    # IMPORT SETTINGS FROM A FILE
    def import_settings(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Nastavenia programu Hector", "*.hector.conf")]
        )
        self.ctx.global_config = ConfigService.load(file_path)
        ConfigService.save(self.ctx.global_config, CONFIG_FILE_PATH)
        self.text_editor.analyze_text(True)

    def export_sentences(self, event=None):
        add_more_blank_lines = messagebox.askyesnocancel("Zalomenie textu", "Pridať medzi vety prázdny riadok?")
        if add_more_blank_lines is None:
            # USER HAS CANCELLED FUNCTION
            return 'break'
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Textové súbory", "*.txt")])
        if file_path:
            ExportService.export_sentences(file_path, self.doc, add_more_blank_lines)
        return 'break'

    def _on_editor_text_paste(self):
        if self.ctx.current_file is not None:
            self.save_htext_file()

    def _on_text_analyzed(self, doc: Doc):
        self.introspect()
        if self.search_debounce_timer is not None:
            self.root.after_cancel(self.search_debounce_timer)
            self.search_debounce_timer = None
        self.doc = doc
        self.display_bottom_bar_info(doc)
        config = ConfigService.select_config(self.ctx.global_config, self.ctx.project, self.ctx.current_file)
        self.display_word_frequencies(doc, config)
        self.highlight_close_words(config)
        self.close_words_text.tag_raise("sel")
        self.word_freq_text.tag_raise("sel")
        if self.ctx.current_file is not None:
            self.save_htext_file()

    def _on_formatting_changed(self):
        if self.ctx.current_file is not None:
            self.save_htext_file()

    def introspect(self):
        carret_position = self.text_editor.get_carret_position(tk.INSERT)
        if carret_position is None:
            GuiUtils.set_text(self.introspection_text, 'Kliknite na slovo v editore')
            return
        span = self.doc.char_span(carret_position, carret_position, alignment_mode='expand')
        if span is not None and len(span.text) > 0 and self.current_instrospection_token != span.root:
            if span.root._.is_word:
                self.current_instrospection_token = span.root
                if ENABLE_DEBUG_DEP_IMAGE:
                    svg = io.StringIO(displacy.render(span.root.sent, minify=True))
                    rlg = svg2rlg(svg)
                    dep_image = renderPM.drawToPIL(rlg)
                    scaling_ratio = 200 / dep_image.width
                    dep_view = ImageTk.PhotoImage(dep_image.resize((200, math.ceil(dep_image.height * scaling_ratio))))
                    self.dep_image_holder.config(image=dep_view)
                    self.dep_image_holder.image = dep_view
                thes_result = self.ctx.thesaurus.lookup(self.current_instrospection_token.lemma_)
                morph = self.current_instrospection_token.morph.to_dict()
                formatted_morph = ''.join([f"  {key}:\t{value}\n" for key, value in morph.items()])

                introspection_resut = f'Slovo: {self.current_instrospection_token}\n\n' \
                                      f'Základný tvar: {self.current_instrospection_token.lemma_}\n' \
                                      f'Komentár: {self.current_instrospection_token._.lemma_comments}\n' \
                                      f'Morfológia: \n' \
                                      f'{formatted_morph}\n' \
                                      f'PDT tag: {self.current_instrospection_token._.pdt_morph}\n' \
                                      f'Slovný druh: {POS_TAG_TRANSLATIONS[self.current_instrospection_token.pos_]}\n' \
                                      f'Vetný člen: {DEP_TAG_TRANSLATION[self.current_instrospection_token.dep_.lower()]}'
                if thes_result is not None:
                    introspection_resut += '\n\nSynonymá\n\n'
                    for mean in thes_result.mean_tuple:
                        introspection_resut += f'{mean.main}: {", ".join(mean.syn_tuple)}\n'
                GuiUtils.set_text(self.introspection_text, introspection_resut)

    # RUN SEARCH ONE SECOND AFTER LAST CHANGE
    def _search_debounced(self, event=None):
        if self.search_debounce_timer is not None:
            self.root.after_cancel(self.search_debounce_timer)
        self.search_debounce_timer = self.root.after(1000, self.text_editor.search_text, self.search_field.get())

    def focus_search(self, event=None):
        self.search_field.focus()
        return

    def open_context_menu(self, event):
        context_menu_items = []
        if GuiUtils.is_child_of(self.project_tree, event.widget):
            # THIS IS CLICK ON PROJECT TREE MENU
            # ADD NEW FILE OPTION
            context_menu_items.append(MenuItem(label="Nový súbor", command=self.open_new_file_dialog))
            iid = self.project_tree.identify_row(event.y)
            if iid and iid != self.project_tree_root:
                # IF USER CLICKED ON ITEM, FOCUS IT AND ADD DELETE FILE OPTION
                self.project_tree.selection_set(iid)
                self.project_tree.focus(iid)
                item = self.project_tree_item_to_project_item[iid]
                context_menu_items.append(
                    MenuItem(
                        label="Vymazať",
                        command=partial(self._on_project_tree_item_delete, event)
                    )
                )
                context_menu_items.append(
                    MenuItem(
                        label="Prispôsobiť nastavenia analýzy",
                        command=partial(self.show_analysis_settings, item.config, ConfigLevel.ITEM, item)
                    )
                )
        if GuiUtils.is_child_of(self.text_editor.text_editor_frame, event.widget):
            # THIS IS CLICK ON EDITOR
            clicked_text_index = self.text_editor.index(tk.CURRENT)
            # ADD PASTE OPTION, IF CLIPBOARDS CONTAINS ANYTHING
            try:
                clipboard_text = event.widget.selection_get(selection='CLIPBOARD')
            except tk.TclError:
                clipboard_text = None
            if clipboard_text:
                context_menu_items.append(MenuItem(
                    label="Prilepiť",
                    shortcut_label="Ctrl+V",
                    command=lambda: Utils.execute_callbacks(
                        [
                            partial(self.text_editor.move_carret, clicked_text_index),
                            partial(self.text_editor.handle_clipboard_paste, event)
                        ]
                    )
                ))
            # ADD COPY OPTION IF EDITOR HAS SELECTED TEXT
            if event.widget.tag_ranges(tk.SEL):
                context_menu_items.append(MenuItem(
                    label="Kopírovať",
                    shortcut_label="Ctrl+C",
                    command=partial(GuiUtils.copy_to_clipboard, self.root, event.widget.selection_get())
                ))

            # IF CLICKED WORD HAS GRAMMAR ERROR, APPEND SUGGESTIONS
            clicked_text_char_position = self.text_editor.get_carret_position(tk.CURRENT)
            if clicked_text_char_position is not None:
                span = self.doc.char_span(clicked_text_char_position, clicked_text_char_position,
                                          alignment_mode='expand')
                if span is not None and len(span.text) > 0 and span.root._.is_word:
                    token = span.root
                    if token._.has_grammar_error:
                        # FOR NOW, WE SUPPORT ONLY HUNSPELL SUGGESTIONS, BUT WE MAY PROVIDE SUGGESTION
                        # FOR MORE ADVANCED SPELLCHECKS IN FUTURE
                        if token._.grammar_error_type == GRAMMAR_ERROR_TYPE_MISSPELLED_WORD:
                            suggestions = self.ctx.spellcheck_dictionary.suggest(token.text)
                            for index, suggestion in enumerate(suggestions):
                                s = suggestion
                                context_menu_items.append(
                                    MenuItem(
                                        label=s,
                                        command=partial(
                                            self.text_editor.apply_suggestion,
                                            span, s, event, clicked_text_index
                                        )
                                    )
                                )

        # IF WE HAVE ANY CONTEXT MENU ITEMS TO DISPLAY SHOW MENU
        if len(context_menu_items) > 0:
            self.context_menu.show(context_menu_items, event)
        return

    # SHOW SETTINGS WINDOW
    def show_analysis_settings(self, c, config_level: ConfigLevel, item: ProjectItem = None):
        if c is None and config_level == ConfigLevel.ITEM:
            i = item
            while i is not None:
                if i.config is None:
                    i = i.parent
                else:
                    c = Config(i.config.to_dict())
                    break
            if c is None and self.ctx.project.config is not None:
                c = Config(self.ctx.project.config.to_dict())
        if c is None:
            c = Config(self.ctx.global_config.to_dict())
        settings_window = AnalysisSettingsModal(self.root, c, lambda: self.text_editor.analyze_text(True), config_level,
                                                item)
        GuiUtils.configure_modal(self.root, settings_window.toplevel, height=660, width=780)

    # SHOW SETTINGS WINDOW
    def show_appearance_settings(self):
        settings_window = AppearanceSettingsModal(self.root, self.ctx.global_config, lambda: self.text_editor.analyze_text(True))
        GuiUtils.configure_modal(self.root, settings_window.toplevel, height=150, width=780)

    # SHOW ABOUT DIALOG
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("O programe")
        GuiUtils.configure_modal(self.root, about_window)
        about_text = tk.Label(about_window, font=(HELVETICA_FONT_NAME, 10), justify=tk.LEFT, wraplength=550, pady=10,
                              text=f"Hector - Analyzátor textu\nVerzia {Utils.get_version_info()}\n\n"
                                   f"Hector je jednoduchý nástroj pre "
                                   f"autorov textov, ktorého cieľom je poskytnúť základnú štylistickú podporu. Je to "
                                   f"plne konfigurovateľný nástroj, ktorý automaticky analyzuje a vyhodnocuje text. "
                                   f"Cieľom programu nie je dodať zoznam problémov, ktoré má autor určite opraviť, "
                                   f"ale len zvýrazniť potenciálne problematické časti. Konečné rozhodnutie je vždy "
                                   f"na autorovi.",
                              )
        about_text.pack()
        link = tk.Label(about_window, text="Viac info", fg="blue", cursor="hand2", font=(HELVETICA_FONT_NAME, 10))
        link.pack()
        link.bind("<Button-1>", lambda e: webbrowser.open(DOCUMENTATION_LINK))
        if self.ctx.has_available_update:
            new_version_button = tk.Label(about_window, text="K dispozícií je nová verzia", fg="blue", cursor="hand2",
                                          font=(HELVETICA_FONT_NAME, 10))
            new_version_button.pack()
            new_version_button.bind("<Button-1>", lambda e: webbrowser.open(DOCUMENTATION_LINK))

    # SHOW ABOUT DIALOG
    def update_dictionaries(self):
        splash = SplashWindow(self.root)
        # noinspection PyBroadException
        splash.update_status("aktualizujem a reinicializujem slovníky...")
        dictionaries = SpellcheckService.upgrade_dictionaries()
        splash.close()
        self.root.deiconify()
        if platform.system() == "Windows" or platform.system() == "Darwin":
            self.root.state("zoomed")
        else:
            self.root.attributes('-zoomed', True)
        if dictionaries is not None:
            self.ctx.spellcheck_dictionary = dictionaries["spellcheck"]
            self.ctx.thesaurus = dictionaries["thesaurus"]
        else:
            messagebox.showerror("Chyba!", "Slovníky sa nepodarilo aktualizovať. Skontrolujte internetové pripojenie.")

    def show_dep_image(self, event=None):
        if self.current_instrospection_token is not None:
            dep_window = tk.Toplevel(self.root)
            dep_window.title("Rozbor vety")
            svg = io.StringIO(displacy.render(self.current_instrospection_token.sent, minify=True))
            rlg = svg2rlg(svg)
            dep_image = renderPM.drawToPIL(rlg)
            scaling_ratio = 1000 / dep_image.width
            dep_view = ImageTk.PhotoImage(dep_image.resize((1000, math.ceil(dep_image.height * scaling_ratio))))
            image_holder = ttk.Label(dep_window, image=dep_view)
            image_holder.image = dep_view
            image_holder.pack(fill=tk.BOTH, expand=True)
            GuiUtils.configure_modal(self.root, dep_window, width=dep_view.width(), height=dep_view.height())

    def _show_project_files(self):
        items = self.project_tree.get_children(self.project_tree_root)
        self.project_tree_item_to_project_item.clear()
        if len(items) > 0:
            for item in items:
                self.project_tree.delete(item)
        for item in self.ctx.project.items:
            self._append_project_file_to_tree(item, self.project_tree_root)

    def _append_project_file_to_tree(self, item, parent_tree_item):
        if item.type == ProjectItemType.HTEXT:
            image = self.htext_image
            if item.imported_path is not None and len(item.imported_path) > 0:
                if os.path.exists(item.imported_path):
                    image = self.htext_image_with_link
                else:
                    image = self.htext_image_with_broken_link
            item_id = self.project_tree.insert(parent_tree_item, tk.END, image=image,
                                               text=item.name)
            self.project_tree_item_to_project_item[item_id] = item
        elif item.type == ProjectItemType.DIRECTORY:
            item_id = self.project_tree.insert(parent_tree_item, tk.END, image=self.directory_image,
                                               text=item.name, open=item.opened)
            self.project_tree_item_to_project_item[item_id] = item
            if item.subitems is not None:
                for subitem in item.subitems:
                    self._append_project_file_to_tree(subitem, item_id)
