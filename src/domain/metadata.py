class Metadata:
    def __init__(self, data=None):
        """
        Constructor accepts a dictionary and sets the class attributes.
        If a key is not provided in the dictionary, the default value is used.

        :param data: Dictionary containing the data to initialize the object. If not provided, default values are used.
        """
        if data is None:
            data = {}
        self.recent_projects = []
        for rp in data.get('recent_projects', []):
            self.recent_projects.append(RecentProject(rp))

    def to_dict(self):
        recent_projects_maps = []
        for recent_project in self.recent_projects:
            recent_projects_maps.append(recent_project.to_dict())
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        return {
            "recent_projects": recent_projects_maps,
        }


class RecentProject:
    """Representation of recept project saved in Metadata.
    Used to display table of recent projects in project selector window"""

    def __init__(self, data=None):
        """
        Constructor accepts a dictionary and sets the class attributes.
        If a key is not provided in the dictionary, the default value is used.

        :param data: Dictionary containing the data to initialize the object. If not provided, default values are used.
        """
        if data is None:
            data = {}
        self.name = data.get('name', [])
        self.path = data.get('path', [])

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        return {
            "name": self.name,
            "path": self.path,
        }
