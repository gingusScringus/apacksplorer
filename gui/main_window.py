import sys
import os
import re
import pprint
import webbrowser
import requests
from pathlib import Path

from PyQt5 import QtCore, QtWidgets, QtGui, uic
from PyQt5.QtWidgets import QFileDialog, QApplication, QMessageBox, QTreeWidgetItem, QTableWidgetItem, QAction, QInputDialog, QDialog, QVBoxLayout
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QSettings, QEvent

# resolve path for core
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# program modules
from core import __version__, __progname__
from core.paths import resource_path
from core.apk import APK
from gui.settings_dialog import SettingsDialog
from gui.adb_dialog import AdbDialog

main_ui = resource_path("forms", "main.ui")
settings_dialog = resource_path("forms", "settings.ui")
adb_box = resource_path("forms", "adbop.ui")
MAX_RECENT_FILES = 10
DEFAULT_RENAME_PATTERN = "%label% %version%.%build%"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, window_id=None):
        super().__init__()

        self.window_id = window_id
        print(f"hello iam window {self.window_id}!")

        uic.loadUi(main_ui, self)
        self.setWindowTitle(__progname__)
        self.setAcceptDrops(True)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # track currently-loaded APK (None when no APK loaded)
        self.current_apk = None

        self.settings = QSettings("gingTEC", "APacKsplorer")

        # File
        self.actionOpen.triggered.connect(self.open_apk)
        self.actionSettings.triggered.connect(self.open_settings)
        self.actionNew_Window.triggered.connect(self.new_window)

        # Utilities
        self.actionADB.triggered.connect(self.open_adb)
        self.actionClean_Rename.triggered.connect(self.clean_rename)
        self.actionPlay_Store.triggered.connect(self.search_play_store)
        self.actionAPKMirror.triggered.connect(self.search_apkmirror)
        self.actionWeb_Search.triggered.connect(self.search_web)
        self.actionVirusTotal.triggered.connect(self.open_virustotal)
        self.actionAPK_Update.triggered.connect(self.apk_update)

        # Help
        self.actionAbout.triggered.connect(self.show_about)
        self.actionAboutQt.triggered.connect(QApplication.aboutQt)
        self.actionCheck_for_Updates.triggered.connect(self.check_for_updates)
        self.actionAAPT_output.triggered.connect(self.aapt_raw_output)

        self.update_recent_menu()

        # weird ass Qt implementation for having readonly checkboxes forced me to do this
        for checkbox in (
            self.androidCheck,
            self.androidTVCheck,
            self.androidAutoCheck,
            self.wearOSCheck,
            self.openGLESCheck,
            self.vulkanCheck,
            self.signedCheck,
            self.xmlIconCheck,
        ):
            checkbox.setCheckable(True)
            checkbox.setEnabled(True)
            checkbox.setFocusPolicy(QtCore.Qt.NoFocus)
            checkbox.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

        # disable utilities item before apk loaded
        self.menuSearch.setEnabled(False)
        self.actionClean_Rename.setEnabled(False)
        # self.actionADB.setEnabled(False)
        self.actionPlay_Store.setEnabled(False)
        self.actionWeb_Search.setEnabled(False)
        self.actionAPKMirror.setEnabled(False)
        self.actionVirusTotal.setEnabled(False)
        self.actionAPK_Update.setEnabled(False)
        self.actionIcon_Browser.setEnabled(False)

    
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

    def event(self, event):
        if event.type() == QEvent.FileOpen:
            self.load_apk(event.file())
            return True
        return super().event(event)

    def new_window(self):
        QApplication.instance().new_window()

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

        print(f"[window {self.window_id}] got {file_path}")
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
            pixmap = pixmap.scaled(96, 96, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.app_icon_label.setPixmap(pixmap)

        pprint.pprint(apk.__dict__)
        text_fields = [
            (self.app_name_field, apk.app_name),
            (self.package_name_field, apk.package),
            (self.version_name_field, apk.versionName),
            (self.version_code_field, apk.versionCode),
            (self.min_sdk_field, apk.format_sdk_level(apk.minSdkVersion)),
            (self.max_sdk_field, apk.format_sdk_level(apk.maxSdkVersion)),
            (self.target_sdk_field, apk.format_sdk_level(apk.targetSdkVersion)),
            (self.compile_sdk_field, apk.format_sdk_level(apk.compileSdkVersion)),
            (self.supported_abis_field, " ".join(apk.native_code)),
            (self.screen_sizes_field, " ".join(apk.supports_screens)),
            (self.densities_field, " ".join(apk.densities)),
            (self.hash_field, " ".join(apk.sha256)),
]

        for field, value in text_fields:
            field.setText(value)
            field.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
            field.setCursorPosition(0)
            field.deselect()

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

        self.setWindowTitle(f"{apk.app_name} | {__progname__}")
        self.current_apk = apk

    def show_about(self):
        QMessageBox.about(
            None,
            f"About {__progname__}",
            f"""
            <h3>{__progname__}</h3>
            <p>Version {__version__}</p>
            <p>some apk reading thingy idgfk</p>
            <p>© 2026 gingusScringus</p>
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
        self.setWindowTitle(f"{apk.app_name} | {__progname__}")

    def check_for_updates(self):
        print("make updater thingy")

    def aapt_raw_output(self):
        if not self.current_apk:
            return

        output = "".join(self.current_apk.raw_output)

        dlg = QDialog()
        dlg.setWindowTitle("AAPT Output")

        layout = QVBoxLayout()

        text = QtWidgets.QPlainTextEdit(dlg)
        text.setReadOnly(True)
        text.setPlainText(output)

        font = QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        text.setFont(font)
        layout.addWidget(text)

        copy_btn = QtWidgets.QPushButton("Copy to Clipboard", dlg)
        copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(text.toPlainText()))
        layout.addWidget(copy_btn)

        dlg.setLayout(layout)
        dlg.exec_()
        

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())