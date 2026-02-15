import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QPushButton, QWidget, QMainWindow, QGridLayout, QComboBox, QLineEdit, QCheckBox, QHBoxLayout, QStyleFactory, QSlider

class Window(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle('App')

        self.container = QWidget()
        self.setCentralWidget(self.container)
        self.main_layout = QGridLayout(self.container)

        self.button = QPushButton(
            'Button'
        )

        self.combobox = QComboBox()
        self.combobox.addItems(['One', 'Two', 'Three', 'Four'])

        self.lineedit = QLineEdit()

        self.container_checbox = QWidget()
        self.checkbox_layout = QHBoxLayout(self.container_checbox)

        self.checkbox1 = QCheckBox('A')
        self.checkbox2 = QCheckBox('B')
        self.checkbox3 = QCheckBox('C')
        
        self.checkbox_layout.addWidget(self.checkbox1, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.checkbox_layout.addWidget(self.checkbox2, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.checkbox_layout.addWidget(self.checkbox3, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)

        self.main_layout.addWidget(self.button, 0, 0)
        self.main_layout.addWidget(self.combobox, 0, 1)
        self.main_layout.addWidget(self.lineedit, 1, 0, 1, -1)
        self.main_layout.addWidget(self.container_checbox, 2, 0, 1, -1)
        self.main_layout.addWidget(self.slider, 3, 0, 1, -1)


app = QApplication(sys.argv)
print(app.libraryPaths())

app.addLibraryPath("/usr/lib/x86_64-linux-gnu/qt5/plugins")
# app.addLibraryPath("/usr/bin")
print(QStyleFactory.keys())
app.setStyle('Breeze')

window = Window()
window.show()

app.exec()
