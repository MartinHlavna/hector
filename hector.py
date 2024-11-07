import ctypes
import platform
import tkinter as tk

import pypandoc
from ttkthemes import ThemedTk

from src.backend.service import Service
from src.const.values import VERSION
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
splash.update_status("sťahujem pandoc...")
Service.download_pandoc()
splash.update_status("kontrolujem aktualizácie...")
has_available_update = False
build_info = Utils.get_build_info()
if build_info['channel'] == "beta":
    has_available_update = Utils.check_updates(VERSION, True)
if build_info['channel'] == "stable":
    has_available_update = Utils.check_updates(VERSION, False)
splash.update_status("inicializujem textový processor...")
splash.close()
main_window = MainWindow(root, nlp, dictionaries["spellcheck"], dictionaries["thesaurus"], has_available_update)
main_window.start_main_loop()
