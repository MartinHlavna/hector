import os
import platform
import re
import shutil

import pytest
from hunspell import Hunspell
from pythes import PyThes
from spacy.lang.sk import Slovak
from spacy.tokens import Doc

from src.backend.run_context import RunContext
from src.backend.service.config_service import ConfigService
from src.backend.service.export_service import ExportService
from src.backend.service.import_service import ImportService
from src.backend.service.metadata_service import MetadataService
from src.backend.service.nlp_service import NlpService
from src.backend.service.project_service import ProjectService
from src.backend.service.spellcheck_service import SpellcheckService
from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD, GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX, \
    GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX, NON_LITERAL_WORDS, GRAMMAR_ERROR_NON_LITERAL_WORD, \
    GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO, GRAMMAR_ERROR_Z_INSTEAD_OF_S, GRAMMAR_ERROR_S_INSTEAD_OF_Z, \
    GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR, GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING
from src.const.paths import DATA_DIRECTORY, CONFIG_FILE_PATH, METADATA_FILE_PATH
from src.const.tags import BOLD_TAG_NAME
from src.const.values import NLP_BATCH_SIZE
from src.domain.config import Config
from src.domain.htext_file import HTextFile, HTextFormattingTag
from src.domain.metadata import Metadata
from src.domain.project import Project, ProjectItemType, ProjectItem, DirectoryProjectItem
from src.utils import Utils
from test_utils import TestUtils

SENTENCES_FILE = "sentences.txt"

TEST_TEXT_1 = 'Toto je testovací text.\nToto je veta.'
TEST_TEXT_2 = 'Toto  je testovací text. Toto      je veta. Haló! A toto je čo?! '
TEST_TEXT_3 = 'Afto išlo po ceste. Tamtý chlapci sú pekný.'
TEST_TEXT_4 = """
Ako šlo vajce na vandrovku? – Nuž urobilo si aj ono, ako si každý robieva:
Kotúľ! zakotúľalo sa a pustilo sa, kadiaľ mu bolo ľahšie, kadiaľ by
nezavadilo do tuhšieho od seba. Jednak stalo sa to ešte za starých časov,
nuž veľa ani neopytujte sa, ako to mohlo byť; dosť, čo je o tom rozprávka.
Za starých časov išlo teda Vajce na vandrovku a stretlo tam raka.
„Kde ty ideš?“ rečie mu ono.
„A tyže kde?“ rečie mu on.
„Ja idem na vandrovku!“
„A veď ani ja nechcem byť horší od teba; pôjdem i ja!“
Už teda boli dvaja a bolo im hneď smelšie. Idú, idú; stretnú kačicu.
„Kde ty ideš?“ opytuje sa vajce.
„A vyže kde?“ rečie táto.
„My ideme na vandrovku; poď, budeme traja.“
Kačica pristala; už boli traja. Všetko dobré do tretice!
Idú, idú; stretnú moriaka.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie tento.
„My ideme na vandrovku; poď do kamarátstva!“
Moriak pristal; boli štyria.
Idú, idú; stretnú koňa.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie kôň.
„My ideme na vandrovku; poď, budeme piati.“
Kôň šiel; bolo ich, koľko na ruke prstov.
Idú, idú; stretnú vola.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie tento.
„My ideme na vandrovku; poď, väčšia hŕbka pýta viac.“
Vôl pristal; už boli šiesti.
Idú, idú pekne v hŕbke; stretnú ešte kohúta.
„Kde ty ideš?“ rečie vajce.
"""
TEST_TEXT_4_CHANGE_AT_START = """
Uff, ako šlo vajce na vandrovku? – Nuž urobilo si aj ono, ako si každý robieva:
Kotúľ! zakotúľalo sa a pustilo sa, kadiaľ mu bolo ľahšie, kadiaľ by
nezavadilo do tuhšieho od seba. Jednak stalo sa to ešte za starých časov,
nuž veľa ani neopytujte sa, ako to mohlo byť; dosť, čo je o tom rozprávka.
Za starých časov išlo teda Vajce na vandrovku a stretlo tam raka.
„Kde ty ideš?“ rečie mu ono.
„A tyže kde?“ rečie mu on.
„Ja idem na vandrovku!“
„A veď ani ja nechcem byť horší od teba; pôjdem i ja!“
Už teda boli dvaja a bolo im hneď smelšie. Idú, idú; stretnú kačicu.
„Kde ty ideš?“ opytuje sa vajce.
„A vyže kde?“ rečie táto.
„My ideme na vandrovku; poď, budeme traja.“
Kačica pristala; už boli traja. Všetko dobré do tretice!
Idú, idú; stretnú moriaka.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie tento.
„My ideme na vandrovku; poď do kamarátstva!“
Moriak pristal; boli štyria.
Idú, idú; stretnú koňa.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie kôň.
„My ideme na vandrovku; poď, budeme piati.“
Kôň šiel; bolo ich, koľko na ruke prstov.
Idú, idú; stretnú vola.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie tento.
„My ideme na vandrovku; poď, väčšia hŕbka pýta viac.“
Vôl pristal; už boli šiesti.
Idú, idú pekne v hŕbke; stretnú ešte kohúta.
„Kde ty ideš?“ rečie vajce.
"""
TEST_TEXT_4_CHANGE_AT_END = """
Ako šlo vajce na vandrovku? – Nuž urobilo si aj ono, ako si každý robieva:
Kotúľ! zakotúľalo sa a pustilo sa, kadiaľ mu bolo ľahšie, kadiaľ by
nezavadilo do tuhšieho od seba. Jednak stalo sa to ešte za starých časov,
nuž veľa ani neopytujte sa, ako to mohlo byť; dosť, čo je o tom rozprávka.
Za starých časov išlo teda Vajce na vandrovku a stretlo tam raka.
„Kde ty ideš?“ rečie mu ono.
„A tyže kde?“ rečie mu on.
„Ja idem na vandrovku!“
„A veď ani ja nechcem byť horší od teba; pôjdem i ja!“
Už teda boli dvaja a bolo im hneď smelšie. Idú, idú; stretnú kačicu.
„Kde ty ideš?“ opytuje sa vajce.
„A vyže kde?“ rečie táto.
„My ideme na vandrovku; poď, budeme traja.“
Kačica pristala; už boli traja. Všetko dobré do tretice!
Idú, idú; stretnú moriaka.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie tento.
„My ideme na vandrovku; poď do kamarátstva!“
Moriak pristal; boli štyria.
Idú, idú; stretnú koňa.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie kôň.
„My ideme na vandrovku; poď, budeme piati.“
Kôň šiel; bolo ich, koľko na ruke prstov.
Idú, idú; stretnú vola.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie tento.
„My ideme na vandrovku; poď, väčšia hŕbka pýta viac.“
Vôl pristal; už boli šiesti.
Idú, idú pekne v hŕbke; stretnú ešte kohúta.
„Kde ty ideš?“ rečie vajce a okúňa sa.
"""
TEST_TEXT_4_CHANGE_IN_MID = """
Ako šlo vajce na vandrovku? – Nuž urobilo si aj ono, ako si každý robieva:
Kotúľ! zakotúľalo sa a pustilo sa, kadiaľ mu bolo ľahšie, kadiaľ by
nezavadilo do tuhšieho od seba. Jednak stalo sa to ešte za starých časov,
nuž veľa ani neopytujte sa, ako to mohlo byť; dosť, čo je o tom rozprávka.
Za starých časov išlo teda Vajce na vandrovku a stretlo tam raka.
„Kde ty ideš?“ rečie mu ono.
„A tyže kde?“ rečie mu on.
„Ja idem na vandrovku!“
„A veď ani ja nechcem byť horší od teba; pôjdem i ja!“
Už teda boli dvaja a bolo im hneď smelšie. Idú, idú; stretnú kačicu.
„Kde ty ideš?“ opytuje sa vajce.
„A vyže kde?“ rečie táto.
„My ideme na vandrovku; poď, budeme traja.“
Kačica pristala; už boli traja. Všetko dobré do tretice!
Idú, idú; stretnú moriaka.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie tento.
„My ideme na vandrovku; poď do kamarátstva!“
Moriak pristal; boli štyria.
Idú, idú, stále idú; stretnú koňa.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie kôň.
„My ideme na vandrovku; poď, budeme piati.“
Kôň šiel; bolo ich, koľko na ruke prstov.
Idú, idú; stretnú vola.
„Kde ty ideš?“ rečie vajce.
„A vyže kde?“ rečie tento.
„My ideme na vandrovku; poď, väčšia hŕbka pýta viac.“
Vôl pristal; už boli šiesti.
Idú, idú pekne v hŕbke; stretnú ešte kohúta.
„Kde ty ideš?“ rečie vajce.
"""
TEST_TEXT_5 = """
jeden
dva dva
tri tri tri
štyri štyri štyri štyri
päť päť päť päť päť
jeden
dva dva
tri tri tri
štyri štyri štyri štyri
päť päť päť päť päť
"""
TEST_TEXT_6 = "Moja malá palička."
TEST_TEXT_6_NON_ACCENTED = "Moja mala palicka."
TEST_TEXT_QUOTES_1 = "“Ahoj„"
TEST_TEXT_QUOTES_2 = "\"Ahoj\""
TEST_TEXT_QUOTES_3 = "“ Ahoj „"


# TEST CORRECTLY INITIALIZED VARS
def test_initialization(setup_teardown):
    assert isinstance(setup_teardown[0], Slovak)
    assert isinstance(setup_teardown[1], Hunspell)
    assert isinstance(setup_teardown[2], PyThes)


# TEST IF NLP IS WORKING
def test_basic_nlp(setup_teardown):
    nlp = setup_teardown[0]
    doc = NlpService.full_analysis(TEST_TEXT_1, nlp, NLP_BATCH_SIZE, Config())
    assert doc is not None
    assert isinstance(doc, Doc)


# TEST RUN CONTEXT
def test_run_context(setup_teardown):
    nlp = setup_teardown[0]
    ctx1 = RunContext()
    ctx1.nlp = nlp
    ctx2 = RunContext()
    assert ctx1.nlp == nlp
    assert ctx2.nlp == nlp
    assert ctx1 == ctx2


# TEST IF PARTIAL NLP IS WORKING
def test_partial_nlp(setup_teardown):
    nlp = setup_teardown[0]
    original_doc = NlpService.full_analysis(TEST_TEXT_4, nlp, NLP_BATCH_SIZE, Config())
    assert original_doc is not None
    assert isinstance(original_doc, Doc)
    doc1 = NlpService.partial_analysis(TEST_TEXT_4_CHANGE_AT_START, original_doc, nlp, Config(), 6)
    assert doc1 is not None
    assert isinstance(doc1, Doc)
    assert doc1._.total_chars == len(TEST_TEXT_4_CHANGE_AT_START.replace('\n', ''))
    assert doc1.text == Utils.normalize_spaces(TEST_TEXT_4_CHANGE_AT_START)
    doc2 = NlpService.partial_analysis(TEST_TEXT_4_CHANGE_AT_END, original_doc, nlp, Config(),
                                       len(TEST_TEXT_4_CHANGE_AT_END) - 1)
    assert doc2 is not None
    assert isinstance(doc2, Doc)
    assert doc2._.total_chars == len(TEST_TEXT_4_CHANGE_AT_END.replace('\n', ''))
    assert doc2.text == Utils.normalize_spaces(TEST_TEXT_4_CHANGE_AT_END)
    doc3 = NlpService.partial_analysis(TEST_TEXT_4_CHANGE_IN_MID, original_doc, nlp, Config(),
                                       897)
    assert doc3 is not None
    assert isinstance(doc3, Doc)
    assert doc3._.total_chars == len(TEST_TEXT_4_CHANGE_AT_END.replace('\n', ''))
    assert doc3.text == Utils.normalize_spaces(TEST_TEXT_4_CHANGE_IN_MID)


# TEST IF CUSTOM_EXTENSION ARE CORRECTLY FILLES
def test_custom_extenstions(setup_teardown):
    nlp = setup_teardown[0]
    doc = NlpService.full_analysis(TEST_TEXT_1, nlp, NLP_BATCH_SIZE, Config())
    assert doc._.words is not None
    assert len(doc._.words) == 7 and doc._.total_words == 7
    assert len(doc._.unique_words) == 5 and doc._.total_unique_words == 5
    assert len(doc._.lemmas) == 5
    assert len(doc._.paragraphs) == 2
    assert doc._.total_chars == len(TEST_TEXT_1.replace('\n', ''))
    assert 0 < doc._.total_pages < 1


def test_find_multiple_spaces(setup_teardown):
    nlp = setup_teardown[0]
    doc = NlpService.full_analysis(TEST_TEXT_2, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in NlpService.find_multiple_spaces(doc)) == 2


def test_find_multiple_punctuation(setup_teardown):
    nlp = setup_teardown[0]
    doc = NlpService.full_analysis(TEST_TEXT_2, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in NlpService.find_multiple_punctuation(doc)) == 1


def test_quote_marks_corrections(setup_teardown):
    nlp = setup_teardown[0]
    doc = NlpService.full_analysis(TEST_TEXT_QUOTES_1, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in NlpService.find_incorrect_lower_quote_marks(doc)) == 1
    assert sum(1 for _ in NlpService.find_incorrect_upper_quote_marks(doc)) == 1


def test_find_computer_quote_marks(setup_teardown):
    nlp = setup_teardown[0]
    doc = NlpService.full_analysis(TEST_TEXT_QUOTES_2, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in NlpService.find_computer_quote_marks(doc)) == 2


def test_find_dangling_quote_marks(setup_teardown):
    nlp = setup_teardown[0]
    doc = NlpService.full_analysis(TEST_TEXT_QUOTES_3, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in NlpService.find_dangling_quote_marks(doc)) == 2


def test_readability(setup_teardown):
    nlp = setup_teardown[0]
    doc = NlpService.full_analysis(TEST_TEXT_4, nlp, NLP_BATCH_SIZE, Config())
    assert NlpService.compute_readability(doc) == 8


def test_word_frequencies(setup_teardown):
    nlp = setup_teardown[0]
    c = Config()
    c.analysis_settings.repeated_words_min_word_frequency = 1
    doc = NlpService.full_analysis(TEST_TEXT_5, nlp, NLP_BATCH_SIZE, c)
    word_frequencies = NlpService.compute_word_frequencies(doc, c)
    assert len(word_frequencies) == 5
    assert word_frequencies[0].text == "päť" and len(word_frequencies[0].occourences) == 10
    assert word_frequencies[1].text == "štyri" and len(word_frequencies[1].occourences) == 8
    assert word_frequencies[2].text == "tri" and len(word_frequencies[2].occourences) == 6
    assert word_frequencies[3].text == "dva" and len(word_frequencies[3].occourences) == 4
    assert word_frequencies[4].text == "jeden" and len(word_frequencies[4].occourences) == 2


def test_evaluate_close_words(setup_teardown):
    nlp = setup_teardown[0]
    c = Config()
    c.analysis_settings.close_words_min_frequency = 1
    doc = NlpService.full_analysis(TEST_TEXT_1, nlp, NLP_BATCH_SIZE, c)
    close_words = NlpService.evaluate_close_words(doc, c)
    # ONE REPEATED WORD
    assert len(close_words) == 1
    assert "toto" in close_words
    cw_partitions = NlpService.partition_close_words(
        close_words["toto"],
        c.analysis_settings.close_words_min_distance_between_words
    )
    # ONE REPETITION GROUP
    assert len(cw_partitions) == 1
    # TWO OCCOURENCES
    assert sum(len(rgroup) for rgroup in cw_partitions) == 2
    assert len(close_words["toto"]) == 2


def test_remove_accents(setup_teardown):
    assert Utils.remove_accents(TEST_TEXT_6) == TEST_TEXT_6_NON_ACCENTED


def test_file_imports():
    txt = ImportService.import_document("test_files/sample.txt")
    docx = ImportService.import_document("test_files/sample.docx")
    odt = ImportService.import_document("test_files/sample.odt")
    rtf = ImportService.import_document("test_files/sample.rtf")
    assert len(txt) > 0
    assert len(docx) > 0
    assert len(odt) > 0
    assert len(rtf) > 0


