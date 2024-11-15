import os
import platform
import shutil

import pytest
from hunspell import Hunspell
from pythes import PyThes
from spacy.lang.sk import Slovak
from spacy.tokens import Doc

from src.backend.service import Service
from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD, GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX, \
    GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX
from src.const.paths import DATA_DIRECTORY, CONFIG_FILE_PATH, METADATA_FILE_PATH
from src.const.values import NLP_BATCH_SIZE
from src.domain.config import Config
from src.domain.metadata import Metadata
from src.utils import Utils
from test_utils import TestUtils

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
    doc = Service.full_nlp(TEST_TEXT_1, nlp, NLP_BATCH_SIZE, Config())
    assert doc is not None
    assert isinstance(doc, Doc)


# TEST IF PARTIAL NLP IS WORKING
def test_partial_nlp(setup_teardown):
    nlp = setup_teardown[0]
    original_doc = Service.full_nlp(TEST_TEXT_4, nlp, NLP_BATCH_SIZE, Config())
    assert original_doc is not None
    assert isinstance(original_doc, Doc)
    doc1 = Service.partial_nlp(TEST_TEXT_4_CHANGE_AT_START, original_doc, nlp, Config(), 6)
    assert doc1 is not None
    assert isinstance(doc1, Doc)
    assert doc1._.total_chars == len(TEST_TEXT_4_CHANGE_AT_START.replace('\n', ''))
    assert doc1.text == TEST_TEXT_4_CHANGE_AT_START
    doc2 = Service.partial_nlp(TEST_TEXT_4_CHANGE_AT_END, original_doc, nlp, Config(),
                               len(TEST_TEXT_4_CHANGE_AT_END) - 1)
    assert doc2 is not None
    assert isinstance(doc2, Doc)
    assert doc2._.total_chars == len(TEST_TEXT_4_CHANGE_AT_END.replace('\n', ''))
    assert doc2.text == TEST_TEXT_4_CHANGE_AT_END
    doc3 = Service.partial_nlp(TEST_TEXT_4_CHANGE_IN_MID, original_doc, nlp, Config(),
                               897)
    assert doc3 is not None
    assert isinstance(doc3, Doc)
    assert doc3._.total_chars == len(TEST_TEXT_4_CHANGE_AT_END.replace('\n', ''))
    assert doc3.text == TEST_TEXT_4_CHANGE_IN_MID


# TEST IF CUSTOM_EXTENSION ARE CORRECTLY FILLES
def test_custom_extenstions(setup_teardown):
    nlp = setup_teardown[0]
    doc = Service.full_nlp(TEST_TEXT_1, nlp, NLP_BATCH_SIZE, Config())
    assert doc._.words is not None
    assert len(doc._.words) == 7 and doc._.total_words == 7
    assert len(doc._.unique_words) == 5 and doc._.total_unique_words == 5
    assert len(doc._.lemmas) == 5
    assert len(doc._.paragraphs) == 2
    assert doc._.total_chars == len(TEST_TEXT_1.replace('\n', ''))
    assert 0 < doc._.total_pages < 1


def test_find_multiple_spaces(setup_teardown):
    nlp = setup_teardown[0]
    doc = Service.full_nlp(TEST_TEXT_2, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in Service.find_multiple_spaces(doc)) == 2


def test_find_multiple_punctuation(setup_teardown):
    nlp = setup_teardown[0]
    doc = Service.full_nlp(TEST_TEXT_2, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in Service.find_multiple_punctuation(doc)) == 1


def test_quote_marks_corrections(setup_teardown):
    nlp = setup_teardown[0]
    doc = Service.full_nlp(TEST_TEXT_QUOTES_1, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in Service.find_incorrect_lower_quote_marks(doc)) == 1
    assert sum(1 for _ in Service.find_incorrect_upper_quote_marks(doc)) == 1


def test_find_computer_quote_marks(setup_teardown):
    nlp = setup_teardown[0]
    doc = Service.full_nlp(TEST_TEXT_QUOTES_2, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in Service.find_computer_quote_marks(doc)) == 2


def test_find_dangling_quote_marks(setup_teardown):
    nlp = setup_teardown[0]
    doc = Service.full_nlp(TEST_TEXT_QUOTES_3, nlp, NLP_BATCH_SIZE, Config())
    assert sum(1 for _ in Service.find_dangling_quote_marks(doc)) == 2


def test_readability(setup_teardown):
    nlp = setup_teardown[0]
    doc = Service.full_nlp(TEST_TEXT_4, nlp, NLP_BATCH_SIZE, Config())
    assert Service.evaluate_readability(doc) == 8


def test_word_frequencies(setup_teardown):
    nlp = setup_teardown[0]
    c = Config()
    c.analysis_settings.repeated_words_min_word_frequency = 1
    doc = Service.full_nlp(TEST_TEXT_5, nlp, NLP_BATCH_SIZE, c)
    word_frequencies = Service.compute_word_frequencies(doc, c)
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
    doc = Service.full_nlp(TEST_TEXT_1, nlp, NLP_BATCH_SIZE, c)
    close_words = Service.evaluate_close_words(doc, c)
    assert len(close_words) == 1
    assert "toto" in close_words and len(close_words["toto"]) == 2


def test_remove_accents(setup_teardown):
    assert Service.remove_accents(TEST_TEXT_6) == TEST_TEXT_6_NON_ACCENTED


def test_file_imports():
    txt = Service.import_document("test_files/sample.txt")
    docx = Service.import_document("test_files/sample.docx")
    odt = Service.import_document("test_files/sample.odt")
    rtf = Service.import_document("test_files/sample.rtf")
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
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Slovo "príkladd" by malo byť označené ako preklep
    assert doc[2].text == "príkladd"
    assert doc[2]._.has_grammar_error
    assert doc[2]._.grammar_error_type == GRAMMAR_ERROR_TYPE_MISSPELLED_WORD


def test_spellcheck_ignores_correct_words(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Toto je príklad textu."
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Žiadne slová by nemali byť označené ako chybné
    for token in doc:
        assert not token._.has_grammar_error


def test_spellcheck_handles_diacritics(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Mám rád slovenské slová s diakritikou."
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Slová s diakritikou by mali byť správne vyhodnotené
    for token in doc:
        assert not token._.has_grammar_error


def test_spellcheck_identifies_unknown_words(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Používam program Horekarpat pre vývoj aplikácií."
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
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
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Slová by nemali byť označené ako chybné
    for token in doc:
        assert not token._.has_grammar_error


def test_spellcheck_wrong_usage_of_y_plural_masculine(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Pekný chlapci prišli na návštevu."
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Slovo "Pekný" je nesprávne v tomto kontexte
    assert doc[0].text == "Pekný"
    assert doc[0]._.has_grammar_error
    assert doc[0]._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX


def test_spellcheck_correct_usage_of_y_singular_masculine(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Pekný chlapec prišiel na návštevu."
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Slová by nemali byť označené ako chybné
    for token in doc:
        assert not token._.has_grammar_error


def test_spellcheck_wrong_usage_of_i_singular_masculine(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Milí chlapec prišiel na návštevu."
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Slovo "Pekní" je nesprávne v tomto kontexte
    assert doc[0].text == "Milí"
    assert doc[0]._.has_grammar_error
    assert doc[0]._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_I_SUFFIX


def test_spellcheck_handles_special_characters(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Máme 20 kusov a cena je 15 € za kus."
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Čísla a symboly by nemali byť označené ako chybné
    for token in doc:
        if not token.is_alpha:
            continue
        assert not token._.has_grammar_error


def test_spellcheck_handles_hyphenated_words(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = "Červeno-biely dres je veľmi pekný."
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Skontrolujeme, či sú slová so spojovníkom správne vyhodnotené
    for token in doc:
        if token.text in ["Červeno-biely"]:
            assert not token._.has_grammar_error


def test_spellcheck_performance_on_large_text(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    # Vygenerujeme veľký text
    text = ("Toto je testovací text. " * 1000) + "Nesprávneslovo."
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Posledné slovo "Nesprávneslovo" by malo byť označené ako preklep
    assert doc[-2].text == "Nesprávneslovo"  # Predpokladáme, že posledný token je bodka
    assert doc[-2]._.has_grammar_error
    assert doc[-2]._.grammar_error_type == GRAMMAR_ERROR_TYPE_MISSPELLED_WORD


def test_spellcheck_optimizes_on_small_changes(setup_teardown):
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    text = ("Toto je text.\n" * 1000)
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    # Simulujeme malú zmenu v texte
    text_changed = "Toto je testovacíy text. " + text
    doc_changed = Service.partial_nlp(text_changed, doc, nlp, Config(), 10)
    Service.spellcheck(hunspell, doc_changed)
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
    doc = Service.full_nlp(text, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
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
    Service.save_config(c, c_path)
    c = Service.load_config(c_path)
    assert c.analysis_settings.long_sentence_words_high == 999


def test_metadata_save_load(setup_teardown):
    m = Metadata()
    m.recent_files = ["TEST"]
    m_path = f"{METADATA_FILE_PATH}.test"
    Service.save_metadata(m, m_path)
    m = Service.load_metadata(m_path)
    assert m.recent_files[0] == "TEST"


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
    result = Service.upgrade_dictionaries(github_token, github_user)
    assert result is not None
    assert result["thesaurus"] is not None
    assert result["spellcheck"] is not None
    TestUtils.disable_socket(monkeypatch)
    result = Service.upgrade_dictionaries(github_token, github_user)
    assert result is None
    TestUtils.enable_socket(monkeypatch)
    result = Service.upgrade_dictionaries(github_token, github_user)
    assert result is not None
    assert result["thesaurus"] is not None
    assert result["spellcheck"] is not None


@pytest.mark.disable_socket
def test_offline_initialization(request):
    if os.path.isdir(DATA_DIRECTORY):
        shutil.rmtree(DATA_DIRECTORY)
    nlp = Service.initialize_nlp()
    dictionaries = Service.initialize_dictionaries(github_token=request.config.option.github_token,
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
