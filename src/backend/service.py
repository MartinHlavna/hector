import json
import os
import re
import shutil
import string
import tarfile
import unicodedata
import urllib

import fsspec
import spacy
import pypandoc
from hunspell import Hunspell
from pythes import PyThes
from spacy.lang.char_classes import LIST_ELLIPSES, LIST_ICONS, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, ALPHA
from spacy.matcher import DependencyMatcher
from spacy.tokenizer import Tokenizer
from spacy.tokens import Doc, Token, Span
from spacy.util import compile_infix_regex

from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD, GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX, \
    GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX
from src.const.paths import DATA_DIRECTORY, SPACY_MODELS_DIR, SK_SPACY_MODEL_DIR, DICTIONARY_DIR, SK_DICTIONARY_DIR, \
    SK_SPELL_DICTIONARY_DIR
from src.const.values import SPACY_MODEL_NAME_WITH_VERSION, SPACY_MODEL_LINK, SPACY_MODEL_NAME, READABILITY_MAX_VALUE
from src.domain.config import Config
from src.domain.unique_word import UniqueWord
from src.utils import Utils

PATTERN_TRAILING_SPACES = r' +$'

PATTERN_MULTIPLE_PUNCTUACTION = r'([!?.,:;]){2,}'

PATTERN_MULTIPLE_SPACES = r' {2,}'

with open(Utils.resource_path(os.path.join('data_files', 'misstagged_words.json')), 'r', encoding='utf-8') as file:
    MISSTAGGED_WORDS = json.load(file)

