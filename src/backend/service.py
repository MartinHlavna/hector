import json
import os
import re
import string
import unicodedata

from enchant import Dict
from spacy.matcher import DependencyMatcher
from spacy.tokens import Doc

from src.backend.unique_word import UniqueWord
from src.const.grammar_error_types import *

# DEFAULT CONFIGURATION VALUES
# SANE DEFAULTS FOR CREATIVE WRITTING
default_config = {
    # MINIMAL LENGTH OF WORD FOR IT TO APPEAR IN FREQUENT WORDS SECTION
    "repeated_words_min_word_length": 3,
    # MINIMAL NUMBER OF WORD REPETITIONS FOR IT TO APPEAR IN REPEATED WORDS SECTION
    "repeated_words_min_word_frequency": 2,
    # SENTENCE IS CONSIDERED MID LONG IF IT HAS MORE WORDS THAN THIS CONFIG
    "long_sentence_words_mid": 8,
    # SENTENCE IS CONSIDERED HIGH LONG IF IT HAS MORE WORDS THAN THIS CONFIG
    "long_sentence_words_high": 16,
    # WORD IS COUNTED TO SENTENCE LENGTH ONLY IF IT HAS MORE MORE CHARS THAN THIS CONFIG
    "long_sentence_min_word_length": 5,
    # MINIMAL LENGTH OF WORD FOR IT TO BE HIGHLIGHTED IF VIA CLOSE_WORDS FUNCTIONALITY
    "close_words_min_word_length": 3,
    # MINIMAL DISTANCE BETWEEN REPEATED WORDS
    "close_words_min_distance_between_words": 100,
    # MINIMAL FREQUENCE FOR REPEATED WORD TO BE HIGHLIGHTED
    "close_words_min_frequency": 3,
    # ENABLE FREQUENT WORDS SIDE PANEL
    "enable_frequent_words": True,
    # ENADBLE HIGHLIGHTING OF LONG SENTENCES
    "enable_long_sentences": True,
    # ENABLE HIGHLIGHTING OF REPEATED SPACES
    "enable_multiple_spaces": True,
    # ENABLE HIGHLIGHTING OF REPEATED PUNCTUATION  (eg. !! ?? ..)
    "enable_multiple_punctuation": True,
    # ENABLE HIGHLIGHTING OF TRAILING SPACES AT THE END OF PARAGRAPH
    "enable_trailing_spaces": True,
    # ENABLE HIGHLIGHTING OF WORD THAT ARE REPEATED AT SAME SPOTS
    "enable_close_words": True,
}


# MAIN BACKEND LOGIC IMPLEMENTATION
class Service:
    # FUNCTION THAT LOADS CONFIG FROM FILE
    @staticmethod
    def load_config(path: string):
        if os.path.exists(path):
            with open(path, 'r') as file:
                c = json.load(file)
                # CHECK IF ALL CONFIG_KEYS ARE PRESENT
                # PROVIDE MISSING KEYS FROM DEFAULTS
                for key, value in default_config.items():
                    if key not in c:
                        c[key] = value
                return c
        else:
            return default_config

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save_config(c, path: string):
        with open(path, 'w') as file:
            json.dump(c, file, indent=4)

    # FUNCTION THAT CALCULATE READABILITY INDICES
    @staticmethod
    def evaluate_readability(doc: Doc):
        if doc._.total_words <= 1:
            return 0
        type_to_token_ratio = doc._.total_words / doc._.total_unique_words
        average_sentence_length = doc._.total_words / sum(1 for _ in doc.sents)
        average_word_length = doc._.total_chars / doc._.total_words / 2
        mistrik_index = 50 - ((average_sentence_length * average_word_length) / type_to_token_ratio)
        return 50 - max(0.0, round(mistrik_index, 0))

    # METHOD THAT REMOVES ACCENTS FROM STRING
    @staticmethod
    def remove_accents(text):
        nfkd_form = unicodedata.normalize('NFD', text)
        return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

    # METHOD THAT ADDS ALL EXTENSION DATA IN SINGLE PASS OVER ALL TOKENS
    @staticmethod
    def fill_custom_data(doc: Doc):
        word_pattern = re.compile("\\w+")
        words = []
        unique_words = {}
        for token in doc:
            token._.is_word = re.match(word_pattern, token.lower_) is not None
            if token._.is_word:
                words.append(token)
                unique_word = unique_words.get(token.text.lower(), None)
                if unique_word is None:
                    unique_word = UniqueWord(token.text.lower())
                    unique_words[token.text.lower()] = unique_word
                unique_word.occourences.append(token)
        doc._.words = words
        doc._.unique_words = unique_words
        doc._.total_chars = len(doc.text)
        doc._.total_words = len(words)
        doc._.total_unique_words = len(unique_words)
        doc._.total_pages = round(doc._.total_chars / 1800, 2)
        return doc

    @staticmethod
    def spellcheck(spellcheck_dictionary: Dict, doc: Doc):
        for word in doc._.unique_words.items():
            for token in word[1].occourences:
                if token._.is_word:
                    if not spellcheck_dictionary.check(token.text):
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
            # TODO: Maybe we can move these mistagged word to separate data files
            if doc[target].lower_ == "ony":
                continue
            if doc[target].pos_ == "NOUN" and (target_morph.get("Gender") != "Masc" or target_morph.get("Case") != "Nom"):
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
                print(mod, doc[target])
                if target_morph.get("Number") == "Plur" and mod.lower_.endswith("ý"):
                    mod._.has_grammar_error = True
                    mod._.grammar_error_type = GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX
                elif target_morph.get("Number") == "Plur" and mod.lower_.endswith("ýsi"):
                    mod._.has_grammar_error = True
                    mod._.grammar_error_type = GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX
                elif target_morph.get("Number") == "Sing" and mod.lower_.endswith("í") and modifier_morph.get("Degree") == "Pos":
                    mod._.has_grammar_error = True
                    mod._.grammar_error_type = GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX
                elif target_morph.get("Number") == "Sing" and mod.lower_.endswith("ísi") and modifier_morph.get("Degree") == "Pos":
                    mod._.has_grammar_error = True
                    mod._.grammar_error_type = GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX
