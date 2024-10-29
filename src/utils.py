import ctypes
import os
import string

from src.const.paths import RUN_DIRECTORY
from PIL import ImageFont, ImageDraw, Image, ImageTk


# UTIL METHODS
class Utils:
    @staticmethod
    def resource_path(relative_path: string):
        return os.path.join(RUN_DIRECTORY, relative_path)

    @staticmethod
    def fa_image(font, background, foreground, char, size, padding=2):
        img = Image.new("L", (size, size), background)
        draw = ImageDraw.Draw(img)
        font_awesome = ImageFont.truetype(font, size-(padding*2))
        draw.text((padding, padding), char, foreground, font_awesome)
        return ImageTk.PhotoImage(img)

    @staticmethod
    def get_windows_scaling_factor():
        # Windows API call to get DPI scaling (for Windows)
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()  # Optional, allows Python process to be aware of the DPI
        dpi = user32.GetDpiForSystem()
        # Standard DPI is 96, so scale factor is based on that
        scaling_factor = dpi / 96
        return scaling_factor
