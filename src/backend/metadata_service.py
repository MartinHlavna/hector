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
