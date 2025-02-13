from enum import Enum

from src.const.values import CURRENT_PROJECT_VERSION
from src.domain.config import Config


class Project:
    """Main project class. Contains all project information and is used to store all project metadata"""

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
        self.config = None
        config = data.get('config', None)
        if config is not None:
            self.config = Config(config)
        for i in data.get('items', []):
            item = Project.construct_project_item(i, None)
            self.items.append(item)

    def to_dict(self) -> dict:
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        items = []
        for i in self.items:
            item = i.to_dict()
            items.append(item)
        output = {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'items': items
        }
        if self.config is not None:
            output['config'] = self.config.to_dict()
        return output

    @staticmethod
    def construct_project_item(data, parent):
        """Helper function that construct ProjectItem or appropiate subclass"""
        if data.get('type', ProjectItemType.UNKNOWN) == ProjectItemType.DIRECTORY:
            return DirectoryProjectItem(data, parent)
        return ProjectItem(data, parent)


class ProjectItem:
    """Single file or directory in project"""

    def __init__(self, data=None, parent=None):
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
        self.config = None
        config = data.get('config', None)
        if config is not None:
            self.config = Config(config)
        # TRANSIENT
        self.contents = None
        self.parent = parent

    def to_dict(self):
        """
        Exports the current state of the object to a dictionary.

        :return: Dictionary containing the current state of the object.
        """
        output = {
            'name': self.name,
            'type': self.type,
            'path': self.path,
            'imported_path': self.imported_path,
        }
        if self.config is not None:
            output['config'] = self.config.to_dict()
        return output


class DirectoryProjectItem(ProjectItem):
    """Special ProjectItem used for directories. Stores opened state and subitems"""

    def __init__(self, data=None, parent=None):
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
            item = Project.construct_project_item(i, parent)
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
    """Enum with available ProjectItemTypes"""
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
