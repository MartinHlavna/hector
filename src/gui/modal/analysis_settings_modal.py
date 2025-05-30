import platform
import tkinter as tk
from tkinter import ttk, messagebox

from src.backend.run_context import RunContext
from src.backend.service.config_service import ConfigService
from src.backend.service.project_service import ProjectService
from src.const.colors import PANEL_TEXT_COLOR, PRIMARY_COLOR, TEXT_EDITOR_FRAME_BG
from src.const.fonts import HELVETICA_FONT_NAME, BOLD_FONT
from src.const.paths import CONFIG_FILE_PATH
from src.domain.config import AnalysisSettings, ConfigLevel
from src.domain.project import ProjectItem
from src.gui.widgets.hector_button import HectorButton


class AnalysisSettingsModal:
    def __init__(self, root, config, on_config_change, config_level: ConfigLevel, item: ProjectItem):
        self.root = root
        self.config = config
        self.on_config_change = on_config_change
        self.toplevel = tk.Toplevel(self.root, background=TEXT_EDITOR_FRAME_BG)
        self.level = config_level
        self.item = item
        if config_level == ConfigLevel.GLOBAL:
            self.toplevel.title("Globálne nastavenia analýzy")
        elif config_level == ConfigLevel.PROJECT:
            self.toplevel.title("Projektové nastavenia analýzy")
        elif config_level == ConfigLevel.ITEM:
            self.toplevel.title("Nastavenia analýzy - pre súbor")
        row = 0
        # Frequent words settings
        tk.Label(self.toplevel, text="Často použité slová", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR ).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        self.frequent_words_var = tk.BooleanVar(value=self.config.analysis_settings.enable_frequent_words)
        frequent_words_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté", variable=self.frequent_words_var, style='hector.TCheckbutton', cursor="hand2")
        frequent_words_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(self.toplevel, text="Porovnávať základný tvar slova", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.frequent_words_use_lemma_var = tk.BooleanVar(value=self.config.analysis_settings.repeated_words_use_lemma)
        frequent_words_use_lemma_var_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté",
                                                                variable=self.frequent_words_use_lemma_var, style='hector.TCheckbutton', cursor="hand2")
        frequent_words_use_lemma_var_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(self.toplevel, text="Minimálna dĺžka slova", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.repeated_words_min_word_length_entry = ttk.Spinbox(self.toplevel, from_=1, to=100, width=6, justify=tk.LEFT, style='hector.TSpinbox')
        self.repeated_words_min_word_length_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.repeated_words_min_word_length_entry.set(self.config.analysis_settings.repeated_words_min_word_length)
        tk.Label(self.toplevel, text="znakov", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(self.toplevel, text="Minimálny počet opakovaní", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.repeated_words_min_word_frequency_entry = ttk.Spinbox(self.toplevel, from_=1, to=100, width=6, style='hector.TSpinbox')
        self.repeated_words_min_word_frequency_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.repeated_words_min_word_frequency_entry.set(self.config.analysis_settings.repeated_words_min_word_frequency)

        # Long sentences settings
        row += 1
        tk.Label(self.toplevel, text="Zvýrazňovanie dlhých viet", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        self.long_sentences_var = tk.BooleanVar(value=self.config.analysis_settings.enable_long_sentences)
        long_sentences_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté", variable=self.long_sentences_var, style='hector.TCheckbutton', cursor="hand2")
        long_sentences_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(self.toplevel, text="Veta je stredne dlhá, ak obsahuje aspoň", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.long_sentence_words_mid_entry = ttk.Spinbox(self.toplevel, from_=1, to=100, width=6, style='hector.TSpinbox')
        self.long_sentence_words_mid_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.long_sentence_words_mid_entry.set(self.config.analysis_settings.long_sentence_words_mid)
        tk.Label(self.toplevel, text="slov", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(self.toplevel, text="Veta je veľmi dlhá, ak obsahuje aspoň", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.long_sentence_words_high_entry = ttk.Spinbox(self.toplevel, from_=1, to=9999, width=6, style='hector.TSpinbox')
        self.long_sentence_words_high_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.long_sentence_words_high_entry.set(self.config.analysis_settings.long_sentence_words_high)
        tk.Label(self.toplevel, text="slov", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(self.toplevel, text="Nepočítať slová kratšie ako", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.long_sentence_min_word_length_entry = ttk.Spinbox(self.toplevel, from_=1, to=100, width=6, style='hector.TSpinbox')
        self.long_sentence_min_word_length_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.long_sentence_min_word_length_entry.set(self.config.analysis_settings.long_sentence_min_word_length)
        tk.Label(self.toplevel, text="znakov", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        # Multiple spaces settings
        row += 1
        tk.Label(self.toplevel, text="Zvýrazňovanie viacnásobných medzier ",
                 font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        self.multiple_spaces_var = tk.BooleanVar(value=self.config.analysis_settings.enable_multiple_spaces)
        multiple_spaces_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté", variable=self.multiple_spaces_var, style='hector.TCheckbutton', cursor="hand2")
        multiple_spaces_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # Multiple punctuation settings
        row += 1
        tk.Label(self.toplevel, text="Zvýrazňovanie viacnásobnej interpunkcie",
                 font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        self.multiple_punctuation_var = tk.BooleanVar(value=self.config.analysis_settings.enable_multiple_punctuation)
        multiple_punctuation_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté",
                                                        variable=self.multiple_punctuation_var, style='hector.TCheckbutton', cursor="hand2")
        multiple_punctuation_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # Trailing spaces settings
        row += 1
        tk.Label(self.toplevel, text="Zvýrazňovanie medzier na konci odstavca",
                 font=(HELVETICA_FONT_NAME, 12, BOLD_FONT), anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        self.trailing_spaces_var = tk.BooleanVar(value=self.config.analysis_settings.enable_trailing_spaces)
        trailing_spaces_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté", variable=self.trailing_spaces_var, style='hector.TCheckbutton', cursor="hand2")
        trailing_spaces_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # Close words settings
        row += 1
        tk.Label(self.toplevel, text="Často sa opakujúce slová", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        self.close_words_var = tk.BooleanVar(value=self.config.analysis_settings.enable_close_words)
        close_words_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté", variable=self.close_words_var, style='hector.TCheckbutton', cursor="hand2")
        close_words_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(self.toplevel, text="Porovnávať základný tvar slova", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.close_words_use_lemma_var = tk.BooleanVar(value=self.config.analysis_settings.close_words_use_lemma)
        close_words_use_lemma_var_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté",
                                                             variable=self.close_words_use_lemma_var, style='hector.TCheckbutton', cursor="hand2")
        close_words_use_lemma_var_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        row += 1
        tk.Label(self.toplevel, text="Minimálna dĺžka slova", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.close_words_min_word_length_entry = ttk.Spinbox(self.toplevel, from_=1, to=100, width=6, style='hector.TSpinbox')
        self.close_words_min_word_length_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.close_words_min_word_length_entry.insert(0, str(self.config.analysis_settings.close_words_min_word_length))
        tk.Label(self.toplevel, text="znakov", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(self.toplevel, text="Minimálna vzdialenosť slov", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.close_words_min_distance_between_words_entry = ttk.Spinbox(self.toplevel, from_=1, to=9999, width=6, style='hector.TSpinbox')
        self.close_words_min_distance_between_words_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.close_words_min_distance_between_words_entry.set(
            self.config.analysis_settings.close_words_min_distance_between_words)
        tk.Label(self.toplevel, text="slov", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=2, padx=10, pady=2, sticky='w'
        )

        row += 1
        tk.Label(self.toplevel, text="Minimálny počet opakovaní", anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, padx=10, pady=2, sticky='w'
        )
        self.close_words_min_frequency_entry = ttk.Spinbox(self.toplevel, from_=1, to=100, width=6, style='hector.TSpinbox')
        self.close_words_min_frequency_entry.grid(row=row, column=1, padx=10, pady=2, sticky='w')
        self.close_words_min_frequency_entry.set(self.config.analysis_settings.close_words_min_frequency)

        # Spellcheck
        row += 1
        tk.Label(self.toplevel, text="Kontrola gramatiky", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        self.spellcheck_var = tk.BooleanVar(value=self.config.analysis_settings.enable_spellcheck)
        spellcheck_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté", variable=self.spellcheck_var, style='hector.TCheckbutton', cursor="hand2")
        spellcheck_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # Spellcheck
        row += 1
        tk.Label(self.toplevel, text="Kontrola správnych úvodzoviek", font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        self.quote_corrections_var = tk.BooleanVar(value=self.config.analysis_settings.enable_quote_corrections)
        quote_corrections_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté", variable=self.quote_corrections_var, style='hector.TCheckbutton', cursor="hand2")
        quote_corrections_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # PARTIAL NLP
        row += 1
        tk.Label(self.toplevel, text="Optimalizácia výkonu pri drobných zmenách textu",
                 font=(HELVETICA_FONT_NAME, 12, BOLD_FONT),
                 anchor='w', background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR).grid(
            row=row, column=0, columnspan=1, padx=(10, 80), pady=(10, 2), sticky='w'
        )
        self.partial_nlp_var = tk.BooleanVar(value=self.config.analysis_settings.enable_partial_nlp)
        partial_nlp_checkbox = ttk.Checkbutton(self.toplevel, text="Zapnuté", variable=self.partial_nlp_var, style='hector.TCheckbutton', cursor="hand2")
        partial_nlp_checkbox.grid(row=row, column=1, padx=(6, 10), pady=2, sticky='w')

        # SAVE BUTTON
        row += 1

        save_btn_col = 2
        revert_btn_col = 1
        if platform.system() == 'Windows':
            save_btn_col = 1
            revert_btn_col = 2
        HectorButton(self.toplevel, text="Uložiť", command=self.save_settings, cursor="hand2",
                     background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0,
                     highlightbackground=PANEL_TEXT_COLOR,
                     padx=10, pady=5).grid(
            row=row, column=save_btn_col, columnspan=1, padx=10, pady=10, sticky='w'
        )
        HectorButton(self.toplevel, text="Obnoviť pôvodné", command=self.reset_settings, cursor="hand2",
                     padx=10, pady=5,
                     background=PRIMARY_COLOR, foreground=PANEL_TEXT_COLOR, relief=tk.FLAT, borderwidth=0).grid(
            row=row, column=revert_btn_col, columnspan=1, padx=10, pady=10, sticky='w'
        )

    # SAVE SETTINGS
    def save_settings(self):
        self.config.analysis_settings.repeated_words_min_word_length = int(self.repeated_words_min_word_length_entry.get())
        self.config.analysis_settings.repeated_words_min_word_frequency = int(
            self.repeated_words_min_word_frequency_entry.get())
        self.config.analysis_settings.repeated_words_use_lemma = self.frequent_words_use_lemma_var.get()
        self.config.analysis_settings.long_sentence_words_mid = int(self.long_sentence_words_mid_entry.get())
        self.config.analysis_settings.long_sentence_words_high = int(self.long_sentence_words_high_entry.get())
        self.config.analysis_settings.long_sentence_min_word_length = int(self.long_sentence_min_word_length_entry.get())
        self.config.analysis_settings.enable_frequent_words = self.frequent_words_var.get()
        self.config.analysis_settings.enable_long_sentences = self.long_sentences_var.get()
        self.config.analysis_settings.enable_multiple_spaces = self.multiple_spaces_var.get()
        self.config.analysis_settings.enable_multiple_punctuation = self.multiple_punctuation_var.get()
        self.config.analysis_settings.enable_trailing_spaces = self.trailing_spaces_var.get()
        self.config.analysis_settings.close_words_use_lemma = self.close_words_use_lemma_var.get()
        self.config.analysis_settings.close_words_min_word_length = int(self.close_words_min_word_length_entry.get())
        self.config.analysis_settings.close_words_min_distance_between_words = int(
            self.close_words_min_distance_between_words_entry.get())
        self.config.analysis_settings.close_words_min_frequency = int(self.close_words_min_frequency_entry.get())
        self.config.analysis_settings.enable_close_words = self.close_words_var.get()
        self.config.analysis_settings.enable_spellcheck = self.spellcheck_var.get()
        self.config.analysis_settings.enable_partial_nlp = self.partial_nlp_var.get()
        self.config.analysis_settings.enable_quote_corrections = self.quote_corrections_var.get()
        if self.level == ConfigLevel.GLOBAL:
            ConfigService.save(self.config, CONFIG_FILE_PATH)
        elif self.level == ConfigLevel.PROJECT:
            ctx = RunContext()
            ctx.project.config = self.config
            ProjectService().save(ctx.project, ctx.project.path)
        elif self.level == ConfigLevel.ITEM and self.item is not None:
            ctx = RunContext()
            self.item.config = self.config
            ProjectService().save(ctx.project, ctx.project.path)
        self.on_config_change()
        self.toplevel.destroy()

    # RESET SETTINGS
    def reset_settings(self):
        should_reset = messagebox.askyesno("Obnoviť pôvodné",
                                           "Pokračovaním obnovíte pôvodné nastavenia programu. Skutočne chcete "
                                           "pokračovať?")
        if should_reset:
            self.config.analysis_settings = AnalysisSettings({})
            ConfigService.save(self.config, CONFIG_FILE_PATH)
            self.on_config_change()
            self.toplevel.destroy()
