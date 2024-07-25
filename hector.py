import tkinter as tk

from ttkthemes import ThemedTk

from src.backend.service import Service
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
# Right click context menu with analysis options on selected text
# On mouse over in right panel word, highlight words in editor
