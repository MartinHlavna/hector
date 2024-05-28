import random
import tkinter as tk
from tkinter import filedialog, messagebox
import textstat
import re
from collections import Counter
import json
import os

CONFIG_FILE = 'config.json'

default_config = {
    "min_word_length": 3,
    "min_word_frequency": 2,
    "long_sentence_length": 8,
    "long_sentence_char_count": 200,
    "long_sentence_min_word_length": 5,
    "enable_frequent_words": True,
    "enable_long_sentences": True,
    "enable_multiple_spaces": True,
    "enable_multiple_punctuation": True,
    "enable_trailing_spaces": True,
    "min_close_word_length": 3,
    "close_word_distance": 100,
    "close_word_frequency": 3,
    "enable_close_words": True
}

text_size = 10  # Default text size

def change_text_size(event):
    global text_size
    if event.state & 0x0004:  # Check if Ctrl is pressed
        if event.delta > 0 or event.num == 4:
            text_size += 1
        elif event.delta < 0 or event.num == 5:
            text_size -= 1
        text_editor.config(font=("Helvetica", text_size))
        for tag in text_editor.tag_names():
            if tag.startswith("close_word_"):
                text_editor.tag_configure(tagName=tag, font=("Helvetica", text_size + 2, "bold"))


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            config = json.load(file)
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    else:
        return default_config


def save_config(config):
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)


config = load_config()


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


def lexical_diversity(text):
    words = text.split()
    unique_words = set(words)
    return len(unique_words) / len(words)


def explain_indices():
    explanations = {
        "Flesch-Kincaid Reading Ease": "This index rates text on a 0 to 100 scale, where higher scores mean easier text. Higher values indicate easier readability.",
        "Flesch-Kincaid Grade Level": "This index estimates the grade level appropriate for the text. Lower numbers indicate easier text.",
        "Gunning Fog Index": "This index estimates the years of formal education needed to understand the text on the first reading. Lower values indicate easier readability.",
        "Automated Readability Index": "This index rates the readability of the text. Lower numbers indicate easier text.",
        "Coleman-Liau Index": "This index is based on the number of letters and sentences per 100 words. Lower values indicate easier text.",
        "SMOG Index": "This index estimates the years of formal education needed to understand text containing at least 30 sentences. Lower numbers indicate easier text.",
        "Lexikálna rôznorodosť (Type-Token Ratio)": "The ratio of unique words (types) to total words (tokens). Higher values indicate greater lexical diversity."
    }
    return explanations


def display_size_info(text):
    char_count = len(text)
    word_count = len(text.split())
    norm_pages = char_count / 1800
    size_info_label.config(
        text=f"Počet znakov s medzerami: {char_count}   Počet slov: {word_count}   Počet normostrán: {norm_pages:.2f}"
    )


def display_word_frequencies(text):
    if not config["enable_frequent_words"]:
        return
    words = re.findall(r'\w+', text.lower())
    words = [word for word in words if len(word) >= config["min_word_length"]]
    word_counts = Counter(words)
    sorted_word_counts = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)

    frequent_words_text = "\n".join(
        [f"{word}: {count}x" for word, count in sorted_word_counts if count >= config["min_word_frequency"]]
    )

    word_freq_text.config(state=tk.NORMAL)
    word_freq_text.delete(1.0, tk.END)
    word_freq_text.insert(tk.END, frequent_words_text)
    word_freq_text.config(state=tk.DISABLED)


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
        if len(words) > config["long_sentence_length"] or len(sentence) > config["long_sentence_char_count"]:
            start_index = f"1.0 + {highlight_start} chars"
            end_index = f"1.0 + {highlight_end} chars"
            text_editor.tag_add("long_sentence", start_index, end_index)
        start = end
    text_editor.tag_config("long_sentence", background="yellow")


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


