
import os
import string
import sys


# UTIL METHODS
class Utils:
    @staticmethod
    def resource_path(relative_path: string):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
