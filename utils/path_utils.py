import sys
from os.path import join, abspath


def resource_path(relative_path: str) -> str:
    """Produces resource path for PyInstaller build and dev build depending which one is detected, since pyinstaller uses temporary folders to store assets.

    Args:
        relative_path (str): relative path to file

    Returns:
        str: formatted path to resource
    """
    if hasattr(sys, "_MEIPASS"):
        return join(sys._MEIPASS, relative_path)
    return join(abspath("."), relative_path)
