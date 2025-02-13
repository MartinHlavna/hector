import copy
import json
import os
import string

from src.domain.config import Config
from src.domain.project import ProjectItem, Project


class ConfigService:
    """Service for manipulation of global config"""
    @staticmethod
    def load(path: string) -> Config:
        """Load config from file"""
        if os.path.exists(path):
            with open(path, 'r') as file:
                c = json.load(file)
                return Config(c)
        else:
            return Config()

    @staticmethod
    def save(c: Config, path: string):
        """Save config to file"""
        with open(path, 'w') as file:
            json.dump(c.to_dict(), file, indent=4)

    @staticmethod
    def select_config(global_config: Config, project: Project, item: ProjectItem) -> Config:
        """Selects config based on priority"""
        if item is not None:
            i = item
            while i is not None:
                if i.config is None:
                    i = i.parent
                else:
                    return i.config

        if project is not None and project.config is not None:
            return project.config
        return global_config
