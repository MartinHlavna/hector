import os
import sys

from src.const.values import SPACY_MODEL_NAME_WITH_VERSION

WORKING_DIRECTORY = '.'
RUN_DIRECTORY = '.'
if "NUITKA_ONEFILE_PARENT" in os.environ:
    # If the application is compiled using nuitka it sets enviroment value
    WORKING_DIRECTORY = os.path.dirname(sys.argv[0])
    # Climb up two directories to get to the root of the project
    RUN_DIRECTORY = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
elif getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True
    WORKING_DIRECTORY = os.path.dirname(sys.executable)
    RUN_DIRECTORY = os.path.dirname(sys.executable)
else:
    WORKING_DIRECTORY = os.getcwd()
    RUN_DIRECTORY = os.getcwd()

DATA_DIRECTORY = os.path.join(WORKING_DIRECTORY, "data")
FONTS_DIRECTORY = os.path.join(RUN_DIRECTORY, "fonts")
FONT_AWESOME_DIRECTORY = os.path.join(FONTS_DIRECTORY, "fontawesome-free-6.6.0-desktop", "otfs")
SPACY_MODELS_DIR = os.path.join(DATA_DIRECTORY, "spacy-models")
SK_SPACY_MODEL_DIR = os.path.join(SPACY_MODELS_DIR, "sk")
CURRENT_SK_SPACY_MODEL_DIR = os.path.join(SK_SPACY_MODEL_DIR, SPACY_MODEL_NAME_WITH_VERSION)
MORPHODITA_MODELS_DIR = os.path.join(DATA_DIRECTORY, "morphodita")
SK_MORPHODITA_MODEL_DIR = os.path.join(MORPHODITA_MODELS_DIR, "slovak-morfflex-pdt-170914")
SK_MORPHODITA_TAGGER = os.path.join(SK_MORPHODITA_MODEL_DIR, "slovak-morfflex-pdt-170914.tagger")
DICTIONARY_DIR = os.path.join(DATA_DIRECTORY, "dictionary")
DICTIONARY_DIR_BACKUP = os.path.join(DATA_DIRECTORY, "dictionary-backup")
SK_DICTIONARY_DIR = os.path.join(DICTIONARY_DIR, "sk-libreoffice")
SK_SPELL_DICTIONARY_DIR = os.path.join(DICTIONARY_DIR, "sk-skspell")
CONFIG_FILE_PATH = os.path.join(DATA_DIRECTORY, "config.json")
METADATA_FILE_PATH = os.path.join(DATA_DIRECTORY, "metadata.json")
