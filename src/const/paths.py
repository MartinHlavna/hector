import os
import sys
WORKING_DIRECTORY = '.'
RUN_DIRECTORY = '.'
if "NUITKA_ONEFILE_PARENT" in os.environ:
    # If the application is compiled using nuitka it sets enviroment value
    WORKING_DIRECTORY = os.path.dirname(sys.argv[0])
    RUN_DIRECTORY = os.path.dirname(sys.executable)
elif getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True
    WORKING_DIRECTORY = os.path.dirname(sys.executable)
    RUN_DIRECTORY = os.path.dirname(sys.executable)
else:
    WORKING_DIRECTORY = os.getcwd()
    RUN_DIRECTORY = os.getcwd()

print(WORKING_DIRECTORY)
print(RUN_DIRECTORY)
# LOCATION OF CONFIG
DATA_DIRECTORY = os.path.join(WORKING_DIRECTORY, "data")
FONTS_DIRECTORY = os.path.join(WORKING_DIRECTORY, "fonts")
FONT_AWESOME_DIRECTORY = os.path.join(FONTS_DIRECTORY, "fontawesome-free-6.6.0-desktop", "otfs")
SPACY_MODELS_DIR = os.path.join(DATA_DIRECTORY, "spacy-models")
SK_SPACY_MODEL_DIR = os.path.join(SPACY_MODELS_DIR, "sk")
DICTIONARY_DIR = os.path.join(DATA_DIRECTORY, "dictionary")
SK_DICTIONARY_DIR = os.path.join(DICTIONARY_DIR, "sk-libreoffice")
SK_SPELL_DICTIONARY_DIR = os.path.join(DICTIONARY_DIR, "sk-skspell")
CONFIG_FILE_PATH = os.path.join(DATA_DIRECTORY, "config.json")
