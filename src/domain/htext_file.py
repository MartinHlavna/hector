class HTextFile:
    """Object representation of internal HTextFile used for persisting HTEXT files.
    Contains only raw_text at the moment but can contain more information in future"""

    def __init__(self, text):
        self.raw_text = text
