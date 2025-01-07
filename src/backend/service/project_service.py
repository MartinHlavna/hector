import json
import os
import pathlib
import shutil
import string
from pathlib import Path
from xml.dom.minidom import parseString

import untangle
from dicttoxml import dicttoxml

from src.domain.htext_file import HTextFile
from src.domain.project import Project, ProjectItem, ProjectItemType, DirectoryProjectItem
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
    def new_file(p: Project, name, parent_item: DirectoryProjectItem):
        data_dir = os.path.join(os.path.dirname(p.path), "data")
        if parent_item is not None:
            dir_path = os.path.join(data_dir, parent_item.path)
        else:
            dir_path = os.path.join(os.path.dirname(p.path), "data")
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, f"{Utils.normalize_file_name(name)}.htext")
        if not os.path.exists(path):
            open(path, 'w')
            item = ProjectItem()
            item.name = name
            item.path = os.path.relpath(path, data_dir)
            item.type = ProjectItemType.HTEXT
            if parent_item is not None:
                parent_item.subitems.append(item)
            else:
                p.items.append(item)
            ProjectService.save(p, p.path)
            return item
        return None

    @staticmethod
    def new_directory(p: Project, name, parent_item: DirectoryProjectItem):
        data_dir = os.path.join(os.path.dirname(p.path), "data")
        if parent_item is not None:
            dir_path = os.path.join(data_dir, parent_item.path, name)
        else:
            dir_path = os.path.join(os.path.dirname(p.path), "data", name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            item = DirectoryProjectItem()
            item.name = name
            item.path = os.path.relpath(dir_path, data_dir)
            item.type = ProjectItemType.DIRECTORY
            if parent_item is not None:
                parent_item.subitems.append(item)
            else:
                p.items.append(item)
            ProjectService.save(p, p.path)
            return item
        return None

    @staticmethod
    def delete_item(p: Project, item: ProjectItem, parent_item: DirectoryProjectItem):
        data_dir = os.path.join(os.path.dirname(p.path), "data")
        path = os.path.join(data_dir, item.path)
        if os.path.exists(path):
            if item.type == ProjectItemType.DIRECTORY:
                shutil.rmtree(path)
            else:
                os.remove(path)
            if parent_item is not None:
                parent_item.subitems.remove(item)
            else:
                p.items.remove(item)
            ProjectService.save(p, p.path)
            return item
        return None

    @staticmethod
    def load_file_contents(p: Project, item: ProjectItem):
        path = os.path.join(os.path.dirname(p.path), "data", item.path)
        if os.path.exists(path):
            content = pathlib.Path(path).read_text()
            if len(content) > 0:
                doc = untangle.parse(path)
                return HTextFile(doc.htext.raw_text.cdata)
            else:
                return HTextFile("")
        return None

    @staticmethod
    def save_file_contents(p: Project, item: ProjectItem):
        path = os.path.join(os.path.dirname(p.path), "data", item.path)
        if os.path.exists(path):
            with open(path, 'w') as file:
                xml = dicttoxml(vars(item.contents), attr_type=False, custom_root='htext', return_bytes=False)
                dom = parseString(xml)
                file.write(dom.toprettyxml(standalone=True))
                return True
        return False
