import io
import json
import math
import os
import platform
import random
import re
import tkinter as tk
import webbrowser
from functools import partial
from tkinter import filedialog, ttk, messagebox

from PIL import ImageTk, Image
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
    TEXT_EDITOR_BG, EDITOR_TEXT_COLOR, CLOSE_WORDS_PALLETE, LONG_SENTENCE_HIGHLIGHT_COLOR_MID, \
    LONG_SENTENCE_HIGHLIGHT_COLOR_HIGH, SEARCH_RESULT_HIGHLIGHT_COLOR, CURRENT_SEARCH_RESULT_HIGHLIGHT_COLOR, \
    TRANSPARENT
from src.const.font_awesome_icons import FontAwesomeIcons
from src.const.fonts import HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER, TEXT_SIZE_BOTTOM_BAR, BOLD_FONT, FA_SOLID
from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD, GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX, \
    GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX, \
    GRAMMAR_ERROR_NON_LITERAL_WORD, NON_LITERAL_WORDS, GRAMMAR_ERROR_S_INSTEAD_OF_Z, \
    GRAMMAR_ERROR_Z_INSTEAD_OF_S, GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO, GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR, \
    GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING
from src.const.paths import CONFIG_FILE_PATH, METADATA_FILE_PATH
from src.const.tags import CLOSE_WORD_PREFIX, LONG_SENTENCE_TAG_NAME_HIGH, LONG_SENTENCE_TAG_NAME_MID, \
    PARAGRAPH_TAG_NAME, TRAILING_SPACES_TAG_NAME, MULTIPLE_PUNCTUATION_TAG_NAME, MULTIPLE_SPACES_TAG_NAME, \
    SEARCH_RESULT_TAG_NAME, CURRENT_SEARCH_RESULT_TAG_NAME, GRAMMAR_ERROR_TAG_NAME, CLOSE_WORD_TAG_NAME, \
    FREQUENT_WORD_PREFIX, FREQUENT_WORD_TAG_NAME, COMPUTER_QUOTE_MARKS_TAG_NAME, DANGLING_QUOTE_MARK_TAG_NAME, \
    SHOULD_USE_LOWER_QUOTE_MARK_TAG_NAME, SHOULD_USE_UPPER_QUOTE_MARK_TAG_NAME, FORMATTING_TAGS, CLOSE_WORD_RANGE_PREFIX
from src.const.values import READABILITY_MAX_VALUE, DOCUMENTATION_LINK, NLP_BATCH_SIZE
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
from src.gui.widgets.tooltip import Tooltip
from src.gui.window.splash_window import SplashWindow
from src.utils import Utils

# A4 SIZE IN INCHES. WE LATER USE DPI TO SET EDITOR WIDTH
A4_SIZE_INCHES = 8.27

EDITOR_LOGO_HEIGHT = 300
EDITOR_LOGO_WIDTH = 300
NLP_DEBOUNCE_LENGTH = 500
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
        # TIMERS FOR DEBOUNCING CHANGE EVENTS
        self.analyze_text_debounce_timer = None
        self.search_debounce_timer = None
        # SEARCH DATA
        self.search_matches = []
        self.last_search = ''
        self.last_match_index = 0
        # CLOSE WORD, THAT IS CURRENTLY HIGHLIGHTED
        self.highlighted_word = ''
        # TOOLTIP WINDOW
        self.tooltip = Tooltip(self.root)
        self.last_tags = set()

        # DEFAULT NLP DOCUMENT INITIALIZED ON EMPTY TEXT
        self.doc = self.ctx.nlp('')
        # TOKEN SELECTED IN LEFT BOTTOM INTOSPECTION WINDOW
        self.current_instrospection_token = None
        # EDITOR TEXT SIZE
        self.text_size = 10
        # DICTIONARY THAT HOLDS COLOR OF WORD TO PREVENT RECOLORING WHILE TYPING
        self.close_word_colors = {}
        # LOAD CONFIG
        self.config = ConfigService.load(CONFIG_FILE_PATH)
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
                                  command=self.save_text_file,
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
                         command=lambda: self.analyze_text(force_reload=True),
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
                        self.config,
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
        text_editor_scroll_frame = tk.Frame(text_editor_frame, width=10, relief=tk.FLAT, background=PRIMARY_COLOR)
        text_editor_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        text_editor_scroll = AutoScrollbar(text_editor_scroll_frame, orient='vertical',
                                           style='arrowless.Vertical.TScrollbar', takefocus=False)
        text_editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
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
        MainWindow.set_text(self.introspection_text, 'Kliknite na slovo v editore')
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
        # MIDDLE TEXT EDITOR CONTENTS
        dpi = self.root.winfo_fpixels('1i')
        text_editor_outer_frame = tk.Frame(text_editor_frame, borderwidth=0, width=int(A4_SIZE_INCHES * dpi),
                                           relief=tk.RAISED, background=TEXT_EDITOR_BG)
        text_editor_outer_frame.pack(expand=True, fill=tk.Y, padx=5, pady=10, )
        self.text_editor = tk.Text(text_editor_outer_frame, wrap=tk.WORD, relief=tk.RAISED, highlightthickness=0,
                                   yscrollcommand=text_editor_scroll.set, background=TEXT_EDITOR_BG,
                                   foreground=EDITOR_TEXT_COLOR, borderwidth=0,
                                   spacing1=1.2, spacing2=1.2, spacing3=1.2, undo=True, autoseparators=True, maxundo=-1,
                                   insertbackground=PANEL_TEXT_COLOR)
        self.text_editor.config(font=(HELVETICA_FONT_NAME, self.text_size), )
        self.text_editor.pack(expand=1, fill=tk.BOTH, padx=20, pady=20)
        text_editor_outer_frame.pack_propagate(False)
        image = Image.open(Utils.resource_path("images/hector-logo.png"))
        logo = ImageTk.PhotoImage(image.resize((EDITOR_LOGO_WIDTH, EDITOR_LOGO_HEIGHT)))
        self.logo_holder = ttk.Label(text_editor_frame, image=logo, background=TEXT_EDITOR_BG)
        self.logo_holder.image = logo
        text_editor_scroll.config(command=self.text_editor.yview)
        # RIGHT PANEL CONTENTS
        tk.Label(right_side_panel, pady=10, compound=tk.LEFT, background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                 text="Hľadať", font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER),
                 anchor='n', justify='left').pack(fill=tk.X)
        search_frame = tk.Frame(right_side_panel, relief=tk.FLAT, background=PRIMARY_COLOR)
        search_frame.pack(fill=tk.X, padx=0)
        prev_search_button = tk.Label(search_frame, text="⮝", background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                                      cursor="hand2")
        prev_search_button.pack(side=tk.RIGHT, padx=2)
        prev_search_button.bind("<Button-1>", self.prev_search)
        next_search_button = tk.Label(search_frame, text="⮟", background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR,
                                      cursor="hand2")
        next_search_button.pack(side=tk.RIGHT, padx=2)
        next_search_button.bind("<Button-1>", self.next_search)
        self.search_field = ttk.Entry(search_frame, width=22, background=TEXT_EDITOR_BG)
        self.search_field.bind('<KeyRelease>', self._search_debounced)
        self.search_field.bind('<Return>', self.next_search)
        self.search_field.bind('<Shift-Return>', self.prev_search)
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
        self.editor_text_size_input.set(self.text_size)
        self.editor_text_size_input.bind("<Return>", lambda e: self.set_text_size(self.editor_text_size_input.get()))
        self.editor_text_size_input.pack(side=tk.RIGHT)
        tk.Label(bottom_panel, text="Veľkosť textu v editore:", anchor='sw', justify='left',
                 background=ACCENT_2_COLOR, foreground=PANEL_TEXT_COLOR,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.RIGHT, padx=(5, 0), pady=5
        )
        # MOUSE AND KEYBOARD BINDINGS
        self.text_editor.unbind('<Control-z>')
        self.text_editor.unbind('<Control-Z>')
        self.text_editor.unbind('<Control-y>')
        self.text_editor.unbind('<Control-Y>')
        self.text_editor.unbind('<Control-Shift-z>')
        self.text_editor.unbind('<Control-Shift-Z>')
        self.text_editor.bind("<KeyRelease>", self._analyze_text_debounced)
        self.text_editor.bind("<Button-1>", lambda e: self.root.after(0, self.introspect))
        self.text_editor.bind("<Control-a>", self.select_all)
        self.text_editor.bind("<Control-A>", self.select_all)
        self.text_editor.bind("<<Paste>>", self.handle_clipboard_paste)
        self.text_editor.bind('<Motion>', self.editor_on_mouse_motion)
        self.text_editor.bind('<Leave>', self.editor_on_mouse_leave)
        self.root.bind("<Control-F>", self.focus_search)
        self.root.bind("<Control-f>", self.focus_search)
        self.root.bind("<Control-e>", self.focus_editor)
        self.root.bind("<Control-E>", self.focus_editor)
        self.root.bind("<Button-3>", self.open_context_menu)
        # WINDOWS SPECIFIC
        self.root.bind("<MouseWheel>", self.change_text_size)
        # LINUX SPECIFIC
        self.root.bind("<Button-4>", self.change_text_size)
        self.root.bind("<Button-5>", self.change_text_size)
        self.menu_bar.bind_events()

    # START MAIN LOOP
    def start_main_loop(self):
        # START MAIN LOOP TO SHOW ROOT WINDOW
        if self.ctx.has_available_update:
            self.root.after(1000, self.show_about)

    # UTIL METHOD TO SET tk.TEXT WIDGET
    # WE NEED TO ENBLE TEXT, DELETE CONTENT AND INSERT NEW TEXT
    @staticmethod
    def set_text(text: tk.Text, value, editable=False):
        text.config(state=tk.NORMAL)
        text.delete(1.0, tk.END)
        text.insert(tk.END, value)
        if not editable:
            text.config(state=tk.DISABLED)

    def get_carret_position(self, index_name=tk.INSERT):
        possible_carret = self.text_editor.count("1.0", self.text_editor.index(index_name), "chars")
        if possible_carret is None:
            return None
        return possible_carret[0]

    def set_text_size(self, text_size):
        self.text_size = min(30, max(1, int(text_size)))
        self.editor_text_size_input.set(self.text_size)
        self.editor_text_size_input.select_clear()
        # CHANGE FONT SIZE IN EDITOR
        self.text_editor.config(font=(HELVETICA_FONT_NAME, self.text_size))
        # CLOSE WORDS ARE ALWAYS HIGHLIGHTED WITH BIGGER FONT. WE NEED TO UPDATE TAGS
        for tag in self.text_editor.tag_names():
            if tag.startswith(CLOSE_WORD_PREFIX):
                self.text_editor.tag_configure(tagName=tag,
                                               font=(HELVETICA_FONT_NAME, self.text_size + 2, BOLD_FONT))

    # CHANGE TEXT SIZE WHEN USER SCROLL MOUSEWHEEL WITH CTRL PRESSED
    def change_text_size(self, event):
        # CHECK IF CTRL IS PRESSED
        if event.state & 0x0004:
            # ON WINDOWS IF USER SCROLLS "UP" event.delta IS POSITIVE
            # ON LINUX IF USER SCROLLS "UP" event.num IS 4
            if event.delta > 0 or event.num == 4:
                self.set_text_size(self.text_size + 1)
            # ON WINDOWS IF USER SCROLLS "DOWN" event.delta IS NEGATIVE
            # ON LINUX IF USER SCROLLS "DOWN" event.num IS 5
            elif event.delta < 0 or event.num == 5:
                self.set_text_size(self.text_size - 1)

    # DISPLAY INFORMATIONS ABOUT TEXT SIZE
    def display_size_info(self, doc: Doc):
        self.char_count_info_value.config(text=f"{doc._.total_chars}")
        self.word_count_info_value.config(text=f"{doc._.total_words}")
        self.page_count_info_value.config(text=f"{doc._.total_pages}")

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
                                          on_enter=lambda e: self.highlight_same_word(
                                              e,
                                              self.word_freq_text,
                                              tag_prefix=FREQUENT_WORD_PREFIX,
                                              tooltip="Kliknutím nájsť další výskyt."
                                          ),
                                          on_leave=lambda e: self.unhighlight_same_word(e),
                                          on_click=lambda e: self.jump_to_next_word_occourence(
                                              e, self.word_freq_text, tag_prefix=FREQUENT_WORD_PREFIX)
                                          )
        self.word_freq_text.config(state=tk.DISABLED)
        # ADD TAG TO ALL OCCOURENCES
        for word in word_counts:
            for occourence in word.occourences:
                start_index = f"1.0 + {occourence.idx} chars"
                end_index = f"1.0 + {occourence.idx + len(occourence.lower_)} chars"
                self.text_editor.tag_add(f'{FREQUENT_WORD_PREFIX}{word.text}', start_index, end_index)

    # HIGHLIGHT LONG SENTENCES
    def highlight_long_sentences(self, doc: Doc, config: Config):
        if not config.analysis_settings.enable_long_sentences:
            return
        doc_size = len(doc.text)
        doc_text = doc.text
        for sentence in doc.sents:
            if sentence._.is_long_sentence or sentence._.is_mid_sentence:
                start = sentence.start_char
                while start < doc_size - 1 and (doc_text[start] == '\n' or doc_text[start] == '\r'):
                    start += 1
                start_index = f"1.0 + {start} chars"
                end_index = f"1.0 + {sentence.end_char} chars"
                if sentence._.is_long_sentence:
                    self.text_editor.tag_add(LONG_SENTENCE_TAG_NAME_HIGH, start_index, end_index)
                else:
                    self.text_editor.tag_add(LONG_SENTENCE_TAG_NAME_MID, start_index, end_index)

    # HIGHLIGHT MULTIPLE SPACES
    def highlight_multiple_spaces(self, doc: Doc, config: Config):
        self.text_editor.tag_remove(MULTIPLE_SPACES_TAG_NAME, "1.0", tk.END)
        if config.analysis_settings.enable_multiple_spaces:
            matches = NlpService.find_multiple_spaces(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(MULTIPLE_SPACES_TAG_NAME, start_index, end_index)

    # HIGHLIGHT MULTIPLE PUNCTUATION
    def highlight_multiple_punctuation(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_multiple_punctuation:
            matches = NlpService.find_multiple_punctuation(doc)
            for match in matches:
                if match.group() not in ["?!"]:
                    start_index = f"1.0 + {match.start()} chars"
                    end_index = f"1.0 + {match.end()} chars"
                    self.text_editor.tag_add(MULTIPLE_PUNCTUATION_TAG_NAME, start_index, end_index)

    # HIGHLIGHT TRAILING SPACES
    def highlight_trailing_spaces(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_trailing_spaces:
            matches = NlpService.find_trailing_spaces(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(TRAILING_SPACES_TAG_NAME, start_index, end_index)

    # HIGHLIGHT QUOTE_MARK_ERRORS
    def highlight_quote_mark_errors(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_quote_corrections:
            matches = NlpService.find_computer_quote_marks(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(COMPUTER_QUOTE_MARKS_TAG_NAME, start_index, end_index)
            matches = NlpService.find_dangling_quote_marks(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(DANGLING_QUOTE_MARK_TAG_NAME, start_index, end_index)
            matches = NlpService.find_incorrect_lower_quote_marks(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(SHOULD_USE_UPPER_QUOTE_MARK_TAG_NAME, start_index, end_index)
            matches = NlpService.find_incorrect_upper_quote_marks(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(SHOULD_USE_LOWER_QUOTE_MARK_TAG_NAME, start_index, end_index)

    # HIGHLIGHT WORDS THAT REPEATS CLOSE TO EACH OTHER
    def highlight_close_words(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_close_words:
            self.text_editor.tag_remove("close_word", "1.0", tk.END)
            close_words = NlpService.evaluate_close_words(doc, config)
            # NOTE
            # In tk, there is problem with scrolling so we default to using on big text to dispaly frequencies
            # There is way of making canvas with scrollregion but this is more performant
            self.close_words_text.config(state=tk.NORMAL)
            self.close_words_text.delete(1.0, tk.END)
            panel_start_char = 0
            for word in close_words:
                total_repetitions = len(close_words[word])
                word_text = f"{word.lower()}\t\t{total_repetitions}x\n"
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
                                              lambda e: self.highlight_same_word(
                                                  e,
                                                  self.close_words_text,
                                                  tooltip="Kliknutím nájsť další výskyt."
                                              ),
                                              lambda e: self.unhighlight_same_word(e),
                                              on_click=lambda e: self.jump_to_next_word_occourence(
                                                  e, self.close_words_text, tag_prefix=CLOSE_WORD_PREFIX)
                                              )
                word_partitions = NlpService.partition_close_words(
                    close_words[word],
                    config.analysis_settings.close_words_min_distance_between_words
                )

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
                                                      lambda e, p=prefix, t=tooltip: self.highlight_same_word(
                                                          e,
                                                          self.close_words_text,
                                                          tag_prefix=p,
                                                          tooltip=t
                                                      ),
                                                      lambda e: self.unhighlight_same_word(e),
                                                      on_click=lambda e, fti=first_token_index: self.move_carret(fti)
                                                      )
                        panel_start_char += len(partition_text)
                    for occ in word_partition:
                        color = random.choice(CLOSE_WORDS_PALLETE)
                        start_index = f"1.0 + {occ.idx} chars"
                        end_index = f"1.0 + {occ.idx + len(occ.lower_)} chars"
                        tag_name = f"{CLOSE_WORD_PREFIX}{word}"
                        original_color = self.close_word_colors.get(tag_name, "")
                        if original_color != "":
                            color = original_color
                        else:
                            self.close_word_colors[tag_name] = color
                        self.text_editor.tag_add(tag_name, start_index, end_index)
                        self.text_editor.tag_add(range_tag_name, start_index, end_index)
                        self.text_editor.tag_add(CLOSE_WORD_TAG_NAME, start_index, end_index)
                        self.text_editor.tag_config(tag_name, foreground=color,
                                                    font=(HELVETICA_FONT_NAME, self.text_size + 2, BOLD_FONT))
            self.close_words_text.config(state=tk.DISABLED)

    # HIGHLIGHT SAME WORD ON MOUSE OVER
    def highlight_same_word(self, event, trigger, tag_prefix=CLOSE_WORD_PREFIX, tooltip=None):
        self.unhighlight_same_word(event)
        # Získanie indexu myši
        mouse_index = trigger.index(f"@{event.x},{event.y}")
        if tooltip is not None:
            abs_x = trigger.winfo_rootx() + event.x
            abs_y = trigger.winfo_rooty() + event.y
            self.tooltip.show(tooltip, abs_x, abs_y)
        # Získanie všetkých tagov na pozícii myši
        tags_at_mouse = trigger.tag_names(mouse_index)
        self.word_freq_text.config(cursor="hand2")
        self.close_words_text.config(cursor="hand2")
        for tag in tags_at_mouse:
            if tag.startswith(tag_prefix):
                self.highlighted_word = tag
                self.text_editor.tag_config(tag, background="white", foreground="black")
                self.close_words_text.tag_config(tag, background="white", foreground="black")
                self.word_freq_text.tag_config(tag, background="white", foreground="black")

    # FOCUS NEXT WORD OCCOURENCE
    def jump_to_next_word_occourence(self, event, trigger, tag_prefix=CLOSE_WORD_PREFIX):
        self.text_editor.focus_set()
        # Získanie indexu myši
        mouse_index = trigger.index(f"@{event.x},{event.y}")
        # Získanie všetkých tagov na pozícii myši
        tags_at_mouse = trigger.tag_names(mouse_index)
        for tag in tags_at_mouse:
            if tag.startswith(tag_prefix):
                next_range = self.text_editor.tag_nextrange(tag, self.text_editor.index(tk.INSERT))
                if not next_range:
                    next_range = self.text_editor.tag_nextrange(tag, '0.0')
                if next_range:
                    self.move_carret(next_range[1])
        return "break"

    # MOVES CARRET TO DIFFERENT POSITION AND ENSURES IT IS IN FOCUS
    def move_carret(self, index):
        self.text_editor.see(index)
        self.text_editor.mark_set(tk.INSERT, index)

    # REMOVE HIGHLIGHTING FROM SAME WORD ON MOUSE OVER END
    def unhighlight_same_word(self, event):
        if self.highlighted_word is not None and len(self.highlighted_word) > 0:
            tags = [self.highlighted_word]
            parts = self.highlighted_word.split(":")
            if len(parts) > 1:
                tags.append(parts[0])
            for tag in tags:
                self.word_freq_text.config(cursor="xterm")
                self.close_words_text.config(cursor="xterm")
                original_color = self.close_word_colors.get(tag, "")
                self.text_editor.tag_config(tag, background="", foreground=original_color)
                self.close_words_text.tag_config(tag, background="", foreground="")
                self.word_freq_text.tag_config(tag, background="", foreground="")
            self.tooltip.hide()
            self.highlighted_word = None

    # HANDLE EVENT MOUSE MOTION EVENT
    def editor_on_mouse_motion(self, event):
        x, y = event.x, event.y
        index = self.text_editor.index(f"@{x},{y}")
        current_tags = set(self.text_editor.tag_names(index)) - FORMATTING_TAGS
        if current_tags != self.last_tags:
            if current_tags:
                # There are tags under the mouse
                error_messages = self.convert_tags_to_error_messages(current_tags, index)
                if error_messages:
                    tooltip_text = "\n---\n".join(error_messages)
                    # Get the absolute position of the mouse
                    abs_x = self.text_editor.winfo_rootx() + x
                    abs_y = self.text_editor.winfo_rooty() + y
                    self.tooltip.show(tooltip_text, abs_x, abs_y)
                else:
                    self.tooltip.hide()
            else:
                # No tags under the mouse
                self.tooltip.hide()
        self.last_tags = current_tags

    # CONVERT SET OF TAGS (USUALLY UNDER CURSOR) TO SET OF ERROR MESSAGES FOR USER
    def convert_tags_to_error_messages(self, current_tags, index):
        error_messages = set()
        tag_message_map = {
            LONG_SENTENCE_TAG_NAME_MID: 'Táto veta je trochu dlhšia.',
            LONG_SENTENCE_TAG_NAME_HIGH: 'Táto veta je dlhá.',
            MULTIPLE_PUNCTUATION_TAG_NAME: 'Viacnásobná interpunkcia.',
            TRAILING_SPACES_TAG_NAME: 'Zbytočná medzera na konci odstavca.',
            COMPUTER_QUOTE_MARKS_TAG_NAME: 'Počítačová úvodzovka. V beletrii by sa mali používať '
                                           'slovenské úvodzovky „ “.\n\nPOZOR! Nesprávne úvodzovky '
                                           'môžu narušiť správne určenie hraníc viet!',
            DANGLING_QUOTE_MARK_TAG_NAME: 'Úvodzovka by nemala mať medzeru z oboch strán.',
            SHOULD_USE_LOWER_QUOTE_MARK_TAG_NAME: 'Tu by mala byť použitá spodná („) úvozdovka.',
            SHOULD_USE_UPPER_QUOTE_MARK_TAG_NAME: 'Tu by mala byť použitá horná (“) úvozdovka.',
            MULTIPLE_SPACES_TAG_NAME: 'Viacnásobná medzera.',
            CLOSE_WORD_TAG_NAME: 'Toto slovo sa opakuje viackrát na krátkom úseku'
        }

        for tag in current_tags:
            if tag in tag_message_map:
                # MAP SIMPLE ERRORS
                error_messages.add(tag_message_map[tag])
            elif tag == GRAMMAR_ERROR_TAG_NAME:
                # SPECIAL HANDLING FOR GRAMMAR_ERRORS
                word_position = self.text_editor.count("1.0", index, "chars")
                if word_position is not None:
                    span = self.doc.char_span(word_position[0], word_position[0], alignment_mode='expand')
                    if span is not None:
                        token = span.root
                        grammar_error_map = {
                            GRAMMAR_ERROR_TYPE_MISSPELLED_WORD: lambda: f'Možný preklep v slove.\n\nNávrhy: '
                                                                        f'{self.get_hunspell_suggestions(token)}',
                            GRAMMAR_ERROR_NON_LITERAL_WORD: lambda: f'Slovo nie je spisovné.\n\n'
                                                                    f'Návrh: {NON_LITERAL_WORDS[token.lower_]}',
                            GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO: lambda: 'Výraz nie je spisovný.\n\nNávrh: to',
                            GRAMMAR_ERROR_S_INSTEAD_OF_Z: lambda: 'Chybná predložka.\n\nNávrh: z/zo',
                            GRAMMAR_ERROR_Z_INSTEAD_OF_S: lambda: 'Chybná predložka.\n\nNávrh: s/so',
                            GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR: lambda: 'Privlasťnovacie zámená majú '
                                                                      'v datíve množného tvar bez dĺžňa.',
                            GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING: lambda: 'Privlasťnovacie zámená majú '
                                                                      'v inštrumentáli jednotného čísla tvar s dĺžňom.',
                            GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX: lambda: f'Slovo by malo končiť na í.\n\n'
                                                                       f'Návrhy: {span.root.text[:-1] + "í"}',
                            GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX: lambda: f'Slovo by malo končiť na ý.\n\n'
                                                                       f'Návrhy: {span.root.text[:-1] + "ý"}',
                            GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX: lambda: f'Slovo by malo končiť na ísi.\n\n'
                                                                         f'Návrhy: {span.root.text[:-3] + "ísi"}',
                            GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX: lambda: f'Slovo by malo končiť na ýsi.\n\n'
                                                                         f'Návrhy: {span.root.text[:-3] + "ýsi"}'
                        }
                        if token._.grammar_error_type in grammar_error_map:
                            error_messages.add(grammar_error_map[token._.grammar_error_type]())
        return error_messages

    def get_hunspell_suggestions(self, token):
        return ", ".join(self.ctx.spellcheck_dictionary.suggest(token.lower_))

    def editor_on_mouse_leave(self, event):
        self.tooltip.hide()
        self.last_tags = set()

    def undo(self, event=None):
        self.text_editor.edit_undo()
        if self.ctx.current_file is not None:
            self.save_text_file()
        self.analyze_text()
        return 'break'

    def redo(self, event=None):
        self.text_editor.edit_redo()
        if self.ctx.current_file is not None:
            self.save_text_file()
        self.analyze_text()
        return 'break'

    # LOAD TEXT FILE
    def import_file_contents(self, item, file_path):
        text = ImportService.import_document(file_path)
        item.contents = HTextFile(text)
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
        self.configure_modal(modal.toplevel, height=120, width=400)

    def save_text_file(self):
        if self.ctx.current_file:
            self.ctx.current_file.contents.raw_text = self.text_editor.get(1.0, tk.END)
            ProjectService.save_file_contents(self.ctx.project, self.ctx.current_file)
        else:
            self.open_new_file_dialog(
                # EXCLUDE DIRECTORY FROM OPTIONS
                type_options={key: val for key, val in ProjectItemType.get_selectable_values().items() if
                              val != ProjectItemType.DIRECTORY},
                callback=lambda item: Utils.execute_callbacks(
                    [partial(self.open_text_file, item), self.save_text_file]
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
                self._show_project_files()

    def _on_project_tree_item_close(self, e=None):
        item_id = self.project_tree.focus()
        item = self.project_tree_item_to_project_item[item_id]
        if item.type == ProjectItemType.DIRECTORY:
            item.opened = False
            ProjectService.save(self.ctx.project, self.ctx.project.path)

    def open_text_file(self, item):
        self.ctx.current_file = item
        self.root.title(f"{item.name} | {self.ctx.project.name} | Hector")
        item.contents = ProjectService.load_file_contents(self.ctx.project, item)
        MainWindow.set_text(self.text_editor, item.contents.raw_text, editable=True)
        self.analyze_text(True)

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
        text = self.text_editor.get(1.0, tk.END)
        ExportService.export_text_file(file_path, text)

    # SAVE SETTINGS TO FILE
    def export_settings(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".hector.conf",
                                                 confirmoverwrite=True,
                                                 filetypes=[("Nastavenia programu Hector", "*.hector.conf")])
        if file_path:
            ConfigService.save(self.config, file_path)

    # IMPORT SETTINGS FROM A FILE
    def import_settings(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Nastavenia programu Hector", "*.hector.conf")]
        )
        self.config = ConfigService.load(file_path)
        ConfigService.save(self.config, CONFIG_FILE_PATH)
        self.analyze_text(True)

    def export_sentences(self, event=None):
        add_more_blank_lines = messagebox.askyesnocancel("Zalomenie textu", "Pridať medzi vety prázdny riadok?")
        if add_more_blank_lines is None:
            # USER HAS CANCELLED FUNCTION
            return 'break'
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Textové súbory", "*.txt")])
        if file_path:
            ExportService.export_sentences(file_path, self.doc, add_more_blank_lines)
        return 'break'

    # HANDLE CLIPBOARD PASTE
    # noinspection PyMethodMayBeStatic
    def handle_clipboard_paste(self, event):
        # GET CLIPBOARD
        try:
            clipboard_text = event.widget.selection_get(selection='CLIPBOARD')
        except tk.TclError:
            clipboard_text = ''

        self.paste_text(clipboard_text, event)
        # CANCEL DEFAULT PASTE
        return "break"

    def paste_text(self, text, event, force_reload=True):
        # IF THERE SI SELECTED TEXT IN EDITOR, OVERWRITE IT WITH SELECTED TEXT
        if event.widget.tag_ranges(tk.SEL):
            event.widget.delete("sel.first", "sel.last")
        # NORMALIZE TEXT
        text = ImportService.normalize_text(text)
        event.widget.insert(tk.INSERT, text)
        self.analyze_text(force_reload=force_reload, event=event)
        if self.ctx.current_file is not None:
            self.save_text_file()

    def create_selection(self, from_char, to_char):
        self.text_editor.tag_add(tk.SEL, f"1.0 + {from_char} chars", f"1.0 + {to_char} chars")

    # ANALYZE TEXT
    def analyze_text(self, force_reload=False, event=None):
        # CLEAR DEBOUNCE TIMER IF ANY
        self.analyze_text_debounce_timer = None
        text = self.text_editor.get(1.0, tk.END)
        if not force_reload and self.doc.text == text:
            self.introspect(event)
            return
        if self.search_debounce_timer is not None:
            self.root.after_cancel(self.search_debounce_timer)
        config = ConfigService.select_config(self.config, self.ctx.project, self.ctx.current_file)
        self.search_debounce_timer = None
        self.search_matches.clear()
        self.last_search = ''
        self.last_match_index = 0
        # GET TEXT FROM EDITOR
        # RUN ANALYSIS
        if not force_reload and len(text) > 100 and abs(
                len(self.doc.text) - len(text)) < 20 and config.analysis_settings.enable_partial_nlp:
            # PARTIAL NLP
            carret_position = self.get_carret_position()
            if carret_position is not None:
                self.doc = NlpService.partial_analysis(text, self.doc, self.ctx.nlp, config, carret_position)
                self.text_editor.edit_separator()
            else:
                # FALLBACK TO FULL NLP
                self.doc = NlpService.full_analysis(text, self.ctx.nlp, NLP_BATCH_SIZE, config)
                self.text_editor.edit_separator()
        else:
            # FULL NLP
            # FALLBACK TO FULL NLP
            self.doc = NlpService.full_analysis(text, self.ctx.nlp, NLP_BATCH_SIZE, config)
        # CLEAR TAGS
        for tag in self.text_editor.tag_names():
            self.text_editor.tag_delete(tag)
        # SETUP PARAGRAPH TAGGING
        for paragraph in self.doc._.paragraphs:
            start_index = f"1.0 + {paragraph.start_char} chars"
            end_index = f"1.0 + {paragraph.end_char} chars"
            self.text_editor.tag_add(PARAGRAPH_TAG_NAME, start_index, end_index)
        # RUN ANALYSIS FUNCTIONS
        self.display_size_info(self.doc)
        self.highlight_long_sentences(self.doc, config)
        self.display_word_frequencies(self.doc, config)
        self.highlight_close_words(self.doc, config)
        self.highlight_multiple_spaces(self.doc, config)
        self.highlight_multiple_punctuation(self.doc, config)
        self.highlight_trailing_spaces(self.doc, config)
        self.highlight_quote_mark_errors(self.doc, config)
        self.run_spellcheck(self.doc, config)
        # CONFIG TAGS
        self.text_editor.tag_config(PARAGRAPH_TAG_NAME,
                                    lmargin1=f'{config.appearance_settings.paragraph_lmargin1}m',
                                    spacing3=f'{config.appearance_settings.paragraph_spacing3}m')
        self.text_editor.tag_config(LONG_SENTENCE_TAG_NAME_MID, background=LONG_SENTENCE_HIGHLIGHT_COLOR_MID)
        self.text_editor.tag_config(LONG_SENTENCE_TAG_NAME_HIGH, background=LONG_SENTENCE_HIGHLIGHT_COLOR_HIGH)
        self.text_editor.tag_config(TRAILING_SPACES_TAG_NAME, background="red")
        self.text_editor.tag_config(COMPUTER_QUOTE_MARKS_TAG_NAME, background="red")
        self.text_editor.tag_config(DANGLING_QUOTE_MARK_TAG_NAME, background="red")
        self.text_editor.tag_config(SHOULD_USE_LOWER_QUOTE_MARK_TAG_NAME, background="red")
        self.text_editor.tag_config(SHOULD_USE_UPPER_QUOTE_MARK_TAG_NAME, background="red")
        self.text_editor.tag_config(MULTIPLE_PUNCTUATION_TAG_NAME, background="red")
        self.text_editor.tag_config(MULTIPLE_SPACES_TAG_NAME, background="red")
        self.text_editor.tag_config(SEARCH_RESULT_TAG_NAME, background=SEARCH_RESULT_HIGHLIGHT_COLOR)
        self.text_editor.tag_config(CURRENT_SEARCH_RESULT_TAG_NAME, background=CURRENT_SEARCH_RESULT_HIGHLIGHT_COLOR)
        self.text_editor.tag_config(GRAMMAR_ERROR_TAG_NAME, underline=True, underlinefg="red")
        self.text_editor.tag_raise(COMPUTER_QUOTE_MARKS_TAG_NAME)
        self.text_editor.tag_raise("sel")
        self.close_words_text.tag_raise("sel")
        self.word_freq_text.tag_raise("sel")
        # MOUSE BINDINGS
        GuiUtils.bind_tag_mouse_event(CLOSE_WORD_TAG_NAME,
                                      self.text_editor,
                                      lambda e: self.highlight_same_word(e, self.text_editor),
                                      lambda e: self.unhighlight_same_word(e)
                                      )
        readability = NlpService.compute_readability(self.doc)
        self.readability_value.configure(text=f"{readability: .0f} / {READABILITY_MAX_VALUE}")
        self.introspect(event)

    # RUN ANALYSIS ONE SECOND AFTER LAST CHANGE
    def _analyze_text_debounced(self, event):
        if self.analyze_text_debounce_timer is not None:
            self.root.after_cancel(self.analyze_text_debounce_timer)
        # PREVENT STANDARD ANALYSIS ON CTRL+V
        if event.state & 0x0004 and event.keysym != 'v':
            return
        if self.ctx.current_file is not None:
            self.analyze_text_debounce_timer = self.root.after(
                NLP_DEBOUNCE_LENGTH,
                lambda: Utils.execute_callbacks([self.save_text_file, self.analyze_text])
            )
        else:
            self.analyze_text_debounce_timer = self.root.after(
                NLP_DEBOUNCE_LENGTH,
                self.analyze_text
            )

    def introspect(self, event=None):
        carret_position = self.get_carret_position()
        if carret_position is None:
            MainWindow.set_text(self.introspection_text, 'Kliknite na slovo v editore')
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
                MainWindow.set_text(self.introspection_text, introspection_resut)

    # FOCUS NEXT SEARCH RESULT
    def next_search(self, event):
        results_count = len(self.search_matches)
        if results_count == 0:
            return
        self.last_match_index = (self.last_match_index + 1) % (results_count)
        self.highlight_search()

    # FOCUS PREVIOUS SEARCH RESULT
    def prev_search(self, event):
        results_count = len(self.search_matches)
        if results_count == 0:
            return
        self.last_match_index = (self.last_match_index - 1) % (results_count)
        self.highlight_search()

    # HIGHLIGHT CURRENT FOCUSED SEARCH RESULT
    def highlight_search(self):
        self.text_editor.tag_remove(CURRENT_SEARCH_RESULT_TAG_NAME, "1.0", tk.END)
        start, end = self.search_matches[self.last_match_index].span()
        start_index = f"1.0 + {start} chars"
        end_index = f"1.0 + {end} chars"
        self.text_editor.tag_add(CURRENT_SEARCH_RESULT_TAG_NAME, start_index, end_index)
        self.move_carret(end_index)

    # SEARCH IN TEXT EDITOR
    def search_text(self):
        search_string = Utils.remove_accents(self.search_field.get().replace("\n", "").lower())
        if self.last_search == search_string:
            return
        self.last_search = search_string
        self.last_match_index = 0
        self.text_editor.tag_remove(SEARCH_RESULT_TAG_NAME, "1.0", tk.END)
        self.text_editor.tag_remove(CURRENT_SEARCH_RESULT_TAG_NAME, "1.0", tk.END)
        expression = rf"{search_string}"
        self.search_matches = list(
            re.finditer(expression, Utils.remove_accents(self.doc.text.lower()), flags=re.UNICODE))
        if len(self.search_matches) == 0:
            return
        editor_counts = self.text_editor.count("1.0", self.text_editor.index(tk.INSERT), "chars")
        carrent_position = 0
        if editor_counts is not None:
            carrent_position = self.text_editor.count("1.0", self.text_editor.index(tk.INSERT), "chars")[0]
        first_match_highlighted = False
        for i, match in enumerate(self.search_matches):
            start, end = match.span()
            start_index = f"1.0 + {start} chars"
            end_index = f"1.0 + {end} chars"
            self.text_editor.tag_add(SEARCH_RESULT_TAG_NAME, start_index, end_index)
            if not first_match_highlighted and start > carrent_position:
                self.last_match_index = i
        self.highlight_search()
        self.text_editor.tag_raise(CURRENT_SEARCH_RESULT_TAG_NAME)

    # RUN SEARCH ONE SECOND AFTER LAST CHANGE
    def _search_debounced(self, event=None):
        if self.search_debounce_timer is not None:
            self.root.after_cancel(self.search_debounce_timer)
        self.search_debounce_timer = self.root.after(1000, self.search_text)

    # SELECT ALL TEXT
    def select_all(self, event=None):
        self.text_editor.tag_add(tk.SEL, "1.0", tk.END)
        self.text_editor.tag_raise(tk.SEL)
        return "break"

    def focus_search(self, event=None):
        self.search_field.focus()
        return

    def focus_editor(self, event=None):
        self.text_editor.focus()
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
        if GuiUtils.is_child_of(self.text_editor, event.widget):
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
                            partial(self.move_carret, clicked_text_index),
                            partial(self.handle_clipboard_paste, event)
                        ]
                    )
                ))
            # ADD COPY OPTION IF EDITOR HAS SELECTED TEXT
            if event.widget.tag_ranges(tk.SEL):
                context_menu_items.append(MenuItem(
                    label="Kopírovať",
                    shortcut_label="Ctrl+C",
                    command=partial(self.copy_to_clipboard, event.widget.selection_get())
                ))

            # IF CLICKED WORD HAS GRAMMAR ERROR, APPEND SUGGESTIONS
            clicked_text_char_position = self.get_carret_position(tk.CURRENT)
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
                                        command=partial(self.apply_suggestion, span, s, event, clicked_text_index)
                                    )
                                )

        # IF WE HAVE ANY CONTEXT MENU ITEMS TO DISPLAY SHOW MENU
        if len(context_menu_items) > 0:
            self.context_menu.show(context_menu_items, event)
        return

    def apply_suggestion(self, span, suggestion, event, carret_index):
        self.move_carret(carret_index)
        self.create_selection(span.start_char, span.end_char)
        self.paste_text(suggestion, event, False)

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    # RUN SPELLCHECK
    def run_spellcheck(self, doc: Doc, config: Config):
        if config.analysis_settings.enable_spellcheck:
            SpellcheckService.spellcheck(self.ctx.spellcheck_dictionary, doc)
            for word in self.doc._.words:
                if word._.has_grammar_error:
                    start_index = f"1.0 + {word.idx} chars"
                    end_index = f"1.0 + {word.idx + len(word.lower_)} chars"
                    self.text_editor.tag_add(GRAMMAR_ERROR_TAG_NAME, start_index, end_index)

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
            c = Config(self.config.to_dict())
        settings_window = AnalysisSettingsModal(self.root, c, lambda: self.analyze_text(True), config_level, item)
        self.configure_modal(settings_window.toplevel, height=660, width=780)

    # SHOW SETTINGS WINDOW
    def show_appearance_settings(self):
        settings_window = AppearanceSettingsModal(self.root, self.config, lambda: self.analyze_text(True))
        self.configure_modal(settings_window.toplevel, height=150, width=780)

    # SHOW ABOUT DIALOG
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("O programe")
        self.configure_modal(about_window)
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
            self.configure_modal(dep_window, width=dep_view.width(), height=dep_view.height())

    def configure_modal(self, modal, width=600, height=400):
        if platform.system() == "Windows":
            scaling_factor = Utils.get_windows_scaling_factor()
            width = width * scaling_factor
            height = height * scaling_factor
        modal.bind('<Escape>', lambda e: modal.destroy())
        modal.geometry("%dx%d" % (width, height))
        modal.resizable(False, False)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width / 2 - (width / 2)
        y = screen_height / 2 - (height / 2)
        modal.geometry("+%d+%d" % (x, y))
        modal.wait_visibility()
        modal.grab_set()
        modal.focus_set()
        modal.transient(self.root)

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
