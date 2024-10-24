
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
    def fa_image(font, background, foreground, char, size):
        img = Image.new("L", (size, size), background)
        draw = ImageDraw.Draw(img)
        font_awesome = ImageFont.truetype(font, size-4)
        draw.text((2, 2), char, foreground, font_awesome)
        return ImageTk.PhotoImage(img)
