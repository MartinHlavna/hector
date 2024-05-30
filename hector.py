import platform
import random
import tkinter as tk
from tkinter import filedialog, messagebox
import textstat
import re
from collections import Counter
import json
import os

# PREFIX FOR CLOSE WORD EDITOR TAGS
CLOSE_WORD_PREFIX = "close_word_"

# WE USE HELVETICA FONT
HELVETICA_FONT_NAME = "Helvetica"
BOLD_FONT = "bold"

# LOCATION OF CONFIG
CONFIG_FILE = 'config.json'

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

# DEFAULT TEXT SIZE IN EDITOR
text_size = 10

# DICTIONARY THAT HOLDS COLOR OF WORD TO PREVENT RECOLORING ON TYPING
close_word_colors = {}

# EXPLANATIONS OF DIFFERENT READABILITY INDICES
# TODO: Translate to SK
READABILITY_INDICES_EXPLANATIONS = {
    "Flesch-Kincaid Reading Ease": "This index rates text on a 0 to 100 scale, where higher scores mean easier text. Higher values indicate easier readability.",
    "Flesch-Kincaid Grade Level": "This index estimates the grade level appropriate for the text. Lower numbers indicate easier text.",
    "Gunning Fog Index": "This index estimates the years of formal education needed to understand the text on the first reading. Lower values indicate easier readability.",
    "Automated Readability Index": "This index rates the readability of the text. Lower numbers indicate easier text.",
    "Coleman-Liau Index": "This index is based on the number of letters and sentences per 100 words. Lower values indicate easier text.",
    "SMOG Index": "This index estimates the years of formal education needed to understand text containing at least 30 sentences. Lower numbers indicate easier text.",
    "Lexikálna rôznorodosť (Type-Token Ratio)": "The ratio of unique words (types) to total words (tokens). Higher values indicate greater lexical diversity."
}

# DEFINITION OF FUNCTIONS
# CHANGE TEXT SIZE WHEN USER SCROLL MOUSEWHEEL WITH CTRL PRESSED
# TODO: MAYBE ADD ANOTHER WAY OF CHANGING TEXT SIZE
def change_text_size(event):
    global text_size
    # CHECK IF CTRL IS PRESSED
    if event.state & 0x0004:
        # ON WINDOWS IF USER SCROLLS "UP" event.delta IS POSITIVE
        # ON LINUX IF USER SCROLLS "UP" event.num IS 4
        # TODO What about mac os?
        if event.delta > 0 or event.num == 4:
            text_size += 1
        # ON WINDOWS IF USER SCROLLS "DOWN" event.delta IS NEGATIVE
        # ON LINUX IF USER SCROLLS "DOWN" event.num IS 5
        # TODO What about mac os?
        elif event.delta < 0 or event.num == 5:
            text_size -= 1

        # CHANGE FONT SIZE IN EDITOR
        text_editor.config(font=(HELVETICA_FONT_NAME, text_size))
        # CLOSE WORDS ARE ALWAYS HIGHLIGHTED WITH BIGGER FONT. WE NEED TO UPDATE TAGS
        for tag in text_editor.tag_names():
            if tag.startswith(CLOSE_WORD_PREFIX):
                text_editor.tag_configure(tagName=tag, font=(HELVETICA_FONT_NAME, text_size + 2, BOLD_FONT))


# FUNCTION THAT LOADS CONFIG FROM FILE
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
def save_config(c):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(c, file, indent=4)


# FUNCTION THAT CALCULATE READABILITY INDICES
def calculate_readability_indices(text):
    indices = {
        "Flesch-Kincaid Reading Ease": textstat.flesch_reading_ease(text),
        "Flesch-Kincaid Grade Level": textstat.flesch_kincaid_grade(text),
        "Gunning Fog Index": textstat.gunning_fog(text),
        "Automated Readability Index": textstat.automated_readability_index(text),
        "Coleman-Liau Index": textstat.coleman_liau_index(text),
        "SMOG Index": textstat.smog_index(text),
        "Lexikálna rôznorodosť (Type-Token Ratio)": lexical_diversity(text)
    }
    return indices


