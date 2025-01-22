class RunContext(object):
    """
        Helper class that holds global information in various parts of application
        Class is singleton. To access data, simple create instance.
    """

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(RunContext, cls).__new__(cls)
            self = cls.instance
            # SPACY NLP INSTANCE
            self.nlp = None
            # THESAURUS INSTANCE
            self.thesaurus = None
            # HUNSPELL DICTIONARY INSTANCE
            self.spellcheck_dictionary = None
            # UPDATE CHECK RESULT
            self.has_available_update = None
            # CURRENT PROJECT
            self.project = None
            # CURRENT FILE OPENED IN EDITOR
            self.current_file = None
        return cls.instance
