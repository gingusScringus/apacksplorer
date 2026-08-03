import os
import sys
import re
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import QProcess
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtWidgets import QMessageBox
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

        self.main_window = parent

        self.process = None
        self.devices_process = None

        self.installButton.clicked.connect(self.install)
        self.uninstallButton.clicked.connect(self.uninstall)
        self.installRunButton.clicked.connect(self.install_run)
        self.nuclearUninstallButton.clicked.connect(self.nuclear_uninstall)
        self.refreshDevicesButton.clicked.connect(self.refresh_devices)
        self.submitButton.clicked.connect(self.run_custom_command)
        self.clearOutputButton.clicked.connect(self.adbLogfield.clear)

        self.deviceList.itemSelectionChanged.connect(self.update_button_states)

        self.set_buttons_enabled(False)
        self.refresh_devices()

        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.adbLogfield.setFont(font)
        

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_devices()

    def set_buttons_enabled(self, enabled):
        self.installButton.setEnabled(enabled)
        self.uninstallButton.setEnabled(enabled)
        self.installRunButton.setEnabled(enabled)
        self.nuclearUninstallButton.setEnabled(enabled)
        # self.refreshDevicesButton.setEnabled(enabled)
        # self.submitButton.setEnabled(enabled)
        # self.clearOutputButton.setEnabled(enabled)

    def update_button_states(self):
        has_selection = len(self.deviceList.selectedItems()) > 0
        busy = self.process is not None and self.process.state() != QProcess.NotRunning
        self.set_buttons_enabled(has_selection and not busy)

    def selected_serial(self):
        items = self.deviceList.selectedItems()
        if not items:
            return None
        return items[0].data(1)  # serial stashed in UserRole+1, see refresh_devices

    def log(self, text):
        self.adbLogfield.appendPlainText(text)

    def refresh_devices(self):
        self.deviceList.clear()

        self.devices_process = QProcess(self)
        self.devices_process.finished.connect(self._on_devices_listed)
        self.devices_process.start("adb", ["devices", "-l"])

    def _on_devices_listed(self):
        process = self.devices_process
        if process is None:
            return
        output = bytes(process.readAllStandardOutput()).decode("utf-8", errors="replace")

        for line in output.splitlines():
            line = line.strip()
            if not line or line.startswith("List of devices attached"):
                continue

            parts = line.split()
            if not parts:
                continue

            serial = parts[0]
            model_match = re.search(r"model:(\S+)", line)
            model = model_match.group(1) if model_match else "Unknown device"

            display = f"{model} ({serial})"
            item = QtWidgets.QListWidgetItem(display)
            item.setData(1, serial)  # Qt.UserRole + 1, stash raw serial for command building
            self.deviceList.addItem(item)

        self.update_button_states()

    def _apk_path(self):
        apk = getattr(self.main_window, "current_apk", None)
        if apk is None:
            self.log("No APK loaded in main window.")
            return None
        return apk.path

    def _package_name(self):
        apk = getattr(self.main_window, "current_apk", None)
        if apk is None:
            return None
        return apk.package

    def _run_adb(self, args, on_finished=None):
        """
        starts a QProcess running `adb <args>`, streaming output to the log box live.
        on_finished, if given, is called with no args once the process finishes cleanly -
        used for chaining install -> run.
        """
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)  # combine stdout+stderr into one stream, matches old AutoIt STDERR_MERGED behavior
        self.process.readyReadStandardOutput.connect(self._on_process_output)

        if on_finished:
            self.process.finished.connect(lambda code, status: self._on_process_finished(code, status, on_finished))
        else:
            self.process.finished.connect(lambda code, status: self._on_process_finished(code, status, None))

        self.set_buttons_enabled(False)
        self.log(f"$ adb {' '.join(args)}")
        self.process.start("adb", args)

    def _on_process_output(self):
        data = bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        for line in data.splitlines():
            self.log(line)

    def _on_process_finished(self, exit_code, exit_status, on_finished):
        self.log(f"(exited {exit_code})")
        self.process = None
        self.update_button_states()
        if on_finished and exit_code == 0:
            on_finished()

    def install(self, file_path):
        print(f"install {file_path}")
        serial = self.selected_serial()
        apk_path = self._apk_path()
        if not serial or not apk_path:
            return
        self._run_adb(["-s", serial, "install", "-r", apk_path])

    def install_run(self, file_path):
        print(f"install and run {file_path}")
        serial = self.selected_serial()
        apk_path = self._apk_path()
        package = self._package_name()
        if not serial or not apk_path or not package:
            return
        
        def run_app():
            self._run_adb([
                "-s", serial, "shell", "monkey",
                "-p", package, "-c", "android.intent.category.LAUNCHER", "1"
            ])

        self._run_adb(["-s", serial, "install", "-r", apk_path], on_finished=run_app)

    def uninstall(self, file_path):
        print(f"uninstall {file_path}")
        serial = self.selected_serial()
        package = self._package_name()
        if not serial or not package:
            return
        self._run_adb(["-s", serial, "uninstall", package])

    def nuclear_uninstall(self, file_path):
        print(f"nuclear uninstall {file_path}")
        warn = QMessageBox.warning(
            self, 
            "Warning", 
            "This will delete your associated app's data and cannot be undone! Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if warn == QMessageBox.Yes:
            print("user clicked yes")
            serial = self.selected_serial()
            package = self._package_name()
            if not serial or not package:
                return
            self._run_adb(["-s", serial, "shell", "pm", "clear", package])

        else:
            print("user clicked no")

    def run_custom_command(self):
        text = self.commandField.text().strip()
        if not text:
            return

        serial = self.selected_serial()
        if not serial:
            self.log("No device selected.")
            return

        args = ["-s", serial] + text.split()
        self._run_adb(args)
        self.commandField.clear()