# CALCULATE LEXICAL DIVERSITY (RATIO OF UNIQUE WORDS TO ALL WORDS)
def lexical_diversity(text):
    words = text.split()
    unique_words = set(words)
    return len(unique_words) / len(words)


# DISPLAY INFORMATIONS ABOUT TEXT SIZE
# TODO: Split every size into its own Text element with label
def display_size_info(text):
    char_count = len(text)
    word_count = len(text.split())
    norm_pages = char_count / 1800
    size_info_label.config(
        text=f"Počet znakov s medzerami: {char_count}   Počet slov: {word_count}   Počet normostrán: {norm_pages:.2f}"
    )


# CALCULATE AND DISPLAY FREQUENT WORDS
def display_word_frequencies(text):
    if not config["enable_frequent_words"]:
        return
    words = re.findall(r'\w+', text.lower())
    words = [word for word in words if len(word) >= config["repeated_words_min_word_length"]]
    word_counts = Counter(words)
    sorted_word_counts = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    # TODO
    # In tk, there is problem with scrolling so we default to using on big text to dispaly frequencies
    # ugly but it works for now
    frequent_words_text = "\n".join(
        [f"{word}: {count}x" for word, count in sorted_word_counts if count >= config["repeated_words_min_word_frequency"]]
    )

    # WE NEED TO ENBLE TEXT, DELETE CONTENT AND INSERT NEW TEXT
    word_freq_text.config(state=tk.NORMAL)
    word_freq_text.delete(1.0, tk.END)
    word_freq_text.insert(tk.END, frequent_words_text)
    # DISABLING AGAIN
    word_freq_text.config(state=tk.DISABLED)


# HIGHLIGHT LONG SENTENCES
# TODO: Optimize highlighting methods so we parse text only once
def highlight_long_sentences(text):
    text_editor.tag_remove("long_sentence", "1.0", tk.END)
    if not config["enable_long_sentences"]:
        return
    sentences = re.split(r'([.!?:]+)', text)
    start = 0
    quote_at_start_pattern = re.compile(r'["“”‘’„”«»‹›‟]\s*\S')
    for sentence in sentences:
        if re.match(r'([.!?:]+)', sentence):
            start = start + len(sentence)
            continue
        end = start + len(sentence)
        highlight_start = start
        highlight_end = end
        if quote_at_start_pattern.match(sentence):
            old_len = len(sentence)
            sentence = re.sub(quote_at_start_pattern, '', sentence)
            highlight_start += old_len - len(sentence) - 1
        if sentence.startswith(' '):
            old_len = len(sentence)
            sentence = sentence.strip()
            highlight_start += old_len - len(sentence)
        if sentence.startswith('\n'):
            old_len = len(sentence)
            sentence = sentence.replace('\n', '')
            highlight_start += old_len - len(sentence)
        words = [word for word in sentence.split() if
                 len(re.sub(r'[.!?]+', '', word)) >= config["long_sentence_min_word_length"]]
        if len(words) > config["long_sentence_words"] or len(sentence) > config["long_sentence_char_count"]:
            start_index = f"1.0 + {highlight_start} chars"
            end_index = f"1.0 + {highlight_end} chars"
            text_editor.tag_add("long_sentence", start_index, end_index)
        start = end
    text_editor.tag_config("long_sentence", background="yellow")


