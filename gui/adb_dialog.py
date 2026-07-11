from PyQt5 import QtWidgets, uic
import os

class AdbDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = os.path.join(os.path.dirname(__file__), "..", "forms", "adbop.ui")
        uic.loadUi(ui_path, self)