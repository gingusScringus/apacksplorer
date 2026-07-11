import sys
from PyQt5.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.crash_handler import install_exception_hook


def main():
    install_exception_hook()
    print(f"{__file__}: exception hook installed")

    app = QApplication(sys.argv)

    window = MainWindow()
    print(f"{__file__}: showing window")
    window.show()

    print(f"{__file__}: entering event loop")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()