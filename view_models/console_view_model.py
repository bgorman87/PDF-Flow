from PySide6.QtCore import QObject, Signal

from view_models import main_view_model


class ConsoleViewModel(QObject):
    """ViewModel to manage console-related operations and interactions."""
    
    console_text_insert = Signal()
    
    def __init__(self, main_view_model: 'main_view_model.MainViewModel'):
        """Initializes the ConsoleViewModel with a connection to the main view model.

        Args:
            main_view_model (main_view_model.MainViewModel): Reference to the main view model.
        """
        super().__init__()
        self.main_view_model = main_view_model
        self.main_view_model.console_text_update.connect(lambda: self.add_console_text(self.main_view_model.console_text))
        self._new_console_text = ""

    def add_console_text(self, console_text: str) -> None:
        """Updates the console text and emits a signal to indicate the insertion.

        Args:
            console_text (str): Text to be added to the console.
        """
        self._new_console_text = console_text
        self.console_text_insert.emit()

    @property
    def text(self) -> str:
        """Returns the new console text to add with a newline appended."""
        return f"{self._new_console_text}\n"

    @text.setter
    def text(self, value: str) -> None:
        """Sets the console text and emits a signal for insertion.

        Args:
            value (str): The new text value to be inserted into the console.
        """
        self._new_console_text = value
        self.console_text_insert.emit()
