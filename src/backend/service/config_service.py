import json
import os
import string

from src.domain.config import Config


class ConfigService:
    """Service for manipulation of global config"""
    @staticmethod
    def load(path: string):
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