# SPELLCHECK SUITE
def test_spellcheck_identifies_misspelled_words(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    # Testovací text s preklepom
    text = "Toto je príkladd textu."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Slovo "príkladd" by malo byť označené ako preklep
    assert doc[2].text == "príkladd"
    assert doc[2]._.has_grammar_error
    assert doc[2]._.grammar_error_type == GRAMMAR_ERROR_TYPE_MISSPELLED_WORD


def test_spellcheck_ignores_correct_words(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Toto je príklad textu."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Žiadne slová by nemali byť označené ako chybné
    for token in doc:
        assert not token._.has_grammar_error


def test_spellcheck_handles_diacritics(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Mám rád slovenské slová s diakritikou."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Slová s diakritikou by mali byť správne vyhodnotené
    for token in doc:
        assert not token._.has_grammar_error


def test_spellcheck_identifies_unknown_words(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Používam program Horekarpat pre vývoj aplikácií."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Predpokladáme, že slovo "Horekarpat" nie je v slovníku
    for token in doc:
        if token.text == "Horekarpat":
            assert token._.has_grammar_error
            assert token._.grammar_error_type == GRAMMAR_ERROR_TYPE_MISSPELLED_WORD
        else:
            assert not token._.has_grammar_error


def test_spellcheck_correct_usage_of_i_plural_masculine(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Pekní chlapci prišli na návštevu."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Slová by nemali byť označené ako chybné
    for token in doc:
        assert not token._.has_grammar_error


def test_spellcheck_wrong_usage_of_y_plural_masculine(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Pekný chlapci prišli na návštevu."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Slovo "Pekný" je nesprávne v tomto kontexte
    assert doc[0].text == "Pekný"
    assert doc[0]._.has_grammar_error
    assert doc[0]._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX


def test_spellcheck_correct_usage_of_y_singular_masculine(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Pekný chlapec prišiel na návštevu."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Slová by nemali byť označené ako chybné
    for token in doc:
        assert not token._.has_grammar_error


def test_spellcheck_wrong_usage_of_i_singular_masculine(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Milí chlapec prišiel na návštevu."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Slovo "Pekní" je nesprávne v tomto kontexte
    assert doc[0].text == "Milí"
    assert doc[0]._.has_grammar_error
    assert doc[0]._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX


def test_spellcheck_handles_special_characters(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Máme 20 kusov a cena je 15 € za kus."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Čísla a symboly by nemali byť označené ako chybné
    for token in doc:
        if not token.is_alpha:
            continue
        assert not token._.has_grammar_error


def test_spellcheck_checks_non_literal_words(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = " ".join(NON_LITERAL_WORDS.keys())
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    for token in doc:
        assert token._.has_grammar_error
        assert token._.grammar_error_type == GRAMMAR_ERROR_NON_LITERAL_WORD


def test_spellcheck_sso_adpositions(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Prišiel zo susedou. Odišiel z otcom. Prišiel so susedou. Odišiel s otcom."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    assert doc[1]._.has_grammar_error
    assert doc[1]._.grammar_error_type == GRAMMAR_ERROR_Z_INSTEAD_OF_S
    assert doc[5]._.has_grammar_error
    assert doc[5]._.grammar_error_type == GRAMMAR_ERROR_Z_INSTEAD_OF_S
    assert not doc[9]._.has_grammar_error
    assert not doc[9]._.grammar_error_type == GRAMMAR_ERROR_Z_INSTEAD_OF_S
    assert not doc[13]._.has_grammar_error
    assert not doc[13]._.grammar_error_type == GRAMMAR_ERROR_Z_INSTEAD_OF_S


def test_spellcheck_zzo_adpositions(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Odišiel so školy. Prehodil s kopy. Odišiel zo školy. Prehodil z kopy."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    assert doc[1]._.has_grammar_error
    assert doc[1]._.grammar_error_type == GRAMMAR_ERROR_S_INSTEAD_OF_Z
    assert doc[5]._.has_grammar_error
    assert doc[5]._.grammar_error_type == GRAMMAR_ERROR_S_INSTEAD_OF_Z
    assert not doc[9]._.has_grammar_error
    assert not doc[9]._.grammar_error_type == GRAMMAR_ERROR_S_INSTEAD_OF_Z
    assert not doc[13]._.has_grammar_error
    assert not doc[13]._.grammar_error_type == GRAMMAR_ERROR_S_INSTEAD_OF_Z


def test_spellcheck_svoj_moj_tvoj_nas_vas(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    sentences = [
        "Chodil so svojim psom každé ráno na prechádzku."
        "S tvojim kamarátom som včera diskutoval o novom projekte."
        "S vašim autom sa ťažko manévruje na úzkej ceste."
        "Pod svojim kabátom schovával malý darček."
        "Nad našim mestom sa usadil hustý mrak."
        "Za tvojim domom rastú divoké maliny."
        # NOT WORKING: "Svojim názorom si často vyvolávaš zbytočné hádky."
        "Tvojím slovám chýba presvedčivosť."
        "S mojim starým bicyklom som najazdil stovky kilometrov."
        # NOT WORKING: "Ľúbim ťa, ale svojím rodičom si to vravieť nemusel."
        "Ľúbim ťa, ale tvojím rodičom si to vravieť nemusel."
        "Ľúbim ťa, ale mojím rodičom si to vravieť nemusel."
        # NOT WORKING: "Stal sa mojim učiteľom."
        "Daj to mojím učiteľom."
    ]
    text = " ".join(sentences)
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    for token in doc:
        if token.lemma_ in ['môj', 'tvoj', 'svoj']:
            assert token._.has_grammar_error
            assert token._.grammar_error_type in [GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_PLUR, GRAMMAR_ERROR_SVOJ_MOJ_TVOJ_SING]


def test_spellcheck_correct_svoj_moj_tvoj_nas_vas(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    sentences = [
        "Chodil so svojím psom každé ráno na prechádzku."
        "S tvojím kamarátom som včera diskutoval o novom projekte."
        "S vaším autom sa ťažko manévruje na úzkej ceste."
        "Pod svojím kabátom schovával malý darček."
        "Nad naším mestom sa usadil hustý mrak."
        "Za tvojím domom rastú divoké maliny."
        "Svojím názorom si často vyvolávaš zbytočné hádky."
        "Tvojim slovám chýba presvedčivosť."
        "S mojím starým bicyklom som najazdil stovky kilometrov."
        "Ľúbim ťa, ale svojim rodičom si to vravieť nemusel."
        "Ľúbim ťa, ale tvojim rodičom si to vravieť nemusel."
        "Ľúbim ťa, ale mojim rodičom si to vravieť nemusel."
        "Stal sa mojím učiteľom."
        "Daj to mojim učiteľom."
    ]
    text = " ".join(sentences)
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    for token in doc:
        if token.lemma_ in ['môj', 'tvoj', 'svoj']:
            assert not token._.has_grammar_error


def test_spellcheck_ignore_literal_words_correct_form(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = " ".join(NON_LITERAL_WORDS.values())
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    for token in doc:
        assert not token._.has_grammar_error
        assert not token._.grammar_error_type == GRAMMAR_ERROR_NON_LITERAL_WORD


def test_spellcheck_checks_non_literal_phrases(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Chápem tomu. Chápem aj tomu. Nechápem ani tomu. Aj tomu chápem."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    for token in doc:
        if token.lower_ == "tomu":
            assert token._.has_grammar_error
            assert token._.grammar_error_type == GRAMMAR_ERROR_TOMU_INSTEAD_OF_TO


def test_spellcheck_handles_hyphenated_words(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Červeno-biely dres je veľmi pekný."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Skontrolujeme, či sú slová so spojovníkom správne vyhodnotené
    for token in doc:
        if token.text in ["Červeno-biely"]:
            assert not token._.has_grammar_error


def test_spellcheck_performance_on_large_text(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    # Vygenerujeme veľký text
    text = ("Toto je testovací text. " * 1000) + "Nesprávneslovo."
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Posledné slovo "Nesprávneslovo" by malo byť označené ako preklep
    assert doc[-2].text == "Nesprávneslovo"  # Predpokladáme, že posledný token je bodka
    assert doc[-2]._.has_grammar_error
    assert doc[-2]._.grammar_error_type == GRAMMAR_ERROR_TYPE_MISSPELLED_WORD


def test_spellcheck_optimizes_on_small_changes(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = ("Toto je text.\n" * 1000)
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Simulujeme malú zmenu v texte
    text_changed = "Toto je testovacíy text. " + text
    doc_changed = NlpService.partial_analysis(text_changed, doc, nlp, Config(), 10)
    SpellcheckService.spellcheck(hunspell, doc_changed)
    # Skontrolujeme, či je iba zmenený token označený ako chybný
    for token in doc_changed:
        if token.text == "testovacíy":
            assert token._.has_grammar_error
            assert token._.grammar_error_type == GRAMMAR_ERROR_TYPE_MISSPELLED_WORD
        else:
            assert not token._.has_grammar_error


def test_spellcheck_handles_empty_document(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = ""
    doc = NlpService.full_analysis(text, nlp, NLP_BATCH_SIZE, Config())
    SpellcheckService.spellcheck(hunspell, doc)
    # Nemalo by dôjsť k výnimke
    assert len(doc) == 0


def test_updates(setup_teardown):
    github_token = setup_teardown[3]
    github_user = setup_teardown[4]
    latest_beta_version = Utils.find_latest_version(True, github_token, github_user)
    previous_beta_version = Utils.find_latest_version(True, github_token, github_user, skip=1)
    assert not Utils.check_updates(latest_beta_version, True, github_token, github_user)
    assert Utils.check_updates(previous_beta_version, True, github_token, github_user)
    # After first stable release add tests for stable


def test_config_save_load(setup_teardown):
    c = Config()
    c.analysis_settings.long_sentence_words_high = 999
    c_path = f"{CONFIG_FILE_PATH}.test"
    ConfigService.save(c, c_path)
    c = ConfigService.load(c_path)
    assert c.analysis_settings.long_sentence_words_high == 999


def test_config_overrides(setup_teardown):
    # PREPERE MULTIPLE CONFIGS TO TEST EVERY POSSIBLE CASCADE
    c1 = Config()
    c1.analysis_settings.long_sentence_words_high = 999
    c1.analysis_settings.enable_long_sentences = False
    c2 = Config(c1.to_dict())
    c2.analysis_settings.long_sentence_words_mid = 666
    c2.analysis_settings.enable_long_sentences = True
    c3 = Config(c2.to_dict())
    c3.analysis_settings.long_sentence_words_mid = 333
    c3.analysis_settings.enable_long_sentences = True
    c4 = Config(c3.to_dict())
    c4.analysis_settings.close_words_use_lemma = True
    # SET CONFIGS TO PROJECT, DIR_ITEM AND ITEM. RETAIN C1 AS GLOBAL CONFIG
    p = Project()
    p.config = c2
    dir_item = DirectoryProjectItem()
    dir_item.config = c3
    item = ProjectItem()
    item.config = c4
    item.parent = dir_item
    # SELECT AND TEST CONFIG. SHOULD CONFORM TO ITEM CONFIG
    c5 = ConfigService.select_config(c1, p, item)
    assert c5.analysis_settings.enable_long_sentences
    assert c5.analysis_settings.long_sentence_words_high == 999
    assert c5.analysis_settings.long_sentence_words_mid == 333
    assert c5.analysis_settings.close_words_use_lemma
    # REMOVE ITEM CONFIG
    # SELECT AND TEST CONFIG. SHOULD CONFORM TO DIR_ITEM CONFIG
    item.config = None
    c6 = ConfigService.select_config(c1, p, item)
    assert c6.analysis_settings.enable_long_sentences
    assert c6.analysis_settings.long_sentence_words_high == 999
    assert c6.analysis_settings.long_sentence_words_mid == 333
    assert not c6.analysis_settings.close_words_use_lemma
    # REMOVE DIR ITEM CONFIG
    # SELECT AND TEST CONFIG. SHOULD CONFORM TO PROJECT CONFIG
    dir_item.config = None
    c7 = ConfigService.select_config(c1, p, item)
    assert c7.analysis_settings.enable_long_sentences
    assert c7.analysis_settings.long_sentence_words_high == 999
    assert c7.analysis_settings.long_sentence_words_mid == 666
    assert not c7.analysis_settings.close_words_use_lemma
    # REMOVE PROJECT CONFIG
    # SELECT AND TEST CONFIG. SHOULD CONFORM TO GLOBAL CONFIG
    p.config = None
    c8 = ConfigService.select_config(c1, p, item)
    assert not c8.analysis_settings.enable_long_sentences
    assert c8.analysis_settings.long_sentence_words_high == 999
    assert c8.analysis_settings.long_sentence_words_mid == 8
    assert not c8.analysis_settings.close_words_use_lemma


def test_export_sentences(setup_teardown):
    nlp = setup_teardown[0]
    doc = NlpService.full_analysis(TEST_TEXT_1, nlp, NLP_BATCH_SIZE, Config())
    ExportService.export_sentences(SENTENCES_FILE, doc, False)
    assert os.path.isfile(SENTENCES_FILE)
    with open(SENTENCES_FILE, 'r', encoding='utf-8') as file:
        sents = file.read()
    assert sents == f'{TEST_TEXT_1}\n'
    os.remove(SENTENCES_FILE)
    ExportService.export_sentences(SENTENCES_FILE, doc, True)
    assert os.path.isfile(SENTENCES_FILE)
    with open(SENTENCES_FILE, 'r', encoding='utf-8') as file:
        sents = file.read()
    with_spaces = "\n\n".join(TEST_TEXT_1.split("\n"))
    assert sents == f'{with_spaces}\n\n'


def test_metadata_save_load():
    m = Metadata()
    for i in range(1, 12):
        p = Project()
        p.name = f'Test {i}'
        MetadataService.put_recent_project(m, p, f'test{i}.hproj')
    assert len(m.recent_projects) == 10
    p = Project()
    p.name = 'Test 5'
    MetadataService.put_recent_project(m, p, 'test5.hproj')
    MetadataService.put_recent_project(m, p, 'test5.hproj')
    assert len(m.recent_projects) == 10
    assert m.recent_projects[0].name == 'Test 5'
    assert m.recent_projects[1].name != 'Test 5'
    MetadataService.remove_recent_project(m, "test5.hproj")
    assert m.recent_projects[0].name != 'Test 5'
    m_path = f"{METADATA_FILE_PATH}.test"
    MetadataService.save(m, m_path)
    m2 = MetadataService.load(m_path)
    assert len(m.recent_projects) == len(m2.recent_projects) == 9


def test_execute_callbacks():
    with pytest.raises(Exception, match="test exception raised") as e_info:
        Utils.execute_callbacks([callback_raise_ex])


def callback_raise_ex():
    raise Exception("test exception raised")


def test_project_create_and_load():
    name = 'testovací projekt'
    desc = 'desc'
    file_name = Utils.normalize_file_name(name)
    if os.path.exists(file_name):
        shutil.rmtree(os.path.dirname(file_name))
    p = ProjectService.create_project(name, desc, file_name)
    assert p.name == name
    assert p.description == desc
    assert p.path is not None
    p2 = ProjectService.load(p.path)
    assert p.name == p2.name
    assert p.description == p2.description
    assert p.path == p2.path
    shutil.rmtree(os.path.dirname(p.path))
    assert ProjectService.load(p.path) is None


def test_project_items():
    name = 'testovací projekt'
    desc = 'desc'
    file_name = Utils.normalize_file_name(name)
    if os.path.exists(file_name):
        shutil.rmtree(file_name)
    p = ProjectService.create_project(name, desc, file_name)
    p.config = Config()
    ProjectService.save(p, p.path)
    item = ProjectService.new_item(p, "001", None, ProjectItemType.HTEXT)
    item.config = Config()
    ProjectService.save(p, p.path)
    assert ProjectService.load_file_contents(p, item).raw_text == ""
    item.contents = HTextFile(TEST_TEXT_1, [
        HTextFormattingTag(BOLD_TAG_NAME, "1.1", "1.4")
    ])
    ProjectService.save_file_contents(p, item)
    fake_item = ProjectItem()
    fake_item.path = "non_existing.htext"
    assert not ProjectService.save_file_contents(p, fake_item)
    item.contents = None
    item2 = ProjectService.load_file_contents(p, item)
    assert item2.raw_text == TEST_TEXT_1
    assert len(item2.formatting) == 1
    assert item2.formatting[0].tag_name == BOLD_TAG_NAME
    assert item2.formatting[0].start_index == "1.1"
    assert item2.formatting[0].end_index == "1.4"
    dir_item = ProjectService.new_item(p, "tests", None, ProjectItemType.DIRECTORY)
    dir_item.config = Config()
    ProjectService.save(p, p.path)
    subitem = ProjectService.new_item(p, "002", dir_item, ProjectItemType.HTEXT)
    with pytest.raises(FileExistsError) as e_info:
        ProjectService.new_item(p, "002", dir_item, ProjectItemType.HTEXT)
    assert subitem.path == os.path.join(dir_item.path, "002.htext")
    assert subitem.path != os.path.join(os.path.dirname(p.path), "data", "002.htext")
    p2 = ProjectService.load(p.path)
    assert len(p2.items) == len(p.items) == 2
    ProjectService.delete_item(p, subitem, dir_item)
    assert len(dir_item.subitems) == 0
    ProjectService.delete_item(p, dir_item, None)
    assert len(p.items) == 1
    shutil.rmtree(os.path.dirname(p.path))


def test_offline_updates(setup_teardown, monkeypatch):
    github_token = setup_teardown[3]
    github_user = setup_teardown[4]
    latest_beta_version = Utils.find_latest_version(True, github_token, github_user)
    previous_beta_version = Utils.find_latest_version(True, github_token, github_user, skip=1)
    TestUtils.disable_socket(monkeypatch)
    assert not Utils.check_updates(latest_beta_version, True, github_token, github_user)
    assert not Utils.check_updates(previous_beta_version, True, github_token, github_user)
    # After first stable release add tests for stable


def test_dictionary_upgrades(setup_teardown, monkeypatch):
    github_token = setup_teardown[3]
    github_user = setup_teardown[4]
    result = SpellcheckService.upgrade_dictionaries(github_token, github_user)
    assert result is not None
    assert result["thesaurus"] is not None
    assert result["spellcheck"] is not None
    TestUtils.disable_socket(monkeypatch)
    result = SpellcheckService.upgrade_dictionaries(github_token, github_user)
    assert result is None
    TestUtils.enable_socket(monkeypatch)
    result = SpellcheckService.upgrade_dictionaries(github_token, github_user)
    assert result is not None
    assert result["thesaurus"] is not None
    assert result["spellcheck"] is not None


@pytest.mark.disable_socket
def test_offline_initialization(request):
    if os.path.isdir(DATA_DIRECTORY):
        shutil.rmtree(DATA_DIRECTORY)
    nlp = NlpService.initialize()
    dictionaries = SpellcheckService.initialize(github_token=request.config.option.github_token,
                                                github_user=request.config.option.github_user)
    spellcheck_dictionary = dictionaries["spellcheck"]
    thesaurus = dictionaries["thesaurus"]
    assert not nlp
    assert not spellcheck_dictionary
    assert not thesaurus


def test_get_windows_scaling():
    scaling_factor = Utils.get_windows_scaling_factor()
    if platform.system() == "Windows":
        assert scaling_factor is not None and scaling_factor != 0
    else:
        assert scaling_factor is None


if __name__ == '__main__':
    pytest.main()