original_colors = {}


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

            if len(word) >= config["min_close_word_length"]:
                if word not in word_positions:
                    word_positions[word] = []
                word_positions[word].append((start_pos, end_pos))
        for word, positions in word_positions.items():
            for i, (start_pos, end_pos) in enumerate(positions):
                if i == 0:
                    continue
                if start_pos - positions[i - 1][1] <= config["close_word_distance"]:
                    if word not in close_word_positions:
                        close_word_positions[word] = []
                    close_word_positions[word].append((positions[i - 1][0], positions[i - 1][1]))
                    close_word_positions[word].append((start_pos, end_pos))

        for word, positions in close_word_positions.items():
            if len(positions) >= config["close_word_frequency"]:
                color = random_dark_color()
                for i, (start_pos, end_pos) in enumerate(positions):
                    start_index = f"1.0 + {start_pos} chars"
                    end_index = f"1.0 + {end_pos} chars"
                    tag_name = f"close_word_{word}"
                    original_color = original_colors.get(tag_name, "")
                    if original_color != "":
                        color = original_color
                    else:
                        original_colors[tag_name] = color
                    text_editor.tag_add(tag_name, start_index, end_index)
                    text_editor.tag_config(tag_name, foreground=color, font=("Helvetica", text_size + 2, "bold"))
                    text_editor.tag_bind(tag_name, "<Enter>", lambda e, w=word: highlight_same_word(w))
                    text_editor.tag_bind(tag_name, "<Leave>", lambda e, w=word: unhighlight_same_word(w))


def highlight_same_word(word):
    for tag in text_editor.tag_names():
        if tag.startswith(f"close_word_{word}"):
            text_editor.tag_config(tag, background="black", foreground="white")


def unhighlight_same_word(word):
    for tag in text_editor.tag_names():
        if tag.startswith(f"close_word_{word}"):
            original_color = original_colors.get(tag, "")
            text_editor.tag_config(tag, background="", foreground=original_color)


def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Textové súbory", "*.txt")])
    if file_path:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            text_editor.delete(1.0, tk.END)
            text_editor.insert(tk.END, text)
            analyze_text()


def save_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Textové súbory", "*.txt")])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as file:
            text = text_editor.get(1.0, tk.END)
            file.write(text)


def analyze_text(event=None):
    text = text_editor.get(1.0, tk.END)
    for tag in text_editor.tag_names():
        text_editor.tag_delete(tag)
    display_word_frequencies(text)
    display_size_info(text)
    highlight_long_sentences(text)
    highlight_multiple_issues(text)
    highlight_close_words(text)


def select_all(event=None):
    text_editor.tag_add(tk.SEL, "1.0", tk.END)
    return "break"


