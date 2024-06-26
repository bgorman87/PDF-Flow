from typing import List, Optional, Callable
from PySide6.QtWidgets import QMessageBox, QPushButton, QLayout, QSpacerItem, QSizePolicy
import os
import json
import uuid
from version import VERSION
import psutil

from utils import text_utils

class MessageBox:
    def __init__(
        self,
        title: str = "",
        icon: QMessageBox.Icon = QMessageBox.Information,
        text: str = "",
        buttons: List[QPushButton] = None,
        button_roles: List[QMessageBox.ButtonRole] = None,
        callback: Optional[Callable] = None,
    ):
        self.title = title
        self.icon = icon
        self.text = text
        self.buttons = buttons or []
        self.button_roles = button_roles or []
        self.callback = callback


class FauxResponse:
    def __init__(self, status_code: int, text: str):
        self.status_code = status_code
        self.text = text

def get_config_data(version: str = VERSION) -> dict:
    """Gets the configuration data from the config.json file.

    Returns:
        dict: The configuration data.
    """
    config_file_path = os.getenv("APPDATA") + "\\PDF Flow\\config.json"
    if os.path.exists(config_file_path):

        with open(config_file_path, "r") as f:
            config = json.load(f)
        
        if config['version'] != version:
            # TODO: Can create popup maybe to display update data here
            config['version'] = version
            set_config_data(config)

        pending = config["telemetry"].setdefault("pending", 0)
        
        config.setdefault("onedrive_check", True)
        config.setdefault("poppler_path", "")
        config.setdefault("tesseract_path", "")
        config.setdefault("backup_directory", "")
        config.setdefault("default_email", "")

        set_config_data(config)

        if pending > 0:
            identifier = config["telemetry"]["identifier"] if not config["telemetry"]["annonymous"] else None
            response = text_utils.post_telemetry_data(pending, identifier, "Update from pending value")
            if response is not None:
                config["telemetry"]["pending"] = 0
                set_config_data(config)
        
    else:
        os.makedirs(os.path.join(os.getenv("APPDATA"), "PDF Flow"), exist_ok=True)
        
        config = {
            "version": VERSION,
            "telemetry": {
                "annonymous": False,
                "identifier": str(uuid.uuid4()),
            },
            "batch-email": False,
            "onedrive_check": True,
            "poppler_path": "",
            "tesseract_path": "",
            "backup_directory": "",
            "default_email": ""
        }
        set_config_data(config)
    return config

def set_config_data(config: dict) -> None:
    """Sets the configuration data in the config.json file.

    Args:
        config (dict): The configuration data.
    """
    config_file_path = os.path.join(os.getenv("APPDATA"), "PDF Flow", "config.json")
    with open(config_file_path, "w") as f:
        json.dump(config, f, indent=4)

def get_key(my_dict, value):
    for key, val in my_dict.items():
        if val == value:
            return key
    return None

def is_onedrive_running() -> bool:
    """Checks if OneDrive is currently running.

    Returns:
        bool: True if OneDrive is running, False otherwise.
    """

    for proc in psutil.process_iter():
        if proc.name() == "OneDrive.exe":
            return True
    return False
    

def change_visibility_of_widgets_in_layout(layout: QLayout, visible: bool):
    """Changes the visibility of all widgets in a layout and maintains layout spacing.
    
    Args:
        layout (QLayout): The layout to change the visibility of.
        visible (bool): True if the widgets should be visible, False otherwise.
    """

    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item.widget():
            widget = item.widget()
            widget.setVisible(visible)

    layout.update()