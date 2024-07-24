import shutil
import tarfile
import tkinter as tk
import urllib

import fsspec
import spacy
from hunspell import Hunspell
from spacy.lang.char_classes import LIST_ELLIPSES, LIST_ICONS, ALPHA_LOWER, ALPHA_UPPER, ALPHA
from spacy.lang.sl.punctuation import CONCAT_QUOTES
from spacy.tokenizer import Tokenizer
from spacy.tokens import Doc, Span
from spacy.tokens.token import Token
from spacy.util import compile_infix_regex
from ttkthemes import ThemedTk

from pythes import PyThes

from src.backend.service import Service
from src.const.paths import *
from src.const.values import *
from src.gui.main_window import MainWindow
from src.gui.splash_window import SplashWindow
from src.utils import Utils

# WE CAN MOVE OVER TO PYTHON SPLASH INSTEAD OF IMAGE NOW
nativeSplashOpened = False
# noinspection PyBroadException
try:
    import pyi_splash

    pyi_splash.update_text('inicializujem ...')
    nativeSplashOpened = True
except:
    pass


root = ThemedTk(theme="clam")
root.title("Hector")
photo = tk.PhotoImage(file=Utils.resource_path('images/hector-icon.png'))
root.wm_iconphoto(True, photo)
splash = SplashWindow(root)
splash.update_status("sťahujem a inicializujem jazykový model...")
# WE CAN MOVE OVER TO PYTHON SPLASH INSTEAD OF IMAGE NOW
if nativeSplashOpened:
    pyi_splash.close()
nlp = Service.initialize_nlp()
splash.update_status("sťahujem a inicializujem slovník...")
dictionaries = Service.initialize_dictionaries()
splash.update_status("inicializujem textový processor...")
splash.close()
main_window = MainWindow(root, nlp, dictionaries["spellcheck"], dictionaries["thesaurus"])
main_window.start_main_loop()

# TODO LEVEL A (production features):

# TODO LEVEL B (nice to have features): Consider adding:
# Heatmap?
# Commas analysis based on some NLP apporach?
# On mouse over in left/ride panel word, highlight words in editor
# Right click context menu with analysis options on selected text
# Importing other document types like doc, docx, rtf, ...
