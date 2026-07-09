from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QWidget
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt


class MacDialog(QDialog):
    def __init__(self, title, message=None, icon_pixmap=None, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setMinimumWidth(300)
        self._buttons = []
        self._result_text = None

        self.setStyleSheet("""
            QDialog {
                background-color: #3a3a3c;
                border-radius: 12px;
            }
        """)

        self._layout = QVBoxLayout(self)
        self._layout.setSpacing(12)
        self._layout.setContentsMargins(24, 24, 24, 20)

        # optional icon
        if icon_pixmap:
            icon_label = QLabel()
            icon_label.setPixmap(icon_pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(icon_label)

        # title
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: white;")
        self._layout.addWidget(title_label)

        # optional subtitle
        if message:
            msg_label = QLabel(message)
            msg_font = QFont()
            msg_font.setPointSize(11)
            msg_label.setFont(msg_font)
            msg_label.setAlignment(Qt.AlignCenter)
            msg_label.setWordWrap(True)
            msg_label.setStyleSheet("color: rgba(255,255,255,0.75);")
            self._layout.addWidget(msg_label)

        self._layout.addSpacing(4)
        self._btn_layout = QVBoxLayout()
        self._btn_layout.setSpacing(8)
        self._layout.addLayout(self._btn_layout)

    def add_button(self, text, primary=False, destructive=False):
        btn = QPushButton(text)
        btn.setMinimumHeight(36)
        btn.setCursor(Qt.PointingHandCursor)

        if primary:
            style = """
                QPushButton {
                    background-color: #e03030;
                    color: white;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #c02020; }
                QPushButton:pressed { background-color: #a01010; }
            """
        elif destructive:
            style = """
                QPushButton {
                    background-color: #555558;
                    color: #ff453a;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #636366; }
                QPushButton:pressed { background-color: #48484a; }
            """
        else:
            style = """
                QPushButton {
                    background-color: #555558;
                    color: white;
                    border-radius: 8px;
                    font-size: 14px;
                }
                QPushButton:hover { background-color: #636366; }
                QPushButton:pressed { background-color: #48484a; }
            """

        btn.setStyleSheet(style)
        btn.clicked.connect(lambda: self._on_click(text))
        self._btn_layout.addWidget(btn)
        self._buttons.append(btn)
        return btn

    def _on_click(self, text):
        self._result_text = text
        self.accept()

    def get_result(self):
        return self._result_text
    
