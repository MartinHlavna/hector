import argparse
import ctypes
import platform
import sys
import tkinter as tk
from tkinter import messagebox

from ttkthemes import ThemedTk

from src.backend.service import Service
from src.const.values import VERSION
from src.gui.main_window import MainWindow
from src.gui.splash_window import SplashWindow
from src.utils import Utils


def handle_error(text):
    messagebox.showerror('Chyba spúštania!', text)


if __name__ == "__main__":
    if platform.system() == 'Windows':
        ctypes.windll.shcore.SetProcessDpiAwareness(True)

    parser = argparse.ArgumentParser()

    parser.add_argument("--github_token", help="Run with this github token for all github calls")
    parser.add_argument("--github_user", help="Run with this github token for all github calls")

    args = parser.parse_args()

    root = ThemedTk(theme="clam")
    root.title("Hector")
    photo = tk.PhotoImage(file=Utils.resource_path('images/hector-icon.png'))
    root.wm_iconphoto(True, photo)
    splash = SplashWindow(root)
    splash.update_status("sťahujem a inicializujem jazykový model...")
    nlp = Service.initialize_nlp()
    if not nlp:
        splash.close()
        handle_error("Nepodarilo sa stiahnuť jazykový model. Overte prosím, že máte internetové pripojenie!")
        sys.exit(1)
    splash.update_status("sťahujem a inicializujem slovník...")
    dictionaries = Service.initialize_dictionaries(github_token=args.github_token, github_user=args.github_user)
    if not nlp:
        splash.close()
        handle_error("Nepodarilo sa stiahnuť slovníky. Overte prosím, že máte internetové pripojenie!")
        sys.exit(1)
    splash.update_status("sťahujem pandoc...")
    # noinspection PyBroadException
    try:
        Service.download_pandoc()
    except Exception:
        splash.close()
        handle_error("Nepodarilo sa stiahnuť modul pandoc. Overte prosím, že máte internetové pripojenie!")
        sys.exit(1)

    if not nlp:
        splash.close()
        handle_error("Nepodarilo sa stiahnuť jazykový model. Overte prosím, že máte internetové pripojenie!")
        sys.exit(1)
    splash.update_status("kontrolujem aktualizácie...")
    has_available_update = False
    build_info = Utils.get_build_info()
    if build_info['channel'].lower() == "beta":
        has_available_update = Utils.check_updates(VERSION, True,
                                                   github_token=args.github_token, github_user=args.github_user)
    if build_info['channel'].lower() == "stable":
        has_available_update = Utils.check_updates(VERSION, False,
                                                   github_token=args.github_token, github_user=args.github_user)
    splash.update_status("inicializujem textový processor...")
    splash.close()
    main_window = MainWindow(root, nlp, dictionaries["spellcheck"], dictionaries["thesaurus"], has_available_update)
    main_window.start_main_loop()
