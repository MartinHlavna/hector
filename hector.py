import ctypes
import platform
import tkinter as tk

from ttkthemes import ThemedTk

from src.backend.service import Service
from src.gui.main_window import MainWindow
from src.gui.splash_window import SplashWindow
from src.utils import Utils

if platform.system() == 'Windows':
    ctypes.windll.shcore.SetProcessDpiAwareness(True)

root = ThemedTk(theme="clam")
root.title("Hector")
photo = tk.PhotoImage(file=Utils.resource_path('images/hector-icon.png'))
root.wm_iconphoto(True, photo)
splash = SplashWindow(root)
splash.update_status("sťahujem a inicializujem jazykový model...")
nlp = Service.initialize_nlp()
splash.update_status("sťahujem a inicializujem slovník...")
dictionaries = Service.initialize_dictionaries()
splash.update_status("inicializujem textový processor...")
splash.close()
main_window = MainWindow(root, nlp, dictionaries["spellcheck"], dictionaries["thesaurus"])
main_window.start_main_loop()
