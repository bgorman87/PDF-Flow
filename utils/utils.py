import sys
import os

def resource_path(relative_path: str) -> str:
    """Produces resource path for PyInstaller build and dev build depending which one is detected, since pyinstaller uses temporary folders to store assets. 

    Args:
        relative_path (str): relative path to file

    Returns:
        str: formatted path to resource
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)

class FauxResponse():
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text