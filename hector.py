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
from spacy.tokens import Doc
from spacy.tokens.token import Token
from spacy.util import compile_infix_regex
from ttkthemes import ThemedTk

from pythes import PyThes
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


# CUSTOM TOKENIZER THAT FOES NOT REMOVE HYPHENATED WORDS
def custom_tokenizer(nlp_pipeline):
    infixes = (
            LIST_ELLIPSES
            + LIST_ICONS
            + [
                r"(?<=[0-9])[+\-\*^](?=[0-9-])",
                r"(?<=[{al}{q}])\.(?=[{au}{q}])".format(
                    al=ALPHA_LOWER, au=ALPHA_UPPER, q=CONCAT_QUOTES
                ),
                r"(?<=[{a}]),(?=[{a}])".format(a=ALPHA),
                # OVERRIDE: r"(?<=[{a}])(?:{h})(?=[{a}])".format(a=ALPHA, h=HYPHENS),
                r"(?<=[{a}0-9])[:<>=/](?=[{a}])".format(a=ALPHA),
            ]
    )
    infix_re = compile_infix_regex(infixes)
    return Tokenizer(nlp_pipeline.vocab, prefix_search=nlp_pipeline.tokenizer.prefix_search,
                     suffix_search=nlp_pipeline.tokenizer.suffix_search,
                     infix_finditer=infix_re.finditer,
                     token_match=nlp_pipeline.tokenizer.token_match,
                     rules=nlp_pipeline.Defaults.tokenizer_exceptions)


root = ThemedTk(theme="clam")
root.title("Hector")
photo = tk.PhotoImage(file=Utils.resource_path('images/hector-icon.png'))
root.wm_iconphoto(True, photo)
splash = SplashWindow(root)
splash.update_status("sťahujem a inicializujem jazykový model...")
# WE CAN MOVE OVER TO PYTHON SPLASH INSTEAD OF IMAGE NOW
if nativeSplashOpened:
    pyi_splash.close()
# INITIALIZE NLP ENGINE
spacy.util.set_data_path = Utils.resource_path('lib/site-packages/spacy/data')
if not os.path.isdir(DATA_DIRECTORY):
    os.mkdir(DATA_DIRECTORY)
if not os.path.isdir(SPACY_MODELS_DIR):
    os.mkdir(SPACY_MODELS_DIR)
if not os.path.isdir(SK_SPACY_MODEL_DIR):
    os.mkdir(SK_SPACY_MODEL_DIR)
    archive_file_name = os.path.join(SPACY_MODELS_DIR, f'{SPACY_MODEL_NAME_WITH_VERSION}.tar.gz')
    with urllib.request.urlopen(SPACY_MODEL_LINK) as response, open(archive_file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
    with tarfile.open(archive_file_name) as tar_file:
        tar_file.extractall(SK_SPACY_MODEL_DIR)
    os.remove(archive_file_name)
nlp = spacy.load(os.path.join(
    SK_SPACY_MODEL_DIR,
    SPACY_MODEL_NAME_WITH_VERSION,
    SPACY_MODEL_NAME,
    SPACY_MODEL_NAME_WITH_VERSION)
)
nlp.tokenizer = custom_tokenizer(nlp)
# SPACY EXTENSIONS
Token.set_extension("is_word", default=False, force=True)
Token.set_extension("grammar_error_type", default=False, force=True)
Token.set_extension("has_grammar_error", default=False, force=True)
Doc.set_extension("words", default=[], force=True)
Doc.set_extension("unique_words", default=[], force=True)
Doc.set_extension("lemmas", default=[], force=True)
Doc.set_extension("total_chars", default=0, force=True)
Doc.set_extension("total_words", default=0, force=True)
Doc.set_extension("total_unique_words", default=0, force=True)
Doc.set_extension("total_pages", default=0, force=True)
splash.update_status("sťahujem a inicializujem slovník...")
if not os.path.isdir(DICTIONARY_DIR):
    os.mkdir(DICTIONARY_DIR)
if not os.path.isdir(SK_DICTIONARY_DIR):
    os.mkdir(SK_DICTIONARY_DIR)
    fs = fsspec.filesystem("github", org="LibreOffice", repo="dictionaries")
    fs.get(fs.ls("sk_SK"), SK_DICTIONARY_DIR, recursive=True)
    fs = fsspec.filesystem("github", org="sk-spell", repo="hunspell-sk")
    fs.get(fs.ls("/"), SK_SPELL_DICTIONARY_DIR, recursive=True)
spellcheck_dictionary = Hunspell('sk_SK', hunspell_data_dir=SK_SPELL_DICTIONARY_DIR)
thesaurus = PyThes(os.path.join(SK_DICTIONARY_DIR, "th_sk_SK_v2.dat"))
splash.update_status("inicializujem textový processor...")
splash.close()
main_window = MainWindow(root, nlp, spellcheck_dictionary, thesaurus)
main_window.start_main_loop()

# TODO LEVEL A (production features):
# Word frequencies and close words should be able to work on lemmas

# TODO LEVEL B (nice to have features): Consider adding:
# Heatmap?
# Commas analysis based on some NLP apporach?
# On mouse over in left/ride panel word, highlight words in editor
# Right click context menu with analysis options on selected text
# Importing other document types like doc, docx, rtf, ...
