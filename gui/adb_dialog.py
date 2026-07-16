import sys
from PyQt5 import QtWidgets, uic
from pathlib import Path

# resolve path for core
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.paths import resource_path

class AdbDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        ui_path = resource_path("forms", "adbop.ui")
        uic.loadUi(ui_path, self)

        self.installButton.clicked.connect(self.install)
        self.uninstallButton.clicked.connect(self.uninstall)
        self.installRunButton.clicked.connect(self.install_run)
        self.listDevicesButton.clicked.connect(self.device_list)
        

    def install(self, file_path):
        print(f"install {file_path}")

    def install_run(self, file_path):
        print(f"install and run {file_path}")

    def uninstall(self, file_path):
        print(f"uninstall {file_path}")
    
    def device_list(self):
        print(f"list devices")