# MAIN BACKEND LOGIC IMPLEMENTATION
class Service:
    # FUNCTION THAT INTIALIZES NLP ENGINE
    @staticmethod
    def initialize_nlp():
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
        nlp.tokenizer = Tokenizer(nlp.vocab, prefix_search=nlp.tokenizer.prefix_search,
                                  suffix_search=nlp.tokenizer.suffix_search,
                                  infix_finditer=infix_re.finditer,
                                  token_match=nlp.tokenizer.token_match,
                                  rules=nlp.Defaults.tokenizer_exceptions)
        # SPACY EXTENSIONS
        Token.set_extension("is_word", default=False, force=True)
        Token.set_extension("grammar_error_type", default=None, force=True)
        Token.set_extension("has_grammar_error", default=False, force=True)
        Token.set_extension("paragraph", default=None, force=True)
        Doc.set_extension("words", default=[], force=True)
        Doc.set_extension("paragraphs", default=[], force=True)
        Doc.set_extension("unique_words", default=[], force=True)
        Doc.set_extension("lemmas", default=[], force=True)
        Doc.set_extension("total_chars", default=0, force=True)
        Doc.set_extension("total_words", default=0, force=True)
        Doc.set_extension("total_unique_words", default=0, force=True)
        Doc.set_extension("total_pages", default=0, force=True)
        Span.set_extension("is_mid_sentence", default=False, force=True)
        Span.set_extension("is_long_sentence", default=False, force=True)
        return nlp

    # FUNCTION THAT INTIALIZES NLP DICTIONARIES
    @staticmethod
    def initialize_dictionaries(github_token=None, github_user=None):
        if not os.path.isdir(DICTIONARY_DIR):
            os.mkdir(DICTIONARY_DIR)
        if not os.path.isdir(SK_DICTIONARY_DIR):
            os.mkdir(SK_DICTIONARY_DIR)
            fs = fsspec.filesystem("github", org="LibreOffice", repo="dictionaries", token=github_token, username=github_user)
            fs.get(fs.ls("sk_SK"), SK_DICTIONARY_DIR, recursive=True)
            fs = fsspec.filesystem("github", org="sk-spell", repo="hunspell-sk", token=github_token, username=github_user)
            fs.get(fs.ls("/"), SK_SPELL_DICTIONARY_DIR, recursive=True)
        return {
            "spellcheck": Hunspell('sk_SK', hunspell_data_dir=SK_SPELL_DICTIONARY_DIR),
            "thesaurus": PyThes(os.path.join(SK_DICTIONARY_DIR, "th_sk_SK_v2.dat"))
        }

    # FUNCTION THAT LOADS CONFIG FROM FILE
    @staticmethod
    def load_config(path: string):
        if os.path.exists(path):
            with open(path, 'r') as file:
                c = json.load(file)
                return Config(c)
                # CHECK IF ALL CONFIG_KEYS ARE PRESENT
                # PROVIDE MISSING KEYS FROM DEFAULTS
        else:
            return Config()

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save_config(c: Config, path: string):
        with open(path, 'w') as file:
            json.dump(c.to_dict(), file, indent=4)

    # METHOD THAT RUNS FULL NLP
    @staticmethod
    def full_nlp(text, nlp: spacy, batch_size, config: Config):
        doc = Doc.from_docs(list(nlp.pipe([text], batch_size=batch_size)), nlp)
        Service.fill_custom_data(doc, config)
        return doc

    # METHOD THAT RUNS PARTIAL NLP BASED ON PARAGRAPHS AROUND CARRET POSITION
    @staticmethod
    def partial_nlp(text, original_doc: Doc, nlp: spacy, config: Config, carret_position):
        span = original_doc.char_span(carret_position, carret_position, alignment_mode='expand')
        if span is not None:
            changed_paragraph = span.root._.paragraph
        else:
            changed_paragraph = original_doc[len(original_doc) - 1]._.paragraph
        first_token = changed_paragraph[0]
        last_token = changed_paragraph[len(changed_paragraph) - 1]
        start = changed_paragraph.start_char
        end = changed_paragraph.end_char
        if first_token.i > 0:
            nbor = first_token.nbor(-1)
            start = nbor._.paragraph.start_char
            first_token = nbor._.paragraph[0]
        if last_token.i < len(original_doc) - 1:
            nbor = last_token.nbor(1)
            end = nbor._.paragraph.end_char
            last_token = nbor._.paragraph[len(nbor._.paragraph) - 1]
        changed_portion_of_text = text[start:(end + len(text) - len(original_doc.text))]
        partial_document = nlp(changed_portion_of_text)
        documents = []
        if first_token.i > 0:
            documents.append(original_doc[:first_token.i].as_doc())
        documents.append(partial_document)
        if last_token.i < len(original_doc) - 1:
            documents.append(original_doc[last_token.i + 1:].as_doc())
        doc = Doc.from_docs(documents, ensure_whitespace=False)
        Service.fill_custom_data(doc, config)
        return doc

    # METHOD THAT ADDS ALL EXTENSION DATA IN SINGLE PASS OVER ALL TOKENS
    @staticmethod
    def fill_custom_data(doc: Doc, config: Config):
        word_pattern = re.compile("\\w+")
        words = []
        paragraphs = []
        cur_paragraph_start = 0
        lemmas = {}
        unique_words = {}
        for token in doc:
            if token.is_space and token.text.count('\n') > 0:
                paragraph = doc[cur_paragraph_start:token.i]
                paragraphs.append(paragraph)
                cur_paragraph_start = token.i
                for t in paragraph:
                    t._.paragraph = paragraph

            token._.is_word = re.match(word_pattern, token.lower_) is not None
            if token._.is_word:
                words.append(token)
                lemma = token.lemma_.lower()
                unique_word = unique_words.get(token.text.lower(), None)
                unique_lemma = lemmas.get(lemma, None)
                if unique_word is None:
                    unique_word = UniqueWord(token.text.lower())
                    unique_words[token.text.lower()] = unique_word
                if unique_lemma is None:
                    unique_lemma = UniqueWord(lemma)
                    lemmas[lemma] = unique_lemma
                unique_word.occourences.append(token)
                unique_lemma.occourences.append(token)
        if len(doc) > cur_paragraph_start:
            paragraph = doc[cur_paragraph_start:]
            paragraphs.append(paragraph)
            for t in paragraph:
                t._.paragraph = paragraph
        doc._.paragraphs = paragraphs
        doc._.words = words
        doc._.unique_words = unique_words
        doc._.lemmas = lemmas
        doc._.total_chars = len(doc.text.replace('\n', ''))
        doc._.total_words = len(words)
        doc._.total_unique_words = len(unique_words)
        doc._.total_pages = round(doc._.total_chars / 1800, 2)
        for sentence in doc.sents:
            words = [word for word in sentence if
                     word._.is_word and len(word.text) >= config.long_sentence_min_word_length]
            if len(words) > config.long_sentence_words_mid:
                if len(words) > config.long_sentence_words_high:
                    sentence._.is_long_sentence = True
                else:
                    sentence._.is_mid_sentence = True
        return doc

    @staticmethod
    def find_multiple_spaces(doc: Doc):
        return re.finditer(PATTERN_MULTIPLE_SPACES, doc.text)

    @staticmethod
    def find_multiple_punctuation(doc: Doc):
        return re.finditer(PATTERN_MULTIPLE_PUNCTUACTION, doc.text)

    @staticmethod
    def find_trailing_spaces(doc: Doc):
        return re.finditer(PATTERN_TRAILING_SPACES, doc.text, re.MULTILINE)

    @staticmethod
    def spellcheck(spellcheck_dictionary: Hunspell, doc: Doc):
        for word in doc._.unique_words.items():
            for token in word[1].occourences:
                if token._.is_word:
                    if not spellcheck_dictionary.spell(token.text):
                        token._.has_grammar_error = True
                        token._.grammar_error_type = GRAMMAR_ERROR_TYPE_MISSPELLED_WORD
        # PATTERN TO FIND ALL ADJECTIVE / DETERMINER / PRONOUN -> NOUN PAIRS
        pattern1 = [
            {
                "RIGHT_ID": "target",
                "RIGHT_ATTRS": {"POS": {"IN": ["NOUN", "DET", "PRON"]}}
            },
            # founded -> subject
            {
                "LEFT_ID": "target",
                "REL_OP": ">",
                "RIGHT_ID": "modifier",
                "RIGHT_ATTRS": {"POS": {"IN": ["ADJ", "DET", "PRON"]}}
            },
        ]

        pattern2 = [
            {
                "RIGHT_ID": "target",
                "RIGHT_ATTRS": {"POS": {"IN": ["NOUN", "DET", "PRON"]}}
            },
            # founded -> subject
            {
                "LEFT_ID": "target",
                "REL_OP": "<",
                "RIGHT_ID": "modifier",
                "RIGHT_ATTRS": {"POS": {"IN": ["ADJ", "DET", "PRON"]}}
            },
        ]

        matcher = DependencyMatcher(doc.vocab)
        matcher.add("PATTERN_1", [pattern1])
        matcher.add("PATTERN_2", [pattern2])
        for match_id, (target, modifier) in matcher(doc):
            target_morph = doc[target].morph.to_dict()
            if not doc[target]._.is_word or not doc[modifier]._.is_word:
                continue
            if (doc[target].pos_ == "DET" or doc[target].pos_ == "PRON") and target_morph.get("Case") != "Nom":
                continue
            # KNOWN MISTAGS
            if doc[target].lower_ in MISSTAGGED_WORDS:
                continue
            if doc[target].pos_ == "NOUN" and (
                    target_morph.get("Gender") != "Masc" or target_morph.get("Case") != "Nom"):
                continue
            modifiers = [doc[modifier]]
            # IF MODIFIER CONJUNTS ANY OTHER MODIFIERS WE NEED TO APPLY SAME RULE FOR ALL
            if doc[modifier].conjuncts is not None:
                for mod in doc[modifier].conjuncts:
                    modifiers.append(mod)
            # IF MODIFIER RELATES TO ANY DET, WE NEED TO APPLY SAME RULE FOR ALL
            for child in doc[modifier].children:
                if child.dep_ == "det":
                    modifiers.append(child)
            for mod in modifiers:
                modifier_morph = mod.morph.to_dict()
                if target_morph.get("Number") == "Plur" and mod.lower_.endswith("ý"):
                    mod._.has_grammar_error = True
                    mod._.grammar_error_type = GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX
                elif target_morph.get("Number") == "Plur" and mod.lower_.endswith("ýsi"):
                    mod._.has_grammar_error = True
                    mod._.grammar_error_type = GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX
                elif target_morph.get("Number") == "Sing" and mod.lower_.endswith("í") and modifier_morph.get(
                        "Degree") == "Pos":
                    mod._.has_grammar_error = True
                    mod._.grammar_error_type = GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX
                elif target_morph.get("Number") == "Sing" and mod.lower_.endswith("ísi") and modifier_morph.get(
                        "Degree") == "Pos":
                    mod._.has_grammar_error = True
                    mod._.grammar_error_type = GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX

    # FUNCTION THAT CALCULATE READABILITY INDICES
    @staticmethod
    def evaluate_readability(doc: Doc):
        if doc._.total_words <= 1:
            return 0
        type_to_token_ratio = doc._.total_words / doc._.total_unique_words
        average_sentence_length = doc._.total_words / sum(1 for _ in doc.sents)
        average_word_length = doc._.total_chars / doc._.total_words / 2
        mistrik_index = READABILITY_MAX_VALUE - ((average_sentence_length * average_word_length) / type_to_token_ratio)
        return READABILITY_MAX_VALUE - max(0.0, round(mistrik_index, 0))

    # METHOD THAT COMPUTES WORD FREQUENCIES
    @staticmethod
    def compute_word_frequencies(doc: Doc, config: Config):
        x = doc._.unique_words
        if config.repeated_words_use_lemma:
            x = doc._.lemmas
        words = {k: v for (k, v) in x.items() if
                 len(k) >= config.repeated_words_min_word_length and len(
                     v.occourences) >= config.repeated_words_min_word_frequency}
        return sorted(words.values(), key=lambda x: len(x.occourences), reverse=True)

    # METHOD THAT EVALUATES CLOSE WORDS
    @staticmethod
    def evaluate_close_words(doc: Doc, config: Config):
        close_words = {}
        x = doc._.unique_words
        if config.close_words_use_lemma:
            x = doc._.lemmas
        words_nlp = {k: v for (k, v) in x.items() if
                     len(k) >= config.close_words_min_word_length}
        for key, unique_word in words_nlp.items():
            # IF WORD DOES NOT OCCOUR ENOUGH TIMES WE DONT NEED TO CHECK IF ITS OCCOURENCES ARE CLOSE
            if len(unique_word.occourences) < config.close_words_min_frequency + 1:
                continue
            for idx, word_occource in enumerate(unique_word.occourences):
                repetitions = []
                for possible_repetition in unique_word.occourences[idx + 1:len(unique_word.occourences) + 1]:
                    if possible_repetition.i - word_occource.i <= config.close_words_min_distance_between_words:
                        repetitions.append(word_occource)
                        repetitions.append(possible_repetition)
                    else:
                        break
                if len(repetitions) > config.close_words_min_frequency:
                    if key not in close_words:
                        close_words[key] = set()
                    close_words[key].update(repetitions)
        return dict(sorted(close_words.items(), key=lambda item: len(item[1]), reverse=True))

    # METHOD THAT REMOVES ACCENTS FROM STRING
    @staticmethod
    def remove_accents(text):
        nfkd_form = unicodedata.normalize('NFD', text)
        return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

    @staticmethod
    def import_document(file_path):
        if file_path.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        extra_args = (
            '--wrap=none',
        )
        return pypandoc.convert_file(file_path, 'plain', extra_args=extra_args)
