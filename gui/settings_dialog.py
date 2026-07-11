from PyQt5 import QtWidgets, uic
import os

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), "..", "forms", "settings.ui")
        uic.loadUi(ui_path, self)

        # wire up whatever buttons settings.ui has, e.g.:
        # self.saveButton.clicked.connect(self.save_settings)