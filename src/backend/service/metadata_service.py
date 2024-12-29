import json
import os
import string

from src.domain.metadata import Metadata


class MetadataService:
    # FUNCTION THAT LOADS EDITOR METADATA FROM FILE
    @staticmethod
    def load(path: string):
        if os.path.exists(path):
            with open(path, 'r') as file:
                metadata = json.load(file)
                return Metadata(metadata)
        else:
            return Metadata()

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save(metadata: Metadata, path: string):
        with open(path, 'w') as file:
            json.dump(metadata.to_dict(), file, indent=4)

    @staticmethod
    def get_recent_file(metadata: Metadata):
        file_path = None
        while len(metadata.recent_files) > 0 and file_path is None:
            file_path = metadata.recent_files[0]
            if not os.path.isfile(file_path):
                file_path = None
                metadata.recent_files.pop(0)
        return file_path

    @staticmethod
    def put_recent_file(metadata: Metadata, file_path: string):
        # MOVE RECENT FILE TO TOP, OR ADD NEW
        if file_path in metadata.recent_files:
            metadata.recent_files.remove(file_path)
        metadata.recent_files.insert(0, file_path)
        if len(metadata.recent_files) > 10:
            metadata.recent_files.pop()
