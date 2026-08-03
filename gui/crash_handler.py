# crash_handler.py
import sys
import traceback
from PyQt5.QtWidgets import QMessageBox

from core import __progname__

print("CRASH HANDLER READY")

def handle_exception(exc_type, exc_value, exc_traceback):
    print("handling exception")
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    tb_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(tb_text, file=sys.stderr)

    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Ouch!")
    msg.setText(f"{__progname__} ran into an unexpected error and needs to close. Please report this to the developer!")
    msg.setDetailedText(tb_text)
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec_()

    sys.exit(1)

def install_exception_hook():
    sys.excepthook = handle_exception
    print("exception hook installed")