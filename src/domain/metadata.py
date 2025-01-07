class Metadata:
    def __init__(self, data=None):
        """
        Constructor accepts a dictionary and sets the class attributes.
        If a key is not provided in the dictionary, the default value is used.

        :param data: Dictionary containing the data to initialize the object. If not provided, default values are used.
        """
        if data is None:
            data = {}
        self.recent_files = data.get('recent_files', [])
        self.recent_projects = data.get('recent_projects', [])

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        return {
            "recent_files": self.recent_files,
            "recent_projects": self.recent_projects,
        }
