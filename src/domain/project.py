from enum import Enum

from src.const.values import CURRENT_PROJECT_VERSION


class Project:
    def __init__(self, data=None):
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
        self.items = []
        for i in data.get('items', []):
            item = ProjectItem(i)
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
        self.imported_path = data.get('imported_path', '')

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        return {
            'type': self.type,
            'path': self.path,
            'imported_path': self.imported_path,
        }


class ProjectItemType(Enum):
    UNKNOWN = 1
    HTEXT = 2