def show_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Nastavenia")

    def save_settings():
        config["min_word_length"] = int(min_word_length_entry.get())
        config["min_word_frequency"] = int(min_word_frequency_entry.get())
        config["long_sentence_length"] = int(long_sentence_length_entry.get())
        config["long_sentence_char_count"] = int(long_sentence_char_count_entry.get())
        config["long_sentence_min_word_length"] = int(long_sentence_min_word_length_entry.get())
        config["enable_frequent_words"] = frequent_words_var.get()
        config["enable_long_sentences"] = long_sentences_var.get()
        config["enable_multiple_spaces"] = multiple_spaces_var.get()
        config["enable_multiple_punctuation"] = multiple_punctuation_var.get()
        config["enable_trailing_spaces"] = trailing_spaces_var.get()
        config["min_close_word_length"] = int(min_close_word_length_entry.get())
        config["close_word_distance"] = int(close_word_distance_entry.get())
        config["close_word_frequency"] = int(close_word_frequency_entry.get())
        config["enable_close_words"] = close_words_var.get()
        save_config(config)
        analyze_text()  # Reanalyze text after saving settings
        settings_window.destroy()

    # Frequent words settings
    tk.Label(settings_window, text="Časté slová", font=("Helvetica", 14, "bold"), anchor='w').grid(row=0, column=0,
                                                                                                   columnspan=2,
                                                                                                   padx=10,
                                                                                                   pady=(10, 2),
                                                                                                   sticky='w')
    tk.Label(settings_window, text="Minimálna dĺžka slova v znakoch", anchor='w').grid(row=1, column=0, padx=10, pady=2,
                                                                                       sticky='w')
    min_word_length_entry = tk.Entry(settings_window)
    min_word_length_entry.grid(row=1, column=1, padx=10, pady=2)
    min_word_length_entry.insert(0, str(config["min_word_length"]))

    tk.Label(settings_window, text="Minimálna početnosť slova", anchor='w').grid(row=2, column=0, padx=10, pady=2,
                                                                                 sticky='w')
    min_word_frequency_entry = tk.Entry(settings_window)
    min_word_frequency_entry.grid(row=2, column=1, padx=10, pady=2)
    min_word_frequency_entry.insert(0, str(config["min_word_frequency"]))

    frequent_words_var = tk.BooleanVar(value=config["enable_frequent_words"])
    frequent_words_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=frequent_words_var)
    frequent_words_checkbox.grid(row=3, column=1, padx=10, pady=2, sticky='w')

    # Spacer
    tk.Label(settings_window, text="", anchor='w').grid(row=4, column=0, padx=10, pady=5, sticky='w')

    # Long sentences settings
    tk.Label(settings_window, text="Dlhé vety", font=("Helvetica", 14, "bold"), anchor='w').grid(row=5, column=0,
                                                                                                 columnspan=2, padx=10,
                                                                                                 pady=(10, 2),
                                                                                                 sticky='w')
    tk.Label(settings_window, text="Zvýrazniť vety, ktoré majú väčší počet slov", anchor='w').grid(row=6, column=0,
                                                                                                   padx=10, pady=2,
                                                                                                   sticky='w')
    long_sentence_length_entry = tk.Entry(settings_window)
    long_sentence_length_entry.grid(row=6, column=1, padx=10, pady=2)
    long_sentence_length_entry.insert(0, str(config["long_sentence_length"]))

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
    tk.Label(settings_window, text="Viacnásobné medzery", font=("Helvetica", 14, "bold"), anchor='w').grid(row=11,
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
    tk.Label(settings_window, text="Viacnásobná interpunkcia", font=("Helvetica", 14, "bold"), anchor='w').grid(row=14,
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
    tk.Label(settings_window, text="Medzery na konci odstavca", font=("Helvetica", 14, "bold"), anchor='w').grid(row=17,
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
    tk.Label(settings_window, text="Slová blízko seba", font=("Helvetica", 14, "bold"), anchor='w').grid(row=20,
                                                                                                         column=0,
                                                                                                         columnspan=2,
                                                                                                         padx=10,
                                                                                                         pady=(10, 2),
                                                                                                         sticky='w')
    tk.Label(settings_window, text="Minimálna dlžka slova", anchor='w').grid(row=21, column=0, padx=10, pady=2,
                                                                             sticky='w')
    min_close_word_length_entry = tk.Entry(settings_window)
    min_close_word_length_entry.grid(row=21, column=1, padx=10, pady=2)
    min_close_word_length_entry.insert(0, str(config["min_close_word_length"]))

    tk.Label(settings_window, text="Povolená medzera medzi opakujúcimi sa slovami", anchor='w').grid(row=22, column=0,
                                                                                                     padx=10, pady=2,
                                                                                                     sticky='w')
    close_word_distance_entry = tk.Entry(settings_window)
    close_word_distance_entry.grid(row=22, column=1, padx=10, pady=2)
    close_word_distance_entry.insert(0, str(config["close_word_distance"]))

    tk.Label(settings_window, text="Minimálna početnosť opakujúceho sa slova", anchor='w').grid(row=23, column=0,
                                                                                                padx=10, pady=2, sticky='w')
    close_word_frequency_entry = tk.Entry(settings_window)
    close_word_frequency_entry.grid(row=23, column=1, padx=10, pady=2)
    close_word_frequency_entry.insert(0, str(config["close_word_frequency"]))

    close_words_var = tk.BooleanVar(value=config["enable_close_words"])
    close_words_checkbox = tk.Checkbutton(settings_window, text="Povolené", variable=close_words_var)
    close_words_checkbox.grid(row=24, column=1, padx=10, pady=2, sticky='w')

    tk.Button(settings_window, text="Uložiť", command=save_settings).grid(row=25, column=0, columnspan=2, pady=10)


def random_dark_color():
    dark_colors = [
        '#8B0000',  # Dark Red
        '#FF0000',  # Red
        '#8B008B',  # Dark Magenta
        '#FF4500',  # Orange Red
        '#CD5C5C',  # Indian Red
    ]
    return random.choice(dark_colors)


def show_about():
    messagebox.showinfo("O programe", "Hector - Analyzátor textu\nVerzia 1.0")


def show_index_explanations():
    indices = calculate_readability_indices(text_editor.get(1.0, tk.END))
    explanations = explain_indices()
    results = "\n".join([f"{index}: {value}" for index, value in indices.items()])
    explanations_text = "\n\n".join([f"{index}:\n{explanation}" for index, explanation in explanations.items()])
    index_window = tk.Toplevel(root)
    index_window.title("Indexy čitateľnosti")
    index_text = tk.Text(index_window, wrap=tk.WORD, font=("Arial", 10))
    index_text.insert(tk.END, f"{results}\n\n{explanations_text}")
    index_text.config(state=tk.DISABLED)
    index_text.pack(expand=1, fill=tk.BOTH)


# GUI settings
root = tk.Tk()
root.title("Hector")

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}")

main_frame = tk.Frame(root)
main_frame.pack(expand=1, fill=tk.BOTH, side=tk.LEFT)

text_editor = tk.Text(main_frame, wrap=tk.WORD)
text_editor.config(font=("Helvetica", text_size))
text_editor.pack(expand=1, fill=tk.BOTH)

text_editor.bind("<KeyRelease>", lambda event: root.after(1000, debouncer.released))
text_editor.bind("<Control-a>", select_all)
text_editor.bind("<Control-A>", select_all)
# MOUSE WHEEL
# Windows OS
root.bind("<MouseWheel>", change_text_size)
# Linux OS
root.bind("<Button-4>", change_text_size)
root.bind("<Button-5>", change_text_size)

side_panel = tk.Frame(root, width=200, relief=tk.SUNKEN, borderwidth=1)
side_panel.pack(fill=tk.BOTH, side=tk.RIGHT)

word_freq_title = tk.Label(side_panel, text="Časté slová", font=("Helvetica", 14, "bold"), anchor='n', justify='left')
word_freq_title.pack()

word_freq_scroll = tk.Scrollbar(side_panel)
word_freq_scroll.pack(side=tk.RIGHT, fill=tk.Y)

word_freq_text = tk.Text(side_panel, wrap=tk.WORD, state=tk.DISABLED, width=20, yscrollcommand=word_freq_scroll.set)
word_freq_text.pack(fill=tk.BOTH, expand=1, pady=10, padx=10)

word_freq_scroll.config(command=word_freq_text.yview)

bottom_panel = tk.Frame(main_frame)
bottom_panel.pack(fill=tk.BOTH, side=tk.BOTTOM)

size_info_label = tk.Label(bottom_panel, text="", anchor='sw', justify='left')
size_info_label.pack(side=tk.LEFT, padx=20, pady=20)

menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Načítať súbor", command=load_file)
file_menu.add_command(label="Uložiť súbor", command=save_file)
menu_bar.add_cascade(label="Súbor", menu=file_menu)

analyze_menu = tk.Menu(menu_bar, tearoff=0)
analyze_menu.add_command(label="Indexy čitateľnosti", command=show_index_explanations)
menu_bar.add_cascade(label="Analýza", menu=analyze_menu)

settings_menu = tk.Menu(menu_bar, tearoff=0)
settings_menu.add_command(label="Parametre analýzy", command=show_settings)
menu_bar.add_cascade(label="Nastavenia", menu=settings_menu)

help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="O programe", command=show_about)
menu_bar.add_cascade(label="Pomoc", menu=help_menu)

root.mainloop()
