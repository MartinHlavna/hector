import json
import os
import shutil
import string

import fsspec
from hunspell import Hunspell
from pythes import PyThes
from spacy.matcher import DependencyMatcher

from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD, NON_LITERAL_WORDS, \
    GRAMMAR_ERROR_NON_LITERAL_WORD, GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX, \
    GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX, GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR, \
    GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING, GRAMMAR_ERROR_Z_INSTEAD_OF_S, GRAMMAR_ERROR_S_INSTEAD_OF_Z, \
    GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO
from src.const.paths import DICTIONARY_DIR, DICTIONARY_DIR_BACKUP, SK_DICTIONARY_DIR, SK_SPELL_DICTIONARY_DIR
from src.const.spellcheck_dep_patterns import TYPE_PEKNY_PATTERNS, SVOJ_MOJ_TVOJ_PATTERNS, ZZO_INSTEAD_OF_SSO_PATTERNS, \
    SSO_INSTEAD_OF_ZZO_PATTERNS, CHAPEM_TO_TOMU_PATTERNS
from src.utils import Utils

with open(Utils.resource_path(os.path.join('data_files', 'misstagged_words.json')), 'r', encoding='utf-8') as file:
    EXCEPTIONS = json.load(file)


class SpellcheckService:
    # FUNCTION FOR UPGRADING DICTIONARIES
    @staticmethod
    def upgrade_dictionaries(github_token: string = None,
                             github_user: string = None):
        if os.path.isdir(DICTIONARY_DIR):
            SpellcheckService.remove_dictionaries_backup()
            os.rename(DICTIONARY_DIR, DICTIONARY_DIR_BACKUP)
        dictionaries = SpellcheckService.initialize_dictionaries(github_token, github_user)
        if dictionaries["spellcheck"] is not None and dictionaries["thesaurus"] is not None:
            if os.path.isdir(DICTIONARY_DIR_BACKUP):
                shutil.rmtree(DICTIONARY_DIR_BACKUP)
            return dictionaries
        else:
            os.rename(DICTIONARY_DIR_BACKUP, DICTIONARY_DIR)
            SpellcheckService.remove_dictionaries_backup()
            return None

    # CLEANUP BACKUP DICTIONARY DIR
    @staticmethod
    def remove_dictionaries_backup():
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

    @staticmethod
    def spellcheck(doc, spellcheck_dictionary):
        SpellcheckService.check_basic_spelling(doc, spellcheck_dictionary)
        SpellcheckService.check_nominative_plurar_adj(doc)
        SpellcheckService.check_chapem_tomu_phrase(doc)
        SpellcheckService.check_correct_adpositions(doc)
        SpellcheckService.check_possesive_pronouns(doc)

    @staticmethod
    def check_basic_spelling(doc, spellcheck_dictionary):
        for word in doc._.unique_words.items():
            # CACHE TO OPTIMIZE CALLS TO HUNSPELL
            # WE NEED TO ITERATE OVER ALL OCOURENCES, BECAUSE THAY CAN BE SPELLED DIFFERENTLY
            # BUT WHEN WE ENCOUNTER SAME SEPLLING AGAIN, WE CAN REUSE RESULT
            spell_cache = {}
            for token in word[1].occourences:
                spell_result = None
                if token.text in spell_cache:
                    spell_result = spell_cache[token.text]
                else:
                    spell_result = spellcheck_dictionary.spell(token.text)
                if not spell_result:
                    # IF WORD IS NOT SPELLED CORRECTLY WE SET GRAMMAR ERROR FLAG AND TYPE OF ERROR
                    token._.has_grammar_error = True
                    token._.grammar_error_type = GRAMMAR_ERROR_TYPE_MISSPELLED_WORD
                if token.lower_ in NON_LITERAL_WORDS:
                    # SOME WORDS NEEDS SPECIAl HANDLING
                    token._.has_grammar_error = True
                    token._.grammar_error_type = GRAMMAR_ERROR_NON_LITERAL_WORD

    # SUPRESSED C901 Method too Complex. SOLVING THIS WOULD MAKE CODE HARDER TO READ
    @staticmethod
    def check_nominative_plurar_adj(doc):  # noqa: C901
        # SOME ADJECTIVES CASED BY TYPE PEKNY CAN HAVE BOTH Y AND I DEPENDING ON NOUN THERE ARE USED WITH
        # THIS ALSO EXTENDS ON SOME PRONOUNS
        # WE USE DEPENDENCY MATCHER TO ROUGHLY FIND POSSIBLE ERRORS
        matcher = DependencyMatcher(doc.vocab)
        matcher.add("TYPE_PEKNY_PATTERNS", TYPE_PEKNY_PATTERNS)
        for match_id, (target, modifier) in matcher(doc):
            target_token = doc[target]
            modifier_token = doc[modifier]
            target_morph = doc[target].morph.to_dict()
            # WE USE SOME STOP CONDITIONS, TO PREVENT FALSE POSITIVE
            if not target_token._.is_word or not modifier_token._.is_word:
                # IF FOUND TOKENS ARE NOT WORDS, SKIP
                continue
            if target_token.pos_ in {"DET", "PRON"} and target_morph.get("Case") != "Nom":
                # IF TARGET TOKEN IS DETERMINER OR PRONOUN IN NOMINATIVE CASE, SKIP
                continue
            if target_token.lower_ in EXCEPTIONS or modifier_token.lower_ in EXCEPTIONS:
                # IF TARGET OR MODIFIER ARE IN LIST OF EXCEPTIONS, SKIP
                continue
            if target_token.pos_ == "NOUN" and (target_morph.get("Gender") != "Masc" or
                                                target_morph.get("Case") != "Nom"):
                # IF TARGET IS NOUN IN Masculine GENDER, OR IT IS NOMINATIVE CASE, SKIP
                continue
            # EXTEND CHECK TO CONJUCTED MODIFIERS
            modifiers = [modifier_token]
            modifiers.extend(modifier_token.conjuncts or [])
            modifiers.extend(child for child in modifier_token.children if child.dep_ == "det")
            for mod in modifiers:
                modifier_morph = mod.morph.to_dict()
                # PERFORM CHECKING BASED ON MORPHS
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

    @staticmethod
    def check_possesive_pronouns(doc):
        # CHECK IF POSSESIVE PRONOUNS ARE USED IN CORRECT FORM BASED ON CONTEXT
        # WE USE DEPENDENCY MATCHER TO FIND POSSIBLE ERRORS AND THEN PERFORM CHECKING
        matcher = DependencyMatcher(doc.vocab)
        matcher.add("SVOJ_MOJ_TVOJ_PATTERNS", SVOJ_MOJ_TVOJ_PATTERNS)
        for match_id, (pronoun, noun) in matcher(doc):
            pronoun_token = doc[pronoun]
            noun_token = doc[noun]
            # FIND CASE MARKING TOKEN, IF AVAILABLE
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

    @staticmethod
    def check_correct_adpositions(doc):
        # CHECK IF ADPOSIONS S/SO AND Z/ZO ARE NOT INTERCHANGED
        # WE USE DEPENDENCY MATCHER TO PERFORM CHECK
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
        return matcher

    @staticmethod
    def check_chapem_tomu_phrase(doc):
        # CHECK IF PHRASE "CHAPEM TO" IS NOT IN INCORRECT FORM "CHAPEM TOMU"
        # WE USE DEPENDENCY MATCHER TO FIND POSSIBLE ERROR AND THEN PERFORM CHEKING
        matcher = DependencyMatcher(doc.vocab)
        matcher.add("CHAPEM_TO_TOMU_PATTERNS", CHAPEM_TO_TOMU_PATTERNS)
        for match_id, (verb, pron) in matcher(doc):
            pron_token = doc[pron]
            if pron_token.lower_ == "tomu":
                pron_token._.has_grammar_error = True
                pron_token._.grammar_error_type = GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO
