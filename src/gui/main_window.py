import io
import json
import math
import platform
import random
import re
import tkinter as tk
import webbrowser
from tkinter import filedialog, ttk

import spacy
from PIL import ImageTk, Image
from reportlab.graphics import renderPM
from spacy import displacy
from spacy.tokens import Doc
from svglib.svglib import svg2rlg
from hunspell import Hunspell
from tkinter_autoscrollbar import AutoScrollbar
from pythes import PyThes
from src.backend.service import Service
from src.const.colors import *
from src.const.fonts import *
from src.const.grammar_error_types import *
from src.const.paths import *
from src.const.tags import *
from src.const.values import *
from src.utils import Utils

EDITOR_LOGO_HEIGHT = 300
EDITOR_LOGO_WIDTH = 300
ENABLE_DEBUG_DEP_IMAGE = False
VERSION = "0.6.2 Alfa"

with open(Utils.resource_path('data_files/pos_tag_translations.json'), 'r', encoding='utf-8') as file:
    POS_TAG_TRANSLATIONS = json.load(file)

with open(Utils.resource_path('data_files/dep_tag_translations.json'), 'r', encoding='utf-8') as file:
    DEP_TAG_TRANSLATION = json.load(file)


# MAIN GUI WINDOW
class MainWindow:
    def __init__(self, r, _nlp: spacy, spellcheck_dictionary: Hunspell, thesaurus: PyThes):
        self.root = r
        r.overrideredirect(False)
        style = ttk.Style(self.root)
        # CUSTOM SCROLLBAR
        style.configure("Vertical.TScrollbar", gripcount=0, troughcolor=PRIMARY_BLUE, bordercolor=PRIMARY_BLUE,
                        background=LIGHT_BLUE, lightcolor=LIGHT_BLUE, darkcolor=MID_BLUE)

        style.layout('arrowless.Vertical.TScrollbar',
                     [('Vertical.Scrollbar.trough',
                       {'children': [('Vertical.Scrollbar.thumb',
                                      {'expand': '1', 'sticky': 'nswe'})],
                        'sticky': 'ns'})])
        self.root.eval('tk::PlaceWindow . center')
        # OPEN WINDOW IN MAXIMIZED STATE
        # FOR WINDOWS AND MAC OS SET STATE ZOOMED
        # FOR LINUX SET ATTRIBUTE ZOOMED
        if platform.system() == "Windows" or platform.system() == "Darwin":
            self.root.state("zoomed")
        else:
            self.root.attributes('-zoomed', True)
        self.nlp = _nlp
        self.spellcheck_dictionary = spellcheck_dictionary
        self.thesaurus = thesaurus
        # TIMERS FOR DEBOUNCING CHANGE EVENTS
        self.analyze_text_debounce_timer = None
        self.search_debounce_timer = None
        # SEARCH DATA
        self.search_matches = []
        self.last_search = ''
        self.last_match_index = 0
        # CLOSE WORD, THAT IS CURRENTLY HIGHLIGHTED
        self.highlighted_close_word = ''
        # TOOLTIP WINDOW
        self.tooltip = None
        # DEFAULT NLP DOCUMENT INITIALIZED ON EMPTY TEXT
        self.doc = self.nlp('')
        # TOKEN SELECTED IN LEFT BOTTOM INTOSPECTION WINDOW
        self.current_instrospection_token = None
        # EDITOR TEXT SIZE
        self.text_size = 10
        # DICTIONARY THAT HOLDS COLOR OF WORD TO PREVENT RECOLORING WHILE TYPING
        self.close_word_colors = {}
        # LOAD CONFIG
        self.config = Service.load_config(CONFIG_FILE_PATH)
        # INIT GUI
        # MAIN FRAME
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=1, fill=tk.BOTH, side=tk.LEFT)
        # LEFT SCROLLABLE SIDE PANEL WITH FREQUENT WORDS
        left_side_panel = tk.Frame(main_frame, width=300, relief=tk.FLAT, borderwidth=1, background=PRIMARY_BLUE)
        left_side_panel.pack(fill=tk.BOTH, side=tk.LEFT, expand=0)
        # RIGHT SCROLLABLE SIDE PANEL WITH FREQUENT WORDS
        right_side_panel = tk.Frame(main_frame, width=200, relief=tk.FLAT, borderwidth=1, background=PRIMARY_BLUE)
        right_side_panel.pack(fill=tk.BOTH, side=tk.RIGHT)
        # MIDDLE TEXT EDITOR WINDOW
        text_editor_frame = tk.Frame(main_frame, background=TEXT_EDITOR_BG, borderwidth=0)
        text_editor_frame.pack(expand=1, fill=tk.BOTH)
        text_editor_scroll_frame = tk.Frame(text_editor_frame, width=10, relief=tk.FLAT, background=PRIMARY_BLUE)
        text_editor_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        text_editor_scroll = AutoScrollbar(text_editor_scroll_frame, orient='vertical',
                                           style='arrowless.Vertical.TScrollbar', takefocus=False)
        text_editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        # BOTTOM PANEL WITH TEXT SIZE
        bottom_panel = tk.Frame(text_editor_frame, background=MID_BLUE, height=20)
        bottom_panel.pack(fill=tk.BOTH, side=tk.BOTTOM)
        # LEFT PANEL CONTENTS
        self.introspection_text = tk.Text(left_side_panel, highlightthickness=0, bd=0, wrap=tk.WORD, state=tk.DISABLED,
                                          width=30, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, height=15,
                                          font=(HELVETICA_FONT_NAME, 9))
        if ENABLE_DEBUG_DEP_IMAGE:
            self.dep_image_holder = ttk.Label(left_side_panel, width=30)
            self.dep_image_holder.pack(pady=10, padx=10, side=tk.BOTTOM)
            self.dep_image_holder.bind("<Button-1>", self.show_dep_image)
        MainWindow.set_text(self.introspection_text, 'Kliknite na slovo v editore')
        self.introspection_text.pack(fill=tk.X, pady=10, padx=10, side=tk.BOTTOM)
        separator = ttk.Separator(left_side_panel, orient='horizontal')
        separator.pack(fill=tk.X, padx=10, side=tk.BOTTOM)
        tk.Label(left_side_panel, pady=10, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                 text="Introspekcia",
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='n',
                 justify='left').pack(side=tk.BOTTOM)
        tk.Label(left_side_panel, pady=10, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                 text="Často sa opakujúce slová",
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='n',
                 justify='left').pack()
        separator = ttk.Separator(left_side_panel, orient='horizontal')
        separator.pack(fill=tk.X, padx=10)
        left_side_panel_scroll_frame = tk.Frame(left_side_panel, width=10, relief=tk.FLAT, background=PRIMARY_BLUE)
        left_side_panel_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        left_side_frame_scroll = AutoScrollbar(left_side_panel_scroll_frame, orient='vertical',
                                               style='arrowless.Vertical.TScrollbar', takefocus=False)
        left_side_frame_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.close_words_text = tk.Text(left_side_panel, highlightthickness=0, bd=0, wrap=tk.WORD, state=tk.DISABLED,
                                        width=20, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                                        yscrollcommand=left_side_frame_scroll.set)
        self.close_words_text.pack(fill=tk.BOTH, expand=1, pady=10, padx=10)
        left_side_frame_scroll.config(command=self.close_words_text.yview)
        # MIDDLE TEXT EDITOR CONTENTS
        self.text_editor = tk.Text(text_editor_frame, wrap=tk.WORD, relief=tk.FLAT, highlightthickness=0,
                                   yscrollcommand=text_editor_scroll.set, background=TEXT_EDITOR_BG, borderwidth=0)
        self.text_editor.config(font=(HELVETICA_FONT_NAME, self.text_size))
        self.text_editor.pack(expand=1, fill=tk.BOTH, padx=5, pady=5)
        image = Image.open(Utils.resource_path("images/hector-logo.png"))
        logo = ImageTk.PhotoImage(image.resize((EDITOR_LOGO_WIDTH, EDITOR_LOGO_HEIGHT)))
        self.logo_holder = ttk.Label(text_editor_frame, image=logo, background=TEXT_EDITOR_BG)
        self.logo_holder.image = logo
        text_editor_scroll.config(command=self.text_editor.yview)
        # RIGHT PANEL CONTENTS
        tk.Label(right_side_panel, pady=10, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                 text="Hľadať", font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER),
                 anchor='n', justify='left').pack(fill=tk.X)
        search_frame = tk.Frame(right_side_panel, relief=tk.FLAT, background=PRIMARY_BLUE)
        search_frame.pack(fill=tk.X, padx=0)
        prev_search_button = tk.Label(search_frame, text="⮝", background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                                      cursor="hand2")
        prev_search_button.pack(side=tk.RIGHT, padx=2)
        prev_search_button.bind("<Button-1>", self.prev_search)
        next_search_button = tk.Label(search_frame, text="⮟", background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                                      cursor="hand2")
        next_search_button.pack(side=tk.RIGHT, padx=2)
        next_search_button.bind("<Button-1>", self.next_search)
        self.search_field = ttk.Entry(search_frame, width=22, background=TEXT_EDITOR_BG)
        self.search_field.bind('<KeyRelease>', self.search_debounced)
        self.search_field.bind('<Return>', self.next_search)
        self.search_field.bind('<Shift-Return>', self.prev_search)
        self.search_field.pack(padx=0)
        tk.Label(right_side_panel, pady=10, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                 text="Často použité slová", font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER),
                 anchor='n', justify='left').pack()
        ttk.Separator(right_side_panel, orient='horizontal').pack(fill=tk.X, padx=10)
        right_side_panel_scroll_frame = tk.Frame(right_side_panel, width=10, relief=tk.FLAT, background=PRIMARY_BLUE)
        right_side_panel_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_side_frame_scroll = AutoScrollbar(right_side_panel_scroll_frame, orient='vertical',
                                                style='arrowless.Vertical.TScrollbar', takefocus=False)
        right_side_frame_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.word_freq_text = tk.Text(right_side_panel, highlightthickness=0, bd=0, wrap=tk.WORD, state=tk.DISABLED,
                                      width=20, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                                      yscrollcommand=right_side_frame_scroll.set)
        self.word_freq_text.pack(fill=tk.BOTH, expand=1, pady=10, padx=10)
        right_side_frame_scroll.config(command=self.word_freq_text.yview)
        # BOTTOM PANEL CONTENTS
        char_count_info_label = tk.Label(bottom_panel, text="Počet znakov s medzerami:", anchor='sw',
                                         justify='left', background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                                         font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        char_count_info_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)
        self.char_count_info_value = tk.Label(bottom_panel, text="0", anchor='sw', justify='left',
                                              background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                                              font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.char_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)
        tk.Label(bottom_panel, text="Počet slov:", anchor='sw', justify='left',
                 background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.LEFT, padx=(5, 0), pady=5
        )
        self.word_count_info_value = tk.Label(bottom_panel, text="0", anchor='sw', justify='left',
                                              background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                                              font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.word_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)
        tk.Label(bottom_panel, text="Počet normostrán:", anchor='sw', justify='left',
                 background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.LEFT, padx=(5, 0), pady=5
        )
        self.page_count_info_value = tk.Label(bottom_panel, text="0", anchor='sw', justify='left',
                                              background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                                              font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.page_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)
        tk.Label(bottom_panel, text="Štylistická zložitosť textu:", anchor='sw', justify='left',
                 background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.LEFT, padx=(5, 0), pady=5
        )
        self.readability_value = tk.Label(bottom_panel, text=f"0 / {READABILITY_MAX_VALUE}", anchor='sw',
                                          justify='left',
                                          background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
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
                 background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.RIGHT, padx=(5, 0), pady=5
        )
        # TOP MENU
        self.menu_bar = tk.Menu(self.root, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, border=1)
        self.root.config(menu=self.menu_bar)
        # FILE MENU
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU))
        self.file_menu.add_command(label="Načítať súbor", command=self.load_file)
        self.file_menu.add_command(label="Uložiť súbor", command=self.save_file)
        self.menu_bar.add_cascade(label="Súbor", menu=self.file_menu)
        # SETTINGS MENU
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                                     font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU))
        self.settings_menu.add_command(label="Parametre analýzy", command=self.show_settings)
        self.menu_bar.add_cascade(label="Nastavenia", menu=self.settings_menu)
        # HELP MENU
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU))
        self.help_menu.add_command(label="O programe", command=self.show_about)
        self.help_menu.add_command(label="Dokumentácia", command=lambda: webbrowser.open(DOCUMENTATION_LINK))
        self.menu_bar.add_cascade(label="Pomoc", menu=self.help_menu)
        # MOUSE AND KEYBOARD BINDINGS
        self.text_editor.bind("<KeyRelease>", self.analyze_text_debounced)
        self.text_editor.bind("<Button-1>", lambda e: self.root.after(0, self.introspect))
        self.text_editor.bind("<Control-a>", self.select_all)
        self.text_editor.bind("<Control-A>", self.select_all)
        self.text_editor.bind("<Configure>", self.evaluate_logo_placement)
        self.root.bind("<Control-F>", self.focus_search)
        self.root.bind("<Control-f>", self.focus_search)
        self.root.bind("<Control-e>", self.focus_editor)
        self.root.bind("<Control-E>", self.focus_editor)
        # WINDOWS SPECIFIC
        self.root.bind("<MouseWheel>", self.change_text_size)
        # LINUX SPECIFIC
        self.root.bind("<Button-4>", self.change_text_size)
        self.root.bind("<Button-5>", self.change_text_size)
        self.root.after(100, self.evaluate_logo_placement)

    # START MAIN LOOP
    def start_main_loop(self):
        # START MAIN LOOP TO SHOW ROOT WINDOW
        self.root.mainloop()

    # UTIL METHOD TO SET tk.TEXT WIDGET
    # WE NEED TO ENBLE TEXT, DELETE CONTENT AND INSERT NEW TEXT
    @staticmethod
    def set_text(text: tk.Text, value):
        text.config(state=tk.NORMAL)
        text.delete(1.0, tk.END)
        text.insert(tk.END, value)
        text.config(state=tk.DISABLED)

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
    def display_word_frequencies(self, doc: Doc):
        if not self.config.enable_frequent_words:
            return
        word_counts = Service.compute_word_frequencies(doc, self.config)
        # NOTE
        # In tk, there is problem with scrolling so we default to using on big text to dispaly frequencies
        # There is way of making canvas with scrollregion but this is more performant
        frequent_words_text = "\n".join(
            [f"{word.text}\t\t{len(word.occourences)}x" for word in word_counts]
        )
        MainWindow.set_text(self.word_freq_text, frequent_words_text)

    # HIGHLIGHT LONG SENTENCES
    def highlight_long_sentences(self, doc: Doc):
        if not self.config.enable_long_sentences:
            return
        for sentence in doc.sents:
            if sentence._.is_long_sentence:
                start_index = f"1.0 + {sentence.start_char} chars"
                end_index = f"1.0 + {sentence.end_char} chars"
                self.text_editor.tag_add(LONG_SENTENCE_TAG_NAME_HIGH, start_index, end_index)
            elif sentence._.is_mid_sentence:
                start_index = f"1.0 + {sentence.start_char} chars"
                end_index = f"1.0 + {sentence.end_char} chars"
                self.text_editor.tag_add(LONG_SENTENCE_TAG_NAME_MID, start_index, end_index)

    # HIGHLIGH MULTIPLE SPACE, MULTIPLE PUNCTATION, AND TRAILING SPACES
    def highlight_multiple_issues(self, doc: Doc):
        self.text_editor.tag_remove(MULTIPLE_SPACES_TAG_NAME, "1.0", tk.END)
        if self.config.enable_multiple_spaces:
            matches = Service.find_multiple_spaces(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(MULTIPLE_SPACES_TAG_NAME, start_index, end_index)

        if self.config.enable_multiple_punctuation:
            matches = Service.find_multiple_punctuation(doc)
            for match in matches:
                if match.group() not in ["?!"]:
                    start_index = f"1.0 + {match.start()} chars"
                    end_index = f"1.0 + {match.end()} chars"
                    self.text_editor.tag_add(MULTIPLE_PUNCTUATION_TAG_NAME, start_index, end_index)

        if self.config.enable_trailing_spaces:
            matches = Service.find_trailing_spaces(doc)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(TRAILING_SPACES_TAG_NAME, start_index, end_index)

    # HIGHLIGHT WORDS THAT REPEATS CLOSE TO EACH OTHER
    def highlight_close_words(self, doc: Doc):
        if self.config.enable_close_words:
            self.text_editor.tag_remove("close_word", "1.0", tk.END)
            close_words = Service.evaluate_close_words(doc, self.config)
            # NOTE
            # In tk, there is problem with scrolling so we default to using on big text to dispaly frequencies
            # There is way of making canvas with scrollregion but this is more performant
            self.close_words_text.config(state=tk.NORMAL)
            self.close_words_text.delete(1.0, tk.END)
            start_char = 0
            for word in close_words:
                word_text = f"{word.lower()}\t\t{len(close_words[word])}x\n"
                tag_name = f"{CLOSE_WORD_PREFIX}{word}"

                # Insert the text
                self.close_words_text.insert(tk.END, word_text)

                # Add the tag to the inserted text
                start_index = f"1.0 + {start_char} chars"
                end_index = f"1.0 + {start_char + len(word_text)} chars"
                self.close_words_text.tag_add(tag_name, start_index, end_index)
                self.close_words_text.tag_add(CLOSE_WORD_TAG_NAME, start_index, end_index)
                start_char += len(word_text)
                self.bind_tag_mouse_event(tag_name,
                                          self.close_words_text,
                                          lambda e: self.highlight_same_word(e, self.close_words_text, False),
                                          lambda e: self.unhighlight_same_word(e)
                                          )
            self.close_words_text.config(state=tk.DISABLED)

            for word in close_words.items():
                key = word[0]
                for occ in word[1]:
                    color = random.choice(CLOSE_WORDS_PALLETE)
                    start_index = f"1.0 + {occ.idx} chars"
                    end_index = f"1.0 + {occ.idx + len(occ.lower_)} chars"
                    tag_name = f"{CLOSE_WORD_PREFIX}{key}"
                    original_color = self.close_word_colors.get(tag_name, "")
                    if original_color != "":
                        color = original_color
                    else:
                        self.close_word_colors[tag_name] = color
                    self.text_editor.tag_add(tag_name, start_index, end_index)
                    self.text_editor.tag_add(CLOSE_WORD_TAG_NAME, start_index, end_index)
                    self.text_editor.tag_config(tag_name, foreground=color,
                                                font=(HELVETICA_FONT_NAME, self.text_size + 2, BOLD_FONT))

    # BIND MOUSE ENTER AND MOUSE LEAVE EVENTS
    def bind_tag_mouse_event(self, tag_name, text, on_enter, on_leave):
        text.tag_bind(tag_name, "<Enter>", on_enter)
        text.tag_bind(tag_name, "<Leave>", on_leave)

    def highlight_grammar_error(self, event):
        # Získanie indexu myši
        mouse_index = self.text_editor.index(f"@{event.x},{event.y}")
        word_position = self.text_editor.count("1.0", mouse_index, "chars")
        if word_position is not None:
            span = self.doc.char_span(word_position[0], word_position[0], alignment_mode='expand')
            if span is not None:
                token = span.root
                if token._.grammar_error_type == GRAMMAR_ERROR_TYPE_MISSPELLED_WORD:
                    suggestions = self.spellcheck_dictionary.suggest(span.root.text)
                    self.show_tooltip(event, f'Možný preklep v slove.\n\nNávrhy: {", ".join(suggestions)}')
                elif token._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX:
                    self.show_tooltip(event, f'Slovo by malo končiť na í.\n\nNávrhy: {span.root.text[:-1] + "í"}')
                elif token._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX:
                    self.show_tooltip(event, f'Slovo by malo končiť na ý.\n\nNávrhy: {span.root.text[:-1] + "ý"}')
                elif token._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX:
                    self.show_tooltip(event, f'Slovo by malo končiť na ísi.\n\nNávrhy: {span.root.text[:-3] + "ísi"}')
                elif token._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX:
                    self.show_tooltip(event, f'Slovo by malo končiť na ýsi.\n\nNávrhy: {span.root.text[:-3] + "ýsi"}')

    # HIGHLIGHT SAME WORD ON MOUSE OVER
    def highlight_same_word(self, event, trigger, with_tooltip=True):
        self.unhighlight_same_word(event)
        # Získanie indexu myši
        mouse_index = trigger.index(f"@{event.x},{event.y}")
        # Získanie všetkých tagov na pozícii myši
        tags_at_mouse = trigger.tag_names(mouse_index)
        if with_tooltip:
            self.show_tooltip(event, 'Toto slovo sa opakuje viackrát na krátkom úseku')
        for tag in tags_at_mouse:
            if tag.startswith(CLOSE_WORD_PREFIX):
                self.highlighted_close_word = tag
                self.text_editor.tag_config(tag, background="black", foreground="white")
                self.close_words_text.tag_config(tag, background="black", foreground="white")

    # REMOVE HIGHLIGHTING FROM SAME WORD ON MOUSE OVER END
    def unhighlight_same_word(self, event):
        self.hide_tooltip(event)
        if self.highlighted_close_word is not None and len(self.highlighted_close_word) > 0:
            original_color = self.close_word_colors.get(self.highlighted_close_word, "")
            self.text_editor.tag_config(self.highlighted_close_word, background="", foreground=original_color)
            self.close_words_text.tag_config(self.highlighted_close_word, background="", foreground="")

    def show_tooltip(self, event, text):
        if self.tooltip:
            self.tooltip.destroy()
        # Get the position of the mouse
        x = event.x_root + 10
        y = event.y_root + 10
        # Create a Toplevel window
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        # Add content to the tooltip
        label = tk.Label(self.tooltip, text=f"{text}", background=LIGHT_BLUE, relief="solid", borderwidth=1,
                         justify="left", padx=5, pady=5)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    # LOAD TEXT FILE
    def load_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Textové súbory", "*.txt")])
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
                self.text_editor.delete(1.0, tk.END)
                self.text_editor.insert(tk.END, text)
                self.analyze_text(True)

    # SAVE TEXT FILE
    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Textové súbory", "*.txt")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                text = self.text_editor.get(1.0, tk.END)
                file.write(text)

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
        self.search_debounce_timer = None
        self.search_matches.clear()
        self.last_search = ''
        self.last_match_index = 0
        self.evaluate_logo_placement()
        # GET TEXT FROM EDITOR
        # RUN ANALYSIS
        # TODO: Evaluate if we can run partial NLP only on changed parts
        self.doc = Doc.from_docs(list(self.nlp.pipe([text], batch_size=NLP_BATCH_SIZE)))
        Service.fill_custom_data(self.doc, self.config)
        # CLEAR TAGS
        for tag in self.text_editor.tag_names():
            self.text_editor.tag_delete(tag)
        # RUN ANALYSIS FUNCTIONS
        self.display_word_frequencies(self.doc)
        self.display_size_info(self.doc)
        self.highlight_long_sentences(self.doc)
        self.highlight_close_words(self.doc)
        self.highlight_multiple_issues(self.doc)
        self.run_spellcheck(self.doc)
        # CONFIG TAGS
        self.text_editor.tag_config(LONG_SENTENCE_TAG_NAME_MID, background=LONG_SENTENCE_HIGHLIGHT_COLOR_MID)
        self.text_editor.tag_config(LONG_SENTENCE_TAG_NAME_HIGH, background=LONG_SENTENCE_HIGHLIGHT_COLOR_HIGH)
        self.text_editor.tag_config(TRAILING_SPACES_TAG_NAME, background="red")
        self.text_editor.tag_config(MULTIPLE_PUNCTUATION_TAG_NAME, background="red")
        self.text_editor.tag_config(MULTIPLE_SPACES_TAG_NAME, background="red")
        self.text_editor.tag_config(SEARCH_RESULT_TAG_NAME, background=SEARCH_RESULT_HIGHLIGHT_COLOR)
        self.text_editor.tag_config(CURRENT_SEARCH_RESULT_TAG_NAME, background=CURRENT_SEARCH_RESULT_HIGHLIGHT_COLOR)
        self.text_editor.tag_config(GRAMMAR_ERROR_TAG_NAME, underline=True, underlinefg="red")
        self.text_editor.tag_raise("sel")
        self.close_words_text.tag_raise("sel")
        # MOUSE BINDINGS
        self.bind_tag_mouse_event(CLOSE_WORD_TAG_NAME,
                                  self.text_editor,
                                  lambda e: self.highlight_same_word(e, self.text_editor),
                                  lambda e: self.unhighlight_same_word(e)
                                  )
        self.bind_tag_mouse_event(GRAMMAR_ERROR_TAG_NAME,
                                  self.text_editor,
                                  lambda e: self.highlight_grammar_error(e),
                                  lambda e: self.hide_tooltip(e)
                                  )
        self.bind_tag_mouse_event(TRAILING_SPACES_TAG_NAME,
                                  self.text_editor,
                                  lambda e: self.show_tooltip(e, f'Zbytočná medzera na konci odstavca.'),
                                  lambda e: self.hide_tooltip(e)
                                  )
        self.bind_tag_mouse_event(LONG_SENTENCE_TAG_NAME_MID,
                                  self.text_editor,
                                  lambda e: self.show_tooltip(e, f'Táto veta je trochu dlhšia.'),
                                  lambda e: self.hide_tooltip(e)
                                  )
        self.bind_tag_mouse_event(LONG_SENTENCE_TAG_NAME_HIGH,
                                  self.text_editor,
                                  lambda e: self.show_tooltip(e, f'Táto veta je dlhá.'),
                                  lambda e: self.hide_tooltip(e)
                                  )
        self.bind_tag_mouse_event(MULTIPLE_PUNCTUATION_TAG_NAME,
                                  self.text_editor,
                                  lambda e: self.show_tooltip(e, f'Viacnásobná interpunkcia.'),
                                  lambda e: self.hide_tooltip(e)
                                  )
        self.bind_tag_mouse_event(MULTIPLE_SPACES_TAG_NAME,
                                  self.text_editor,
                                  lambda e: self.show_tooltip(e, f'Viacnásobná medzera.'),
                                  lambda e: self.hide_tooltip(e)
                                  )
        readability = Service.evaluate_readability(self.doc)
        self.readability_value.configure(text=f"{readability: .0f} / {READABILITY_MAX_VALUE}")
        self.introspect(event)

    # RUN ANALYSIS ONE SECOND AFTER LAST CHANGE
    def analyze_text_debounced(self, event=None):
        self.evaluate_logo_placement()
        if self.analyze_text_debounce_timer is not None:
            self.root.after_cancel(self.analyze_text_debounce_timer)
        self.analyze_text_debounce_timer = self.root.after(1000, self.analyze_text)

    def introspect(self, event=None):
        possible_carret = self.text_editor.count("1.0", self.text_editor.index(tk.INSERT), "chars")
        if possible_carret is None:
            MainWindow.set_text(self.introspection_text, 'Kliknite na slovo v editore')
            return
        carret_position = possible_carret[0]
        span = self.doc.char_span(carret_position, carret_position, alignment_mode='expand')
        if span is not None and self.current_instrospection_token != span.root:
            if span.root._.is_word:
                self.current_instrospection_token = span.root
                if ENABLE_DEBUG_DEP_IMAGE:
                    rlg = svg2rlg(io.StringIO(displacy.render(span.root.sent, minify=True)))
                    dep_image = renderPM.drawToPIL(rlg)
                    scaling_ratio = 200 / dep_image.width
                    dep_view = ImageTk.PhotoImage(dep_image.resize((200, math.ceil(dep_image.height * scaling_ratio))))
                    self.dep_image_holder.config(image=dep_view)
                    self.dep_image_holder.image = dep_view
                thes_result = self.thesaurus.lookup(self.current_instrospection_token.lemma_)
                morph = self.current_instrospection_token.morph.to_dict()
                introspection_resut = f'Slovo: {self.current_instrospection_token}\n\n' \
                                      f'Základný tvar: {self.current_instrospection_token.lemma_}\n' \
                                      f'Morfológia: {morph.get("Case")} {morph.get("Number")} {morph.get("Gender")}\n' \
                                      f'Slovný druh: {POS_TAG_TRANSLATIONS[self.current_instrospection_token.pos_]}\n' \
                                      f'Vetný člen: {DEP_TAG_TRANSLATION[self.current_instrospection_token.dep_.lower()]}'
                if thes_result is not None:
                    introspection_resut += f'\n\nSynonymá\n\n'
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
        self.text_editor.see(start_index)
        self.text_editor.mark_set(tk.INSERT, end_index)

    # SEARCH IN TEXT EDITOR
    def search_text(self):
        search_string = Service.remove_accents(self.search_field.get().replace("\n", "").lower())
        if self.last_search == search_string:
            return
        self.last_search = search_string
        self.last_match_index = 0
        self.text_editor.tag_remove(SEARCH_RESULT_TAG_NAME, "1.0", tk.END)
        self.text_editor.tag_remove(CURRENT_SEARCH_RESULT_TAG_NAME, "1.0", tk.END)
        expression = rf"{search_string}"
        self.search_matches = list(
            re.finditer(expression, Service.remove_accents(self.doc.text.lower()), flags=re.UNICODE))
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
    def search_debounced(self, event=None):
        if self.search_debounce_timer is not None:
            self.root.after_cancel(self.search_debounce_timer)
        self.search_debounce_timer = self.root.after(1000, self.search_text)

    def evaluate_logo_placement(self, event=None):
        text = self.text_editor.get(1.0, tk.END)
        if len(text) > 1:
            self.logo_holder.place_forget()
        else:
            screen_width = self.text_editor.winfo_width()
            screen_height = self.text_editor.winfo_height()
            x = screen_width / 2 - (EDITOR_LOGO_WIDTH / 2)
            y = screen_height / 2 - (EDITOR_LOGO_HEIGHT / 2)
            self.logo_holder.place(x=x, y=y)

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

    # RUN SPELLCHECK
    def run_spellcheck(self, doc: Doc):
        if self.config.enable_spellcheck:
            Service.spellcheck(self.spellcheck_dictionary, doc)
            for word in self.doc._.words:
                if word._.has_grammar_error:
                    start_index = f"1.0 + {word.idx} chars"
                    end_index = f"1.0 + {word.idx + len(word.lower_)} chars"
                    self.text_editor.tag_add(GRAMMAR_ERROR_TAG_NAME, start_index, end_index)

    # SHOW SETTINGS WINDOW
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Nastavenia")
        self.configure_modal(settings_window, height=560)

        # SAVE SETTINGS
        def save_settings():
            self.config.repeated_words_min_word_length = int(repeated_words_min_word_length_entry.get())
            self.config.repeated_words_min_word_frequency = int(repeated_words_min_word_frequency_entry.get())
            self.config.repeated_words_use_lemma = frequent_words_use_lemma_var.get()
            self.config.long_sentence_words_mid = int(long_sentence_words_mid_entry.get())
            self.config.long_sentence_words_high = int(long_sentence_words_high_entry.get())
            self.config.long_sentence_min_word_length = int(long_sentence_min_word_length_entry.get())
            self.config.enable_frequent_words = frequent_words_var.get()
            self.config.enable_long_sentences = long_sentences_var.get()
            self.config.enable_multiple_spaces = multiple_spaces_var.get()
            self.config.enable_multiple_punctuation = multiple_punctuation_var.get()
            self.config.enable_trailing_spaces = trailing_spaces_var.get()
            self.config.close_words_use_lemma = close_words_use_lemma_var.get()
            self.config.close_words_min_word_length = int(close_words_min_word_length_entry.get())
            self.config.close_words_min_distance_between_words = int(close_words_min_distance_between_words_entry.get())
            self.config.close_words_min_frequency = int(close_words_min_frequency_entry.get())
            self.config.enable_close_words = close_words_var.get()
            self.config.enable_spellcheck = spellcheck_var.get()
            Service.save_config(self.config, CONFIG_FILE_PATH)
            self.analyze_text(True)  # Reanalyze text after saving settings
            settings_window.destroy()

        row = 0
        # Frequent words settings
        tk.Label(settings_window, text="Často použité slová", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w').grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        frequent_words_var = tk.BooleanVar(value=self.config.enable_frequent_words)
        frequent_words_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=frequent_words_var)
        frequent_words_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(settings_window, text="Porovnávať základný tvar slova", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        frequent_words_use_lemma_var = tk.BooleanVar(value=self.config.repeated_words_use_lemma)
        frequent_words_use_lemma_var_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=frequent_words_use_lemma_var)
        frequent_words_use_lemma_var_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(settings_window, text="Minimálna dĺžka slova", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        repeated_words_min_word_length_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6, justify=tk.LEFT)
        repeated_words_min_word_length_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        repeated_words_min_word_length_entry.set(self.config.repeated_words_min_word_length)
        tk.Label(settings_window, text="znakov", anchor='w').grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(settings_window, text="Minimálny počet opakovaní", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        repeated_words_min_word_frequency_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        repeated_words_min_word_frequency_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        repeated_words_min_word_frequency_entry.set(self.config.repeated_words_min_word_frequency)

        # Long sentences settings
        row += 1
        tk.Label(settings_window, text="Zvýrazňovanie dlhých viet", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w').grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        long_sentences_var = tk.BooleanVar(value=self.config.enable_long_sentences)
        long_sentences_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=long_sentences_var)
        long_sentences_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(settings_window, text="Veta je stredne dlhá, ak obsahuje aspoň", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        long_sentence_words_mid_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        long_sentence_words_mid_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        long_sentence_words_mid_entry.set(self.config.long_sentence_words_mid)
        tk.Label(settings_window, text="slov", anchor='w').grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(settings_window, text="Veta je veľmi dlhá, ak obsahuje aspoň", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        long_sentence_words_high_entry = ttk.Spinbox(settings_window, from_=1, to=9999, width=6)
        long_sentence_words_high_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        long_sentence_words_high_entry.set(self.config.long_sentence_words_high)
        tk.Label(settings_window, text="slov", anchor='w').grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(settings_window, text="Nepočítať slová kratšie ako", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        long_sentence_min_word_length_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        long_sentence_min_word_length_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        long_sentence_min_word_length_entry.set(self.config.long_sentence_min_word_length)
        tk.Label(settings_window, text="znakov", anchor='w').grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        # Multiple spaces settings
        row += 1
        tk.Label(settings_window, text="Zvýrazňovanie viacnásobných medzier ", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w').grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        multiple_spaces_var = tk.BooleanVar(value=self.config.enable_multiple_spaces)
        multiple_spaces_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=multiple_spaces_var)
        multiple_spaces_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # Multiple punctuation settings
        row += 1
        tk.Label(settings_window, text="Zvýrazňovanie viacnásobnej interpunkcie", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w').grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        multiple_punctuation_var = tk.BooleanVar(value=self.config.enable_multiple_punctuation)
        multiple_punctuation_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=multiple_punctuation_var)
        multiple_punctuation_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # Trailing spaces settings
        row += 1
        tk.Label(settings_window, text="Zvýrazňovanie medzier na konci odstavca", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w').grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        trailing_spaces_var = tk.BooleanVar(value=self.config.enable_trailing_spaces)
        trailing_spaces_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=trailing_spaces_var)
        trailing_spaces_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # Close words settings
        row += 1
        tk.Label(settings_window, text="Často sa opakujúce slová", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w').grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        close_words_var = tk.BooleanVar(value=self.config.enable_close_words)
        close_words_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=close_words_var)
        close_words_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(settings_window, text="Porovnávať základný tvar slova", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        close_words_use_lemma_var = tk.BooleanVar(value=self.config.close_words_use_lemma)
        close_words_use_lemma_var_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=close_words_use_lemma_var)
        close_words_use_lemma_var_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(settings_window, text="Minimálna dĺžka slova", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        close_words_min_word_length_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        close_words_min_word_length_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        close_words_min_word_length_entry.insert(0, str(self.config.close_words_min_word_length))
        tk.Label(settings_window, text="znakov", anchor='w').grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(settings_window, text="Minimálna vzdialenosť slov", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        close_words_min_distance_between_words_entry = ttk.Spinbox(settings_window, from_=1, to=9999, width=6)
        close_words_min_distance_between_words_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        close_words_min_distance_between_words_entry.set(self.config.close_words_min_distance_between_words)
        tk.Label(settings_window, text="slov", anchor='w').grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(settings_window, text="Minimálny počet opakovaní", anchor='w').grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        close_words_min_frequency_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        close_words_min_frequency_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        close_words_min_frequency_entry.set(self.config.close_words_min_frequency)

        # Spellcheck
        row += 1
        tk.Label(settings_window, text="Kontrola gramatiky", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w').grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        spellcheck_var = tk.BooleanVar(value=self.config.enable_spellcheck)
        spellcheck_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=spellcheck_var)
        spellcheck_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # SAVE BUTTON
        row += 1
        ttk.Button(settings_window, text="Uložiť", command=save_settings).grid(
            row=row, column=1, columnspan=2, padx=10, pady=10, sticky='w'
        )

    # SHOW ABOUT DIALOG
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("O programe")
        self.configure_modal(about_window)
        about_text = tk.Label(about_window, font=(HELVETICA_FONT_NAME, 10), justify=tk.LEFT, wraplength=550, pady=10,
                              text=f"Hector - Analyzátor textu\nVerzia {VERSION}\n\nHector je jednoduchý nástroj pre "
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

    def show_dep_image(self, event=None):
        if self.current_instrospection_token is not None:
            dep_window = tk.Toplevel(self.root)
            dep_window.title("Rozbor vety")
            rlg = svg2rlg(io.StringIO(displacy.render(self.current_instrospection_token.sent, minify=True)))
            dep_image = renderPM.drawToPIL(rlg)
            scaling_ratio = 1000 / dep_image.width
            dep_view = ImageTk.PhotoImage(dep_image.resize((1000, math.ceil(dep_image.height * scaling_ratio))))
            image_holder = ttk.Label(dep_window, image=dep_view)
            image_holder.image = dep_view
            image_holder.pack(fill=tk.BOTH, expand=True)
            self.configure_modal(dep_window, width=dep_view.width(), height=dep_view.height())

    def configure_modal(self, modal, width=600, height=400):
        modal.geometry("%dx%d" % (width, height))
        modal.resizable(False, False)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width / 2 - (width / 2)
        y = screen_height / 2 - (height / 2)
        modal.geometry("+%d+%d" % (x, y))
        modal.wait_visibility()
        modal.grab_set()
        modal.transient(self.root)
