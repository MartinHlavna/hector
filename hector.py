import json
import os
import platform
import random
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from ttkthemes import ThemedTk

import stanza
from PIL import ImageTk, Image

MULTIPLE_PUNCTUATION_TAG_NAME = "multiple_punctuation"
TRAILING_SPACES_TAG_NAME = "trailing_spaces"
MULTIPLE_SPACES_TAG_NAME = "multiple_spaces"

EDITOR_LOGO_HEIGHT = 300

EDITOR_LOGO_WIDTH = 300

TEXT_SIZE_SECTION_HEADER = 12
TEXT_SIZE_MENU = 10
TEXT_SIZE_BOTTOM_BAR = 10

TEXT_COLOR_WHITE = "#ffffff"
TEXT_EDITOR_BG = "#E0E0E0"

# COLORS
PRIMARY_BLUE = "#42659d"
LIGHT_BLUE = "#bfd5e3"
MID_BLUE = "#7ea6d7"
LIGHT_WHITE = "#d7e6e1"

# CONSTANTS
# PREFIX FOR CLOSE WORD EDITOR TAGS
CLOSE_WORD_PREFIX = "close_word_"

# WE USE HELVETICA FONT
HELVETICA_FONT_NAME = "Helvetica"
BOLD_FONT = "bold"

# LOCATION OF CONFIG
CONFIG_FILE = 'config.json'

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

