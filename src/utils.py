
import os
import string
from src.const.paths import RUN_DIRECTORY


# UTIL METHODS
class Utils:
    @staticmethod
    def resource_path(relative_path: string):
        return os.path.join(RUN_DIRECTORY, relative_path)