# HIGHLIGH MULTIPLE SPACE, MULTIPLE PUNCTATION, AND TRAILING SPACES
def highlight_multiple_issues(text):
    text_editor.tag_remove("multiple_issues", "1.0", tk.END)
    if config["enable_multiple_spaces"]:
        matches = re.finditer(r' {2,}', text)
        for match in matches:
            start_index = f"1.0 + {match.start()} chars"
            end_index = f"1.0 + {match.end()} chars"
            text_editor.tag_add("multiple_issues", start_index, end_index)
    if config["enable_multiple_punctuation"]:
        matches = re.finditer(r'([!?.,:;]){2,}', text)
        for match in matches:
            if match.group() not in ["?!"]:
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                text_editor.tag_add("multiple_issues", start_index, end_index)
    if config["enable_trailing_spaces"]:
        matches = re.finditer(r' +$', text, re.MULTILINE)
        for match in matches:
            start_index = f"1.0 + {match.start()} chars"
            end_index = f"1.0 + {match.end()} chars"
            text_editor.tag_add("multiple_issues", start_index, end_index)
    text_editor.tag_config("multiple_issues", background="red")


# RANDOMLY PICK COLOR FOR WORD
def get_color_for_close_words():
    # TODO: CREATE PALLETE FOR SUITABLE COLORS
    dark_colors = [
        '#8B0000',  # Dark Red
        '#FF0000',  # Red
        '#8B008B',  # Dark Magenta
        '#FF4500',  # Orange Red
        '#CD5C5C',  # Indian Red
    ]
    return random.choice(dark_colors)


# HIGHLIGHT WORDS THAT REPEATS CLOSE TO EACH OTHER
# TODO: Maybe we could provide list of "CLOSE WORDS" IN RIGHT PANEL AND HIGHLIGHT ON MOUSE OVER
def highlight_close_words(text):
    global text_size
    if config["enable_close_words"]:
        text_editor.tag_remove("close_word", "1.0", tk.END)
        words = re.findall(r'\w+', text.lower())
        word_positions = {}
        close_word_positions = {}

        for match in re.finditer(r'\w+', text):
            word = match.group().lower()
            start_pos = match.start()
            end_pos = match.end()

            if len(word) >= config["close_words_min_word_length"]:
                if word not in word_positions:
                    word_positions[word] = []
                word_positions[word].append((start_pos, end_pos))
        for word, positions in word_positions.items():
            for i, (start_pos, end_pos) in enumerate(positions):
                if i == 0:
                    continue
                if start_pos - positions[i - 1][1] <= config["close_words_min_distance_between_words"]:
                    if word not in close_word_positions:
                        close_word_positions[word] = []
                    close_word_positions[word].append((positions[i - 1][0], positions[i - 1][1]))
                    close_word_positions[word].append((start_pos, end_pos))

        for word, positions in close_word_positions.items():
            if len(positions) >= config["close_words_min_frequency"]:
                color = get_color_for_close_words()
                for i, (start_pos, end_pos) in enumerate(positions):
                    start_index = f"1.0 + {start_pos} chars"
                    end_index = f"1.0 + {end_pos} chars"
                    tag_name = f"{CLOSE_WORD_PREFIX}{word}"
                    original_color = close_word_colors.get(tag_name, "")
                    if original_color != "":
                        color = original_color
                    else:
                        close_word_colors[tag_name] = color
                    text_editor.tag_add(tag_name, start_index, end_index)
                    text_editor.tag_config(tag_name, foreground=color, font=(HELVETICA_FONT_NAME, text_size + 2, BOLD_FONT))
                    # ON MOUSE OVER, HIGHLIGHT SAME WORDS
                    text_editor.tag_bind(tag_name, "<Enter>", lambda e, w=word: highlight_same_word(w))
                    text_editor.tag_bind(tag_name, "<Leave>", lambda e, w=word: unhighlight_same_word(w))


# HIGHLIGHT SAME WORD ON MOUSE OVER
def highlight_same_word(word):
    for tag in text_editor.tag_names():
        if tag.startswith(f"{CLOSE_WORD_PREFIX}{word}"):
            text_editor.tag_config(tag, background="black", foreground="white")


# REMOVE HIGHLIGHTING FROM SAME WORD ON MOUSE OVER END
def unhighlight_same_word(word):
    for tag in text_editor.tag_names():
        if tag.startswith(f"{CLOSE_WORD_PREFIX}{word}"):
            original_color = close_word_colors.get(tag, "")
            text_editor.tag_config(tag, background="", foreground=original_color)


# LOAD TEXT FILE
# TODO: Maybe we could extract text from MS WORD?
def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Textové súbory", "*.txt")])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            text_editor.delete(1.0, tk.END)
            text_editor.insert(tk.END, text)
            analyze_text()


# SAVE TEXT FILE
def save_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Textové súbory", "*.txt")])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as file:
            text = text_editor.get(1.0, tk.END)
            file.write(text)


# ANALYZE TEXT
def analyze_text(event=None):
    text = text_editor.get(1.0, tk.END)
    for tag in text_editor.tag_names():
        text_editor.tag_delete(tag)
    display_word_frequencies(text)
    display_size_info(text)
    highlight_long_sentences(text)
    highlight_multiple_issues(text)
    highlight_close_words(text)


# SELECT ALL TEXT
# TODO: SELECT WORD ON DOUBLE CLICK
def select_all(event=None):
    text_editor.tag_add(tk.SEL, "1.0", tk.END)
    return "break"


# SHOW SETTINGS WINDOW
def show_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Nastavenia")

    # SAVE SETTINGS
    # TODO: Maybe we could extract this?
    def save_settings():
        config["repeated_words_min_word_length"] = int(repeated_words_min_word_length_entry.get())
        config["repeated_words_min_word_frequency"] = int(repeated_words_min_word_frequency_entry.get())
        config["long_sentence_words"] = int(long_sentence_words_entry.get())
        config["long_sentence_char_count"] = int(long_sentence_char_count_entry.get())
        config["long_sentence_min_word_length"] = int(long_sentence_min_word_length_entry.get())
        config["enable_frequent_words"] = frequent_words_var.get()
        config["enable_long_sentences"] = long_sentences_var.get()
        config["enable_multiple_spaces"] = multiple_spaces_var.get()
        config["enable_multiple_punctuation"] = multiple_punctuation_var.get()
        config["enable_trailing_spaces"] = trailing_spaces_var.get()
        config["close_words_min_word_length"] = int(close_words_min_word_length_entry.get())
        config["close_words_min_distance_between_words"] = int(close_words_min_distance_between_words_entry.get())
        config["close_words_min_frequency"] = int(close_words_min_frequency_entry.get())
        config["enable_close_words"] = close_words_var.get()
        save_config(config)
        analyze_text()  # Reanalyze text after saving settings
        settings_window.destroy()

    # TODO: WE NEED TO DESIGN THIS A BIT
    # Frequent words settings
    tk.Label(settings_window, text="Časté slová", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(row=0, column=0,
                                                                                                   columnspan=2,
                                                                                                   padx=10,
                                                                                                   pady=(10, 2),
                                                                                                   sticky='w')
    tk.Label(settings_window, text="Minimálna dĺžka slova v znakoch", anchor='w').grid(row=1, column=0, padx=10, pady=2,
                                                                                       sticky='w')
    repeated_words_min_word_length_entry = tk.Entry(settings_window)
    repeated_words_min_word_length_entry.grid(row=1, column=1, padx=10, pady=2)
    repeated_words_min_word_length_entry.insert(0, str(config["repeated_words_min_word_length"]))

    tk.Label(settings_window, text="Minimálna početnosť slova", anchor='w').grid(row=2, column=0, padx=10, pady=2,
                                                                                 sticky='w')
    repeated_words_min_word_frequency_entry = tk.Entry(settings_window)
    repeated_words_min_word_frequency_entry.grid(row=2, column=1, padx=10, pady=2)
    repeated_words_min_word_frequency_entry.insert(0, str(config["repeated_words_min_word_frequency"]))

    frequent_words_var = tk.BooleanVar(value=config["enable_frequent_words"])
    frequent_words_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=frequent_words_var)
    frequent_words_checkbox.grid(row=3, column=1, padx=10, pady=2, sticky='w')

    # Spacer
    tk.Label(settings_window, text="", anchor='w').grid(row=4, column=0, padx=10, pady=5, sticky='w')

    # Long sentences settings
    tk.Label(settings_window, text="Dlhé vety", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(row=5, column=0,
                                                                                                 columnspan=2, padx=10,
                                                                                                 pady=(10, 2),
                                                                                                 sticky='w')
    tk.Label(settings_window, text="Zvýrazniť vety, ktoré majú väčší počet slov", anchor='w').grid(row=6, column=0,
                                                                                                   padx=10, pady=2,
                                                                                                   sticky='w')
    long_sentence_words_entry = tk.Entry(settings_window)
    long_sentence_words_entry.grid(row=6, column=1, padx=10, pady=2)
    long_sentence_words_entry.insert(0, str(config["long_sentence_words"]))

    tk.Label(settings_window, text="Zvýrazniť vety, ktoré majú viac znakov", anchor='w').grid(row=7, column=0, padx=10,
                                                                                              pady=2, sticky='w')
    long_sentence_char_count_entry = tk.Entry(settings_window)
    long_sentence_char_count_entry.grid(row=7, column=1, padx=10, pady=2)
    long_sentence_char_count_entry.insert(0, str(config["long_sentence_char_count"]))

    tk.Label(settings_window, text="Nepočítať slová kratšie ako", anchor='w').grid(row=8, column=0, padx=10, pady=2,
                                                                                   sticky='w')
    long_sentence_min_word_length_entry = tk.Entry(settings_window)
    long_sentence_min_word_length_entry.grid(row=8, column=1, padx=10, pady=2)
    long_sentence_min_word_length_entry.insert(0, str(config["long_sentence_min_word_length"]))

    long_sentences_var = tk.BooleanVar(value=config["enable_long_sentences"])
    long_sentences_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=long_sentences_var)
    long_sentences_checkbox.grid(row=9, column=1, padx=10, pady=2, sticky='w')

    # Spacer
    tk.Label(settings_window, text="", anchor='w').grid(row=10, column=0, padx=10, pady=5, sticky='w')

    # Multiple spaces settings
    tk.Label(settings_window, text="Viacnásobné medzery", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(row=11,
                                                                                                           column=0,
                                                                                                           columnspan=2,
                                                                                                           padx=10,
                                                                                                           pady=(10, 2),
                                                                                                           sticky='w')
    multiple_spaces_var = tk.BooleanVar(value=config["enable_multiple_spaces"])
    multiple_spaces_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=multiple_spaces_var)
    multiple_spaces_checkbox.grid(row=12, column=1, padx=10, pady=2, sticky='w')

    # Spacer
    tk.Label(settings_window, text="", anchor='w').grid(row=13, column=0, padx=10, pady=5, sticky='w')

    # Multiple punctuation settings
    tk.Label(settings_window, text="Viacnásobná interpunkcia", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(row=14,
                                                                                                                column=0,
                                                                                                                columnspan=2,
                                                                                                                padx=10,
                                                                                                                pady=(
                                                                                                                    10, 2),
                                                                                                                sticky='w')
    multiple_punctuation_var = tk.BooleanVar(value=config["enable_multiple_punctuation"])
    multiple_punctuation_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=multiple_punctuation_var)
    multiple_punctuation_checkbox.grid(row=15, column=1, padx=10, pady=2, sticky='w')

    # Spacer
    tk.Label(settings_window, text="", anchor='w').grid(row=16, column=0, padx=10, pady=5, sticky='w')

    # Trailing spaces settings
    tk.Label(settings_window, text="Medzery na konci odstavca", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(row=17,
                                                                                                                 column=0,
                                                                                                                 columnspan=2,
                                                                                                                 padx=10,
                                                                                                                 pady=(
                                                                                                                     10, 2),
                                                                                                                 sticky='w')
    trailing_spaces_var = tk.BooleanVar(value=config["enable_trailing_spaces"])
    trailing_spaces_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=trailing_spaces_var)
    trailing_spaces_checkbox.grid(row=18, column=1, padx=10, pady=2, sticky='w')

    # Close words settings
    tk.Label(settings_window, text="Slová blízko seba", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='w').grid(row=20,
                                                                                                         column=0,
                                                                                                         columnspan=2,
                                                                                                         padx=10,
                                                                                                         pady=(10, 2),
                                                                                                         sticky='w')
    tk.Label(settings_window, text="Minimálna dlžka slova", anchor='w').grid(row=21, column=0, padx=10, pady=2,
                                                                             sticky='w')
    close_words_min_word_length_entry = tk.Entry(settings_window)
    close_words_min_word_length_entry.grid(row=21, column=1, padx=10, pady=2)
    close_words_min_word_length_entry.insert(0, str(config["close_words_min_word_length"]))

    tk.Label(settings_window, text="Povolená medzera medzi opakujúcimi sa slovami", anchor='w').grid(row=22, column=0,
                                                                                                     padx=10, pady=2,
                                                                                                     sticky='w')
    close_words_min_distance_between_words_entry = tk.Entry(settings_window)
    close_words_min_distance_between_words_entry.grid(row=22, column=1, padx=10, pady=2)
    close_words_min_distance_between_words_entry.insert(0, str(config["close_words_min_distance_between_words"]))

    tk.Label(settings_window, text="Minimálna početnosť opakujúceho sa slova", anchor='w').grid(row=23, column=0,
                                                                                                padx=10, pady=2, sticky='w')
    close_words_min_frequency_entry = tk.Entry(settings_window)
    close_words_min_frequency_entry.grid(row=23, column=1, padx=10, pady=2)
    close_words_min_frequency_entry.insert(0, str(config["close_words_min_frequency"]))

    close_words_var = tk.BooleanVar(value=config["enable_close_words"])
    close_words_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=close_words_var)
    close_words_checkbox.grid(row=24, column=1, padx=10, pady=2, sticky='w')

    tk.Button(settings_window, text="Uložiť", command=save_settings).grid(row=25, column=0, columnspan=2, pady=10)


# SHOW ABOUT DIALOG
# TODO: ADD BASIC INFO
# TODO: Maybe add documentation
def show_about():
    messagebox.showinfo("O programe", "Hector - Analyzátor textu\nVerzia 1.0")


# CALCULATE AND SHOW VARIOUS READABILITY INDECES WITH EXPLANATIONS
def show_readability_indices():
    indices = calculate_readability_indices(text_editor.get(1.0, tk.END))
    results = "\n".join([f"{index}: {value}" for index, value in indices.items()])
    explanations_text = "\n\n".join([f"{index}:\n{explanation}" for index, explanation in READABILITY_INDICES_EXPLANATIONS.items()])
    index_window = tk.Toplevel(root)
    index_window.title("Indexy čitateľnosti")
    index_text = tk.Text(index_window, wrap=tk.WORD, font=("Arial", 10))
    index_text.insert(tk.END, f"{results}\n\n{explanations_text}")
    index_text.config(state=tk.DISABLED)
    index_text.pack(expand=1, fill=tk.BOTH)


# MAIN PROGRAM RUN
# LOAD CONFIG
config = load_config()

# MAIN GUI WINDOW
root = tk.Tk()
root.title("Hector")
# TODO: ACreate simple logo and add icon

# OPEN WINDOW IN MAXIMIZED STATE
# FOR WINDOWS SET STATE ZOOMED
# FOR LINUX SET ATTRIBUTE ZOOMED
# TODO: MacOs?
if platform.system() == "Windows":
    root.state("zoomed")
else:
    root.attributes('-zoomed', True)

# MAIN FRAME
main_frame = tk.Frame(root)
main_frame.pack(expand=1, fill=tk.BOTH, side=tk.LEFT)

# TEXT EDITOR WINDOW
# TODO: Maybe add visible scrollbar for text editor window
# TODO Maybe add logo as background if editor is empty
text_editor = tk.Text(main_frame, wrap=tk.WORD)
text_editor.config(font=(HELVETICA_FONT_NAME, text_size))
text_editor.pack(expand=1, fill=tk.BOTH)

# MOUSE AND KEYBOARD BINDINGS FOR TEXT EDITOR
text_editor.bind("<KeyRelease>", lambda event: root.after(1000, analyze_text))
text_editor.bind("<Control-a>", select_all)
text_editor.bind("<Control-A>", select_all)
# MOUSE WHEEL BINDING ON ROOT WINDOW
# Windows OS
root.bind("<MouseWheel>", change_text_size)
# Linux OS
root.bind("<Button-4>", change_text_size)
root.bind("<Button-5>", change_text_size)

# RIGHT SCROLLABLE SIDE PANEL WITH FREQUENT WORDS
side_panel = tk.Frame(root, width=200, relief=tk.SUNKEN, borderwidth=1)
side_panel.pack(fill=tk.BOTH, side=tk.RIGHT)

