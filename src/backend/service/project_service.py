import json
import os
import string

from src.domain.config import Config
from src.domain.project import Project


class ProjectService:
    # FUNCTION THAT LOADS PROJECT FROM FILE
    @staticmethod
    def load(path: string):
        if os.path.exists(path):
            with open(path, 'r') as file:
                p = json.load(file)
                return Project(p)
        else:
            return None

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save(p: Project, path: string):
        with open(path, 'w') as file:
            json.dump(p.to_dict(), file, indent=4)
