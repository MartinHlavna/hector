import os
import re
import sys

import pypandoc

from src.utils import Utils


class ImportService:
    @staticmethod
    def normalize_text(text):
        clrf = re.compile("\r\n")
        corrected_text = re.sub(clrf, "\n", text)
        return corrected_text

    @staticmethod
    def import_document(file_path):
        if file_path.endswith(".txt"):
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        extra_args = (
            '--wrap=none',
            f'--lua-filter={Utils.resource_path(os.path.join("data_files", "fix_odt_blockquotes.lua"))}'
        )
        text = pypandoc.convert_file(file_path, 'plain', extra_args=extra_args)
        return ImportService.normalize_text(os.linesep.join([s for s in text.splitlines() if s]))

    @staticmethod
    def ensure_pandoc_available():
        """Download pandoc if not already installed"""

    try:
        # Check whether it is already installed
        pypandoc.get_pandoc_version()
    except OSError:
        # Pandoc not installed. Let's download it silently.
        with open(os.devnull, 'w') as devnull:
            sys.stdout = devnull
            pypandoc.download_pandoc()
            sys.stdout = sys.__stdout__

        # Hack to delete the downloaded file from the folder,
        # otherwise it could get accidently committed to the repo
        # by other scripts in the repo.
        pf = sys.platform
        if pf.startswith('linux'):
            pf = 'linux'
        url = pypandoc.pandoc_download._get_pandoc_urls()[0][pf]
        filename = url.split('/')[-1]
        os.remove(filename)
