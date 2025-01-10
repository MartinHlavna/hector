import os
import re
import shutil
import tarfile
import urllib
import zipfile

import spacy
from spacy.lang.char_classes import LIST_ELLIPSES, LIST_ICONS, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, ALPHA
from spacy.tokenizer import Tokenizer
from spacy.tokens import Doc, Span, Token
from spacy.util import compile_infix_regex

from src.backend.morphodita_tagger_morphologizer_lemmatizer import MORPHODITA_COMPONENT_FACTORY_NAME, \
    MORPHODITA_RESET_SENTENCES_COMPONENT
from src.const.paths import DATA_DIRECTORY, SPACY_MODELS_DIR, SK_SPACY_MODEL_DIR, CURRENT_SK_SPACY_MODEL_DIR, \
    MORPHODITA_MODELS_DIR, SK_MORPHODITA_MODEL_DIR, SK_MORPHODITA_TAGGER
from src.const.patterns import PATTERN_MULTIPLE_SPACES, PATTERN_COMPUTER_QUOTE_MARKS, PATTERN_DANGLING_QUOTE_MARKS, \
    PATTERN_INCORRECT_LOWER_QUOTE_MARKS, PATTERN_INCORRECT_UPPER_QUOTE_MARKS, PATTERN_MULTIPLE_PUNCTUACTION, \
    PATTERN_TRAILING_SPACES
from src.const.values import SPACY_MODEL_NAME_WITH_VERSION, SPACY_MODEL_LINK, MORPHODITA_MODEL_LINK, \
    MORPHODITA_MODEL_NAME, SPACY_MODEL_NAME, READABILITY_MAX_VALUE
from src.domain.config import Config
from src.domain.unique_word import UniqueWord
from src.utils import Utils


