import json
import os
import string

from src.domain.metadata import Metadata, RecentProject
from src.domain.project import Project


class MetadataService:
    """Service for manipulation of global metadata"""
    @staticmethod
    def load(path: string):
        """Load metadata from file"""
        if os.path.exists(path):
            with open(path, 'r') as file:
                metadata = json.load(file)
                return Metadata(metadata)
        else:
            return Metadata()

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save(metadata: Metadata, path: string):
        """Save metadata to file"""
        with open(path, 'w') as file:
            json.dump(metadata.to_dict(), file, indent=4)

    @staticmethod
    def get_recent_file(metadata: Metadata):
        """Get latest available recent file"""
        file_path = None
        while len(metadata.recent_files) > 0 and file_path is None:
            file_path = metadata.recent_files[0]
            if not os.path.isfile(file_path):
                file_path = None
                metadata.recent_files.pop(0)
        return file_path

    @staticmethod
    def put_recent_file(metadata: Metadata, file_path: string):
        """Move recent file to top, or add new"""
        if file_path in metadata.recent_files:
            metadata.recent_files.remove(file_path)
        metadata.recent_files.insert(0, file_path)
        if len(metadata.recent_files) > 10:
            metadata.recent_files.pop()

    @staticmethod
    def put_recent_project(metadata: Metadata, project: Project, file_path: string):
        """Move recent project to top or add new"""
        rp = RecentProject()
        rp.path = file_path
        rp.name = project.name
        # MOVE RECENT FILE TO TOP, OR ADD NEW
        MetadataService.remove_recent_project(metadata, file_path)
        metadata.recent_projects.insert(0, rp)
        if len(metadata.recent_projects) > 10:
            metadata.recent_projects.pop()

    @staticmethod
    def remove_recent_project(metadata: Metadata, file_path: string):
        """Remove obsolete recent project"""
        metadata.recent_projects = [p for p in metadata.recent_projects if p.path != file_path]
