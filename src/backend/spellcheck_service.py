import json
import os

from spacy.matcher import DependencyMatcher

from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD, NON_LITERAL_WORDS, \
    GRAMMAR_ERROR_NON_LITERAL_WORD, GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_YSI_SUFFIX, \
    GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX, GRAMMAR_ERROR_TYPE_WRONG_ISI_SUFFIX, GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR, \
    GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING, GRAMMAR_ERROR_Z_INSTEAD_OF_S, GRAMMAR_ERROR_S_INSTEAD_OF_Z, \
    GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO
from src.const.spellcheck_dep_patterns import TYPE_PEKNY_PATTERNS, SVOJ_MOJ_TVOJ_PATTERNS, ZZO_INSTEAD_OF_SSO_PATTERNS, \
    SSO_INSTEAD_OF_ZZO_PATTERNS, CHAPEM_TO_TOMU_PATTERNS
from src.utils import Utils

with open(Utils.resource_path(os.path.join('data_files', 'misstagged_words.json')), 'r', encoding='utf-8') as file:
    EXCEPTIONS = json.load(file)

class SpellcheckService:

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
            for token in word[1].occourences:
                if token._.is_word:
                    if not spellcheck_dictionary.spell(token.text):
                        token._.has_grammar_error = True
                        token._.grammar_error_type = GRAMMAR_ERROR_TYPE_MISSPELLED_WORD
                    if token.lower_ in NON_LITERAL_WORDS:
                        token._.has_grammar_error = True
                        token._.grammar_error_type = GRAMMAR_ERROR_NON_LITERAL_WORD

    @staticmethod
    def check_nominative_plurar_adj(doc):
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

    @staticmethod
    def check_possesive_pronouns(doc):
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

    @staticmethod
    def check_correct_adpositions(doc):
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
        matcher = DependencyMatcher(doc.vocab)
        matcher.add("CHAPEM_TO_TOMU_PATTERNS", CHAPEM_TO_TOMU_PATTERNS)
        for match_id, (verb, pron) in matcher(doc):
            pron_token = doc[pron]
            if pron_token.lower_ == "tomu":
                pron_token._.has_grammar_error = True
                pron_token._.grammar_error_type = GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO
