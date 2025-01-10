import ctypes
import json
import os
import platform
import re
import string
import unicodedata

import requests
from semver import VersionInfo

from src.const.paths import RUN_DIRECTORY
from src.const.values import VERSION, GITHUB_REPO


# UTIL METHODS
class Utils:
    @staticmethod
    def resource_path(relative_path: string):
        return os.path.join(RUN_DIRECTORY, relative_path)

    @staticmethod
    def get_windows_scaling_factor():
        if platform.system() == "Windows":
            # Windows API call to get DPI scaling (for Windows)
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()  # Optional, allows Python process to be aware of the DPI
            dpi = user32.GetDpiForSystem()
            # Standard DPI is 96, so scale factor is based on that
            scaling_factor = dpi / 96
            return scaling_factor
        return None

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
    def check_updates(current_version: string, beta: bool = False, github_token: string = None,
                      github_user: string = None) -> bool:
        """
        Checks if there is available update

        :param current_version: Current version.
        :param beta: If True, includes prerelease versions.
        :return: Tag name of the latest release or prerelease version, or None if unavailable.
        """
        latest_version = Utils.find_latest_version(beta, github_token, github_user)
        if latest_version is not None:
            current_version = VersionInfo.parse(current_version)
            return latest_version > current_version
        return False

    @staticmethod
    def find_latest_version(beta: bool = False, github_token: string = None,
                            github_user: string = None, skip: int = 0) -> string:
        """
        Fetches the latest release version from a GitHub repository.

        :param beta: If True, includes prerelease versions.
        :return: Tag name of the latest release or prerelease version, or None if unavailable.
        """
        # noinspection PyBroadException
        try:
            url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
            headers = {}
            if github_token is not None:
                headers['Authorization'] = f'Bearer {github_token}'
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()  # Raise an error for HTTP errors
            releases = response.json()

            # Filter releases based on the 'beta' parameter
            if not beta:
                releases = [release for release in releases if not release['prerelease']]
            else:
                releases = [release for release in releases if release['prerelease']]

            # Get the latest release (GitHub returns them in descending order by release date)
            if releases:
                return Utils.extract_version_from_tag(releases[min(len(releases) - 1, skip)]['tag_name'])
            return None

        except Exception as e:
            print(e)
            print("Unable to retrieve data. Please check your internet connection.")
            return None

    # METHOD THAT REMOVES ACCENTS FROM STRING
    @staticmethod
    def remove_accents(text):
        nfkd_form = unicodedata.normalize('NFD', text)
        return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

    # METHOD THAT NORMALIZES UNICODE SPACES TO SIMPLE SPACE
    @staticmethod
    def normalize_spaces(text):
        return re.sub(r"[^\S\n]", " ", text, flags=re.UNICODE)