import json
import os
import platform
import random
import re
import shutil
import sys
import tarfile
import tkinter as tk
import urllib
import webbrowser
from tkinter import filedialog, ttk

from spacy.lang.char_classes import LIST_ELLIPSES, LIST_ICONS, ALPHA_LOWER, ALPHA_UPPER, ALPHA
from spacy.lang.sl.punctuation import CONCAT_QUOTES
from spacy.matcher import Matcher
from spacy.tokenizer import Tokenizer
from spacy.tokens import Doc
from spacy.tokens.token import Token
from spacy.util import compile_infix_regex
from ttkthemes import ThemedTk
import spacy
from PIL import ImageTk, Image

# WE CAN MOVE OVER TO PYTHON SPLASH INSTEAD OF IMAGE NOW
nativeSplashOpened = False
# noinspection PyBroadException
try:
    import pyi_splash
    pyi_splash.update_text('inicializujem ...')
    nativeSplashOpened = True
except:
    pass

VERSION = "0.3.0 Alfa"
SPACY_MODEL_NAME = "sk_ud_sk_snk"
SPACY_MODEL_VERSION = "1.0.0"
SPACY_MODEL_NAME_WITH_VERSION=f"{SPACY_MODEL_NAME}-{SPACY_MODEL_VERSION}"
DOCUMENTATION_LINK = "https://github.com/MartinHlavna/hector"
SPACY_MODEL_LINK = f"https://github.com/MartinHlavna/hector-spacy-model/releases/download/v.{SPACY_MODEL_VERSION}/{SPACY_MODEL_NAME_WITH_VERSION}.tar.gz"

# COLORS
PRIMARY_BLUE = "#42659d"
LIGHT_BLUE = "#bfd5e3"
MID_BLUE = "#7ea6d7"
LIGHT_WHITE = "#d7e6e1"
TEXT_COLOR_WHITE = "#ffffff"
TEXT_EDITOR_BG = "#E0E0E0"
LONG_SENTENCE_HIGHLIGH_COLOR = "#ffe8a8"

# CONSTANTS
# PREFIX FOR CLOSE WORD EDITOR TAGS
CLOSE_WORD_PREFIX = "close_word_"
MULTIPLE_PUNCTUATION_TAG_NAME = "multiple_punctuation"
TRAILING_SPACES_TAG_NAME = "trailing_spaces"
MULTIPLE_SPACES_TAG_NAME = "multiple_spaces"
LONG_SENTENCE_TAG_NAME = "long_sentence"
READABILITY_MAX_VALUE = 50
EDITOR_LOGO_HEIGHT = 300
EDITOR_LOGO_WIDTH = 300
TEXT_SIZE_SECTION_HEADER = 12
TEXT_SIZE_MENU = 10
TEXT_SIZE_BOTTOM_BAR = 10

# WE USE HELVETICA FONT
HELVETICA_FONT_NAME = "Helvetica"
BOLD_FONT = "bold"
# LOCATION OF CONFIG
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True
    WORKING_DIRECTORY = os.path.dirname(sys.executable)
else:
    WORKING_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

DATA_DIRECTORY = os.path.join(WORKING_DIRECTORY, "data")
SPACY_MODELS_DIR = os.path.join(DATA_DIRECTORY, "spacy-models")
SK_SPACY_MODEL_DIR = os.path.join(SPACY_MODELS_DIR, "sk")
CONFIG_FILE = os.path.join(DATA_DIRECTORY, "config.json")

# COLOR PALLETE FOR CLOSE WORDS
dark_colors = [
    '#8B0000',  # Dark Red
    '#FF0000',  # Red
    '#0000FF',  # Red
    '#8B008B',  # Dark Magenta
    '#FF4500',  # Orange Red
    '#CD5C5C',  # Indian Red
]

