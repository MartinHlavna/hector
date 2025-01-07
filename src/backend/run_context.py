class RunContext(object):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(RunContext, cls).__new__(cls)
            self = cls.instance
            self.nlp = None
            self.project = None
            self.thesaurus = None
            self.spellcheck_dictionary = None
            self.has_available_update = None
            self.current_file = None
        return cls.instance

