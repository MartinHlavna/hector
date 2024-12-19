# PATTERNS FOR CHECKING I/Ý AND ÍSY/ÝSY SUFFIXES IN WORD CASE BY TYPE PEKNY
TYPE_PEKNY_PATTERNS = [
    # FIND ANY NOUN/DETERMINER/PRONOUN FOLLOWED BY ADJECTIVE/DETERMINER/PRONOUN
    # FURTHER CHECKING WILL BE DONE IN CODE
    [
        {
            "RIGHT_ID": "target",
            "RIGHT_ATTRS": {"POS": {"IN": ["NOUN", "DET", "PRON"]}}
        },
        {
            "LEFT_ID": "target",
            "REL_OP": ">",
            "RIGHT_ID": "modifier",
            "RIGHT_ATTRS": {"POS": {"IN": ["ADJ", "DET", "PRON"]}}
        },
    ],
    # PATTERN FOR REVERSE ORDER
    [
        {
            "RIGHT_ID": "target",
            "RIGHT_ATTRS": {"POS": {"IN": ["NOUN", "DET", "PRON"]}}
        },
        {
            "LEFT_ID": "target",
            "REL_OP": "<",
            "RIGHT_ID": "modifier",
            "RIGHT_ATTRS": {"POS": {"IN": ["ADJ", "DET", "PRON"]}}
        },
    ]
]
# PATERNS FOR CHECKING INCORRECT PHRASE CHAPEM TOMU (SHOULD BE CHAPEM TO)
CHAPEM_TO_TOMU_PATTERNS = [
    # FIND ANY FORM OF VERB CHAPAT, FOLLOWED BY ANY FORM OF PRONOUN TEN
    # FURTHER CHECKING WILL BE DONE IN CODE
    [
        {
            "RIGHT_ID": "verb",
            "RIGHT_ATTRS": {"LEMMA": "chápať"}
        },
        {
            "LEFT_ID": "verb",
            "REL_OP": ">",
            "RIGHT_ID": "pron",
            "RIGHT_ATTRS": {"LEMMA": "ten"}
        },
    ],
    # PATTERN FOR REVERSE ORDER
    [
        {
            "RIGHT_ID": "verb",
            "RIGHT_ATTRS": {"LEMMA": "chápať"}
        },
        {
            "LEFT_ID": "verb",
            "REL_OP": "<",
            "RIGHT_ID": "pron",
            "RIGHT_ATTRS": {"LEMMA": "ten"}
        },
    ]
]
# PATTERNS FORCH CHECKING INCCORECT USAGE OF ADPOSITION Z/ZO INSTEAD OF S/SO
ZZO_INSTEAD_OF_SSO_PATTERNS = [
    # FIND ANY FORM OF Z PREPOSITION THAT RELATES TO NOUN IN INSTRUMENTAL CASE
    [
        {
            "RIGHT_ID": "preposition",
            "RIGHT_ATTRS": {"LEMMA": "z"}
        },
        {
            "LEFT_ID": "preposition",
            "REL_OP": "<",
            "RIGHT_ID": "noun",
            "RIGHT_ATTRS": {"MORPH": {"INTERSECTS": ["Case=Ins"]}}
        },
    ]
]
# PATTERNS FORCH CHECKING INCCORECT USAGE OF ADPOSITION S/SO INSTEAD OF Z/ZO
SSO_INSTEAD_OF_ZZO_PATTERNS = [
    # FIND ANY FORM OF S PREPOSITION THAT RELATES TO NOUN IN GENITIVE CASE
    [
        {
            "RIGHT_ID": "preposition",
            "RIGHT_ATTRS": {"LEMMA": "s"}
        },
        {
            "LEFT_ID": "preposition",
            "REL_OP": "<",
            "RIGHT_ID": "noun",
            "RIGHT_ATTRS": {"MORPH": {"INTERSECTS": ["Case=Gen", "Case=Acc"]}}
        },
    ],
    # FIND ANY FORM OF S PREPOSITION THAT RELATES TO NOUN IN NOMINATIVE CASE
    # THIS IS BECAUSE SOME WORDS WITH THIS ERROR MIGHT BE MISMORPHED
    [
        {
            "RIGHT_ID": "preposition",
            "RIGHT_ATTRS": {"LEMMA": "s"}
        },
        {
            "LEFT_ID": "preposition",
            "REL_OP": "<",
            "RIGHT_ID": "noun",
            "RIGHT_ATTRS": {"MORPH": {"INTERSECTS": ["Case=Nom"]}}
        },
    ]
]
SVOJ_MOJ_TVOJ_PATTERNS = [
    # FIND DATIVE FORMS OF PRONOUNS svoj, môj, tvoj THAT IS RELATED TO NOUN IN INSTRUMENTAL CASE
    # FURTHER CHECKINGS DONE IN CODE
    [
        {
            "RIGHT_ID": "pronoun",
            "RIGHT_ATTRS": {
                "LEMMA": {"IN": ["svoj", "môj", "tvoj"]},
                "MORPH": {"INTERSECTS": ["Gender=Masc", "Gender=Neut", "Gender=Com"]}
            }
        },
        {
            "LEFT_ID": "pronoun",
            "REL_OP": "<",
            "RIGHT_ID": "noun",
            "RIGHT_ATTRS": {"POS": {"IN": ["NOUN"]}}
        },
    ],
    # PATTERN FOR REVERSE ORDER
    [
        {
            "RIGHT_ID": "pronoun",
            "RIGHT_ATTRS": {"LEMMA": {"IN": ["svoj", "môj", "tvoj"]}}
        },
        {
            "LEFT_ID": "pronoun",
            "REL_OP": ">",
            "RIGHT_ID": "noun",
            "RIGHT_ATTRS": {"POS": {"IN": ["NOUN"]}}
        },
    ]
]
