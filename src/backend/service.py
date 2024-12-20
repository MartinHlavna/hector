import string

import spacy
from hunspell import Hunspell
from spacy.tokens import Doc

from src.backend.config_service import ConfigService
from src.backend.export_service import ExportService
from src.backend.import_service import ImportService
from src.backend.metadata_service import MetadataService
from src.backend.nlp_service import NlpService
from src.backend.spellcheck_service import SpellcheckService
from src.domain.config import Config
from src.domain.metadata import Metadata


# TODO: Split to multiple services?
# MAIN BACKEND LOGIC IMPLEMENTATION
class Service:

    # FUNCTION THAT INTIALIZES NLP ENGINE
    @staticmethod
    def initialize_nlp():
        return NlpService.initialize()

    # FUNCTION FOR UPGRADING DICTIONARIES
    @staticmethod
    def upgrade_dictionaries(github_token: string = None,
                             github_user: string = None):
        return SpellcheckService.upgrade_dictionaries(github_token, github_user)

    @staticmethod
    def remove_dictionaries_backup():
        SpellcheckService.remove_dictionaries_backup()

    # FUNCTION THAT INTIALIZES NLP DICTIONARIES
    @staticmethod
    def initialize_dictionaries(github_token=None, github_user=None):
        return SpellcheckService.initialize_dictionaries(github_token, github_user)

    # FUNCTION THAT LOADS CONFIG FROM FILE
    @staticmethod
    def load_config(path: string):
        return ConfigService.load(path)

    # FUNCTION THAT LOADS EDITOR METADATA FROM FILE
    @staticmethod
    def load_metadata(path: string):
        return MetadataService.load(path)

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save_config(c: Config, path: string):
        ConfigService.save(c, path)

    # FUNCTION THAT SAVES METADATA TO FILE
    @staticmethod
    def save_metadata(metadata: Metadata, path: string):
        MetadataService.save(metadata, path)

    # METHOD THAT RUNS FULL NLP
    @staticmethod
    def full_nlp(text, nlp: spacy, batch_size, config: Config):
        return NlpService.full_analysis(text, nlp, batch_size, config)

    # METHOD THAT RUNS PARTIAL NLP BASED ON PARAGRAPHS AROUND CARRET POSITION
    @staticmethod
    def partial_nlp(text, original_doc: Doc, nlp: spacy, config: Config, carret_position):
        return NlpService.partial_analysis(text, original_doc, nlp, config, carret_position)

    @staticmethod
    def normalize_text(text):
        return ImportService.normalize_text(text)

    @staticmethod
    def import_document(file_path):
        return ImportService.import_document(file_path)

    @staticmethod
    def ensure_pandoc_available():
        ImportService.ensure_pandoc_available()

    @staticmethod
    def find_multiple_spaces(doc: Doc):
        return NlpService.find_multiple_spaces(doc)

    @staticmethod
    def find_computer_quote_marks(doc: Doc):
        return NlpService.find_computer_quote_marks(doc)

    @staticmethod
    def find_dangling_quote_marks(doc: Doc):
        return NlpService.find_dangling_quote_marks(doc)

    @staticmethod
    def find_incorrect_lower_quote_marks(doc: Doc):
        return NlpService.find_incorrect_lower_quote_marks(doc)

    @staticmethod
    def find_incorrect_upper_quote_marks(doc: Doc):
        return NlpService.find_incorrect_upper_quote_marks(doc)

    @staticmethod
    def find_multiple_punctuation(doc: Doc):
        return NlpService.find_multiple_punctuation(doc)

    @staticmethod
    def find_trailing_spaces(doc: Doc):
        return NlpService.find_trailing_spaces(doc)

    @staticmethod
    def spellcheck(spellcheck_dictionary: Hunspell, doc: Doc):
        SpellcheckService.spellcheck(doc, spellcheck_dictionary)

    # FUNCTION THAT CALCULATE READABILITY INDICES
    @staticmethod
    def evaluate_readability(doc: Doc):
        return NlpService.evaluate_readability(doc)

    # METHOD THAT COMPUTES WORD FREQUENCIES
    @staticmethod
    def compute_word_frequencies(doc: Doc, config: Config):
        return NlpService.compute_word_frequencies(doc, config)

    # METHOD THAT EVALUATES CLOSE WORDS
    @staticmethod
    def evaluate_close_words(doc: Doc, config: Config):
        return NlpService.evaluate_close_words(doc, config)

    @staticmethod
    def partition_close_words(close_words, max_distance):
        return NlpService.partition_close_words(close_words, max_distance)

    @staticmethod
    def export_sentences(path, doc, blank_line_between_sents):
        ExportService.export_sentences(path, doc, blank_line_between_sents)
