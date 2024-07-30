import pytest
from hunspell import Hunspell
from pythes import PyThes
from spacy.lang.sk import Slovak
from spacy.tokens import Doc

from src.backend.service import Service
from src.const.grammar_error_types import GRAMMAR_ERROR_TYPE_MISSPELLED_WORD, GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX
from src.const.values import NLP_BATCH_SIZE
from src.domain.config import Config

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


def test_spellcheck(setup_teardown):
    # TODO: Make more robust test on spellcheck
    nlp = setup_teardown[0]
    hunspell = setup_teardown[1]
    doc = Service.full_nlp(TEST_TEXT_3, nlp, NLP_BATCH_SIZE, Config())
    Service.spellcheck(hunspell, doc)
    assert doc[0]._.has_grammar_error and doc[0]._.grammar_error_type == GRAMMAR_ERROR_TYPE_MISSPELLED_WORD
    assert not doc[1]._.has_grammar_error
    assert doc[5]._.has_grammar_error and doc[5]._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX
    assert doc[8]._.has_grammar_error and doc[8]._.grammar_error_type == GRAMMAR_ERROR_TYPE_WRONG_Y_SUFFIX


def test_readability(setup_teardown):
    nlp = setup_teardown[0]
    doc = Service.full_nlp(TEST_TEXT_4, nlp, NLP_BATCH_SIZE, Config())
    assert Service.evaluate_readability(doc) == 9


def test_word_frequencies(setup_teardown):
    nlp = setup_teardown[0]
    c = Config()
    c.repeated_words_min_word_frequency = 1
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
    c.close_words_min_frequency = 1
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


if __name__ == '__main__':
    pytest.main()
