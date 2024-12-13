import spacy
from spacy.language import Language
import ufal.morphodita as morphodita
from spacy.tokens import Token, Doc

MORPHODITA_RESET_SENTENCES_COMPONENT = "reset_sentences_after_morphodita_component"
MORPHODITA_COMPONENT_FACTORY_NAME = "morphodita_tagger_morphologizer_lemmatizer"

# MAPPING BETWEEN PDT TAGS AND SPACY TAGS

pos_map = {
    'A': 'ADJ',
    'C': 'NUM',
    'D': 'ADV',
    'I': 'INTJ',
    'J': 'CCONJ',
    'N': 'NOUN',
    'P': 'PRON',
    'V': 'VERB',
    'R': 'ADP',
    'T': 'PART',
    'X': 'X',
    'Z': 'PUNCT',
}

sumpos_map = {
    '#': 'PUNCT',  # Sentence boundary
    '%': 'NOUN',  # Author's signature
    '*': 'NUM',  # Word "krát" (lit.: times)
    ',': 'SCONJ',  # Subordinate conjunction
    '}': 'NUM',  # Numeral written in Roman numerals
    ':': 'PUNCT',  # General punctuation
    '=': 'NUM',  # Number written in digits
    '?': 'NUM',  # Numeral "kolik" (how many/how much)
    '@': 'X',  # Unrecognized word form
    '^': 'CCONJ',  # Coordinating conjunction
    '4': 'PRON',  # Relative/interrogative pronoun with adjectival declension
    '5': 'PRON',  # Pronoun "he" after preposition
    '6': 'PRON',  # Reflexive pronoun "se" in long forms
    '7': 'PRON',  # Reflexive pronouns "se", "si", contracted forms
    '8': 'PRON',  # Possessive reflexive pronoun "svůj"
    '9': 'PRON',  # Relative pronoun "jenž" after a preposition
    'A': 'ADJ',  # General adjective
    'B': 'VERB',  # Verb, present or future form
    'C': 'ADJ',  # Adjective, nominal (short, participial) form
    'D': 'PRON',  # Demonstrative pronoun
    'E': 'PRON',  # Relative pronoun "což"
    'F': 'ADP',  # Preposition, part of
    'G': 'ADJ',  # Adjective derived from present transgressive verb
    'H': 'PRON',  # Personal pronoun, clitic form
    'I': 'INTJ',  # Interjection
    'J': 'PRON',  # Relative pronoun "jenž" not after a preposition
    'K': 'PRON',  # Relative/interrogative pronoun "kdo"
    'L': 'PRON',  # Indefinite pronoun
    'M': 'ADJ',  # Adjective derived from past transgressive verb
    'N': 'NOUN',  # General noun
    'O': 'PRON',  # Pronoun "svůj" or similar
    'P': 'PRON',  # Personal pronoun "já, ty, on"
    'Q': 'PRON',  # Relative/interrogative pronoun "co"
    'R': 'ADP',  # General preposition
    'S': 'PRON',  # Possessive pronoun "můj, tvůj, jeho"
    'T': 'PART',  # Particle
    'U': 'ADJ',  # Possessive adjective
    'V': 'ADP',  # Preposition with vocalization
    'W': 'PRON',  # Negative pronoun
    'X': 'X',  # Temporary word form
    'Y': 'PRON',  # Relative/interrogative pronoun "co" as enclitic
    'Z': 'PRON',  # Indefinite pronoun
    'a': 'NUM',  # Indefinite numeral
    'b': 'ADV',  # Adverb without negation/comparison
    'c': 'VERB',  # Conditional form of "být"
    'd': 'NUM',  # Generic numeral with adjectival declension
    'e': 'VERB',  # Verb, transgressive present
    'f': 'VERB',  # Verb, infinitive
    'g': 'ADV',  # Adverb forming negation and comparison
    'h': 'NUM',  # Generic numeral "jedny, nejedny"
    'i': 'VERB',  # Verb, imperative
    'j': 'NUM',  # Generic numeral as a noun
    'k': 'NUM',  # Generic numeral as an adjective
    'l': 'NUM',  # Cardinal numeral
    'm': 'VERB',  # Verb, past transgressive
    'n': 'NUM',  # Cardinal numeral (>=5)
    'o': 'NUM',  # Multiplicative indefinite numeral
    'p': 'VERB',  # Verb, past participle active
    'q': 'VERB',  # Verb, past participle active (archaic)
    'r': 'NUM',  # Ordinal numeral
    's': 'VERB',  # Verb, past participle passive
    't': 'VERB',  # Verb, present/future with enclitic
    'u': 'NUM',  # Interrogative numeral
    'v': 'NUM',  # Multiplicative definite numeral
    'w': 'NUM',  # Indefinite numeral with adjectival declension
    'y': 'NUM',  # Fraction numeral as a noun
    'z': 'NUM',  # Interrogative ordinal numeral
}

gender_map = {
    'F': 'Fem',  # Feminine
    # 'H': 'Fem', 'Neut',  # Feminine or Neuter
    'I': 'Masc',  # Masculine inanimate
    'M': 'Masc',  # Masculine animate
    'N': 'Neut',  # Neuter
    # 'Q': 'Fem', 'Neut',  # Feminine (singular only) or Neuter (plural only)
    # 'T': 'Masc', 'Fem',  # Masculine inanimate or Feminine (plural only)
    'X': 'Com',  # Any
    'Y': 'Masc',  # Masculine (either animate or inanimate)
    # 'Z': 'Masc', 'Neut'  # Not feminine (Masculine animate/inanimate or Neuter)
}