# CLASS DEFINITIONS
# TEXT STATISTICS
class Statistics:
    # TOTAL CHARS IN DOCUMENT
    total_chars = 0
    # NUMBER OF TOTAL WORDS IN DOCUMENT. LOOKS LIKE STANZA COUNTS PUNCTATION AS WORDS
    total_words = 0
    # NUMBER OF NORM PAGES (1800 CHARS) IN DOCUMENT
    total_pages = 0
    # DICTIONARY OF ALL WORDS IN DOCUMENTS (UniqueWord)
    words = {}


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
    def evaluate_readability(doc, statistics: Statistics):
        # TODO: Allow to run on part of text
        if statistics.total_chars <= 0:
            return {
                "Počet unikátnych slov": 0,
                "Priemerná dĺžka slova": 0,
                "Priemerný počet slov vo vete": 0,
                "Index opakovania": 0,
                "Mistríkov index": 0
            }

        type_to_token_ratio = Service.lexical_diversity(statistics)
        average_sentence_length = statistics.total_words / len(doc.sentences)
        average_word_length = statistics.total_chars / statistics.total_words / 2
        # NOTE lexical_diversity index is oposite of mistrik index of repetition.
        #  Therefore we need to use multiplication instead of division
        mistrik_index = 50 - (average_sentence_length * average_word_length * type_to_token_ratio)

        return {
            "Počet unikátnych slov": len(statistics.words),
            "Priemerná dĺžka slova": round(average_word_length * 2, 1),
            "Priemerný počet slov vo vete": round(average_sentence_length, 1),
            "Index opakovania": max(0.0, round(type_to_token_ratio, 4)),
            "Mistríkov index": max(0.0, round(mistrik_index, 0))
        }

    # CALCULATE LEXICAL DIVERSITY (RATIO OF UNIQUE WORDS TO ALL WORDS)
    @staticmethod
    def lexical_diversity(statistics: Statistics):
        if statistics.total_words == 0:
            return 0
        # UNIQUE WORDS / TOTAL WORDS
        return len(statistics.words) / statistics.total_words

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
    nlp: stanza.Pipeline = None

    def __init__(self, r, _nlp: stanza.Pipeline):
        self.nlp = _nlp
        self.root = r
        r.overrideredirect(False)
        style = ttk.Style(self.root)
        print(style.element_options("Vertical.TScrollbar.trough"))
        style.configure("Vertical.TScrollbar", gripcount=0, troughcolor=PRIMARY_BLUE, bordercolor=PRIMARY_BLUE, background=LIGHT_BLUE, lightcolor=LIGHT_BLUE, darkcolor=MID_BLUE)

        # create new scrollbar layout
        style.layout('arrowless.Vertical.TScrollbar',
                     [('Vertical.Scrollbar.trough',
                       {'children': [('Vertical.Scrollbar.thumb',
                                      {'expand': '1', 'sticky': 'nswe'})],
                        'sticky': 'ns'})])
        # TIMER FOR DEBOUNCING EDITOR CHANGE EVENT
        self.analyze_text_debounce_timer = None
        self.tooltip = None
        self.doc = nlp('', processors='tokenize')
        # WE NEED TO COMPUTE SOME MORE INFORMATION
        self.statistics = Statistics()
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
        text_editor_scroll = AutoScrollbar(text_editor_scroll_frame, orient='vertical', style='arrowless.Vertical.TScrollbar', takefocus=False)
        text_editor_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # BOTTOM PANEL WITH TEXT SIZE
        # TODO: Add text size input to change editor text size without mouse
        self.bottom_panel = tk.Frame(text_editor_frame, background=MID_BLUE, height=20)
        self.bottom_panel.pack(fill=tk.BOTH, side=tk.BOTTOM)
        close_words_title = tk.Label(left_side_panel, pady=10,  background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, text="Často sa opakujúce slová", font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='n',
                                     justify='left')
        close_words_title.pack()

        separator = ttk.Separator(left_side_panel, orient='horizontal')
        separator.pack(fill=tk.X, padx=10)

        left_side_panel_scroll_frame = tk.Frame(left_side_panel, width=10, relief=tk.FLAT, background=PRIMARY_BLUE)
        left_side_panel_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        left_side_frame_scroll = AutoScrollbar(left_side_panel_scroll_frame, orient='vertical', style='arrowless.Vertical.TScrollbar', takefocus=False)
        left_side_frame_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.word_freq_text = tk.Text(left_side_panel, highlightthickness=0, bd=0, wrap=tk.WORD, state=tk.DISABLED, width=20, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, yscrollcommand=left_side_frame_scroll.set)
        self.word_freq_text.pack(fill=tk.BOTH, expand=1, pady=10, padx=10)

        left_side_frame_scroll.config(command=self.word_freq_text.yview)

        self.text_editor = tk.Text(text_editor_frame, wrap=tk.WORD, relief=tk.FLAT, yscrollcommand=text_editor_scroll.set, background=TEXT_EDITOR_BG, borderwidth=0)
        self.text_editor.config(font=(HELVETICA_FONT_NAME, self.text_size))
        self.text_editor.pack(expand=1, fill=tk.BOTH, padx=5)

        image = Image.open("images/hector-logo.png")
        logo = ImageTk.PhotoImage(image.resize((EDITOR_LOGO_WIDTH, EDITOR_LOGO_HEIGHT), Image.ANTIALIAS))

        self.logo_holder = tk.Label(text_editor_frame, image=logo, background=TEXT_EDITOR_BG)
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



        word_freq_title = tk.Label(right_side_panel, pady=10,  background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, text="Často použité slová", font=(HELVETICA_FONT_NAME, TEXT_SIZE_SECTION_HEADER), anchor='n',
                                   justify='left')
        word_freq_title.pack()

        separator = ttk.Separator(right_side_panel, orient='horizontal')
        separator.pack(fill=tk.X, padx=10)

        right_side_panel_scroll_frame = tk.Frame(right_side_panel, width=10, relief=tk.FLAT, background=PRIMARY_BLUE)
        right_side_panel_scroll_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_side_frame_scroll = AutoScrollbar(right_side_panel_scroll_frame, orient='vertical', style='arrowless.Vertical.TScrollbar', takefocus=False)
        right_side_frame_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.word_freq_text = tk.Text(right_side_panel, highlightthickness=0, bd=0, wrap=tk.WORD, state=tk.DISABLED, width=20, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, yscrollcommand=right_side_frame_scroll.set)
        self.word_freq_text.pack(fill=tk.BOTH, expand=1, pady=10, padx=10)

        right_side_frame_scroll.config(command=self.word_freq_text.yview)


        char_count_info_label = tk.Label(self.bottom_panel, text="Počet znakov s medzerami:", anchor='sw', justify='left', background=MID_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        char_count_info_label.pack(side=tk.LEFT, padx=(5,0), pady=5)

        self.char_count_info_value = tk.Label(self.bottom_panel, text="0", anchor='sw', justify='left', background=MID_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.char_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)

        word_count_info_label = tk.Label(self.bottom_panel, text="Počet slov:", anchor='sw', justify='left', background=MID_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        word_count_info_label.pack(side=tk.LEFT, padx=(5,0), pady=5)

        self.word_count_info_value = tk.Label(self.bottom_panel, text="0", anchor='sw', justify='left', background=MID_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.word_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)

        page_count_info_label = tk.Label(self.bottom_panel, text="Počet normostrán:", anchor='sw', justify='left', background=MID_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        page_count_info_label.pack(side=tk.LEFT, padx=(5,0), pady=5)

        self.page_count_info_value = tk.Label(self.bottom_panel, text="0", anchor='sw', justify='left', background=MID_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_BOTTOM_BAR))
        self.page_count_info_value.pack(side=tk.LEFT, padx=0, pady=5)


        # TOP MENU
        self.menu_bar = tk.Menu(self.root, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, border=1)
        self.root.config(menu=self.menu_bar)

        # FILE MENU
        # TODO: Maybe add a way to import MS word or other document type
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU))
        self.file_menu.add_command(label="Načítať súbor", command=self.load_file)
        self.file_menu.add_command(label="Uložiť súbor", command=self.save_file)
        self.menu_bar.add_cascade(label="Súbor", menu=self.file_menu)

        # ANALYZE MENU
        # TODO: We need to think of more things we can analyze... because everything can be and should be analyzed xD
        self.analyze_menu = tk.Menu(self.menu_bar, tearoff=0, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU))
        self.analyze_menu.add_command(label="Indexy čitateľnosti", command=self.show_readability_indices)
        self.menu_bar.add_cascade(label="Analýza", menu=self.analyze_menu)

        # SETTINGS MENU
        self.settings_menu = tk.Menu(self.menu_bar, tearoff=0, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU))
        self.settings_menu.add_command(label="Parametre analýzy", command=self.show_settings)
        self.menu_bar.add_cascade(label="Nastavenia", menu=self.settings_menu)

        # HELP MENU
        # TODO: Add link to documentation
        self.help_menu = tk.Menu(self.menu_bar, tearoff=0, background=PRIMARY_BLUE, foreground=TEXT_COLOR_WHITE, font=(HELVETICA_FONT_NAME, TEXT_SIZE_MENU))
        self.help_menu.add_command(label="O programe", command=self.show_about)
        self.menu_bar.add_cascade(label="Pomoc", menu=self.help_menu)
        root.after(100, self.evaluate_logo_placement)

    #START MAIN LOOP
    def start_main_loop(self):
        # START MAIN LOOP TO SHOW ROOT WINDOW
        self.root.mainloop()
    # CHANGE TEXT SIZE WHEN USER SCROLL MOUSEWHEEL WITH CTRL PRESSED
    # TODO: MAYBE ADD ANOTHER WAY OF CHANGING TEXT SIZE
    def change_text_size(self, event):
        # CHECK IF CTRL IS PRESSED
        if event.state & 0x0004:
            # ON WINDOWS IF USER SCROLLS "UP" event.delta IS POSITIVE
            # ON LINUX IF USER SCROLLS "UP" event.num IS 4
            # TODO What about mac os?
            if event.delta > 0 or event.num == 4:
                self.text_size += 1
            # ON WINDOWS IF USER SCROLLS "DOWN" event.delta IS NEGATIVE
            # ON LINUX IF USER SCROLLS "DOWN" event.num IS 5
            # TODO What about mac os?
            elif event.delta < 0 or event.num == 5:
                self.text_size -= 1

            # CHANGE FONT SIZE IN EDITOR
            self.text_editor.config(font=(HELVETICA_FONT_NAME, self.text_size))
            # CLOSE WORDS ARE ALWAYS HIGHLIGHTED WITH BIGGER FONT. WE NEED TO UPDATE TAGS
            for tag in self.text_editor.tag_names():
                if tag.startswith(CLOSE_WORD_PREFIX):
                    self.text_editor.tag_configure(tagName=tag, font=(HELVETICA_FONT_NAME, self.text_size + 2, BOLD_FONT))
    # DISPLAY INFORMATIONS ABOUT TEXT SIZE
    def display_size_info(self, statistics: Statistics):
        self.char_count_info_value.config(text=f"{statistics.total_chars}")
        self.word_count_info_value.config(text=f"{statistics.total_words}")
        self.page_count_info_value.config(text=f"{statistics.total_pages}")

    # CALCULATE AND DISPLAY FREQUENT WORDS
    def display_word_frequencies(self, statistics: Statistics):
        if not self.config["enable_frequent_words"]:
            return
        words = {k: v for (k, v) in statistics.words.items() if
                 len(k) >= self.config["repeated_words_min_word_length"] and len(v.occourences) >= self.config[
                     "repeated_words_min_word_frequency"]}
        sorted_word_counts = sorted(words.values(), key=lambda x: len(x.occourences), reverse=True)

        # TODO
        # In tk, there is problem with scrolling so we default to using on big text to dispaly frequencies
        # ugly but it works for now
        frequent_words_text = "\n".join(
            [f"{word.text}: {len(word.occourences)}x" for word in sorted_word_counts]
        )

        # WE NEED TO ENBLE TEXT, DELETE CONTENT AND INSERT NEW TEXT
        self.word_freq_text.config(state=tk.NORMAL)
        self.word_freq_text.delete(1.0, tk.END)
        self.word_freq_text.insert(tk.END, frequent_words_text)
        # DISABLING AGAIN
        self.word_freq_text.config(state=tk.DISABLED)

    # HIGHLIGHT LONG SENTENCES
    def highlight_long_sentences(self, doc):
        self.text_editor.tag_remove("long_sentence", "1.0", tk.END)
        if not self.config["enable_long_sentences"]:
            return
        for sentence in doc.sentences:
            first_token = sentence.tokens[0]
            last_token = sentence.tokens[len(sentence.tokens) - 1]
            highlight_start = first_token.start_char
            highlight_end = last_token.end_char

            words = [word for word in sentence.words if
                     len(word.text) >= self.config["long_sentence_min_word_length"]]
            if len(words) > self.config["long_sentence_words"] or len(sentence.text) > self.config["long_sentence_char_count"]:
                start_index = f"1.0 + {highlight_start} chars"
                end_index = f"1.0 + {highlight_end} chars"
                self.text_editor.tag_add("long_sentence", start_index, end_index)
        self.text_editor.tag_config("long_sentence", background="yellow")

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
                self.text_editor.tag_bind(MULTIPLE_SPACES_TAG_NAME, "<Enter>", lambda e: self.show_tooltip(e, 'Viacnásobná medzera'))
                self.text_editor.tag_bind(MULTIPLE_SPACES_TAG_NAME, "<Leave>", lambda e: self.hide_tooltip(e))

        if self.config["enable_multiple_punctuation"]:
            matches = re.finditer(r'([!?.,:;]){2,}', text)
            for match in matches:
                if match.group() not in ["?!"]:
                    start_index = f"1.0 + {match.start()} chars"
                    end_index = f"1.0 + {match.end()} chars"
                    self.text_editor.tag_add(MULTIPLE_PUNCTUATION_TAG_NAME, start_index, end_index)
                    # ON MOUSE OVER, SHOW TOOLTIP
                    self.text_editor.tag_bind(MULTIPLE_PUNCTUATION_TAG_NAME, "<Enter>", lambda e: self.show_tooltip(e, 'Viacnásobná interpunkcia'))
                    self.text_editor.tag_bind(MULTIPLE_PUNCTUATION_TAG_NAME, "<Leave>", lambda e: self.hide_tooltip(e))
        if self.config["enable_trailing_spaces"]:
            matches = re.finditer(r' +$', text, re.MULTILINE)
            for match in matches:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.text_editor.tag_add(TRAILING_SPACES_TAG_NAME, start_index, end_index)
                # ON MOUSE OVER, SHOW TOOLTIP
                self.text_editor.tag_bind(TRAILING_SPACES_TAG_NAME, "<Enter>", lambda e: self.show_tooltip(e, 'Zbytočná medzera na konci odstavca'))
                self.text_editor.tag_bind(TRAILING_SPACES_TAG_NAME, "<Leave>", lambda e: self.hide_tooltip(e))

        self.text_editor.tag_config(TRAILING_SPACES_TAG_NAME, background="red")
        self.text_editor.tag_config(MULTIPLE_PUNCTUATION_TAG_NAME, background="red")
        self.text_editor.tag_config(MULTIPLE_SPACES_TAG_NAME, background="red")

    # HIGHLIGHT WORDS THAT REPEATS CLOSE TO EACH OTHER
    # TODO: Maybe we could provide list of "CLOSE WORDS" IN RIGHT PANEL AND HIGHLIGHT ON MOUSE OVER
    def highlight_close_words(self, statistics: Statistics):
        if self.config["enable_close_words"]:
            self.text_editor.tag_remove("close_word", "1.0", tk.END)
            clusters = []
            words_nlp = {k: v for (k, v) in statistics.words.items() if len(k) >= self.config["close_words_min_word_length"]}
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
                    if word_occource.start_char - reference.start_char < self.config["close_words_min_distance_between_words"]:
                        # IF OCCOURENCE IS TOO CLOSE TO REFERENCE ADD TO CURRENT CLUSTER
                        current_cluster.add(reference)
                        current_cluster.add(word_occource)
                    else:
                        # CLUSTER IS BROKEN, START NEW
                        if len(current_cluster) > self.config["close_words_min_frequency"]:
                            clusters.append(current_cluster)
                        current_cluster = set()
                        # MOVE REFERENCE TO NEXT WORD
                        reference = word_occource
                # PUSH REMAINING CLUSTER
                if len(current_cluster) >= self.config["close_words_min_frequency"]:
                    clusters.append(current_cluster)

            for cluster in clusters:
                color = random.choice(dark_colors)
                for word in cluster:
                    start_index = f"1.0 + {word.start_char} chars"
                    end_index = f"1.0 + {word.end_char} chars"
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
                    self.text_editor.tag_bind(tag_name, "<Enter>", lambda e, w=word.text.lower(): self.highlight_same_word(e,w))
                    self.text_editor.tag_bind(tag_name, "<Leave>", lambda e, w=word.text.lower(): self.unhighlight_same_word(e, w))

    # HIGHLIGHT SAME WORD ON MOUSE OVER
    def highlight_same_word(self, event, word):
        self.show_tooltip(event,  'Toto slovo sa opakuje viackrát na krátkom úseku')
        for tag in self.text_editor.tag_names():
            if tag.startswith(f"{CLOSE_WORD_PREFIX}{word}"):
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
        label = tk.Label(self.tooltip, text=f"{text}", background=LIGHT_BLUE, relief="solid", borderwidth=1, justify="left", padx=5, pady=5)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    # LOAD TEXT FILE
    # TODO: Maybe we could extract text from MS WORD?
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
        self.evaluate_logo_placement()
        # CLEAR DEBOUNCE TIMER IF ANY
        self.analyze_text_debounce_timer = None
        # GET TEXT FROM EDITOR
        text = self.text_editor.get(1.0, tk.END)
        # RUN ANALYSIS
        self.doc = nlp(text, processors='tokenize')
        self.statistics.words = {}
        self.statistics.total_words = 0
        self.statistics.total_chars = len(text)
        self.statistics.total_pages = round(self.statistics.total_chars / 1800, 2)
        for sentence in self.doc.sentences:
            for token in sentence.tokens:
                if re.match('\\w', token.text):
                    self.statistics.total_words += 1
                    word = self.statistics.words.get(token.text.lower())
                    if word is None:
                        word = UniqueWord(token.text.lower())
                        self.statistics.words[token.text.lower()] = word
                    word.occourences.append(token)
        # CLEAR TAGS
        for tag in self.text_editor.tag_names():
            self.text_editor.tag_delete(tag)
        # RUN ANALYSIS FUNCTIONS
        self.display_word_frequencies(self.statistics)
        self.display_size_info(self.statistics)
        self.highlight_long_sentences(self.doc)
        self.highlight_close_words(self.statistics)
        self.highlight_multiple_issues(text)
        self.text_editor.tag_raise("sel")

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
            x = screen_width/2 - (EDITOR_LOGO_WIDTH / 2)
            y = screen_height/2 - (EDITOR_LOGO_HEIGHT / 2)
            self.logo_holder.place(x=x,y=y)
    # SELECT ALL TEXT
    def select_all(self, event=None):
        self.text_editor.tag_add(tk.SEL, "1.0", tk.END)
        return "break"


    # SHOW SETTINGS WINDOW
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Nastavenia")

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
            self.config["close_words_min_distance_between_words"] = int(close_words_min_distance_between_words_entry.get())
            self.config["close_words_min_frequency"] = int(close_words_min_frequency_entry.get())
            self.config["enable_close_words"] = close_words_var.get()
            Service.save_config(self.config)
            self.analyze_text()  # Reanalyze text after saving settings
            settings_window.destroy()

        # Frequent words settings
        tk.Label(settings_window, text="Časté slová", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(row=0,
                                                                                                                  column=0,
                                                                                                                  columnspan=2,
                                                                                                                  padx=10,
                                                                                                                  pady=(
                                                                                                                      10,
                                                                                                                      2),
                                                                                                                  sticky='w')
        tk.Label(settings_window, text="Minimálna dĺžka slova v znakoch", anchor='w').grid(row=1, column=0, padx=10, pady=2,
                                                                                           sticky='w')
        repeated_words_min_word_length_entry = tk.Entry(settings_window)
        repeated_words_min_word_length_entry.grid(row=1, column=1, padx=10, pady=2)
        repeated_words_min_word_length_entry.insert(0, str(self.config["repeated_words_min_word_length"]))

        tk.Label(settings_window, text="Minimálna početnosť slova", anchor='w').grid(row=2, column=0, padx=10, pady=2,
                                                                                     sticky='w')
        repeated_words_min_word_frequency_entry = tk.Entry(settings_window)
        repeated_words_min_word_frequency_entry.grid(row=2, column=1, padx=10, pady=2)
        repeated_words_min_word_frequency_entry.insert(0, str(self.config["repeated_words_min_word_frequency"]))

        frequent_words_var = tk.BooleanVar(value=self.config["enable_frequent_words"])
        frequent_words_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=frequent_words_var)
        frequent_words_checkbox.grid(row=3, column=1, padx=10, pady=2, sticky='w')

        # Spacer
        tk.Label(settings_window, text="", anchor='w').grid(row=4, column=0, padx=10, pady=5, sticky='w')

        # Long sentences settings
        tk.Label(settings_window, text="Dlhé vety", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(row=5,
                                                                                                                column=0,
                                                                                                                columnspan=2,
                                                                                                                padx=10,
                                                                                                                pady=(
                                                                                                                    10, 2),
                                                                                                                sticky='w')
        tk.Label(settings_window, text="Zvýrazniť vety, ktoré majú väčší počet slov", anchor='w').grid(row=6, column=0,
                                                                                                       padx=10, pady=2,
                                                                                                       sticky='w')
        long_sentence_words_entry = tk.Entry(settings_window)
        long_sentence_words_entry.grid(row=6, column=1, padx=10, pady=2)
        long_sentence_words_entry.insert(0, str(self.config["long_sentence_words"]))

        tk.Label(settings_window, text="Zvýrazniť vety, ktoré majú viac znakov", anchor='w').grid(row=7, column=0, padx=10,
                                                                                                  pady=2, sticky='w')
        long_sentence_char_count_entry = tk.Entry(settings_window)
        long_sentence_char_count_entry.grid(row=7, column=1, padx=10, pady=2)
        long_sentence_char_count_entry.insert(0, str(self.config["long_sentence_char_count"]))

        tk.Label(settings_window, text="Nepočítať slová kratšie ako", anchor='w').grid(row=8, column=0, padx=10, pady=2,
                                                                                       sticky='w')
        long_sentence_min_word_length_entry = tk.Entry(settings_window)
        long_sentence_min_word_length_entry.grid(row=8, column=1, padx=10, pady=2)
        long_sentence_min_word_length_entry.insert(0, str(self.config["long_sentence_min_word_length"]))

        long_sentences_var = tk.BooleanVar(value=self.config["enable_long_sentences"])
        long_sentences_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=long_sentences_var)
        long_sentences_checkbox.grid(row=9, column=1, padx=10, pady=2, sticky='w')

        # Spacer
        tk.Label(settings_window, text="", anchor='w').grid(row=10, column=0, padx=10, pady=5, sticky='w')

        # Multiple spaces settings
        tk.Label(settings_window, text="Viacnásobné medzery", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(
            row=11,
            column=0,
            columnspan=2,
            padx=10,
            pady=(10, 2),
            sticky='w')
        multiple_spaces_var = tk.BooleanVar(value=self.config["enable_multiple_spaces"])
        multiple_spaces_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=multiple_spaces_var)
        multiple_spaces_checkbox.grid(row=12, column=1, padx=10, pady=2, sticky='w')

        # Spacer
        tk.Label(settings_window, text="", anchor='w').grid(row=13, column=0, padx=10, pady=5, sticky='w')

        # Multiple punctuation settings
        tk.Label(settings_window, text="Viacnásobná interpunkcia", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT),
                 anchor='w').grid(row=14,
                                  column=0,
                                  columnspan=2,
                                  padx=10,
                                  pady=(
                                      10, 2),
                                  sticky='w')
        multiple_punctuation_var = tk.BooleanVar(value=self.config["enable_multiple_punctuation"])
        multiple_punctuation_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=multiple_punctuation_var)
        multiple_punctuation_checkbox.grid(row=15, column=1, padx=10, pady=2, sticky='w')

        # Spacer
        tk.Label(settings_window, text="", anchor='w').grid(row=16, column=0, padx=10, pady=5, sticky='w')

        # Trailing spaces settings
        tk.Label(settings_window, text="Medzery na konci odstavca", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT),
                 anchor='w').grid(row=17,
                                  column=0,
                                  columnspan=2,
                                  padx=10,
                                  pady=(
                                      10, 2),
                                  sticky='w')
        trailing_spaces_var = tk.BooleanVar(value=self.config["enable_trailing_spaces"])
        trailing_spaces_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=trailing_spaces_var)
        trailing_spaces_checkbox.grid(row=18, column=1, padx=10, pady=2, sticky='w')

        # Close words settings
        tk.Label(settings_window, text="Slová blízko seba", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(
            row=20,
            column=0,
            columnspan=2,
            padx=10,
            pady=(10, 2),
            sticky='w')
        tk.Label(settings_window, text="Minimálna dlžka slova", anchor='w').grid(row=21, column=0, padx=10, pady=2,
                                                                                 sticky='w')
        close_words_min_word_length_entry = tk.Entry(settings_window)
        close_words_min_word_length_entry.grid(row=21, column=1, padx=10, pady=2)
        close_words_min_word_length_entry.insert(0, str(self.config["close_words_min_word_length"]))

        tk.Label(settings_window, text="Povolená medzera medzi opakujúcimi sa slovami", anchor='w').grid(row=22, column=0,
                                                                                                         padx=10, pady=2,
                                                                                                         sticky='w')
        close_words_min_distance_between_words_entry = tk.Entry(settings_window)
        close_words_min_distance_between_words_entry.grid(row=22, column=1, padx=10, pady=2)
        close_words_min_distance_between_words_entry.insert(0, str(self.config["close_words_min_distance_between_words"]))

        tk.Label(settings_window, text="Minimálna početnosť opakujúceho sa slova", anchor='w').grid(row=23, column=0,
                                                                                                    padx=10, pady=2,
                                                                                                    sticky='w')
        close_words_min_frequency_entry = tk.Entry(settings_window)
        close_words_min_frequency_entry.grid(row=23, column=1, padx=10, pady=2)
        close_words_min_frequency_entry.insert(0, str(self.config["close_words_min_frequency"]))

        close_words_var = tk.BooleanVar(value=self.config["enable_close_words"])
        close_words_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=close_words_var)
        close_words_checkbox.grid(row=24, column=1, padx=10, pady=2, sticky='w')

        tk.Button(settings_window, text="Uložiť", command=save_settings).grid(row=25, column=0, columnspan=2, pady=10)

    # SHOW ABOUT DIALOG
    # TODO: ADD BASIC INFO
    # TODO: Maybe add documentation
    def show_about(self):
        messagebox.showinfo("O programe", "Hector - Analyzátor textu\nVerzia 1.0")


    # CALCULATE AND SHOW VARIOUS READABILITY INDECES WITH EXPLANATIONS
    def show_readability_indices(self):
        indices = Service.evaluate_readability(self.doc, self.statistics)
        results = "\n".join([f"{index}: {value}" for index, value in indices.items()])
        index_window = tk.Toplevel(self.root)
        index_window.title("Indexy čitateľnosti")
        index_text = tk.Text(index_window, wrap=tk.WORD, font=("Arial", 10))
        index_text.insert(tk.END, f"{results}")
        index_text.config(state=tk.DISABLED)
        index_text.pack(expand=1, fill=tk.BOTH)

