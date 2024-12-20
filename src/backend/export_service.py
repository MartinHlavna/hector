import os
import re
import sys

import pypandoc

from src.utils import Utils


class ExportService:
    @staticmethod
    def export_sentences(path, doc, blank_line_between_sents):
        text = ""
        cur_sent = ""
        for sent in doc.sents:
            # STRIP NEWLINES
            sent_text = sent.text.replace("\r\n", "").replace("\n", "")
            if len(sent_text) > 1:
                # ADD CURRENT SENTENCE TO TEXT
                if len(cur_sent) > 0:
                    text += f"{cur_sent}\n"
                    if blank_line_between_sents:
                        text += '\n'
                    cur_sent = ""
                if len(sent_text) > 0:
                    cur_sent = sent_text
            elif len(sent_text) > 0:
                # MERGE TO PREVIOUS SENTENCE
                cur_sent += sent_text
        # ADD LAST SENTENCE TO TEXT
        if len(cur_sent) > 0:
            text += f"{cur_sent}\n"
            if blank_line_between_sents:
                text += '\n'
        with open(path, 'w', encoding='utf-8') as file:
            file.write(text)