class NlpService:
    # FUNCTION THAT INTIALIZES NLP ENGINE
    @staticmethod
    def initialize():
        # noinspection PyBroadException
        try:
            spacy.util.set_data_path = Utils.resource_path('lib/site-packages/spacy/data')
            old_model_exists = False
            # EBSURE DIRECTORY STRUCTURE EXISTS
            if not os.path.isdir(DATA_DIRECTORY):
                os.mkdir(DATA_DIRECTORY)
            if not os.path.isdir(SPACY_MODELS_DIR):
                os.mkdir(SPACY_MODELS_DIR)
            if not os.path.isdir(SK_SPACY_MODEL_DIR):
                os.mkdir(SK_SPACY_MODEL_DIR)
            else:
                old_model_exists = True
            if not os.path.isdir(CURRENT_SK_SPACY_MODEL_DIR):
                # IF WE ARE UPGRADING SPACY MODEL, WE NEED TO REMOVE OLD MODELS
                if old_model_exists:
                    shutil.rmtree(SK_SPACY_MODEL_DIR)
                    os.mkdir(SK_SPACY_MODEL_DIR)
                archive_file_name = os.path.join(SPACY_MODELS_DIR, f'{SPACY_MODEL_NAME_WITH_VERSION}.tar.gz')
                with urllib.request.urlopen(SPACY_MODEL_LINK) as response, open(archive_file_name, 'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                with tarfile.open(archive_file_name) as tar_file:
                    tar_file.extractall(SK_SPACY_MODEL_DIR)
                os.remove(archive_file_name)
            if not os.path.isdir(MORPHODITA_MODELS_DIR):
                os.mkdir(MORPHODITA_MODELS_DIR)
            if not os.path.isdir(SK_MORPHODITA_MODEL_DIR):
                archive_file_name = os.path.join(MORPHODITA_MODELS_DIR, f'{MORPHODITA_MODEL_NAME}.zip')
                with urllib.request.urlopen(MORPHODITA_MODEL_LINK) as response, open(archive_file_name,
                                                                                     'wb') as out_file:
                    shutil.copyfileobj(response, out_file)
                with zipfile.ZipFile(archive_file_name, 'r') as zip_file:
                    zip_file.extractall(MORPHODITA_MODELS_DIR)
                os.remove(archive_file_name)
            nlp = spacy.load(os.path.join(
                SK_SPACY_MODEL_DIR,
                SPACY_MODEL_NAME_WITH_VERSION,
                SPACY_MODEL_NAME,
                SPACY_MODEL_NAME_WITH_VERSION)
            )
            # CUSTOM TOKENIZER THAT TREATS HYPTHENATED WORDS AS SINGLE TOKEN
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
            nlp.tokenizer = HectorTokenizer(Tokenizer(nlp.vocab, prefix_search=nlp.tokenizer.prefix_search,
                                                      suffix_search=nlp.tokenizer.suffix_search,
                                                      infix_finditer=infix_re.finditer,
                                                      token_match=nlp.tokenizer.token_match,
                                                      rules=nlp.Defaults.tokenizer_exceptions))
            # ADD SENTENCIZER SO MORPHODITA CAN WORK ON AT LEAST SOME SENTENCES
            nlp.add_pipe('sentencizer', after='trainable_lemmatizer')
            # ADD CUSTOM COMPONENT FOR MORPHODITA
            nlp.add_pipe(
                MORPHODITA_COMPONENT_FACTORY_NAME,
                name='morphodita_tagger_morphologizer_lemmatizer',
                after='sentencizer',
                config={"tagger_path": SK_MORPHODITA_TAGGER}
            )
            # ADD CUSTOM COMPONENT THAT RESETS SENTENCE BOUNDARIES SO DEPENDENCY ANALYZER WILL WORK
            nlp.add_pipe(MORPHODITA_RESET_SENTENCES_COMPONENT, after='morphodita_tagger_morphologizer_lemmatizer')
            # REMOVE UNUSED PIPES REPLACED BY MORPHODITA
            nlp.remove_pipe('tagger')
            nlp.remove_pipe('morphologizer')
            nlp.remove_pipe('trainable_lemmatizer')
            print(nlp.pipe_names)
            # REGISTER SPACY EXTENSIONS
            Token.set_extension("is_word", default=False, force=True)
            Token.set_extension("word_index", default=None, force=True)
            Token.set_extension("grammar_error_type", default=None, force=True)
            Token.set_extension("has_grammar_error", default=False, force=True)
            Token.set_extension("paragraph", default=None, force=True)
            Doc.set_extension("words", default=[], force=True)
            Doc.set_extension("paragraphs", default=[], force=True)
            Doc.set_extension("unique_words", default=[], force=True)
            Doc.set_extension("lemmas", default=[], force=True)
            Doc.set_extension("total_chars", default=0, force=False)
            Doc.set_extension("total_words", default=0, force=True)
            Doc.set_extension("total_unique_words", default=0, force=True)
            Doc.set_extension("total_pages", default=0, force=True)
            Span.set_extension("is_mid_sentence", default=False, force=True)
            Span.set_extension("is_long_sentence", default=False, force=True)
            return nlp
        except Exception as e:
            print(e)
            print("Unable to retrieve data. Please check your internet connection.")
            return None

    # METHOD THAT RUNS FULL NLP ANALYSIS
    @staticmethod
    def full_analysis(text, nlp: spacy, batch_size, config: Config):
        doc = Doc.from_docs(list(nlp.pipe([text], batch_size=batch_size)), nlp)
        NlpService.fill_custom_data(text, doc, config)
        return doc

    # METHOD THAT RUNS PARTIAL NLP BASED ON PARAGRAPHS AROUND CARRET POSITION
    @staticmethod
    def partial_analysis(text, original_doc: Doc, nlp: spacy, config: Config, carret_position):
        # GET TOKEN ON CARRET POSITION
        span = original_doc.char_span(carret_position, carret_position, alignment_mode='expand')
        if span is not None:
            changed_paragraph = span.sent.root._.paragraph
        else:
            # IF TOKEN ON CARRENT POSITION IS NOT AVAILABLE, CARRET IS AT END OF DOCUMENT
            # WE TAKE LAST PARAGRAPH
            changed_paragraph = original_doc[len(original_doc) - 1]._.paragraph
        # WE FIND FIRST AND LAST TOKEN OF MODIFIED PARAGRAPH
        first_token = changed_paragraph[0]
        last_token = changed_paragraph[len(changed_paragraph) - 1]
        start = changed_paragraph.start_char
        end = changed_paragraph.end_char
        # IF WE ARE NOT AT START OF DOCUMENT, WE EXPAND SELECTION TO PREVIOUS PARAGRAPH
        if first_token.i > 0:
            nbor = first_token.nbor(-1)
            start = nbor._.paragraph.start_char
            first_token = nbor._.paragraph[0]
            # IF WE ARE NOT AT END OF DOCUMENT, WE EXPAND SELECTION TO NEXT PARAGRAPH
        if last_token.i < len(original_doc) - 1:
            nbor = last_token.nbor(1)
            end = nbor._.paragraph.end_char
            last_token = nbor._.paragraph[len(nbor._.paragraph) - 1]
        # RUN NLP ON SELECTED TEXT
        changed_portion_of_text = text[start:(end + len(text) - len(original_doc.text))]
        partial_document = nlp(changed_portion_of_text)
        # MERGE DOCUMENTS:
        # 1. FROM START OF DOCUMENT TO START OF SELECTION
        # 2. SELECTION - WITH FRESH NLP RESULTS
        # 3. FROM END OF SELECTION TO END OF DOCUMENT
        documents = []
        if first_token.i > 0:
            documents.append(original_doc[:first_token.i].as_doc())
        documents.append(partial_document)
        if last_token.i < len(original_doc) - 1:
            documents.append(original_doc[last_token.i + 1:].as_doc())
        doc = Doc.from_docs(documents, ensure_whitespace=False)
        # RECOMPUTE CUSTOM DATA ON MERGED DOCUMENT.
        NlpService.fill_custom_data(text, doc, config)
        return doc

    # METHOD THAT ADDS ALL EXTENSION DATA IN SINGLE PASS OVER ALL TOKENS
    @staticmethod
    def fill_custom_data(original_text: str, doc: Doc, config: Config):
        word_pattern = re.compile("\\w+")
        words = []
        word_index = 0
        paragraphs = []
        cur_paragraph_start = 0
        unique_lemmas = {}
        unique_words = {}
        for token in doc:
            if token.is_space and token.text.count('\n') > 0:
                paragraph = doc[cur_paragraph_start:token.i]
                cur_paragraph_start = token.i
                NlpService.append_paragraph(paragraph, paragraphs)
            token._.is_word = re.match(word_pattern, token.lower_) is not None
            if token._.is_word:
                NlpService.append_word(token, word_index, unique_lemmas, unique_words, words)
                word_index += 1
        if len(doc) > cur_paragraph_start:
            paragraph = doc[cur_paragraph_start:]
            NlpService.append_paragraph(paragraph, paragraphs)
        doc._.paragraphs = paragraphs
        doc._.words = words
        doc._.unique_words = unique_words
        doc._.lemmas = unique_lemmas
        doc._.total_chars = len(original_text.replace('\n', ''))
        doc._.total_words = len(words)
        doc._.total_unique_words = len(unique_words)
        doc._.total_pages = round(doc._.total_chars / 1800, 2)
        NlpService.evaluate_sentence_length(config, doc)
        return doc

    # METHOD THAT ADDS WORD AND ALL WORD RELATED DATA TO TOKEN AND INPUT COLLECTIONS
    @staticmethod
    def append_word(token, word_index, unique_lemmas, unique_words, words):
        token._.word_index = word_index
        words.append(token)
        lemma = token.lemma_.lower()
        unique_word = unique_words.get(token.lower_, None)
        unique_lemma = unique_lemmas.get(lemma, None)
        if unique_word is None:
            unique_word = UniqueWord(token.lower_)
            unique_words[token.lower_] = unique_word
        if unique_lemma is None:
            unique_lemma = UniqueWord(lemma)
            unique_lemmas[lemma] = unique_lemma
        unique_word.occourences.append(token)
        unique_lemma.occourences.append(token)

    # METHOD THAT ADDS PARAGRAPH TO COLLECTION AND SETS REFERENCE TO ALL INNER TOKENS TO THAT PARAGRAPH
    @staticmethod
    def append_paragraph(paragraph, paragraphs):
        paragraphs.append(paragraph)
        for t in paragraph:
            t._.paragraph = paragraph

    @staticmethod
    def evaluate_sentence_length(config, doc):
        for sentence in doc.sents:
            words = [word for word in sentence if
                     word._.is_word and len(word.text) >= config.analysis_settings.long_sentence_min_word_length]
            if len(words) > config.analysis_settings.long_sentence_words_mid:
                if len(words) > config.analysis_settings.long_sentence_words_high:
                    sentence._.is_long_sentence = True
                else:
                    sentence._.is_mid_sentence = True

    @staticmethod
    def evaluate_readability(doc: Doc):
        if doc._.total_words <= 1:
            return 0
        # SHORTER THAN 3 CHAR SENTENCES ARE JUST GARBAGE
        sentence_count = 0
        for sent in doc.sents:
            if len(sent.text) > 2:
                sentence_count += 1
        type_to_token_ratio = doc._.total_words / doc._.total_unique_words
        average_sentence_length = doc._.total_words / sentence_count
        average_word_length = doc._.total_chars / doc._.total_words / 2
        mistrik_index = READABILITY_MAX_VALUE - ((average_sentence_length * average_word_length) / type_to_token_ratio)
        return READABILITY_MAX_VALUE - max(0.0, round(mistrik_index, 0))

    # METHOD THAT COMPUTES WORD FREQUENCIES
    @staticmethod
    def compute_word_frequencies(doc: Doc, config: Config):
        x = doc._.unique_words
        if config.analysis_settings.repeated_words_use_lemma:
            x = doc._.lemmas
        words = {k: v for (k, v) in x.items() if
                 len(k) >= config.analysis_settings.repeated_words_min_word_length and len(
                     v.occourences) >= config.analysis_settings.repeated_words_min_word_frequency}
        return sorted(words.values(), key=lambda x: len(x.occourences), reverse=True)

    # METHOD THAT EVALUATES CLOSE WORDS
    @staticmethod
    def evaluate_close_words(doc: Doc, config: Config):
        close_words = {}
        x = doc._.unique_words
        if config.analysis_settings.close_words_use_lemma:
            x = doc._.lemmas
        words_nlp = {k: v for (k, v) in x.items() if
                     len(k) >= config.analysis_settings.close_words_min_word_length}
        for key, unique_word in words_nlp.items():
            # IF WORD DOES NOT OCCOUR ENOUGH TIMES WE DONT NEED TO CHECK IF ITS OCCOURENCES ARE CLOSE
            if len(unique_word.occourences) < config.analysis_settings.close_words_min_frequency + 1:
                continue
            for idx, word_occource in enumerate(unique_word.occourences):
                repetitions = []
                for possible_repetition in unique_word.occourences[idx + 1:len(unique_word.occourences) + 1]:
                    word_distance = possible_repetition._.word_index - word_occource._.word_index
                    if word_distance <= config.analysis_settings.close_words_min_distance_between_words:
                        repetitions.append(word_occource)
                        repetitions.append(possible_repetition)
                    else:
                        break
                if len(repetitions) > config.analysis_settings.close_words_min_frequency:
                    if key not in close_words:
                        close_words[key] = set()
                    close_words[key].update(repetitions)
        return dict(sorted(close_words.items(), key=lambda item: len(item[1]), reverse=True))

    @staticmethod
    def partition_close_words(close_words, max_distance):
        if close_words is None:
            return []
        repetition_groups = []
        cw = (list(close_words))
        cw.sort(key=lambda x: x._.word_index)
        current_group = [cw[0]]
        for i in range(1, len(cw)):
            if cw[i]._.word_index - cw[i - 1]._.word_index > max_distance:
                repetition_groups.append(current_group)
                current_group = []
            current_group.append(cw[i])

        # Append the last subarray
        if current_group:
            repetition_groups.append(current_group)

        return repetition_groups

    @staticmethod
    def find_multiple_spaces(doc: Doc):
        return re.finditer(PATTERN_MULTIPLE_SPACES, doc.text)

    @staticmethod
    def find_computer_quote_marks(doc: Doc):
        return re.finditer(PATTERN_COMPUTER_QUOTE_MARKS, doc.text)

    @staticmethod
    def find_dangling_quote_marks(doc: Doc):
        return re.finditer(PATTERN_DANGLING_QUOTE_MARKS, doc.text)

    @staticmethod
    def find_incorrect_lower_quote_marks(doc: Doc):
        return re.finditer(PATTERN_INCORRECT_LOWER_QUOTE_MARKS, doc.text)

    @staticmethod
    def find_incorrect_upper_quote_marks(doc: Doc):
        return re.finditer(PATTERN_INCORRECT_UPPER_QUOTE_MARKS, doc.text)

    @staticmethod
    def find_multiple_punctuation(doc: Doc):
        return re.finditer(PATTERN_MULTIPLE_PUNCTUACTION, doc.text)

    @staticmethod
    def find_trailing_spaces(doc: Doc):
        return re.finditer(PATTERN_TRAILING_SPACES, doc.text, re.MULTILINE)


class HectorTokenizer:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, string):
        doc = self.tokenizer(Utils.normalize_spaces(string))
        return doc


