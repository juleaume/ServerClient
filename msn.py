import os
import sys
import json
import threading
from typing import Union

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QWidget, QHBoxLayout, \
    QGroupBox, QVBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from playsound import playsound

from client import Client
from gui import MessageBox, SocketConfigurator
from utils import log, socket
from themes import COLOR_SCHEME, THEMES, DEFAULT_THEME

CONFIG_FILE = ".config"
DEFAULT_NAME = f"{os.getlogin()}@{socket.gethostname()}"


class Window(QMainWindow):
    client_signal = pyqtSignal()
    agnostic = False

    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Messenger")
        if not os.path.isfile(CONFIG_FILE):
            with open(CONFIG_FILE, 'w') as conf:
                json.dump(
                    {
                        "theme": DEFAULT_THEME,
                        "username": DEFAULT_NAME,
                        "ip": "127.0.0.1",
                        "port": "7979"
                    }, conf)
        with open(".config", 'r') as conf:
            self.config = json.load(conf)
        self.setStyleSheet(THEMES.get(self.config.get("theme", "Solarized")))
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)
        self._setup_page()
        self.messenger_box = MessageBox(self, "MSN")
        self.layout.addWidget(self.messenger_box)
        self.client = None  # type: Union[None, Client]
        self._name = self.config.get("username", DEFAULT_NAME)
        self.show()

    def _set_stylesheet(self):
        self.icon_label.clear()
        theme = self.theme_combo.currentText()
        theme_icon = QPixmap(
            os.path.join("icons", theme)
        ).scaledToWidth(128).scaledToHeight(128)
        self.icon_label.setPixmap(theme_icon)
        self.setStyleSheet(THEMES.get(theme))
        self.save_config("theme", theme)

    def _save_address(self):
        self.save_config("ip", self.address_box.ip)
        self.save_config("port", self.address_box.port)

    def save_config(self, key, value):
        self.config[key] = value
        with open(CONFIG_FILE, 'w') as conf:
            json.dump(self.config, conf)

    def create_client(self):
        self._save_address()
        self.client = Client(
            self.address_box.ip, self.address_box.port, self.client_signal
        )
        self.client.name = self._name
        self.messenger_box.connect(self.client)
        self.client_signal.connect(self.messenger_box.update_text)
        self.client.connect()
        self.client.run()
        self.messenger_box.user_text_message_box.setEnabled(self.client.connected)
        self.client_signal.connect(self._send_notification)

    def _send_notification(self):
        app.alert(self)
        threading.Thread(
            target=playsound,
            args=(os.path.join("sounds", "notification.mp3"),)
        ).start()

    def _setup_page(self):
        setup_layout = QVBoxLayout()

        self.address_box = SocketConfigurator("Server")
        self.address_box.ip = self.config.get("ip", "127.0.0.1")
        self.address_box.port = self.config.get("port", 7979)
        self.address_box.address_button.clicked.connect(self.create_client)

        setup_layout.addWidget(self.address_box)

        setup_box = QGroupBox("User")
        layout = QVBoxLayout()
        setup_box.setLayout(layout)
        setup_layout.addWidget(setup_box)
        username_label = QLabel("Username")
        username_label.setStyleSheet("text-decoration: underline")
        layout.addWidget(username_label, alignment=Qt.AlignTop)
        self.username_entry = QLineEdit(
            self.config.get("username", DEFAULT_NAME)
        )
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
        self.theme_combo.setCurrentText(self.config.get("theme", ""))
        self.theme_combo.currentTextChanged.connect(self._set_stylesheet)
        layout.addWidget(self.theme_combo, Qt.AlignTop)

        theme_icon = QPixmap(
            os.path.join("icons", self.config.get("theme"))
        ).scaledToWidth(128).scaledToHeight(128)
        self.icon_label = QLabel()
        self.icon_label.setPixmap(theme_icon)
        layout.addWidget(self.icon_label, 0, Qt.AlignCenter)

        self.layout.addLayout(setup_layout)

    def _set_username(self):
        if self.username_entry.text():
            name = self.username_entry.text()
        else:
            name = DEFAULT_NAME
        self._name = name
        self.save_config("username", name)
        if self.client is not None:
            if self.client.name != name:
                former_name = self.client.name
                self.client.name = name
                change_text = f"<{former_name} is now {name}>\n"
                self.client.send_message(change_text)
                self.messenger_box.append_message(change_text)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        log.info("closing window")
        if self.client is not None:
            self.client.stop()
            del self.client


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
