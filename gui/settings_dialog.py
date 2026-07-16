from PyQt5 import QtWidgets, uic

from core.paths import resource_path


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = resource_path("forms", "settings.ui")
        uic.loadUi(ui_path, self)

        # wire up whatever buttons settings.ui has, e.g.:
        # self.saveButton.clicked.connect(self.save_settings)