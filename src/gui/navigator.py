class Navigator(object):
    MAIN_WINDOW = "MAIN_WINDOW"
    PROJECT_SELECTOR_WINDOW = "PROJECT_SELECTOR_WINDOW"
    """
        Helper class that holds global information in various parts of application
        Class is singleton. To access data, simple create instance.
    """

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Navigator, cls).__new__(cls)
            self = cls.instance
            # GUI ROOT
            self.root = None
            self.windows = {}
        return cls.instance

    def navigate(self, path):
        if path in self.windows:
            self.windows[path](self.root)
