import json
import os
import string

from src.domain.config import Config
from src.domain.project import Project, ProjectItem, ProjectItemType
from src.utils import Utils


class ProjectService:
    # FUNCTION THAT LOADS PROJECT FROM FILE
    @staticmethod
    def load(path: string):
        if os.path.exists(path):
            with open(path, 'r') as file:
                p = json.load(file)
                return Project(p, path)
        else:
            return None

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save(p: Project, path: string):
        with open(path, 'w') as file:
            json.dump(p.to_dict(), file, indent=4)

    @staticmethod
    def new_file(p: Project, name):
        data_dir = os.path.join(os.path.dirname(p.path), "data")
        os.makedirs(data_dir, exist_ok=True)
        path = os.path.join(data_dir, f"{Utils.normalize_file_name(name)}.htext")
        if not os.path.exists(path):
            open(path, 'w')
            item = ProjectItem()
            item.name = name
            item.path = os.path.relpath(path, data_dir)
            item.type = ProjectItemType.HTEXT
            p.items.append(item)
            ProjectService.save(p, p.path)
            return True
        return False


