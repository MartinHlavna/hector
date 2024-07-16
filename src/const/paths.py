import os
import sys

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True
    WORKING_DIRECTORY = os.path.dirname(sys.executable)
else:
    WORKING_DIRECTORY = os.getcwd()

# LOCATION OF CONFIG
DATA_DIRECTORY = os.path.join(WORKING_DIRECTORY, "data")
SPACY_MODELS_DIR = os.path.join(DATA_DIRECTORY, "spacy-models")
SK_SPACY_MODEL_DIR = os.path.join(SPACY_MODELS_DIR, "sk")
DICTIONARY_DIR = os.path.join(DATA_DIRECTORY, "dictionary")
SK_DICTIONARY_DIR = os.path.join(DICTIONARY_DIR, "sk-libreoffice")
SK_SPELL_DICTIONARY_DIR = os.path.join(DICTIONARY_DIR, "sk-skspell")
CONFIG_FILE_PATH = os.path.join(DATA_DIRECTORY, "config.json")