plurality_map = {
    'D': 'Dual',  # Dual
    'P': 'Plur',  # Plural
    'S': 'Sing',  # Singular
    # 'W': 'Sing', 'Plur',  # Singular (feminine), Plural (neuter)
    'X': 'Other'  # Any (includes all forms)
}

case_map = {
    '1': 'Nom',  # Nominative
    '2': 'Gen',  # Genitive
    '3': 'Dat',  # Dative
    '4': 'Acc',  # Accusative
    '5': 'Voc',  # Vocative
    '6': 'Loc',  # Locative
    '7': 'Ins',  # Instrumental
}

possessor_gender_map = {
    'F': 'Fem',  # Feminine
    'M': 'Masc',  # Masculine animate (adjectives only)
    'X': 'Neut'
    # 'X': 'Masc', 'Fem', 'Neut',  # Any (includes all genders)
    # 'Z': 'Masc', 'Neut'  # Not feminine (Masculine animate/inanimate or Neuter)
}

possessor_plurality_map = {
    'P': 'Plur',  # Plural
    'S': 'Sing',  # Singular
}

person_map = {
    '1': '1',  # First person
    '2': '2',  # Second person
    '3': '3'  # Third person
}

degree_map = {
    '1': 'Pos',  # Positive
    '2': 'Cmp',  # Comparative
    '3': 'Sup'  # Superlative
}

tense_map = {
    'F': 'Fut',  # Future
    'H': 'Pqp',  # Plusquamperfektum (archaic)
    'P': 'Pres',  # Present
    'R': 'Past',  # Past
}

polarity_map = {
    'A': 'Pos',  # Positive (not negated)
    'N': 'Neg'  # Negated
}

voice_map = {
    'A': 'Act',  # Active
    'P': 'Pass'  # Passive
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
        if not Token.has_extension("lemma_comments"):
            Token.set_extension("lemma_comments", default='')
        if not Token.has_extension("pdt_morph"):
            Token.set_extension("pdt_morph", default='')

    def convert_pdt_tag_to_spacy(self, tag):
        morph_attrs = {}
        # https://ufal.mff.cuni.cz/pdt2.0/doc/manuals/en/m-layer/html/ch02s02s01.html
        # PDT TAGS SHOULD HAVE EXACTLY 15 POSITIONS
        tag = tag.ljust(15, '-')
        # POS TAG
        pos = tag[0]
        # SUB POS
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
        # VOICE
        voice = tag[11]
        # UNUSED
        # UNUSED
        variant = tag[14]
        # TRY TO DETERMINE POS TAG ACCORDING TO SUBPOS
        spacy_pos = sumpos_map.get(sub_pos, None)
        if spacy_pos is None:
            # IF FAILED TO DETERMINE FROM SUB POS, FALLBACK TO BASIC POS
            spacy_pos = pos_map.get(pos)
        morph_attrs['POS'] = spacy_pos
        if gender in gender_map:
            morph_attrs['Gender'] = gender_map[gender]
        if poss_gender in possessor_gender_map:
            morph_attrs['Gender'] = possessor_gender_map[poss_gender]
            morph_attrs['Poss'] = 'Yes'
        if number in plurality_map:
            morph_attrs['Number'] = plurality_map[number]
        if poss_number in possessor_plurality_map:
            morph_attrs['Number'] = possessor_plurality_map[poss_number]
            morph_attrs['Poss'] = 'Yes'
        if case in case_map:
            morph_attrs['Case'] = case_map[case]
        if person in person_map:
            morph_attrs['Person'] = person_map[person]
        if tense in tense_map:
            morph_attrs['Tense'] = tense_map[tense]
        if voice in voice_map:
            morph_attrs['Voice'] = voice_map[voice]
        if degree in degree_map:
            morph_attrs['Degree'] = degree_map[degree]
        if polarity in polarity_map:
            morph_attrs['Polarity'] = polarity_map[polarity]
        return morph_attrs

    def __call__(self, doc: Doc) -> Doc:
        # FOR EVERY SENTENCE
        for sent in doc.sents:
            forms = morphodita.Forms()
            # WE NEED TO RETAIN TOKEN INDEXES
            sentence_tokens = [token for token in sent]
            for token in sent:
                forms.push_back(token.text)

            lemmas = morphodita.TaggedLemmas()
            # TAG SENTENCE
            self.tagger.tag(forms, lemmas)

            # PROCESS TOKEN LEMMA PAIRS
            for token, tagged_lemma in zip(sentence_tokens, lemmas):
                lemma = tagged_lemma.lemma
                tag = tagged_lemma.tag
                token._.full_lemma = lemma
                token._.pdt_morph = tag
                token.lemma_ = self.morpho.rawLemma(lemma)
                token._.lemma_comments = (lemma.replace(token.lemma_, "")
                                          .replace("_", " ")
                                          .replace("^", "")
                                          .replace("`", "")
                                          .strip())
                morph_attrs = self.convert_pdt_tag_to_spacy(tag)
                token.pos_ = morph_attrs.get('POS', 'X')
                morph_attrs.pop('POS', None)
                token.morph = spacy.tokens.MorphAnalysis(doc.vocab, morph_attrs)
        return doc


@Language.factory(MORPHODITA_COMPONENT_FACTORY_NAME, default_config={"tagger_path": None})
def morphodita_tagger_morphologizer_lemmatizer(nlp, name, tagger_path: str):
    return MorphoditaTaggerMorphologizerLemmatizer(nlp, tagger_path=tagger_path)


@Language.component(MORPHODITA_RESET_SENTENCES_COMPONENT)
def reset_sentences_component(doc):
    if len(doc) > 0:
        for token in doc:
            token.is_sent_start = None
    return doc
