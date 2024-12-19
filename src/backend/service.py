import json
import os
import re
import shutil
import string
import sys
import tarfile
import unicodedata
import urllib
import zipfile

import fsspec
import pypandoc
import spacy
from hunspell import Hunspell
from pythes import PyThes
from spacy.lang.char_classes import LIST_ELLIPSES, LIST_ICONS, ALPHA_LOWER, ALPHA_UPPER, CONCAT_QUOTES, ALPHA
from spacy.matcher import DependencyMatcher
from spacy.tokenizer import Tokenizer
from spacy.tokens import Doc, Token, Span
from spacy.util import compile_infix_regex

from src.backend.morphodita_tagger_morphologizer_lemmatizer import MORPHODITA_COMPONENT_FACTORY_NAME, \
    MORPHODITA_RESET_SENTENCES_COMPONENT
from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD, GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX, \
    GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX, \
    NON_LITERAL_WORDS, GRAMMAR_ERROR_NON_LITERAL_WORD, GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO, \
    GRAMMAR_ERROR_S_INSTEAD_OF_Z, GRAMMAR_ERROR_Z_INSTEAD_OF_S, GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR, \
    GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING
from src.const.paths import DATA_DIRECTORY, SPACY_MODELS_DIR, SK_SPACY_MODEL_DIR, DICTIONARY_DIR, SK_DICTIONARY_DIR, \
    SK_SPELL_DICTIONARY_DIR, CURRENT_SK_SPACY_MODEL_DIR, DICTIONARY_DIR_BACKUP, SK_MORPHODITA_MODEL_DIR, \
    SK_MORPHODITA_TAGGER, MORPHODITA_MODELS_DIR
from src.const.spellcheck_dep_patterns import TYPE_PEKNY_PATTERNS, CHAPEM_TO_TOMU_PATTERNS, ZZO_INSTEAD_OF_SSO_PATTERNS, \
    SSO_INSTEAD_OF_ZZO_PATTERNS, SVOJ_MOJ_TVOJ_PATTERNS
from src.const.values import SPACY_MODEL_NAME_WITH_VERSION, SPACY_MODEL_LINK, SPACY_MODEL_NAME, READABILITY_MAX_VALUE, \
    MORPHODITA_MODEL_NAME, MORPHODITA_MODEL_LINK
from src.domain.config import Config
from src.domain.metadata import Metadata
from src.domain.unique_word import UniqueWord
from src.utils import Utils

PATTERN_TRAILING_SPACES = r' +$'
PATTERN_MULTIPLE_PUNCTUACTION = r'([!?.,:;]){2,}'
PATTERN_MULTIPLE_SPACES = r' {2,}'
PATTERN_COMPUTER_QUOTE_MARKS = r'["‟]'
PATTERN_DANGLING_QUOTE_MARKS = r'(\s|^)["„“‟](\s|$)'
PATTERN_INCORRECT_LOWER_QUOTE_MARKS = r'\S[„]'
PATTERN_INCORRECT_UPPER_QUOTE_MARKS = r'[“]\S'
PATTERN_UPPER_QUOTE_MARKS_FROM_DIFFERENT_LANGUAGES = r'[‟]'
UPPER_QUOTE_MARK = "“"
with open(Utils.resource_path(os.path.join('data_files', 'misstagged_words.json')), 'r', encoding='utf-8') as file:
    EXCEPTIONS = json.load(file)


