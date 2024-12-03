import spacy
from spacy.language import Language
import ufal.morphodita as morphodita
from spacy.tokens import Token, Doc

# MAPPING BETWEEN PDT TAGS AND SPACY TAGS

pos_map = {
    'N': 'NOUN',
    'A': 'ADJ',
    'P': 'PRON',
    'V': 'VERB',
    'D': 'NUM',
    'R': 'ADV',
    'C': 'CCONJ',
    'S': 'ADP',
    'T': 'PART',
    'I': 'INTJ',
    'M': 'X',
    'Y': 'SYM',
    'Z': 'PUNCT'
}

gender_map = {
    'M': 'Masc',
    'F': 'Fem',
    'N': 'Neut'
}

plurality_map = {
    'S': 'Sing',
    'P': 'Plur'
}

case_map = {
    '1': 'Nom',
    '2': 'Gen',
    '3': 'Dat',
    '4': 'Acc',
    '5': 'Voc',
    '6': 'Loc',
    '7': 'Ins'
}

person_map = {
    '1': '1',
    '2': '2',
    '3': '3'
}

tense_map = {
    'P': 'Pres',
    'F': 'Fut',
    'R': 'Past',
    'H': 'Pqp'  # Plusquamperfektum (archaic)
}

mood_map = {
    'I': 'Ind',
    'C': 'Cnd',
    'M': 'Imp',
    'N': 'Nec'
}

aspect_map = {
    'P': 'Perf',
    'I': 'Imp'
}

degree_map = {
    '1': 'Pos',
    '2': 'Cmp',
    '3': 'Sup'
}

polarity_map = {
    'A': 'Pos',
    'N': 'Neg'
}

animacy_map = {
    'Y': 'Anim',
    'N': 'Inan'
}


class MorphoditaTaggerMorphologizerLemmatizer:
    def __init__(self, nlp: Language, tagger_path: str):
        self.tagger = morphodita.Tagger.load(tagger_path)
        self.nlp = nlp
        self.forms = morphodita.Forms()
        self.lemmas = morphodita.TaggedLemmas()
        self.morpho = self.tagger.getMorpho()
        if not Token.has_extension("full_lemma"):
            Token.set_extension("full_lemma", default='')
        if not Token.has_extension("pdt_morph"):
            Token.set_extension("pdt_morph", default='')

    def convert_pdt_tag_to_spacy(self, tag):
        morph_attrs = {}
        # https://ufal.mff.cuni.cz/pdt2.0/doc/manuals/en/m-layer/html/ch02s02s01.html
        # PDT TAGS SHOULD HAVE EXACTLY 15 POSITIONS
        tag = tag.ljust(15, '-')
        # POS TAG
        pos = tag[0]
        # SUB POS (UNUSED)
        sub_pos = tag[1]
        # GENDER
        gender = tag[2]
        # PLURALITY (Number)
        number = tag[3]
        # CASE
        case = tag[4]
        # PossGender (unused)
        poss_gender = tag[5]
        # PossNumber (unused)
        poss_number = tag[6]
        # PERSON
        person = tag[7]
        # TENSE
        tense = tag[8]
        # DEGREE
        degree = tag[9]
        # POLARITY
        polarity = tag[10]
        # ASPECT
        aspect = tag[11]
        # UNUSED
        # UNUSED
        variant = tag[14]
        spacy_pos = pos_map.get(pos, 'X')
        morph_attrs['POS'] = spacy_pos
        # SUBPOS SUBCATEGORY (Unused)
        # GENDER
        if gender in gender_map:
            morph_attrs['Gender'] = gender_map[gender]
        if number in plurality_map:
            morph_attrs['Number'] = plurality_map[number]
        if case in case_map:
            morph_attrs['Case'] = case_map[case]

        if person in person_map:
            morph_attrs['Person'] = person_map[person]

        if tense in tense_map:
            morph_attrs['Tense'] = tense_map[tense]

        if aspect in aspect_map:
            morph_attrs['Aspect'] = aspect_map[aspect]

        if degree in degree_map:
            morph_attrs['Degree'] = degree_map[degree]

        if polarity in polarity_map:
            morph_attrs['Polarity'] = polarity_map[polarity]

        return morph_attrs

    def __call__(self, doc: Doc) -> Doc:
        for i, token in enumerate(doc):
            self.forms.clear()
            self.forms.push_back(token.text)
            self.tagger.tag(self.forms, self.lemmas)
            if len(self.lemmas) > 0:
                lemma = self.lemmas[0].lemma
                tag = self.lemmas[0].tag
                token._.full_lemma = lemma
                token._.pdt_morph = tag
                token.lemma_ = self.morpho.rawLemma(lemma)
                morph_attrs = self.convert_pdt_tag_to_spacy(tag)
                token.pos_ = morph_attrs.get('POS', 'X')
                morph_attrs.pop('POS', None)
                token.morph = spacy.tokens.MorphAnalysis(doc.vocab, morph_attrs)
        return doc


@Language.factory("morphodita_tagger_morphologizer_lemmatizer", default_config={"tagger_path": None})
def morphodita_tagger_morphologizer_lemmatizer(nlp, name, tagger_path: str):
    return MorphoditaTaggerMorphologizerLemmatizer(nlp, tagger_path=tagger_path)
