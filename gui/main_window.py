import sys
import os
from pathlib import Path

from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QApplication, QMessageBox
from PyQt5.QtGui import QPixmap

# resolve path for core
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# program modules
from core.apk import APK
from gui.settings_dialog import SettingsDialog
from gui.adb_dialog import AdbDialog


# resolve root path
def resource_path(*parts):
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).resolve().parents[1]
    return base.joinpath(*parts)

main_ui = resource_path("forms", "main.ui")
settings_dialog = resource_path("forms", "settings.ui")
adb_box = resource_path("forms", "adbop.ui")
prog_name = "APacKsplorer"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        print("hello am window!")

        uic.loadUi(main_ui, self)
        self.setWindowTitle(prog_name)
        self.actionOpen.triggered.connect(self.open_apk)
        self.actionAbout.triggered.connect(self.show_about)
        self.actionAboutQt.triggered.connect(QApplication.aboutQt)
        self.actionADB.triggered.connect(self.open_adb)
        self.actionSettings.triggered.connect(self.open_settings)
        
    def open_apk(self):
        # insert open file dialog
        print("should open file picker for apk")
        file_path, _ = QFileDialog.getOpenFileName(
            None, 
            "Select a File", 
            "", 
            "Android Packages (*.apk *.xapk *.apkm *.apks);;All Files (*)"
        )
        if not file_path:
            return
        
        print(f"got {file_path}")

        apk = APK(file_path)
        apk.parse()
        if apk.icon_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(apk.icon_bytes)
            self.app_icon_label.setPixmap(pixmap)

        print("Package:", apk.package)
        print("VersionCode:", apk.versionCode)
        print("VersionName:", apk.versionName)
        print("Native code:", apk.native_code)

        self.app_name_field.setText(apk.app_name)
        self.package_name_field.setText(apk.package)
        self.version_name_field.setText(apk.versionName)
        self.version_code_field.setText(apk.versionCode)
        self.min_sdk_field.setText(apk.minSdkVersion)
        self.target_sdk_field.setText(apk.targetSdkVersion)
        self.supported_abis_field.setText(" ".join(apk.native_code))
        self.screen_sizes_field.setText(" ".join(apk.supports_screens))  
        self.densities_field.setText(" ".join(apk.densities))

        self.setWindowTitle(f"{apk.app_name} | {prog_name}")

    def show_about(self):
        QMessageBox.about(
            None,
            "About APacKsplorer",
            """
            <h3>APacKsplorer</h3>
            <p>Version 69</p>
            <p>some apk reading thingy idgfk</p>
            <p>© 20006 ging</p>
            """
        )

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec_()

    def open_adb(self):
        self.adb_dlg = AdbDialog(self)
        self.adb_dlg.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())