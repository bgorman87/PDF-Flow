from typing import List, Optional, Callable
from PySide6.QtWidgets import QMessageBox, QPushButton
import os
import json
import uuid
from version import VERSION

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
            # Can display update data here
            config['version'] = version
            set_config_data(config)

        if not config["telemetry"].get("pending"):
            config["telemetry"]["pending"] = 0
            set_config_data(config)
        else:
            pending = config["telemetry"]["pending"]

        if pending > 0:
            identifier = config["telemetry"]["identifier"] if not config["telemetry"]["annonymous"] else None
            response = text_utils.post_telemetry_data(pending, identifier, "Update from pending value")
            if response is not None:
                config["telemetry"]["pending"] = 0
                set_config_data(config)
        
    else:
        os.makedirs(os.getenv("APPDATA") + "\\PDF Flow\\", exist_ok=True)
        
        config = {
            "version": VERSION,
            "telemetry": {
                "annonymous": False,
                "identifier": str(uuid.uuid4()),
            },
            "batch-email": False,
        }
        set_config_data(config)
    return config

def set_config_data(config: dict) -> None:
    """Sets the configuration data in the config.json file.

    Args:
        config (dict): The configuration data.
    """
    config_file_path = os.getenv("APPDATA") + "\\PDF Flow\\config.json"
    with open(config_file_path, "w") as f:
        json.dump(config, f, indent=4)

def get_key(my_dict, value):
    for key, val in my_dict.items():
        if val == value:
            return key
    return None


    