import sys
from PyQt5 import QtWidgets, uic

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi(".../ui/free.ui", self)

        self.pushButton.clicked.connect(self.button_clicked)
    
    def button_clicked(self):
        print("FREE SHIT CUMMING!!!")


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())