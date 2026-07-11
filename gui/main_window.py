import sys
import os
import re
import pprint
import webbrowser
import requests
from pathlib import Path

from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtWidgets import QFileDialog, QApplication, QMessageBox, QTreeWidgetItem, QTableWidgetItem, QAction, QInputDialog
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QSettings

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
MAX_RECENT_FILES = 10
DEFAULT_RENAME_PATTERN = "%label% %version%.%build%"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        print("hello am window!")

        uic.loadUi(main_ui, self)
        self.setWindowTitle(prog_name)
        self.setAcceptDrops(True)

        self.settings = QSettings("gingTEC", "APacKsplorer")

        self.actionOpen.triggered.connect(self.open_apk)
        self.actionAbout.triggered.connect(self.show_about)
        self.actionAboutQt.triggered.connect(QApplication.aboutQt)
        self.actionADB.triggered.connect(self.open_adb)
        self.actionSettings.triggered.connect(self.open_settings)
        self.actionPlay_Store.triggered.connect(self.search_play_store)
        self.actionAPKMirror.triggered.connect(self.search_apkmirror)
        self.actionWeb_Search.triggered.connect(self.search_web)
        self.actionVirusTotal.triggered.connect(self.open_virustotal)
        self.actionAPK_Update.triggered.connect(self.apk_update)
        self.actionClean_Rename.triggered.connect(self.clean_rename)

        self.update_recent_menu()

        # weird ass Qt implementation for having readonly checkboxes forced me to do this
        for checkbox in (
            self.androidCheck,
            self.androidTVCheck,
            self.androidAutoCheck,
            self.wearOSCheck,
            self.openGLESCheck,
            self.vulkanCheck,
        ):
            checkbox.setCheckable(True)
            checkbox.setEnabled(True)
            checkbox.setFocusPolicy(QtCore.Qt.NoFocus)
            checkbox.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

        # disable utilities item before apk loaded
        self.menuSearch.setEnabled(False)
        self.actionClean_Rename.setEnabled(False)
        self.actionADB.setEnabled(False)
        self.actionPlay_Store.setEnabled(False)
        self.actionWeb_Search.setEnabled(False)
        self.actionAPKMirror.setEnabled(False)
        self.actionVirusTotal.setEnabled(False)
        self.actionAPK_Update.setEnabled(False)

    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if not urls:
            return

        file_path = urls[0].toLocalFile()

        if not os.path.isfile(file_path):
            return

        self.load_apk(file_path)

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
        
        self.load_apk(file_path)

    def load_apk(self, file_path):

        print(f"got {file_path}")
        apk = APK(file_path)
        try:
            apk.parse()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid APK", str(e))
            return
        except RuntimeError as e:
            QMessageBox.critical(self, "APacKsplorer Error", str(e))
            return
        
        self.add_recent_file(file_path)
        
        if apk.icon_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(apk.icon_bytes)
            self.app_icon_label.setPixmap(pixmap)

        pprint.pprint(apk.__dict__)

        self.app_name_field.setText(apk.app_name)
        self.package_name_field.setText(apk.package)
        self.version_name_field.setText(apk.versionName)
        self.version_code_field.setText(apk.versionCode)
        self.min_sdk_field.setText(apk.format_sdk_level(apk.minSdkVersion))
        self.max_sdk_field.setText(apk.format_sdk_level(apk.maxSdkVersion))
        self.target_sdk_field.setText(apk.format_sdk_level(apk.targetSdkVersion))
        self.compile_sdk_field.setText(apk.format_sdk_level(apk.compileSdkVersion))
        self.supported_abis_field.setText(" ".join(apk.native_code))
        self.screen_sizes_field.setText(" ".join(apk.supports_screens))  
        self.densities_field.setText(" ".join(apk.densities))

        self.androidCheck.setChecked(apk.supports_android)
        self.androidTVCheck.setChecked(apk.supports_android_tv)
        self.androidAutoCheck.setChecked(apk.supports_android_auto)
        self.wearOSCheck.setChecked(apk.supports_wear_os)
        self.openGLESCheck.setChecked(apk.uses_opengles)
        self.openGLESCheck.setText(f"OpenGL ES {apk.opengl_es_version}")
        self.vulkanCheck.setChecked(apk.uses_vulkan)

        self.featuresTree.clear()

        uses_root = QTreeWidgetItem(self.featuresTree, ["Uses"])
        for feature in apk.uses_features['uses']:
            QTreeWidgetItem(uses_root, ["", feature])

        implied_root = QTreeWidgetItem(self.featuresTree, ["Implied"])
        for feature in apk.uses_features['implied']:
            item = QTreeWidgetItem(implied_root, ["", feature['name']])
            item.setToolTip(1, feature['reason'])

        not_required_root = QTreeWidgetItem(self.featuresTree, ["Not Required"])
        for feature in apk.uses_features['not_required']:
            QTreeWidgetItem(not_required_root, ["", feature])

        self.featuresTree.expandAll()

        self.permissionsList.clear()
        self.permissionsList.addItems(apk.uses_permissions)

        self.appLocalesTable.setRowCount(0)
        self.appLocalesTable.setRowCount(len(apk.locales))

        for row, locale in enumerate(apk.locales):
            display_locale = "default" if locale == "--_--" else locale

            locale_item = QTableWidgetItem(display_locale)
            self.appLocalesTable.setItem(row, 0, locale_item)

            label = apk.application_labels.get(display_locale, '')
            label_item = QTableWidgetItem(label)
            self.appLocalesTable.setItem(row, 1, label_item)
        
        self.menuSearch.setEnabled(True)
        self.actionClean_Rename.setEnabled(True)
        self.actionADB.setEnabled(True)
        self.actionPlay_Store.setEnabled(True)
        self.actionWeb_Search.setEnabled(True)
        self.actionAPKMirror.setEnabled(True)
        self.actionVirusTotal.setEnabled(True)
        self.actionAPK_Update.setEnabled(True)

        self.setWindowTitle(f"{apk.app_name} | {prog_name}")
        self.current_apk = apk

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

    def get_recent_files(self):
        return self.settings.value("recentFiles", [])

    def add_recent_file(self, file_path):
        recent = self.get_recent_files()

        if file_path in recent:
            recent.remove(file_path)  # move to top instead of duplicating

        recent.insert(0, file_path)
        recent = recent[:MAX_RECENT_FILES]

        self.settings.setValue("recentFiles", recent)
        self.update_recent_menu()

    def update_recent_menu(self):
        self.menuOpen_Recent.clear()

        recent = self.get_recent_files()

        if not recent:
            empty_action = QAction("(no recent files)", self)
            empty_action.setEnabled(False)
            self.menuOpen_Recent.addAction(empty_action)
            return

        for file_path in recent:
            action = QAction(os.path.basename(file_path), self)
            action.setToolTip(file_path)
            action.triggered.connect(lambda checked, path=file_path: self.load_apk(path))
            self.menuOpen_Recent.addAction(action)

        self.menuOpen_Recent.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self.clear_recent_files)
        self.menuOpen_Recent.addAction(clear_action)

    def clear_recent_files(self):
        self.settings.setValue("recentFiles", [])
        self.update_recent_menu()

    def search_play_store(self):
        if not self.current_apk:
            return
        url = f"https://play.google.com/store/apps/details?id={self.current_apk.package}"
        webbrowser.open(url)

    def search_apkmirror(self):
        if not self.current_apk:
            return
        url = f"https://www.apkmirror.com/?post_type=app_release&searchtype=app&s={self.current_apk.package}"
        webbrowser.open(url)

    def search_web(self):
        if not self.current_apk:
            return
        url = f"https://www.google.com/search?q={self.current_apk.package}"
        webbrowser.open(url)

    def open_virustotal(self):
        if not self.current_apk:
            return
        url = f"https://www.virustotal.com/gui/file/{self.current_apk.sha256}/detection"
        webbrowser.open(url)

    def apk_update(self):
        if not self.current_apk:
            return

        pkg = self.current_apk.package
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:62.0) Gecko/20100101 Firefox/62.0"}

        results = []

        # Play Store
        try:
            resp = requests.get(f"https://play.google.com/store/apps/details?hl=en&id={pkg}", headers=headers, timeout=10)
            match = re.search(r"Current Version</div><span .*?>([^<]*?)</span></div>", resp.text)
            play_version = match.group(1).strip() if match else "not found"
        except requests.RequestException:
            play_version = "error fetching"

        # APKPure
        try:
            resp = requests.get(f"https://apkpure.com/apk-info/{pkg}", headers=headers, timeout=10)
            match = re.search(r"version_name: '([^']*?)'", resp.text)
            apkpure_version = match.group(1).strip() if match else "not found"
        except requests.RequestException:
            apkpure_version = "error fetching"

        current = self.current_apk.versionName
        msg = f"Current installed version: {current}\n\nPlay Store: {play_version}\nAPKPure: {apkpure_version}"
        QMessageBox.information(self, "Check for Update", msg)
    def clean_rename(self):
        if not self.current_apk:
            return

        apk = self.current_apk
        proposed = apk.sanitize_filename(apk.format_filename(DEFAULT_RENAME_PATTERN)) + ".apk"

        new_name, ok = QInputDialog.getText(
            self, "Clean Rename", "New filename:", text=proposed
        )
        if not ok or not new_name:
            return

        old_path = apk.path
        new_path = os.path.join(os.path.dirname(old_path), new_name)

        if os.path.exists(new_path):
            QMessageBox.warning(self, "Rename Failed", f"A file named '{new_name}' already exists.")
            return

        try:
            os.rename(old_path, new_path)
        except OSError as e:
            QMessageBox.warning(self, "Rename Failed", str(e))
            return

        apk.path = new_path
        self.setWindowTitle(f"{apk.app_name} | {prog_name}")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())