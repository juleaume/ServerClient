import sys
from typing import Union

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QHBoxLayout, \
    QGroupBox, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox

from client import Client
from gui import MessageBox
from utils import log, socket

THEMES = {
    "Cyberpunk": "background-color: #002b36; "
                 "color: #b58900;"
                 "font-size: 15px",
    "Fallout": "background-color: #001f00; "
               "color: #1bff80;"
               "font-size: 15px"
}


class Window(QMainWindow):
    client_signal = pyqtSignal()
    agnostic = False

    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Messenger")
        self.setStyleSheet(THEMES.get("Cyberpunk"))
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)
        self._setup_page()
        self.client_box = MessageBox(self, "MSN")
        self.layout.addWidget(self.client_box)
        self.client = None  # type: Union[None, Client]
        self._name = socket.gethostname()
        self.client_box.address_button.clicked.connect(self.create_client)
        self.show()

    def _set_stylesheet(self):
        theme = self.theme_combo.currentText()
        self.setStyleSheet(THEMES.get(theme))

    def create_client(self):
        self.client = Client(
            self.client_box.ip, self.client_box.port, self.client_signal
        )
        self.client.name = self._name
        self.client_box.connect(self.client)
        self.client_signal.connect(self.client_box.update_text)
        self.client.connect()
        self.client.run()
        self.client_box.user_text_message_box.setEnabled(self.client.connected)

    def _setup_page(self):
        setup_box = QGroupBox("User")
        layout = QVBoxLayout()
        setup_box.setLayout(layout)
        self.layout.addWidget(setup_box)
        username_label = QLabel("Username")
        username_label.setStyleSheet("text-decoration: underline")
        layout.addWidget(username_label, alignment=Qt.AlignTop)
        self.username_entry = QLineEdit()
        layout.addWidget(self.username_entry, alignment=Qt.AlignTop)
        self.set_username = QPushButton("Set username")
        layout.addWidget(self.set_username, alignment=Qt.AlignTop)
        self.set_username.clicked.connect(self._set_username)
        self.username_entry.returnPressed.connect(self.set_username.click)
        theme_label = QLabel("Theme")
        theme_label.setStyleSheet("text-decoration: underline")
        layout.addWidget(theme_label, alignment=Qt.AlignTop)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(list(THEMES.keys()))
        self.theme_combo.currentTextChanged.connect(self._set_stylesheet)
        layout.addWidget(self.theme_combo, Qt.AlignTop)

    def _set_username(self):
        if self.username_entry.text():
            name = self.username_entry.text()
        else:
            name = socket.gethostname()
        self._name = name
        if self.client is not None:
            if self.client.name != name:
                former_name = self.client.name
                self.client.name = name
                self.client.send_message(f"<{former_name} is now {name}>")

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        log.info("closing window")
        if self.client is not None:
            self.client.stop()
            del self.client


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