# DEFAULT CONFIGURATION VALUES
# SANE DEFAULTS FOR CREATIVE WRITTING
default_config = {
    # MINIMAL LENGTH OF WORD FOR IT TO APPEAR IN FREQUENT WORDS SECTION
    "repeated_words_min_word_length": 3,
    # MINIMAL NUMBER OF WORD REPETITIONS FOR IT TO APPEAR IN REPEATED WORDS SECTION
    "repeated_words_min_word_frequency": 2,
    # SENTENCE IS CONSIDERED LONG IF IT HAS MORE WORDS THAN THIS CONFIG
    "long_sentence_words": 8,
    # SENTENCE IS CONSIDERED LONG IF IT HAS MORE CHARS THAN THIS CONFIG
    "long_sentence_char_count": 200,
    # WORD IS COUNTED TO SENTENCE LENGTH ONLY IF IT HAS MORE MORE CHARS THAN THIS CONFIG
    "long_sentence_min_word_length": 5,
    # MINIMAL LENGTH OF WORD FOR IT TO BE HIGHLIGHTED IF VIA CLOSE_WORDS FUNCTIONALITY
    "close_words_min_word_length": 3,
    # MINIMAL DISTANCE BETWEEN REPEATED WORDS
    "close_words_min_distance_between_words": 100,
    # MINIMAL FREQUENCE FOR REPEATED WORD TO BE HIGHLIGHTED
    "close_words_min_frequency": 3,
    # ENABLE FREQUENT WORDS SIDE PANEL
    "enable_frequent_words": True,
    # ENADBLE HIGHLIGHTING OF LONG SENTENCES
    "enable_long_sentences": True,
    # ENABLE HIGHLIGHTING OF REPEATED SPACES
    "enable_multiple_spaces": True,
    # ENABLE HIGHLIGHTING OF REPEATED PUNCTUATION  (eg. !! ?? ..)
    "enable_multiple_punctuation": True,
    # ENABLE HIGHLIGHTING OF TRAILING SPACES AT THE END OF PARAGRAPH
    "enable_trailing_spaces": True,
    # ENABLE HIGHLIGHTING OF WORD THAT ARE REPEATED AT SAME SPOTS
    "enable_close_words": True,
}


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_doc_words(doc):
    matcher = Matcher(nlp.vocab)
    pattern = [{"_": {"is_word": True}}]
    matcher.add("IS_WORD_PATTERN", [pattern])
    words = []
    matches = matcher(doc)
    for match_id, start, end in matches:
        words.append(doc[start])
    return words


def get_doc_unique_words(doc):
    matcher = Matcher(nlp.vocab)
    pattern = [{"_": {"is_word": True}}]
    matcher.add("IS_WORD_PATTERN", [pattern])
    words = {}
    matches = matcher(doc)
    for match_id, start, end in matches:
        token = doc[start]
        unique_word = words.get(token.text.lower(), None)
        if unique_word is None:
            unique_word = UniqueWord(token.text.lower())
            words[token.text.lower()] = unique_word
        unique_word.occourences.append(token)
    return words


# CLASS DEFINITIONS
# UNIQUE WORD WITH IT's OCCOURENCES
class UniqueWord:
    def __init__(self, text):
        self.text = text
        self.occourences = []


class Service:
    # FUNCTION THAT LOADS CONFIG FROM FILE
    @staticmethod
    def load_config():
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                c = json.load(file)
                # CHECK IF ALL CONFIG_KEYS ARE PRESENT
                # PROVIDE MISSING KEYS FROM DEFAULTS
                for key, value in default_config.items():
                    if key not in c:
                        c[key] = value
                return c
        else:
            return default_config

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save_config(c):
        with open(CONFIG_FILE, 'w') as file:
            json.dump(c, file, indent=4)

    # FUNCTION THAT CALCULATE READABILITY INDICES
    @staticmethod
    def evaluate_readability(doc: Doc):
        if doc._.total_chars <= 1:
            return 0
        type_to_token_ratio = doc._.total_words / len(doc._.unique_words)
        average_sentence_length = doc._.total_words / sum(1 for _ in doc.sents)
        average_word_length = doc._.total_chars / doc._.total_words / 2
        mistrik_index = 50 - ((average_sentence_length * average_word_length) / type_to_token_ratio)
        return 50 - max(0.0, round(mistrik_index, 0))


class AutoScrollbar(ttk.Scrollbar):
    """Create a scrollbar that hides itself if it's not needed. Only
    works if you use the pack geometry manager from tkinter.
    """

    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            self.pack_forget()
        else:
            if self.cget("orient") == tk.HORIZONTAL:
                self.pack(fill=tk.X, side=tk.BOTTOM)
            else:
                self.pack(fill=tk.Y, side=tk.RIGHT)
        tk.Scrollbar.set(self, lo, hi)

    def grid(self, **kw):
        raise tk.TclError("cannot use grid with this widget")

    def place(self, **kw):
        raise tk.TclError("cannot use place with this widget")


