from PIL import ImageFont, ImageDraw, Image, ImageTk


class GuiUtils:
    @staticmethod
    def fa_image(font, background, foreground, char, size, padding=2):
        img = Image.new("L", (size, size), background)
        draw = ImageDraw.Draw(img)
        font_awesome = ImageFont.truetype(font, size - (padding * 2))
        draw.text((padding, padding), char, foreground, font_awesome)
        return ImageTk.PhotoImage(img)