# MAIN BACKEND LOGIC IMPLEMENTATION
class Service:
    @staticmethod
    def download_pandoc():
        """Download pandoc if not already installed"""

    try:
        # Check whether it is already installed
        pypandoc.get_pandoc_version()
    except OSError:
        # Pandoc not installed. Let's download it silently.
        with open(os.devnull, 'w') as devnull:
            sys.stdout = devnull
            pypandoc.download_pandoc()
            sys.stdout = sys.__stdout__

        # Hack to delete the downloaded file from the folder,
        # otherwise it could get accidently committed to the repo
        # by other scripts in the repo.
        pf = sys.platform
        if pf.startswith('linux'):
            pf = 'linux'
        url = pypandoc.pandoc_download._get_pandoc_urls()[0][pf]
        filename = url.split('/')[-1]
        os.remove(filename)

    # FUNCTION THAT INTIALIZES NLP ENGINE
    @staticmethod
    def initialize_nlp():
        # noinspection PyBroadException
        try:
            old_model_exists = False
            # INITIALIZE NLP ENGINE
            spacy.util.set_data_path = Utils.resource_path('lib/site-packages/spacy/data')
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
                with urllib.request.urlopen(MORPHODITA_MODEL_LINK) as response, open(archive_file_name, 'wb') as out_file:
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
            nlp.tokenizer = Tokenizer(nlp.vocab, prefix_search=nlp.tokenizer.prefix_search,
                                      suffix_search=nlp.tokenizer.suffix_search,
                                      infix_finditer=infix_re.finditer,
                                      token_match=nlp.tokenizer.token_match,
                                      rules=nlp.Defaults.tokenizer_exceptions)
            nlp.add_pipe('sentencizer', after='trainable_lemmatizer')
            nlp.add_pipe(
                MORPHODITA_COMPONENT_FACTORY_NAME,
                name='morphodita_tagger_morphologizer_lemmatizer',
                after='sentencizer',
                config={"tagger_path": SK_MORPHODITA_TAGGER}
            )
            nlp.add_pipe(MORPHODITA_RESET_SENTENCES_COMPONENT, after='morphodita_tagger_morphologizer_lemmatizer')
            nlp.remove_pipe('tagger')
            nlp.remove_pipe('morphologizer')
            nlp.remove_pipe('trainable_lemmatizer')
            print(nlp.pipe_names)
            # SPACY EXTENSIONS
            Token.set_extension("is_word", default=False, force=True)
            Token.set_extension("word_index", default=None, force=True)
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
        except Exception as e:
            print(e)
            print("Unable to retrieve data. Please check your internet connection.")
            return None

    # FUNCTION FOR UPGRADING DICTIONARIES
    @staticmethod
    def upgrade_dictionaries(github_token: string = None,
                             github_user: string = None):
        if os.path.isdir(DICTIONARY_DIR):
            Service.cleanup_old_dictionaries()
            os.rename(DICTIONARY_DIR, DICTIONARY_DIR_BACKUP)
        dictionaries = Service.initialize_dictionaries(github_token, github_user)
        if dictionaries["spellcheck"] is not None and dictionaries["thesaurus"] is not None:
            if os.path.isdir(DICTIONARY_DIR_BACKUP):
                shutil.rmtree(DICTIONARY_DIR_BACKUP)
            return dictionaries
        else:
            os.rename(DICTIONARY_DIR_BACKUP, DICTIONARY_DIR)
            Service.cleanup_old_dictionaries()
            return None

    @staticmethod
    def cleanup_old_dictionaries():
        if os.path.isdir(DICTIONARY_DIR_BACKUP):
            shutil.rmtree(DICTIONARY_DIR_BACKUP)

    # FUNCTION THAT INTIALIZES NLP DICTIONARIES
    @staticmethod
    def initialize_dictionaries(github_token=None, github_user=None):
        # noinspection PyBroadException
        try:
            if not os.path.isdir(DICTIONARY_DIR):
                os.mkdir(DICTIONARY_DIR)
            if not os.path.isdir(SK_DICTIONARY_DIR):
                os.mkdir(SK_DICTIONARY_DIR)
                fs = fsspec.filesystem("github", org="LibreOffice", repo="dictionaries", token=github_token,
                                       username=github_user)
                fs.get(fs.ls("sk_SK"), SK_DICTIONARY_DIR, recursive=True)
                fs = fsspec.filesystem("github", org="sk-spell", repo="hunspell-sk", token=github_token,
                                       username=github_user)
                fs.get(fs.ls("/"), SK_SPELL_DICTIONARY_DIR, recursive=True)
            return {
                "spellcheck": Hunspell('sk_SK', hunspell_data_dir=SK_SPELL_DICTIONARY_DIR),
                "thesaurus": PyThes(os.path.join(SK_DICTIONARY_DIR, "th_sk_SK_v2.dat"))
            }
        except Exception as e:
            print(e)
            print("Unable to retrieve data. Please check your internet connection.")
            if os.path.isdir(DICTIONARY_DIR):
                shutil.rmtree(DICTIONARY_DIR)
            return {
                "spellcheck": None,
                "thesaurus": None
            }

    # FUNCTION THAT LOADS CONFIG FROM FILE
    @staticmethod
    def load_config(path: string):
        if os.path.exists(path):
            with open(path, 'r') as file:
                c = json.load(file)
                return Config(c)
        else:
            return Config()

    # FUNCTION THAT LOADS EDITOR METADATA FROM FILE
    @staticmethod
    def load_metadata(path: string):
        if os.path.exists(path):
            with open(path, 'r') as file:
                metadata = json.load(file)
                return Metadata(metadata)
        else:
            return Metadata()

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save_config(c: Config, path: string):
        with open(path, 'w') as file:
            json.dump(c.to_dict(), file, indent=4)

    # FUNCTION THAT SAVES METADATA TO FILE
    @staticmethod
    def save_metadata(metadata: Metadata, path: string):
        with open(path, 'w') as file:
            json.dump(metadata.to_dict(), file, indent=4)

    # METHOD THAT RUNS FULL NLP
    @staticmethod
    def full_nlp(text, nlp: spacy, batch_size, config: Config):
        doc = Doc.from_docs(list(nlp.pipe([text], batch_size=batch_size)), nlp)
        Service.fill_custom_data(doc, config)
        return doc

    @staticmethod
    def normalize_text(text):
        clrf = re.compile("\r\n")
        corrected_text = re.sub(clrf, "\n", text)
        return corrected_text

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
        word_index = 0
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
                token._.word_index = word_index
                word_index += 1
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
                     word._.is_word and len(word.text) >= config.analysis_settings.long_sentence_min_word_length]
            if len(words) > config.analysis_settings.long_sentence_words_mid:
                if len(words) > config.analysis_settings.long_sentence_words_high:
                    sentence._.is_long_sentence = True
                else:
                    sentence._.is_mid_sentence = True
        return doc

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

    @staticmethod
    def spellcheck(spellcheck_dictionary: Hunspell, doc: Doc):
        for word in doc._.unique_words.items():
            for token in word[1].occourences:
                if token._.is_word:
                    if not spellcheck_dictionary.spell(token.text):
                        token._.has_grammar_error = True
                        token._.grammar_error_type = GRAMMAR_ERROR_TYPE_MISSPELLED_WORD
                    if token.lower_ in NON_LITERAL_WORDS:
                        token._.has_grammar_error = True
                        token._.grammar_error_type = GRAMMAR_ERROR_NON_LITERAL_WORD
        matcher = DependencyMatcher(doc.vocab)
        matcher.add("TYPE_PEKNY_PATTERNS", TYPE_PEKNY_PATTERNS)
        for match_id, (target, modifier) in matcher(doc):
            target_morph = doc[target].morph.to_dict()
            if not doc[target]._.is_word or not doc[modifier]._.is_word:
                continue
            if (doc[target].pos_ == "DET" or doc[target].pos_ == "PRON") and target_morph.get("Case") != "Nom":
                continue
            # KNOWN MISTAGS
            if doc[target].lower_ in EXCEPTIONS or doc[modifier].lower_ in EXCEPTIONS:
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

        matcher = DependencyMatcher(doc.vocab)
        matcher.add("CHAPEM_TO_TOMU_PATTERNS", CHAPEM_TO_TOMU_PATTERNS)
        for match_id, (verb, pron) in matcher(doc):
            pron_token = doc[pron]
            if pron_token.lower_ == "tomu":
                pron_token._.has_grammar_error = True
                pron_token._.grammar_error_type = GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO
        matcher = DependencyMatcher(doc.vocab)
        matcher.add("ZZO_INSTEAD_OF_SSO_PATTERNS", ZZO_INSTEAD_OF_SSO_PATTERNS)
        for match_id, (preposition, noun) in matcher(doc):
            preposition_token = doc[preposition]
            preposition_token._.has_grammar_error = True
            preposition_token._.grammar_error_type = GRAMMAR_ERROR_Z_INSTEAD_OF_S
        matcher = DependencyMatcher(doc.vocab)
        matcher.add("SSO_INSTEAD_OF_ZZO_PATTERNS", SSO_INSTEAD_OF_ZZO_PATTERNS)
        for match_id, (preposition, noun) in matcher(doc):
            preposition_token = doc[preposition]
            preposition_token._.has_grammar_error = True
            preposition_token._.grammar_error_type = GRAMMAR_ERROR_S_INSTEAD_OF_Z
        matcher = DependencyMatcher(doc.vocab)
        matcher.add("SVOJ_MOJ_TVOJ_PATTERNS", SVOJ_MOJ_TVOJ_PATTERNS)
        for match_id, (pronoun, noun) in matcher(doc):
            pronoun_token = doc[pronoun]
            noun_token = doc[noun]
            case_marking = None
            for left_token in noun_token.lefts:
                if left_token != pronoun_token and left_token.dep_ == "case":
                    case_marking = left_token
            pronoun_morph = pronoun_token.morph.to_dict()
            noun_morph = noun_token.morph.to_dict()
            # LETS CHECK RELATION BETWEEN PRONOUN AND NOUN
            if ((pronoun_morph.get("Case") == "Ins") and
                    (noun_morph.get("Case") == "Dat" or noun_morph.get("Number") == "Plur")):
                pronoun_token._.has_grammar_error = True
                pronoun_token._.grammar_error_type = GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR
            elif pronoun_morph.get("Case") == "Dat" and noun_morph.get("Case") == "Ins":
                pronoun_token._.has_grammar_error = True
                pronoun_token._.grammar_error_type = GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING
            elif case_marking is not None:
                # RELATION BETWEEN PRONOUN AND NOUN LOOKS GOOD, BUT WE ALSO HAVE CASE MARKING DEP AVAILABLE
                # LET'S DOUBLECHECK, NOUN WITH PRONOUN MAY HAVE BEEN MISSTAGGED
                case_marking_morph = case_marking.morph.to_dict()
                if (pronoun_morph.get("Case") == "Ins" and
                        (case_marking_morph.get("Case") == "Dat" or case_marking_morph.get("Number") == "Plur")):
                    pronoun_token._.has_grammar_error = True
                    pronoun_token._.grammar_error_type = GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR
                elif pronoun_morph.get("Case") == "Dat" and case_marking_morph.get("Case") == "Ins":
                    pronoun_token._.has_grammar_error = True
                    pronoun_token._.grammar_error_type = GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING

    # FUNCTION THAT CALCULATE READABILITY INDICES
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
            f'--lua-filter={Utils.resource_path(os.path.join("data_files", "fix_odt_blockquotes.lua"))}'
        )
        text = pypandoc.convert_file(file_path, 'plain', extra_args=extra_args)
        return Service.normalize_text(os.linesep.join([s for s in text.splitlines() if s]))

    @staticmethod
    def export_sentences(path, doc, blank_line_between_sents):
        text = ""
        cur_sent = ""
        for sent in doc.sents:
            # STRIP NEWLINES
            sent_text = sent.text.replace("\r\n", "").replace("\n", "")
            if len(sent_text) > 1:
                # ADD CURRENT SENTENCE TO TEXT
                if len(cur_sent) > 0:
                    text += f"{cur_sent}\n"
                    if blank_line_between_sents:
                        text += '\n'
                    cur_sent = ""
                if len(sent_text) > 0:
                    cur_sent = sent_text
            elif len(sent_text) > 0:
                # MERGE TO PREVIOUS SENTENCE
                cur_sent += sent_text
        # ADD LAST SENTENCE TO TEXT
        if len(cur_sent) > 0:
            text += f"{cur_sent}\n"
            if blank_line_between_sents:
                text += '\n'
        with open(path, 'w', encoding='utf-8') as file:
            file.write(text)
