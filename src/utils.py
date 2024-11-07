import ctypes
import json
import os
import re
import string

import requests
import semver;
from semver import VersionInfo

from src.const.paths import RUN_DIRECTORY
from PIL import ImageFont, ImageDraw, Image, ImageTk

from src.const.values import VERSION, GITHUB_REPO


# UTIL METHODS
class Utils:
    @staticmethod
    def resource_path(relative_path: string):
        return os.path.join(RUN_DIRECTORY, relative_path)

    @staticmethod
    def fa_image(font, background, foreground, char, size, padding=2):
        img = Image.new("L", (size, size), background)
        draw = ImageDraw.Draw(img)
        font_awesome = ImageFont.truetype(font, size - (padding * 2))
        draw.text((padding, padding), char, foreground, font_awesome)
        return ImageTk.PhotoImage(img)

    @staticmethod
    def get_windows_scaling_factor():
        # Windows API call to get DPI scaling (for Windows)
        user32 = ctypes.windll.user32
        user32.SetProcessDPIAware()  # Optional, allows Python process to be aware of the DPI
        dpi = user32.GetDpiForSystem()
        # Standard DPI is 96, so scale factor is based on that
        scaling_factor = dpi / 96
        return scaling_factor

    @staticmethod
    def get_build_info():
        with open(Utils.resource_path(os.path.join('data_files', 'build_info.json')), 'r', encoding='utf-8') as file:
            return json.load(file)

    @staticmethod
    def get_version_info():
        build_info = Utils.get_build_info()
        return f'{VERSION} {build_info["channel"]} {build_info["platform"]}'

    def extract_version_from_tag(tag: str) -> str:
        """
        Extracts the version number from a tag string.

        :param tag: Tag string, e.g., "v.0.10.3-beta".
        :return: Extracted version number, e.g., "0.10.3", or None if no version is found.
        """
        match = re.search(r'\b(\d+\.\d+\.\d+)\b', tag)
        return match.group(1) if match else None

    @staticmethod
    def check_updates(current_version: string, beta: bool = False) -> bool:
        """
        Fetches the latest release version from a GitHub repository.

        :param current_version: Current version.
        :param beta: If True, includes prerelease versions.
        :return: Tag name of the latest release or prerelease version, or None if unavailable.
        """
        url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise an error for HTTP errors
            releases = response.json()

            # Filter releases based on the 'beta' parameter
            if not beta:
                releases = [release for release in releases if not release['prerelease']]
            else:
                releases = [release for release in releases if release['prerelease']]

            # Get the latest release (GitHub returns them in descending order by release date)
            if releases:
                latest_version = VersionInfo.parse(Utils.extract_version_from_tag(releases[0]['tag_name']))
                current_version = VersionInfo.parse(VERSION)
                return latest_version > current_version
            return False

        except requests.RequestException:
            print("Unable to retrieve data. Please check your internet connection.")
            return None
