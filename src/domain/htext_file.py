class HTextFile:
    """Object representation of internal HTextFile used for persisting HTEXT files.
    Contains only raw_text at the moment but can contain more information in future"""

    def __init__(self, text=None, formatting=None):
        self.raw_text = text
        self.formatting = formatting


class HTextFormattingTag:
    """Persistent information about HTextFormatting"""
    def __init__(self, tag_name=None, start_index=None, end_index=None):
        self.tag_name = tag_name
        self.start_index = start_index
        self.end_index = end_index
