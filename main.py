import sys, os, platform
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEvent

from gui.main_window import MainWindow
from gui.crash_handler import install_exception_hook


class Application(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.windows = []
        self._next_window_id = 0
        

    def new_window(self, file_path=None):
        window = MainWindow(self._next_window_id)
        self._next_window_id += 1
        window.destroyed.connect(lambda: self.windows.remove(window) if window in self.windows else None)
        self.windows.append(window)
        window.show()
        if file_path:
            window.load_apk(file_path)
        return window

    def event(self, event):
        if event.type() == QEvent.FileOpen:
            file_path = event.file()
            print(f"FileOpen event caught: {file_path}")
            self.new_window(file_path)
            return True

        if event.type() == QEvent.ApplicationActivate:
            if not any(w.isVisible() for w in self.windows):
                self.new_window()
            return True

        return super().event(event)

def main():
    install_exception_hook()
    print(f"{__file__}: exception hook installed")

    app = Application(sys.argv)
    app.setQuitOnLastWindowClosed(platform.system() != "Darwin")

    initial_file = None
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        initial_file = sys.argv[1]

    app.new_window(initial_file)

    print(f"{__file__}: entering event loop")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()