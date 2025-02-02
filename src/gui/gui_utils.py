import os

from PIL import ImageFont, ImageDraw, Image, ImageTk
import tkinter as tk
from tkinter import messagebox, ttk

from src.backend.run_context import RunContext
from src.backend.service.metadata_service import MetadataService
from src.backend.service.project_service import ProjectService
from src.const.paths import METADATA_FILE_PATH
from src.domain.metadata import RecentProject
from src.domain.project import Project


class GuiUtils:
    @staticmethod
    def is_child_of(parent, widget):
        """ Recursively check if widget is child of parent """
        while widget:
            if widget == parent:
                return True
            widget = widget.master
        return False

    @staticmethod
    def fa_image(font, background, foreground, char, size, padding=2):
        return ImageTk.PhotoImage(GuiUtils.fa_image_raw(font, background, foreground, char, size, padding))

    @staticmethod
    def fa_image_raw(font, background, foreground, char, size, padding=2):
        img = Image.new("RGBA", (size, size), background)
        draw = ImageDraw.Draw(img)
        font_awesome = ImageFont.truetype(font, size - (padding * 2))
        draw.text((padding, padding), char, foreground, font_awesome)
        return img

    @staticmethod
    def merge_icons(icon1: Image, icon2: Image, space_between=2) -> Image:
        """Merge two icons into one"""
        width = icon1.width + icon2.width + space_between
        height = max(icon1.height, icon2.height)
        merged_image = Image.new("RGBA", (width, height))
        merged_image.paste(icon1, (0, 0))
        merged_image.paste(icon2, (icon1.width + space_between, 0))
        return merged_image

    @staticmethod
    def open_recent_project(project: RecentProject, e=None):
        if project.path is None or not os.path.isfile(project.path):
            metadata = MetadataService.load(METADATA_FILE_PATH)
            MetadataService.remove_recent_project(metadata, project.path)
            MetadataService.save(metadata, METADATA_FILE_PATH)
            messagebox.showerror("Nie je možné otvoriť projekt", "Projekt bol pravdepodobne zmazaný, alebo presnutý.")
            return False
        return GuiUtils.open_project(ProjectService.load(project.path))

    @staticmethod
    def open_project(project: Project):
        metadata = MetadataService.load(METADATA_FILE_PATH)
        MetadataService.put_recent_project(metadata, project, project.path)
        MetadataService.save(metadata, METADATA_FILE_PATH)
        ctx = RunContext()
        ctx.project = project
        ctx.current_file = None
        return True

    @staticmethod
    def stylename_elements_options(stylename):
        '''Function to expose the options of every element associated to a widget
           stylename.'''
        try:
            # Get widget elements
            style = ttk.Style()
            layout = str(style.layout(stylename))
            print('Stylename = {}'.format(stylename))
            print('Layout    = {}'.format(layout))
            elements=[]
            for n, x in enumerate(layout):
                if x=='(':
                    element=""
                    for y in layout[n+2:]:
                        if y != ',':
                            element=element+str(y)
                        else:
                            elements.append(element[:-1])
                            break
            print('\nElement(s) = {}\n'.format(elements))

            # Get options of widget elements
            for element in elements:
                print('{0:30} options: {1}'.format(
                    element, style.element_options(element)))

        except tk.TclError:
            print('_tkinter.TclError: "{0}" in function'
                  'widget_elements_options({0}) is not a regonised stylename.'
                  .format(stylename))
