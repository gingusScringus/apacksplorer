import os
import platform
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox

from core.paths import resource_path
from core.file_assoc import associate_apk, AssocError

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = resource_path("forms", "settings.ui")
        uic.loadUi(ui_path, self)

        self.setWindowTitle("APacKsplorer - Settings")

        self.assocFilesButton.clicked.connect(self.associate_apks)

    def associate_apks(self):
        if platform.system() == "Darwin":
            QMessageBox.information(
                self,
                "File Associations",
                "on macOS, .apk file association is handled automatically by "
                "the app bundle - no need to do anything here."
            )
            return

        try:
            associate_apk()
        except AssocError as e:
            QMessageBox.warning(self, "Couldn't Associate Files", str(e))
            return

        QMessageBox.information(
            self,
            "File Associations",
            ".apk files are now associated with APacKsplorer."
        )