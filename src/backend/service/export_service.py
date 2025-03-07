import os
import re
import pypandoc
import zipfile
import xml.etree.ElementTree as ET
import shutil

from src.utils import Utils


class ExportService:
    """Service for generating hector exports"""

    @staticmethod
    def export_sentences(path, doc, blank_line_between_sents):
        """Export sentences as a text file."""
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
                        text += "\n"
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
                text += "\n"
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)

    @staticmethod
    def export_text_file(file_path, text):
        """Export raw text file."""
        if file_path:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(text)

    @staticmethod
    def export_rich_file(file_path: str,
                         html: str,
                         default_font: str = "Arial",
                         heading_font: str = "Verdana",
                         first_line_indent: float = 12.7,
                         line_spacing: float = 1.2,
                         spacing_before: float = 0.0,
                         spacing_after: float = 0.0) -> None:
        """
        Converts an HTML string to a target format (docx, odt, rtf) and saves it to file_path using pypandoc.
        Additionally, if exporting to DOCX, or RTF, the document is post-processed with default fonts and paragraph settings.

        The parameters first_line_indent, spacing_before, and spacing_after are expected in millimeters.
        The line_spacing parameter is expected as a multiple (e.g. 1.15, 1.2, 1.5).
        :param html: The HTML string to convert.
        :param file_path: The output file path. The file extension (e.g. 'docx', 'odt', 'rtf')
                          determines the output format.
        :param default_font: The default font for regular text (default: Arial).
        :param heading_font: The font for headings (default: Verdana).
        :param first_line_indent: The first line indent in millimeters (default: 12.7 mm).
        :param line_spacing: The line spacing as a multiple (default: 1.15).
        :param spacing_before: Spacing before paragraph in millimeters (default: 0.0).
        :param spacing_after: Spacing after paragraph in millimeters (default: 0.0).
        :raises ValueError: If the file extension is not one of the supported types.
        """
        ext = os.path.splitext(file_path)[1].lower().strip(".")
        allowed_formats = ["docx", "rtf"]
        if ext not in allowed_formats:
            raise ValueError(f"Unsupported output format: {ext}. Supported formats: {allowed_formats}")

        # Convert HTML to target format and save to file_path.
        pypandoc.convert_text(
            html,
            to=ext,
            format="html",
            outputfile=file_path,
            extra_args=[
                f"--css={Utils.resource_path(os.path.join('data_files', 'pandoc.css'))}",
                "--embed-resources",
                "--standalone"
            ]
        )

        # Post-process the exported file based on its type.
        if ext == "docx":
            ExportService._set_docx_styles(
                file_path,
                default_font,
                heading_font,
                first_line_indent,
                line_spacing,
                spacing_before,
                spacing_after
            )
        elif ext == "rtf":
            ExportService._set_rtf_styles(
                file_path,
                default_font,
                first_line_indent=first_line_indent,
                line_spacing=line_spacing,
                spacing_before=spacing_before,
                spacing_after=spacing_after
            )

    @staticmethod
    def _set_docx_styles(file_path: str,
                         default_font: str = "Arial",
                         heading_font: str = "Verdana",
                         first_line_indent: float = 12.7,
                         line_spacing: float = 1.15,
                         spacing_before: float = 0.0,
                         spacing_after: float = 0.0) -> None:
        """
        Prepares a DOCX file by modifying its styles.xml to set the default font, heading font,
        first line indent, line spacing (as a multiple), spacing before/after paragraphs, and paragraph alignment (justify).

        The parameters first_line_indent, spacing_before, and spacing_after are expected in millimeters.
        The line_spacing parameter is expected as a multiple (e.g. 1.15, 1.2, 1.5).
        """
        # Conversion factor: 1 mm = 1440/25.4 twips
        twips_per_mm = 1440 / 25.4
        first_line_indent_twips = int(round(first_line_indent * twips_per_mm))
        spacing_before_twips = int(round(spacing_before * twips_per_mm))
        spacing_after_twips = int(round(spacing_after * twips_per_mm))
        # For DOCX, 1.0 line spacing equals 240 twips.
        line_spacing_twips = int(round(line_spacing * 240))
        print(first_line_indent_twips, line_spacing_twips)

        temp_dir = "temp_docx"
        with zipfile.ZipFile(file_path, "r") as zin:
            zin.extractall(temp_dir)

        styles_path = os.path.join(temp_dir, "word", "styles.xml")
        tree = ET.parse(styles_path)
        root = tree.getroot()
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

        def set_paragraph_properties(pPr):
            # Set first line indent
            ind = pPr.find("w:ind", ns)
            if ind is None:
                ind = ET.SubElement(pPr, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ind")
            ind.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}firstLine",
                    str(first_line_indent_twips))
            # Set spacing before, after and line spacing (as a multiple)
            spacing = pPr.find("w:spacing", ns)
            if spacing is None:
                spacing = ET.SubElement(pPr, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}spacing")
            spacing.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}line", str(line_spacing_twips))
            spacing.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}lineRule", "auto")
            spacing.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}before", str(spacing_before_twips))
            spacing.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}after", str(spacing_after_twips))
            # Set paragraph alignment to justify
            jc = pPr.find("w:jc", ns)
            if jc is None:
                jc = ET.SubElement(pPr, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}jc")
            jc.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", "both")

        # Update docDefaults for run properties (fonts)
        for rPr in root.findall(".//w:docDefaults/w:rPrDefault/w:rPr", ns):
            rFonts = rPr.find("w:rFonts", ns)
            if rFonts is None:
                rFonts = ET.SubElement(rPr, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
            rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii", default_font)
            rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi", default_font)
            rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia", default_font)
            rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cs", default_font)

        # Update docDefaults for paragraph properties (indentation, spacing and alignment)
        for pPr in root.findall(".//w:docDefaults/w:pPrDefault/w:pPr", ns):
            set_paragraph_properties(pPr)

        # Update each style: font and paragraph properties
        for style in root.findall(".//w:style", ns):
            style_id = style.get("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}styleId")
            chosen_font = heading_font if style_id and style_id.lower().startswith("heading") else default_font

            # Update run properties for font
            rPr = style.find("w:rPr", ns)
            if rPr is None:
                rPr = ET.SubElement(style, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rPr")
            rFonts = rPr.find("w:rFonts", ns)
            if rFonts is None:
                rFonts = ET.SubElement(rPr, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}rFonts")
            rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}ascii", chosen_font)
            rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}hAnsi", chosen_font)
            rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia", chosen_font)
            rFonts.set("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cs", chosen_font)

            # Update paragraph properties
            pPr = style.find("w:pPr", ns)
            if pPr is None:
                pPr = ET.SubElement(style, "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pPr")
            set_paragraph_properties(pPr)

        tree.write(styles_path, encoding="utf-8", xml_declaration=True)

        # Repackage the DOCX file with the updated styles.xml
        with zipfile.ZipFile(file_path, "w") as zout:
            for foldername, subfolders, filenames in os.walk(temp_dir):
                for filename in filenames:
                    filepath = os.path.join(foldername, filename)
                    arcname = os.path.relpath(filepath, temp_dir)
                    zout.write(filepath, arcname)
        shutil.rmtree(temp_dir)

    @staticmethod
    def _set_rtf_styles(file_path: str,
                        default_font: str = "Arial",
                        # heading_font is not applied in this simple RTF implementation
                        first_line_indent: float = 12.7,
                        line_spacing: float = 1.15,
                        spacing_before: float = 0.0,
                        spacing_after: float = 0.0) -> None:
        """
        Prepares an RTF file by modifying its content to set the default font,
        first line indent, line spacing (as a multiple), spacing before/after paragraphs,
        and paragraph alignment (justify).

        This implementation uses a simple regex replacement for demonstration purposes.
        """
        # Conversion factors
        twips_per_mm = 1440 / 25.4
        first_line_indent_twips = int(round(first_line_indent * twips_per_mm))
        spacing_before_twips = int(round(spacing_before * twips_per_mm))
        spacing_after_twips = int(round(spacing_after * twips_per_mm))
        line_spacing_twips = int(round(line_spacing * 240))

        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            rtf_content = file.read()

        # Build the RTF paragraph formatting control words.
        new_paragraph_code = (
            f"\\fi{first_line_indent_twips}"
            f"\\sb{spacing_before_twips}"
            f"\\sa{spacing_after_twips}"
            f"\\sl{line_spacing_twips}\\qj"
        )
        # Use a lambda function to safely insert our new paragraph codes before each \par.
        rtf_content = re.sub(r"(\\par)", lambda m: new_paragraph_code + m.group(1), rtf_content)

        # Replace the default font in the font table for \f0 with the default_font.
        rtf_content = re.sub(r"({\\fonttbl.*?\\f0\s+)([^;]+)(;)",
                             r"\1" + default_font + r"\3", rtf_content, flags=re.DOTALL)

        with open(file_path, "w", encoding="utf-8") as file:
            file.write(rtf_content)
