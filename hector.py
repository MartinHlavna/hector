import argparse
import ctypes
import platform
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from pygments.styles.dracula import foreground
from ttkthemes import ThemedTk

from src.backend.run_context import RunContext
from src.backend.service.import_service import ImportService
from src.backend.service.nlp_service import NlpService
from src.backend.service.spellcheck_service import SpellcheckService
from src.const.colors import ACCENT_COLOR, PRIMARY_COLOR, ACCENT_2_COLOR, PANEL_TEXT_COLOR, TEXT_EDITOR_FRAME_BG, \
    TEXT_EDITOR_BG, EDITOR_TEXT_COLOR
from src.const.values import VERSION
from src.gui.navigator import Navigator
from src.gui.window.main_window import MainWindow
from src.gui.window.project_selector_window import ProjectSelectorWindow
from src.gui.window.splash_window import SplashWindow
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
    style = ttk.Style(root)
    # CUSTOM SCROLLBAR
    style.configure("Vertical.TScrollbar", gripcount=0, troughcolor=PRIMARY_COLOR, bordercolor=PRIMARY_COLOR,
                    background=ACCENT_COLOR, lightcolor=ACCENT_COLOR, darkcolor=ACCENT_2_COLOR)

    style.layout('arrowless.Vertical.TScrollbar',
                 [('Vertical.Scrollbar.trough',
                   {'children': [('Vertical.Scrollbar.thumb',
                                  {'expand': '1', 'sticky': 'nswe'})],
                    'sticky': 'ns'})])
    style.configure("Grey.TSeparator",
                    background=ACCENT_2_COLOR)
    style.configure("panel.TNotebook",
                    background=PRIMARY_COLOR,
                    foreground=PRIMARY_COLOR,
                    bordercolor=ACCENT_2_COLOR,
                    darkcolor=PRIMARY_COLOR,
                    lightcolor=PRIMARY_COLOR
                    )
    style.configure("panel.TNotebook.Tab",
                    background=ACCENT_2_COLOR,
                    foreground=PANEL_TEXT_COLOR,
                    bordercolor=ACCENT_2_COLOR, )
    style.map(
        "panel.TNotebook.Tab",
        # "selected" je stav, keď je záložka aktívna
        background=[("selected", PRIMARY_COLOR)],  # Pozadie aktívnej záložky
        foreground=[("selected", PANEL_TEXT_COLOR)],  # Text aktívnej záložky
        bordercolor=[("selected", ACCENT_2_COLOR)],  # Text aktívnej záložky
    )
    style.configure("panel.Treeview", background=TEXT_EDITOR_FRAME_BG, foreground=PANEL_TEXT_COLOR,
                    fieldbackground=TEXT_EDITOR_FRAME_BG, bordercolor=ACCENT_2_COLOR, lightcolor=ACCENT_2_COLOR)
    style.configure('hector.TSpinbox',
                    fieldbackground=TEXT_EDITOR_BG,
                    bordercolor=TEXT_EDITOR_BG,
                    darkcolor=TEXT_EDITOR_BG,
                    selectbackground=TEXT_EDITOR_BG,
                    background=TEXT_EDITOR_BG,
                    lightcolor=TEXT_EDITOR_BG,
                    arrowcolor=EDITOR_TEXT_COLOR,
                    foreground=EDITOR_TEXT_COLOR,
                    insertcolor=EDITOR_TEXT_COLOR,
                    arrowsize=12
                    )
    style.configure('hector.TCheckbutton',
                    background=TEXT_EDITOR_FRAME_BG,
                    focuscolor=TEXT_EDITOR_FRAME_BG,
                    foreground=EDITOR_TEXT_COLOR,
                    )
    style.map('hector.TCheckbutton', background=[
        ('disabled', TEXT_EDITOR_FRAME_BG),
        ('selected', TEXT_EDITOR_FRAME_BG),
        ('!selected', TEXT_EDITOR_FRAME_BG)])
    photo = tk.PhotoImage(file=Utils.resource_path('images/hector-icon.png'))
    root.wm_iconphoto(True, photo)
    splash = SplashWindow(root)
    splash.update_status("sťahujem a inicializujem jazykový model...")
    nlp = NlpService.initialize()
    if not nlp:
        splash.close()
        handle_error("Nepodarilo sa stiahnuť jazykový model. Overte prosím, že máte internetové pripojenie!")
        sys.exit(1)
    splash.update_status("sťahujem a inicializujem slovník...")
    dictionaries = SpellcheckService.initialize(github_token=args.github_token, github_user=args.github_user)
    if not nlp:
        splash.close()
        handle_error("Nepodarilo sa stiahnuť slovníky. Overte prosím, že máte internetové pripojenie!")
        sys.exit(1)
    splash.update_status("sťahujem pandoc...")
    # noinspection PyBroadException
    try:
        ImportService.ensure_pandoc_available()
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
    ctx = RunContext()
    ctx.nlp = nlp
    ctx.spellcheck_dictionary = dictionaries["spellcheck"]
    ctx.thesaurus = dictionaries["thesaurus"]
    ctx.has_available_update = has_available_update
    navigator = Navigator()
    navigator.root = root
    navigator.windows[Navigator.MAIN_WINDOW] = lambda r: MainWindow(r)
    navigator.windows[Navigator.PROJECT_SELECTOR_WINDOW] = lambda r: ProjectSelectorWindow(r)
    splash.close()
    # OPEN WINDOW IN MAXIMIZED STATE
    # FOR WINDOWS AND MAC OS SET STATE ZOOMED
    # FOR LINUX SET ATTRIBUTE ZOOMED
    if platform.system() == "Windows" or platform.system() == "Darwin":
        root.state("zoomed")
    else:
        root.attributes('-zoomed', True)
    navigator.navigate(Navigator.PROJECT_SELECTOR_WINDOW)
    root.mainloop()
