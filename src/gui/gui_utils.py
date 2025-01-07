from PIL import ImageFont, ImageDraw, Image, ImageTk
import tkinter as tk
from tkinter import messagebox, ttk

class GuiUtils:
    @staticmethod
    def fa_image(font, background, foreground, char, size, padding=2):
        img = Image.new("RGBA", (size, size), background)
        draw = ImageDraw.Draw(img)
        font_awesome = ImageFont.truetype(font, size - (padding * 2))
        draw.text((padding, padding), char, foreground, font_awesome)
        return ImageTk.PhotoImage(img)

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