# SPLASH SCREEN TO SHOW WHILE INITIALIZING MAIN APP
class SplashWindow:
    def __init__(self, r):
        self.root = r
        self.root.geometry("600x400")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = screen_width/2 - 300
        y = screen_height/2 - 200

        self.root.geometry("+%d+%d" % (x, y))
        self.root.overrideredirect(True)
        # MAIN FRAME
        self.main_frame = tk.Frame(self.root, background=PRIMARY_BLUE)
        self.main_frame.pack(expand=1, fill=tk.BOTH, side=tk.LEFT)
        image = Image.open("images/hector-logo.png")
        logo = ImageTk.PhotoImage(image.resize((300, 300), Image.ANTIALIAS))

        logo_holder = tk.Label(self.main_frame, image=logo, background=PRIMARY_BLUE)
        logo_holder.image = logo
        logo_holder.pack()
        self.status = tk.Label(self.main_frame, text="inicializujem...", background=PRIMARY_BLUE, font=(HELVETICA_FONT_NAME, 10), foreground="#ffffff")
        self.status.pack()
        ## required to make window show before the program gets to the mainloop
        self.root.update()
    def close(self):
        self.main_frame.destroy()
    def update_status(self, text):
        self.status.config(text=text)
        self.root.update()
initialized = False


root = ThemedTk(theme="clam")
root.title("Hector")
photo = tk.PhotoImage(file='images/hector-icon.png')
root.wm_iconphoto(False, photo)
splash = SplashWindow(root)
splash.update_status("sťahujem a inicializujem jazykový model...")
# INITIALIZE NLP ENGINE
stanza.download('sk')
splash.update_status("inicializujem textový processor...")
nlp = stanza.Pipeline('sk', processors='tokenize')
splash.close()
main_window = MainWindow(root, nlp)
main_window.start_main_loop()


# TODO LEVEL 0 (knowm bugs)

# TODO LEVEL A (must have for "production"):
# Redesign to have nice and intuitive UI - basic things should be done

# TODO LEVEL B (nice to have features): Consider adding:
# Heatmap?
# Commas analysis based on some NLP apporach?
# Left side panel with list of close words. On mouse over word, highlight words in editor
# Highlighting words selected in right panel
