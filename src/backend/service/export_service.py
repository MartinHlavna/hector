class ExportService:
    """Service for generating hector exports"""
    @staticmethod
    def export_sentences(path, doc, blank_line_between_sents):
        """Export sentences as an text file."""
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

    @staticmethod
    def export_text_file(file_path, text):
        """Export raw text file"""
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(text)
