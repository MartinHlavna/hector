import json
import os
import pathlib
import shutil
import string
from xml.dom.minidom import parseString

import untangle
from dicttoxml import dicttoxml

from src.domain.htext_file import HTextFile
from src.domain.project import Project, ProjectItem, ProjectItemType, DirectoryProjectItem
from src.utils import Utils


class ProjectService:

    @staticmethod
    def create_project(name, description, folder_path):
        """Crate new project in selected folder"""
        project = Project()
        project.name = name
        project.description = description
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)
        project_file_path = os.path.join(folder_path, f"{Utils.normalize_file_name(name)}.hproj")
        project.path = project_file_path
        ProjectService.save(project, project_file_path)
        return project

    """Service for project manipulation"""
    @staticmethod
    def load(path: string):
        """Load project from file"""
        if os.path.exists(path):
            with open(path, 'r') as file:
                p = json.load(file)
                return Project(p, path)
        else:
            return None

    @staticmethod
    def save(p: Project, path: string):
        """Save project to file"""
        with open(path, 'w') as file:
            p.path = path
            json.dump(p.to_dict(), file, indent=4)

    @staticmethod
    def new_item(p: Project, name: str, parent_item: DirectoryProjectItem, item_type: ProjectItemType):
        """Add new project item"""
        item = None
        data_dir = os.path.join(os.path.dirname(p.path), "data")
        if parent_item is not None:
            dir_path = os.path.join(data_dir, parent_item.path)
        else:
            dir_path = os.path.join(data_dir, "data")
        if item_type == ProjectItemType.DIRECTORY:
            path = os.path.join(dir_path, name)
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                item = DirectoryProjectItem()
                item.type = ProjectItemType.DIRECTORY
        else:
            os.makedirs(dir_path, exist_ok=True)
            path = os.path.join(dir_path, f"{Utils.normalize_file_name(name)}.htext")
            if not os.path.exists(path):
                open(path, 'w').close()
                item = ProjectItem()
                item.type = ProjectItemType.HTEXT
        item.path = os.path.relpath(path, data_dir)
        item.name = name
        if parent_item is not None:
            parent_item.subitems.append(item)
        else:
            p.items.append(item)

        ProjectService.save(p, p.path)
        return item

    @staticmethod
    def delete_item(p: Project, item: ProjectItem, parent_item: DirectoryProjectItem):
        """Delete existing item"""
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
        """Save contents of a HTEXT file"""
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
        """Save contents of a HTEXT file"""
        path = os.path.join(os.path.dirname(p.path), "data", item.path)
        if os.path.exists(path):
            with open(path, 'w') as file:
                xml = dicttoxml(vars(item.contents), attr_type=False, custom_root='htext', return_bytes=False)
                dom = parseString(xml)
                file.write(dom.toprettyxml(standalone=True))
                return True
        return False
