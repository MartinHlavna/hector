import json
import os
import string

from src.domain.config import Config


class ConfigService:
    # FUNCTION THAT LOADS CONFIG FROM FILE
    @staticmethod
    def load(path: string):
        if os.path.exists(path):
            with open(path, 'r') as file:
                c = json.load(file)
                return Config(c)
        else:
            return Config()

    # FUNCTION THAT SAVES CONFIG TO FILE
    @staticmethod
    def save(c: Config, path: string):
        with open(path, 'w') as file:
            json.dump(c.to_dict(), file, indent=4)
