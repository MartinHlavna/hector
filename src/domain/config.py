class Config:
    def __init__(self, data=None):
        """
        Constructor accepts a dictionary and sets the class attributes.
        If a key is not provided in the dictionary, the default value is used.

        :param data: Dictionary containing the data to initialize the object. If not provided, default values are used.
        """
        if data is None:
            data = {}
        # BACKWARDS COMPATIBILITY
        if 'analysis_settings' not in data:
            tmp = data
            data = {'analysis_settings': tmp}
        self.analysis_settings = AnalysisSettings(data.get('analysis_settings', {}))
        self.appearance_settings = AppearanceSettings(data.get('appearance_settings', {}))

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        return {
            "analysis_settings": self.analysis_settings.to_dict(),
            "appearance_settings": self.appearance_settings.to_dict()
        }


class AnalysisSettings:
    def __init__(self, data):
        if data is None:
            data = {}
        # USE LEMMA COMPARISION IN CLOSE_WORDS FUNCTIONALITY
        self.repeated_words_use_lemma = data.get('repeated_words_use_lemma', False)
        # MINIMAL LENGTH OF WORD FOR IT TO APPEAR IN FREQUENT WORDS SECTION
        self.repeated_words_min_word_length = data.get('repeated_words_min_word_length', 3)
        # MINIMAL NUMBER OF WORD REPETITIONS FOR IT TO APPEAR IN REPEATED WORDS SECTION
        self.repeated_words_min_word_frequency = data.get('repeated_words_min_word_frequency', 10)
        # SENTENCE IS CONSIDERED MID LONG IF IT HAS MORE WORDS THAN THIS CONFIG
        self.long_sentence_words_mid = data.get('long_sentence_words_mid', 8)
        # SENTENCE IS CONSIDERED HIGH LONG IF IT HAS MORE WORDS THAN THIS CONFIG
        self.long_sentence_words_high = data.get('long_sentence_words_high', 16)
        # WORD IS COUNTED TO SENTENCE LENGTH ONLY IF IT HAS MORE CHARS THAN THIS CONFIG
        self.long_sentence_min_word_length = data.get('long_sentence_min_word_length', 5)
        # MINIMAL LENGTH OF WORD FOR IT TO BE HIGHLIGHTED IF VIA CLOSE_WORDS FUNCTIONALITY
        self.close_words_min_word_length = data.get('close_words_min_word_length', 3)
        # USE LEMMA COMPARISION IN CLOSE_WORDS FUNCTIONALITY
        self.close_words_use_lemma = data.get('close_words_use_lemma', False)
        # MINIMAL DISTANCE BETWEEN REPEATED WORDS (DEFAULT VALUE IS ABOUT THIRD OF PAGE)
        self.close_words_min_distance_between_words = data.get(
            'close_words_min_distance_between_words',
            100
        )
        # MINIMAL FREQUENCY FOR REPEATED WORD TO BE HIGHLIGHTED
        self.close_words_min_frequency = data.get('close_words_min_frequency', 3)
        # ENABLE FREQUENT WORDS SIDE PANEL
        self.enable_frequent_words = data.get('enable_frequent_words', True)
        # ENABLE HIGHLIGHTING OF LONG SENTENCES
        self.enable_long_sentences = data.get('enable_long_sentences', True)
        # ENABLE HIGHLIGHTING OF REPEATED SPACES
        self.enable_multiple_spaces = data.get('enable_multiple_spaces', True)
        # ENABLE HIGHLIGHTING OF REPEATED PUNCTUATION (eg. !! ?? ..)
        self.enable_multiple_punctuation = data.get('enable_multiple_punctuation', True)
        # ENABLE HIGHLIGHTING OF TRAILING SPACES AT THE END OF PARAGRAPH
        self.enable_trailing_spaces = data.get('enable_trailing_spaces', True)
        # ENABLE HIGHLIGHTING OF WORDS THAT ARE REPEATED AT SAME SPOTS
        self.enable_close_words = data.get('enable_close_words', True)
        # ENABLE SPELLCHECK
        self.enable_spellcheck = data.get('enable_spellcheck', True)
        # ENABLE PARTIAL NLP
        self.enable_partial_nlp = data.get('enable_partial_nlp', True)
        # ENABLE QUOTE CORRECTIONS
        self.enable_quote_corrections = data.get('enable_quote_corrections', True)

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        return {
            "repeated_words_min_word_length": self.repeated_words_min_word_length,
            "repeated_words_min_word_frequency": self.repeated_words_min_word_frequency,
            "repeated_words_use_lemma": self.repeated_words_use_lemma,
            "long_sentence_words_mid": self.long_sentence_words_mid,
            "long_sentence_words_high": self.long_sentence_words_high,
            "long_sentence_min_word_length": self.long_sentence_min_word_length,
            "close_words_min_word_length": self.close_words_min_word_length,
            "close_words_min_distance_between_words": self.close_words_min_distance_between_words,
            "close_words_min_frequency": self.close_words_min_frequency,
            "close_words_use_lemma": self.close_words_use_lemma,
            "enable_frequent_words": self.enable_frequent_words,
            "enable_long_sentences": self.enable_long_sentences,
            "enable_multiple_spaces": self.enable_multiple_spaces,
            "enable_multiple_punctuation": self.enable_multiple_punctuation,
            "enable_trailing_spaces": self.enable_trailing_spaces,
            "enable_close_words": self.enable_close_words,
            "enable_spellcheck": self.enable_spellcheck,
            "enable_partial_nlp": self.enable_partial_nlp,
            "enable_quote_corrections": self.enable_quote_corrections,
        }


class AppearanceSettings:
    def __init__(self, data):
        if data is None:
            data = {}
        # LEFT MARGIN OF FIRST LINE IN PARAGRAPH
        self.paragraph_lmargin1 = data.get('paragraph_lmargin1', 7)
        # SPACING BELLOW PARAGRAPH
        self.paragraph_spacing3 = data.get('paragraph_spacing3', 0)

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        return {
            "paragraph_lmargin1": self.paragraph_lmargin1,
            "paragraph_spacing3": self.paragraph_spacing3,
        }