# MAIN GUI WINDOW
class MainWindow:
    nlp: spacy = None

    def __init__(self, r, _nlp: spacy):
        self.nlp = _nlp
        self.root = r
        r.overrideredirect(False)
        style = ttk.Style(self.root)
        style.configure("Vertical.TScrollbar", gripcount=0, troughcolor=PRIMARY_BLUE, bordercolor=PRIMARY_BLUE,
                        background=LIGHT_BLUE, lightcolor=LIGHT_BLUE, darkcolor=MID_BLUE)

        # create new scrollbar layout
        style.layout('arrowless.Vertical.TScrollbar',
                     [('Vertical.Scrollbar.trough',
                       {'children': [('Vertical.Scrollbar.thumb',
                                      {'expand': '1', 'sticky': 'nswe'})],
                        'sticky': 'ns'})])
        # TIMER FOR DEBOUNCING EDITOR CHANGE EVENT
        self.analyze_text_debounce_timer = None
        self.tooltip = None
        self.doc = nlp('')
        # EDITOR TEXT SIZE
        self.text_size = 10
        # DICTIONARY THAT HOLDS COLOR OF WORD TO PREVENT RECOLORING ON TYPING
        self.close_word_colors = {}
        # MAIN PROGRAM RUN
        # LOAD CONFIG
        self.config = Service.load_config()
        self.root.eval('tk::PlaceWindow . center')
        # OPEN WINDOW IN MAXIMIZED STATE
        # FOR WINDOWS AND MAC OS SET STATE ZOOMED
        # FOR LINUX SET ATTRIBUTE ZOOMED
        if platform.system() == "Windows" or platform.system() == "Darwin":
            self.root.state("zoomed")
        else:
            self.root.attributes('-zoomed', True)

        # MAIN FRAME
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=1, fill=tk.BOTH, side=tk.LEFT)

        # LEFT SCROLLABLE SIDE PANEL WITH FREQUENT WORDS
        left_side_panel = tk.Frame(main_frame, width=200, relief=tk.FLAT, borderwidth=1, background=PRIMARY_BLUE)
        left_side_panel.pack(fill=tk.BOTH, side=tk.LEFT)

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
        self.bottom_panel = tk.Frame(text_editor_frame, background=MID_BLUE, height=20)
        self.bottom_panel.pack(fill=tk.BOTH, side=tk.BOTTOM)
        close_words_title = tk.Label(left_side_panel, pady=10, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                                     text="Často sa opakujúce slová",
                                     font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='n',
                                     justify='left')
        close_words_title.pack()

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

        self.text_editor = tk.Text(text_editor_frame, wrap=tk.WORD, relief=tk.FLAT, highlightthickness=0,
                                   yscrollcommand=text_editor_scroll.set, background=TEXT_EDITOR_BG, borderwidth=0)
        self.text_editor.config(font=(HELVETICA_FONT_NAME, self.text_size))
        self.text_editor.pack(expand=1, fill=tk.BOTH, padx=5, pady=5)

        image = Image.open(resource_path("images/hector-logo.png"))
        logo = ImageTk.PhotoImage(image.resize((EDITOR_LOGO_WIDTH, EDITOR_LOGO_HEIGHT)))

        self.logo_holder = ttk.Label(text_editor_frame, image=logo, background=TEXT_EDITOR_BG)
        self.logo_holder.image = logo

        text_editor_scroll.config(command=self.text_editor.yview)

        # MOUSE AND KEYBOARD BINDINGS FOR TEXT EDITOR
        self.text_editor.bind("<KeyRelease>", self.analyze_text_debounced)
        self.text_editor.bind("<Control-a>", self.select_all)
        self.text_editor.bind("<Control-A>", self.select_all)
        self.text_editor.bind("<Configure>", self.evaluate_logo_placement)

        # MOUSE WHEEL BINDING ON ROOT WINDOW
        # Windows OS
        self.root.bind("<MouseWheel>", self.change_text_size)
        # Linux OS
        self.root.bind("<Button-4>", self.change_text_size)
        self.root.bind("<Button-5>", self.change_text_size)

        word_freq_title = tk.Label(right_side_panel, pady=10, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE,
                                   text="Často použité slová", font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER),
                                   anchor='n',
                                   justify='left')
        word_freq_title.pack()

        separator = ttk.Separator(right_side_panel, orient='horizontal')
        separator.pack(fill=tk.X, padx=10)

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

        char_count_info_label = tk.Label(self.bottom_panel, text="Počet znakov s medzerami:", anchor='sw',
                                         justify='left', background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                                         font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        char_count_info_label.pack(side=tk.LEFT, padx=(5, 0), pady=5)

        self.char_count_info_value = tk.Label(self.bottom_panel, text="0", anchor='sw', justify='left',
                                              background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                                              font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.char_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)

        tk.Label(self.bottom_panel, text="Počet slov:", anchor='sw', justify='left',
                 background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.LEFT, padx=(5, 0), pady=5
        )

        self.word_count_info_value = tk.Label(self.bottom_panel, text="0", anchor='sw', justify='left',
                                              background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                                              font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.word_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)

        tk.Label(self.bottom_panel, text="Počet normostrán:", anchor='sw', justify='left',
                 background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.LEFT, padx=(5, 0), pady=5
        )

        self.page_count_info_value = tk.Label(self.bottom_panel, text="0", anchor='sw', justify='left',
                                              background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                                              font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.page_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)

        tk.Label(self.bottom_panel, text="Štylistická zložitosť textu:", anchor='sw', justify='left',
                 background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                 font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR)).pack(
            side=tk.LEFT, padx=(5, 0), pady=5
        )

        self.readability_value = tk.Label(self.bottom_panel, text=f"0 / {READABILITY_MAX_VALUE}", anchor='sw',
                                          justify='left',
                                          background=MID_BLUE, foreground=TEXT_COLOR_WHITE,
                                          font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.readability_value.pack(side=tk.LEFT, padx=0, pady=5)

        self.editor_text_size_input = ttk.Spinbox(self.bottom_panel, from_=1, to=30, width=10,
                                                  font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR),
                                                  style='info.TSpinbox', takefocus=False,
                                                  command=lambda: self.set_text_size(self.editor_text_size_input.get()))
        self.editor_text_size_input.set(self.text_size)
        self.editor_text_size_input.bind("<Return>", lambda e: self.set_text_size(self.editor_text_size_input.get()))
        self.editor_text_size_input.pack(side=tk.RIGHT)
        tk.Label(self.bottom_panel, text="Veľkosť textu v editore:", anchor='sw', justify='left',
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
        root.after(100, self.evaluate_logo_placement)

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
        if not self.config["enable_frequent_words"]:
            return
        words = {k: v for (k, v) in doc._.unique_words.items() if
                 len(k) >= self.config["repeated_words_min_word_length"] and len(v.occourences) >= self.config[
                     "repeated_words_min_word_frequency"]}
        sorted_word_counts = sorted(words.values(), key=lambda x: len(x.occourences), reverse=True)

        # NOTE
        # In tk, there is problem with scrolling so we default to using on big text to dispaly frequencies
        # There is way of making canvas with scrollregion but this is more performant
        frequent_words_text = "\n".join(
            [f"{word.text}\t\t{len(word.occourences)}x" for word in sorted_word_counts]
        )
        MainWindow.set_text(self.word_freq_text, frequent_words_text)

    # HIGHLIGHT LONG SENTENCES
    def highlight_long_sentences(self, doc: Doc):
        self.text_editor.tag_remove(LONG_SENTENCE_TAG_NAME, "1.0", tk.END)
        if not self.config["enable_long_sentences"]:
            return
        for sentence in doc.sents:
            highlight_start = sentence.start_char
            highlight_end = sentence.end_char

            words = [word for word in sentence if
                     word._.is_word and len(word.text) >= self.config["long_sentence_min_word_length"]]
            if len(words) > self.config["long_sentence_words"] or len(sentence.text) > self.config[
                "long_sentence_char_count"]:
                start_index = f"1.0 + {highlight_start} chars"
                end_index = f"1.0 + {highlight_end} chars"
                self.text_editor.tag_add(LONG_SENTENCE_TAG_NAME, start_index, end_index)
                # ON MOUSE OVER, SHOW TOOLTIP
                self.text_editor.tag_bind(LONG_SENTENCE_TAG_NAME, "<Enter>",
                                          lambda e: self.show_tooltip(e, f'Táto veta je dlhá.'))
                self.text_editor.tag_bind(LONG_SENTENCE_TAG_NAME, "<Leave>", lambda e: self.hide_tooltip(e))
        self.text_editor.tag_config(LONG_SENTENCE_TAG_NAME, background=LONG_SENTENCE_HIGHLIGH_COLOR)

    # HIGHLIGH MULTIPLE SPACE, MULTIPLE PUNCTATION, AND TRAILING SPACES
    def highlight_multiple_issues(self, text):
        self.text_editor.tag_remove(MULTIPLE_SPACES_TAG_NAME, "1.0", tk.END)
        if self.config["enable_multiple_spaces"]:
            matches = re.finditer(r' {2,}', text)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(MULTIPLE_SPACES_TAG_NAME, start_index, end_index)
                # ON MOUSE OVER, SHOW TOOLTIP
                self.text_editor.tag_bind(MULTIPLE_SPACES_TAG_NAME, "<Enter>",
                                          lambda e: self.show_tooltip(e, 'Viacnásobná medzera'))
                self.text_editor.tag_bind(MULTIPLE_SPACES_TAG_NAME, "<Leave>", lambda e: self.hide_tooltip(e))

        if self.config["enable_multiple_punctuation"]:
            matches = re.finditer(r'([!?.,:;]){2,}', text)
            for match in matches:
                if match.group() not in ["?!"]:
                    start_index = f"1.0 + {match.start()} chars"
                    end_index = f"1.0 + {match.end()} chars"
                    self.text_editor.tag_add(MULTIPLE_PUNCTUATION_TAG_NAME, start_index, end_index)
                    # ON MOUSE OVER, SHOW TOOLTIP
                    self.text_editor.tag_bind(MULTIPLE_PUNCTUATION_TAG_NAME, "<Enter>",
                                              lambda e: self.show_tooltip(e, 'Viacnásobná interpunkcia'))
                    self.text_editor.tag_bind(MULTIPLE_PUNCTUATION_TAG_NAME, "<Leave>", lambda e: self.hide_tooltip(e))
        if self.config["enable_trailing_spaces"]:
            matches = re.finditer(r' +$', text, re.MULTILINE)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(TRAILING_SPACES_TAG_NAME, start_index, end_index)
                # ON MOUSE OVER, SHOW TOOLTIP
                self.text_editor.tag_bind(TRAILING_SPACES_TAG_NAME, "<Enter>",
                                          lambda e: self.show_tooltip(e, 'Zbytočná medzera na konci odstavca'))
                self.text_editor.tag_bind(TRAILING_SPACES_TAG_NAME, "<Leave>", lambda e: self.hide_tooltip(e))

        self.text_editor.tag_config(TRAILING_SPACES_TAG_NAME, background="red")
        self.text_editor.tag_config(MULTIPLE_PUNCTUATION_TAG_NAME, background="red")
        self.text_editor.tag_config(MULTIPLE_SPACES_TAG_NAME, background="red")

    # HIGHLIGHT WORDS THAT REPEATS CLOSE TO EACH OTHER
    def highlight_close_words(self, doc: Doc):
        if self.config["enable_close_words"]:
            self.text_editor.tag_remove("close_word", "1.0", tk.END)
            clusters = []
            close_words_counts = {}
            words_nlp = {k: v for (k, v) in doc._.unique_words.items() if
                         len(k) >= self.config["close_words_min_word_length"]}
            for unique_word in words_nlp.values():
                # IF WORD DOES NOT OCCOUR ENOUGH TIMES WE DONT NEED TO CHECK IF ITS OCCOURENCES ARE CLOSE
                if len(unique_word.occourences) < self.config["close_words_min_frequency"]:
                    continue

                current_cluster = set()
                reference = None
                for word_occource in unique_word.occourences:
                    if reference is None:
                        reference = word_occource
                        continue
                    if word_occource.idx - reference.idx < self.config[
                        "close_words_min_distance_between_words"]:
                        # IF OCCOURENCE IS TOO CLOSE TO REFERENCE ADD TO CURRENT CLUSTER
                        current_cluster.add(reference)
                        current_cluster.add(word_occource)
                    else:
                        # CLUSTER IS BROKEN, START NEW
                        if len(current_cluster) > self.config["close_words_min_frequency"]:
                            clusters.append(current_cluster)
                            if word_occource.text.lower() not in close_words_counts:
                                close_words_counts[word_occource.text.lower()] = len(current_cluster)
                            else:
                                close_words_counts[word_occource.text.lower()] += len(current_cluster)
                        current_cluster = set()
                        # MOVE REFERENCE TO NEXT WORD
                        reference = word_occource
                # PUSH REMAINING CLUSTER
                if len(current_cluster) >= self.config["close_words_min_frequency"]:
                    clusters.append(current_cluster)
                    word_occource = next(iter(current_cluster))
                    if word_occource.text.lower() not in close_words_counts:
                        close_words_counts[word_occource.text.lower()] = len(current_cluster)
                    else:
                        close_words_counts[word_occource.text.lower()] += len(current_cluster)
            close_words_counts = dict(sorted(close_words_counts.items(), key=lambda item: item[1], reverse=True))

            # NOTE
            # In tk, there is problem with scrolling so we default to using on big text to dispaly frequencies
            # There is way of making canvas with scrollregion but this is more performant
            close_words_value_text = "\n".join(
                [f"{word.lower()}\t\t{close_words_counts[word]}x" for word in close_words_counts]
            )
            MainWindow.set_text(self.close_words_text, close_words_value_text)
            for cluster in clusters:
                color = random.choice(dark_colors)
                for word in cluster:
                    start_index = f"1.0 + {word.idx} chars"
                    end_index = f"1.0 + {word.idx + len(word)} chars"
                    tag_name = f"{CLOSE_WORD_PREFIX}{word.text.lower()}"
                    original_color = self.close_word_colors.get(tag_name, "")
                    if original_color != "":
                        color = original_color
                    else:
                        self.close_word_colors[tag_name] = color
                    self.text_editor.tag_add(tag_name, start_index, end_index)
                    self.text_editor.tag_config(tag_name, foreground=color,
                                                font=(HELVETICA_FONT_NAME, self.text_size + 2, BOLD_FONT))
                    # ON MOUSE OVER, HIGHLIGHT SAME WORDS
                    self.text_editor.tag_bind(tag_name, "<Enter>",
                                              lambda e, w=word.text.lower(): self.highlight_same_word(e, w))
                    self.text_editor.tag_bind(tag_name, "<Leave>",
                                              lambda e, w=word.text.lower(): self.unhighlight_same_word(e, w))

    # HIGHLIGHT SAME WORD ON MOUSE OVER
    def highlight_same_word(self, event, word):
        self.show_tooltip(event, 'Toto slovo sa opakuje viackrát na krátkom úseku')
        for tag in self.text_editor.tag_names():
            if tag == f"{CLOSE_WORD_PREFIX}{word}":
                self.text_editor.tag_config(tag, background="black", foreground="white")

    # REMOVE HIGHLIGHTING FROM SAME WORD ON MOUSE OVER END
    def unhighlight_same_word(self, event, word):
        self.hide_tooltip(event)
        for tag in self.text_editor.tag_names():
            if tag.startswith(f"{CLOSE_WORD_PREFIX}{word}"):
                original_color = self.close_word_colors.get(tag, "")
                self.text_editor.tag_config(tag, background="", foreground=original_color)

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
                self.analyze_text()

    # SAVE TEXT FILE
    def save_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Textové súbory", "*.txt")])
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                text = self.text_editor.get(1.0, tk.END)
                file.write(text)

    # ANALYZE TEXT
    def analyze_text(self, event=None):
        # CLEAR DEBOUNCE TIMER IF ANY
        self.analyze_text_debounce_timer = None
        self.evaluate_logo_placement()
        # GET TEXT FROM EDITOR
        text = self.text_editor.get(1.0, tk.END)
        # RUN ANALYSIS
        self.doc = nlp(text).doc
        # CLEAR TAGS
        for tag in self.text_editor.tag_names():
            self.text_editor.tag_delete(tag)
        # RUN ANALYSIS FUNCTIONS
        self.display_word_frequencies(self.doc)
        self.display_size_info(self.doc)
        self.highlight_long_sentences(self.doc)
        self.highlight_close_words(self.doc)
        self.highlight_multiple_issues(text)
        self.text_editor.tag_raise("sel")
        readability = Service.evaluate_readability(self.doc)
        self.readability_value.configure(text=f"{readability: .0f} / {READABILITY_MAX_VALUE}")

    # RUN ANALYSIS ONE SECOND AFTER LAST CHANGE
    def analyze_text_debounced(self, event=None):
        self.evaluate_logo_placement()
        if self.analyze_text_debounce_timer is not None:
            self.root.after_cancel(self.analyze_text_debounce_timer)
        self.analyze_text_debounce_timer = self.root.after(1000, self.analyze_text)

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
        return "break"

    # SHOW SETTINGS WINDOW
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Nastavenia")
        self.configure_modal(settings_window, height=500)

        # SAVE SETTINGS
        def save_settings():
            self.config["repeated_words_min_word_length"] = int(repeated_words_min_word_length_entry.get())
            self.config["repeated_words_min_word_frequency"] = int(repeated_words_min_word_frequency_entry.get())
            self.config["long_sentence_words"] = int(long_sentence_words_entry.get())
            self.config["long_sentence_char_count"] = int(long_sentence_char_count_entry.get())
            self.config["long_sentence_min_word_length"] = int(long_sentence_min_word_length_entry.get())
            self.config["enable_frequent_words"] = frequent_words_var.get()
            self.config["enable_long_sentences"] = long_sentences_var.get()
            self.config["enable_multiple_spaces"] = multiple_spaces_var.get()
            self.config["enable_multiple_punctuation"] = multiple_punctuation_var.get()
            self.config["enable_trailing_spaces"] = trailing_spaces_var.get()
            self.config["close_words_min_word_length"] = int(close_words_min_word_length_entry.get())
            self.config["close_words_min_distance_between_words"] = int(
                close_words_min_distance_between_words_entry.get())
            self.config["close_words_min_frequency"] = int(close_words_min_frequency_entry.get())
            self.config["enable_close_words"] = close_words_var.get()
            Service.save_config(self.config)
            self.analyze_text()  # Reanalyze text after saving settings
            settings_window.destroy()

        # Frequent words settings
        tk.Label(settings_window, text="Často použité slová", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w').grid(
            row=0, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        frequent_words_var = tk.BooleanVar(value=self.config["enable_frequent_words"])
        frequent_words_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=frequent_words_var)
        frequent_words_checkbox.grid(row=0, column=1, padx=(6, 10), pady=2, sticky='w')
        tk.Label(settings_window, text="Minimálna dĺžka slova", anchor='w').grid(
            row=1, column=0, padx=10, pady=2, sticky='w'
        )
        repeated_words_min_word_length_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6, justify=tk.LEFT)
        repeated_words_min_word_length_entry.grid(row=1, column=1, padx=10, pady=2, sticky='w')
        repeated_words_min_word_length_entry.set(self.config["repeated_words_min_word_length"])
        tk.Label(settings_window, text="znakov", anchor='w').grid(
            row=1, column=2, padx=10, pady=2, sticky='w'
        )
        tk.Label(settings_window, text="Minimálny počet opakovaní", anchor='w').grid(
            row=2, column=0, padx=10, pady=2, sticky='w'
        )
        repeated_words_min_word_frequency_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        repeated_words_min_word_frequency_entry.grid(row=2, column=1, padx=10, pady=2, sticky='w')
        repeated_words_min_word_frequency_entry.set(self.config["repeated_words_min_word_frequency"])
        # Long sentences settings
        tk.Label(settings_window, text="Zvýrazňovanie dlhých viet", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w').grid(
            row=5, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        long_sentences_var = tk.BooleanVar(value=self.config["enable_long_sentences"])
        long_sentences_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=long_sentences_var)
        long_sentences_checkbox.grid(row=5, column=1, padx=(6, 10), pady=2, sticky='w')
        tk.Label(settings_window, text="Veta je dlhá, ak obsahuje aspoň", anchor='w').grid(
            row=6, column=0, padx=10, pady=2, sticky='w'
        )
        long_sentence_words_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        long_sentence_words_entry.grid(row=6, column=1, padx=10, pady=2, sticky='w')
        long_sentence_words_entry.set(self.config["long_sentence_words"])
        tk.Label(settings_window, text="slov", anchor='w').grid(
            row=6, column=2, padx=10, pady=2, sticky='w'
        )
        tk.Label(settings_window, text="Veta je dlhá, ak obsahuje aspoň", anchor='w').grid(
            row=7, column=0, padx=10, pady=2, sticky='w'
        )
        long_sentence_char_count_entry = ttk.Spinbox(settings_window, from_=1, to=9999, width=6)
        long_sentence_char_count_entry.grid(row=7, column=1, padx=10, pady=2, sticky='w')
        long_sentence_char_count_entry.set(self.config["long_sentence_char_count"])
        tk.Label(settings_window, text="znakov", anchor='w').grid(
            row=7, column=2, padx=10, pady=2, sticky='w'
        )
        tk.Label(settings_window, text="Nepočítať slová kratšie ako", anchor='w').grid(
            row=8, column=0, padx=10, pady=2, sticky='w'
        )
        long_sentence_min_word_length_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        long_sentence_min_word_length_entry.grid(row=8, column=1, padx=10, pady=2, sticky='w')
        long_sentence_min_word_length_entry.set(self.config["long_sentence_min_word_length"])
        tk.Label(settings_window, text="znakov", anchor='w').grid(
            row=8, column=2, padx=10, pady=2, sticky='w'
        )
        # Multiple spaces settings
        tk.Label(settings_window, text="Zvýraňovanie viacnásobných medzier ", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w').grid(
            row=11, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        multiple_spaces_var = tk.BooleanVar(value=self.config["enable_multiple_spaces"])
        multiple_spaces_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=multiple_spaces_var)
        multiple_spaces_checkbox.grid(row=11, column=1, padx=(6, 10), pady=2, sticky='w')
        # Multiple punctuation settings
        tk.Label(settings_window, text="Zvýrazňovanie viacnásobnej interpunkcie",
                 font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w').grid(
            row=14, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        multiple_punctuation_var = tk.BooleanVar(value=self.config["enable_multiple_punctuation"])
        multiple_punctuation_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté",
                                                        variable=multiple_punctuation_var)
        multiple_punctuation_checkbox.grid(row=14, column=1, padx=(6, 10), pady=2, sticky='w')
        # Trailing spaces settings
        tk.Label(settings_window, text="Zvýrazňovanie medzier na konci odstavca",
                 font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w').grid(
            row=17, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        trailing_spaces_var = tk.BooleanVar(value=self.config["enable_trailing_spaces"])
        trailing_spaces_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=trailing_spaces_var)
        trailing_spaces_checkbox.grid(row=17, column=1, padx=(6, 10), pady=2, sticky='w')
        # Close words settings
        tk.Label(settings_window, text="Slová blízko seba", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w').grid(
            row=20, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        close_words_var = tk.BooleanVar(value=self.config["enable_close_words"])
        close_words_checkbox = ttk.Checkbutton(settings_window, text="Zapnuté", variable=close_words_var)
        close_words_checkbox.grid(row=20, column=1, padx=(6, 10), pady=2, sticky='w')
        tk.Label(settings_window, text="Minimálna dlžka slova", anchor='w').grid(
            row=21, column=0, padx=10, pady=2, sticky='w'
        )
        close_words_min_word_length_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        close_words_min_word_length_entry.grid(row=21, column=1, padx=10, pady=2, sticky='w')
        close_words_min_word_length_entry.insert(0, str(self.config["close_words_min_word_length"]))
        tk.Label(settings_window, text="znakov", anchor='w').grid(
            row=21, column=2, padx=10, pady=2, sticky='w'
        )
        tk.Label(settings_window, text="Minimálna vzdialenosť slov", anchor='w').grid(
            row=22, column=0, padx=10, pady=2, sticky='w'
        )
        close_words_min_distance_between_words_entry = ttk.Spinbox(settings_window, from_=1, to=9999, width=6)
        close_words_min_distance_between_words_entry.grid(row=22, column=1, padx=10, pady=2, sticky='w')
        close_words_min_distance_between_words_entry.set(self.config["close_words_min_distance_between_words"])
        tk.Label(settings_window, text="znakov", anchor='w').grid(
            row=22, column=2, padx=10, pady=2, sticky='w'
        )
        tk.Label(settings_window, text="Minimálny počet opakovaní", anchor='w').grid(
            row=23, column=0, padx=10, pady=2, sticky='w'
        )
        close_words_min_frequency_entry = ttk.Spinbox(settings_window, from_=1, to=100, width=6)
        close_words_min_frequency_entry.grid(row=23, column=1, padx=10, pady=2, sticky='w')
        close_words_min_frequency_entry.set(self.config["close_words_min_frequency"])
        # SAVE BUTTON
        ttk.Button(settings_window, text="Uložiť", command=save_settings).grid(
            row=25, column=1, columnspan=2, padx=10, pady=10, sticky='w'
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

    def configure_modal(self, modal, width=600, height=400):
        modal.geometry("%dx%d" % (width, height))
        modal.resizable(False, False)
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width / 2 - (width / 2)
        y = screen_height / 2 - (height / 2)

        self.root.geometry("+%d+%d" % (x, y))
        modal.grab_set()
        modal.transient(self.root)


# SPLASH SCREEN TO SHOW WHILE INITIALIZING MAIN APP
class SplashWindow:
    def __init__(self, r):
        self.root = r
        self.root.geometry("600x400")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width / 2 - 300
        y = screen_height / 2 - 200

        self.root.geometry("+%d+%d" % (x, y))
        self.root.overrideredirect(True)
        # MAIN FRAME
        self.main_frame = tk.Frame(self.root, background=PRIMARY_BLUE)
        self.main_frame.pack(expand=1, fill=tk.BOTH, side=tk.LEFT)
        image = Image.open(resource_path("images/hector-logo.png"))
        logo = ImageTk.PhotoImage(image.resize((300, 300)))

        logo_holder = ttk.Label(self.main_frame, image=logo, background=PRIMARY_BLUE)
        logo_holder.image = logo
        logo_holder.pack()
        self.status = tk.Label(self.main_frame, text="inicializujem...", background=PRIMARY_BLUE,
                               font=(HELVETICA_FONT_NAME, 10), foreground="#ffffff")
        self.status.pack()
        # required to make window show before the program gets to the mainloop
        self.root.update()

    def close(self):
        self.main_frame.destroy()

    def update_status(self, text):
        self.status.config(text=text)
        self.root.update()


root = ThemedTk(theme="clam")
root.title("Hector")
photo = tk.PhotoImage(file=resource_path('images/hector-icon.png'))
root.wm_iconphoto(True, photo)
splash = SplashWindow(root)
splash.update_status("sťahujem a inicializujem jazykový model...")
# WE CAN MOVE OVER TO PYTHON SPLASH INSTEAD OF IMAGE NOW
if nativeSplashOpened:
    pyi_splash.close()
# INITIALIZE NLP ENGINE
spacy.util.set_data_path = resource_path('lib/site-packages/spacy/data')
if not os.path.isdir(DATA_DIRECTORY):
    os.mkdir(DATA_DIRECTORY)
if not os.path.isdir(SPACY_MODELS_DIR):
    os.mkdir(SPACY_MODELS_DIR)
if not os.path.isdir(SK_SPACY_MODEL_DIR):
    os.mkdir(SK_SPACY_MODEL_DIR)
    archive_file_name = os.path.join(SPACY_MODELS_DIR, f'{SPACY_MODEL_NAME_WITH_VERSION}.tar.gz')
    with urllib.request.urlopen(SPACY_MODEL_LINK) as response, open(archive_file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    with tarfile.open(archive_file_name) as tar_file:
        tar_file.extractall(SK_SPACY_MODEL_DIR)
    os.remove(archive_file_name)
nlp = spacy.load(os.path.join(
    SK_SPACY_MODEL_DIR,
    SPACY_MODEL_NAME_WITH_VERSION,
    SPACY_MODEL_NAME,
    SPACY_MODEL_NAME_WITH_VERSION)
)


def custom_tokenizer(nlp):
    infixes = (
            LIST_ELLIPSES
            + LIST_ICONS
            + [
                r"(?<=[0-9])[+\-\*^](?=[0-9-])",
                r"(?<=[{al}{q}])\.(?=[{au}{q}])".format(
                    al=ALPHA_LOWER, au=ALPHA_UPPER, q=CONCAT_QUOTES
                ),
                r"(?<=[{a}]),(?=[{a}])".format(a=ALPHA),
                #r"(?<=[{a}])(?:{h})(?=[{a}])".format(a=ALPHA, h=HYPHENS),
                r"(?<=[{a}0-9])[:<>=/](?=[{a}])".format(a=ALPHA),
            ]
    )

    infix_re = compile_infix_regex(infixes)

    return Tokenizer(nlp.vocab, prefix_search=nlp.tokenizer.prefix_search,
                     suffix_search=nlp.tokenizer.suffix_search,
                     infix_finditer=infix_re.finditer,
                     token_match=nlp.tokenizer.token_match,
                     rules=nlp.Defaults.tokenizer_exceptions)

nlp.tokenizer = custom_tokenizer(nlp)

# SPACY EXTENSIONS
word_pattern = re.compile("\\w+")
Token.set_extension("is_word", getter=lambda t: re.match(word_pattern, t.text.lower()) is not None)
Doc.set_extension("words", getter=get_doc_words)
Doc.set_extension("unique_words", getter=get_doc_unique_words)
Doc.set_extension("total_chars", getter=lambda d: len(d.text))
Doc.set_extension("total_words", getter=lambda d: len(d._.words))
Doc.set_extension("total_pages", getter=lambda d: round(len(d.text) / 1800, 2))
splash.update_status("inicializujem textový processor...")
splash.close()
main_window = MainWindow(root, nlp)
main_window.start_main_loop()

# TODO LEVEL B (nice to have features): Consider adding:
# Heatmap?
# Commas analysis based on some NLP apporach?
# On mouse over in left/ride panel word, highlight words in editor
# Right click context menu with analysis options on selected text
# Importing other document types like doc, docx, rtf, ...