word_freq_title = tk.Label(side_panel, text="Časté slová", font=(HELVETICA_FONT_NAME, 14, BOLD_FONT), anchor='n', justify='left')
word_freq_title.pack()

word_freq_scroll = tk.Scrollbar(side_panel)
word_freq_scroll.pack(side=tk.RIGHT, fill=tk.Y)

word_freq_text = tk.Text(side_panel, wrap=tk.WORD, state=tk.DISABLED, width=20, yscrollcommand=word_freq_scroll.set)
word_freq_text.pack(fill=tk.BOTH, expand=1, pady=10, padx=10)

word_freq_scroll.config(command=word_freq_text.yview)

# BOTTOM PANEL WITH TEXT SIZE
# TODO: Add text size input to change editor text size without mouse
bottom_panel = tk.Frame(main_frame)
bottom_panel.pack(fill=tk.BOTH, side=tk.BOTTOM)

# TODO: We should add different elements for evey information. For now we are just appending text
size_info_label = tk.Label(bottom_panel, text="", anchor='sw', justify='left')
size_info_label.pack(side=tk.LEFT, padx=20, pady=20)

# TOP MENU
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# FILE MENU
# TODO: Maybe add a way to import MS word or other document type
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Načítať súbor", command=load_file)
file_menu.add_command(label="Uložiť súbor", command=save_file)
menu_bar.add_cascade(label="Súbor", menu=file_menu)

# ANALYZE MENU
# TODO: We need to think of more things we can analyze... because everything can be and should be analyzed xD
analyze_menu = tk.Menu(menu_bar, tearoff=0)
analyze_menu.add_command(label="Indexy čitateľnosti", command=show_readability_indices)
menu_bar.add_cascade(label="Analýza", menu=analyze_menu)

# SETTINGS MENU
settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_command(label="Parametre analýzy", command=show_settings)
menu_bar.add_cascade(label="Nastavenia", menu=settings_menu)

# HELP MENU
# TODO: Add link to documentation
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="O programe", command=show_about)
menu_bar.add_cascade(label="Pomoc", menu=help_menu)

# START MAIN LOOP TO SHOW ROOT WINDOW
root.mainloop()

# TODO LEVEL 0 (knowm bugs)
# Long sentences: Sometimes start of sentence is not highlighted. Need to debug

# TODO LEVEL A (must have for "production"):
# Redesign to have nice and intuitive UI
# Optimize text processing algo. Currently we pass text for every functionality. On longer text,
#   or after adding more functionality, this can be litlle clunky
# Debounce change events in editor. We should reanalyze text only when user stops typing

# TODO LEVEL B (nice to have features): Consider adding:
# Heatmap?
# Commas analysis based on some NLP apporach? Maybe SlovakBert model could help
# Left side panel with list of close words. On mouse over word, highlight words in editor
# Highlighting words selected in right panel
