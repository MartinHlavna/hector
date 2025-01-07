from enum import Enum

from src.const.values import CURRENT_PROJECT_VERSION


class Project:
    def __init__(self, data=None, path=None):
        """
        Constructor accepts a dictionary and sets the class attributes.
        If a key is not provided in the dictionary, the default value is used.

        :param data: Dictionary containing the data to initialize the object. If not provided, default values are used.
        """
        if data is None:
            data = {}
        self.name = data.get('name', None)
        self.version = data.get('version', CURRENT_PROJECT_VERSION)
        self.description = data.get('description', None)
        self.path = path
        self.items = []
        for i in data.get('items', []):
            item = Project.construct_project_item(i)
            self.items.append(item)

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        items = []
        for i in self.items:
            item = i.to_dict()
            items.append(item)
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'items': items

        }

    @staticmethod
    def construct_project_item(data):
        if data.get('type', ProjectItemType.UNKNOWN) == ProjectItemType.DIRECTORY:
            return DirectoryProjectItem(data)
        return ProjectItem(data)


class ProjectItem:
    def __init__(self, data=None):
        """
        Constructor accepts a dictionary and sets the class attributes.
        If a key is not provided in the dictionary, the default value is used.

        :param data: Dictionary containing the data to initialize the object. If not provided, default values are used.
        """
        if data is None:
            data = {}
        self.type = data.get('type', ProjectItemType.UNKNOWN)
        self.path = data.get('path', '')
        self.name = data.get('name', '')
        self.imported_path = data.get('imported_path', '')
        # TRANSIENT
        self.contents = None

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        return {
            'name': self.name,
            'type': self.type,
            'path': self.path,
            'imported_path': self.imported_path,
        }


class DirectoryProjectItem(ProjectItem):
    def __init__(self, data=None):
        """
        Constructor accepts a dictionary and sets the class attributes.
        If a key is not provided in the dictionary, the default value is used.

        :param data: Dictionary containing the data to initialize the object. If not provided, default values are used.
        """
        if data is None:
            data = {}
        super().__init__(data)
        self.subitems = []
        self.opened = data.get("opened", False)
        for i in data.get('subitems', []):
            item = Project.construct_project_item(i)
            self.subitems.append(item)

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        output = super().to_dict()
        subitems = []
        for i in self.subitems:
            item = i.to_dict()
            subitems.append(item)
        output['opened'] = self.opened
        output['subitems'] = subitems
        return output


class ProjectItemType(str, Enum):
    UNKNOWN = "UNKNOWN"
    HTEXT = "HTEXT"
    DIRECTORY = "DIRECTORY"

    @staticmethod
    def get_selectable_values():
        return {
            "Textový súbor": ProjectItemType.HTEXT,
            "Priečinok": ProjectItemType.DIRECTORY
        }

    @staticmethod
    def get_translations():
        return {
            ProjectItemType.HTEXT: "textový súbor",
            ProjectItemType.DIRECTORY: "priečinok"
        }
