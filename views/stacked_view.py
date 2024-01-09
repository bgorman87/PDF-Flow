"""Holds all of the stacked items"""

from PySide6 import QtWidgets
from views import console_view, file_name_view, template_view, data_viewer_view, process_view, email_view, settings_view
from view_models import file_name_view_model, main_view_model, stacked_view_model, console_view_model, template_view_model, data_viewer_view_model, process_view_model, email_view_model, settings_view_model

class StackedWidget(QtWidgets.QStackedWidget):
    def __init__(self, main_view_model: main_view_model.MainViewModel, Dispatch):
        super().__init__()
        self.main_view_model = main_view_model
        self.view_model = stacked_view_model.StackedViewModel(self.main_view_model)
        self.view_model.stacked_item_id_update.connect(lambda: self.setCurrentIndex(self.view_model.new_id))
        self.currentChanged.connect(lambda: self.view_model.reset_console_handler(self.indexOf(self.console_view)))
        
        self.process_view = process_view.ProcessView(process_view_model.ProcessViewModel(self.main_view_model, Dispatch))
        self.data_viewer_view = data_viewer_view.DataViewerView(data_viewer_view_model.DataViewerViewModel(self.main_view_model))
        self.template_view = template_view.TemplateView(template_view_model.TemplateViewModel(self.main_view_model))
        self.file_name_view = file_name_view.FileNameView(file_name_view_model.FileNameViewModel(self.main_view_model))
        self.email_view = email_view.EmailView(email_view_model.EmailViewModel(self.main_view_model))
        self.console_view = console_view.ConsoleWidget(console_view_model.ConsoleViewModel(self.main_view_model))
        self.settings_view = settings_view.SettingsView(settings_view_model.SettingsViewModel(self.main_view_model))

        self.addWidget(self.process_view)
        self.addWidget(self.data_viewer_view)
        self.addWidget(self.template_view)
        self.addWidget(self.file_name_view)
        self.addWidget(self.email_view)
        self.addWidget(self.console_view)
        self.addWidget(self.settings_view)