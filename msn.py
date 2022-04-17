import os
import pickle
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

from gui import MessageBox, ServerConfigurator
from utils import log, socket, Messenger
from themes import COLOR_SCHEME, THEMES, DEFAULT_THEME

CONFIG_FILE = ".config"
DEFAULT_NAME = f"{os.getlogin()}@{socket.gethostname()}"


class MSNClient(Messenger):
    def __init__(self, ip=None, port=None,
                 message_signal=None, info_signal=None):
        super().__init__(ip, port, message_signal)
        self.info_signal = info_signal  # type: pyqtSignal
        self.server_info = list()
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection.settimeout(2)

    def connect(self, propagate=False):
        if self.address == (None, None):
            log.error(f"[{self}] No address used")
        try:
            log.info(f"[{self}] Trying to connect to {self.address}")
            self.connection.settimeout(10)
            self.connection.connect(self.address)
            self.connection.settimeout(2)
            self.connected = True
            self.connection.send(pickle.dumps(("info", self.name)))
        except (ConnectionError, socket.timeout):
            log.warning("Could not reach host")
            if propagate:
                raise

    def _run(self):
        while self.connected:
            try:
                data = self.connection.recv(4096)
                if data == b'':
                    self.connected = False
                    break
                else:
                    command, value = pickle.loads(data)
                    if command == "message":
                        self.message = value
                    elif command == "info":
                        self.server_info = value
                        if self.info_signal is not None:
                            self.info_signal.emit()
            except socket.timeout:
                pass
            except ConnectionError:
                self.connected = False
        log.info(f"{self} stops listening")

    def send_message(self, message: str):
        if self.connected:
            try:
                data = ("message", message)
                self.connection.send(pickle.dumps(data))
            except ConnectionError:
                log.warning(f"[{self}] Connection failed")
            except AttributeError:
                log.warning(f"[{self}] Sending failed, not connected")
        else:
            log.warning(f"[{self}] Not connected")

    def closing_statement(self):
        self.connection.send(pickle.dumps(("info", "remove")))

    def __str__(self):
        return "Client"


class Window(QMainWindow):
    client_signal = pyqtSignal()
    server_signal = pyqtSignal()
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
        self.client = None  # type: Union[None, MSNClient]
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
        self.client = MSNClient(
            self.address_box.ip, self.address_box.port,
            self.client_signal, self.server_signal
        )
        self.client.name = self._name
        try:
            self.client.connect(propagate=True)
        except (socket.timeout, ConnectionError):
            del self.client
            return
        self.messenger_box.connect(self.client)
        self.client_signal.connect(self.messenger_box.update_text)
        self.client.run()
        self.messenger_box.user_text_message_box.setEnabled(
            self.client.connected)
        self.client_signal.connect(self._send_notification)

    def _send_notification(self):
        app.alert(self)
        threading.Thread(
            target=playsound,
            args=(os.path.join("sounds", "notification.mp3"),)
        ).start()

    def update_server_info(self):
        if self.client is not None:
            text = ''
            for name in self.client.server_info:
                text += f"{name}\n"
            self.address_box.server_info.setText(text)

    def _setup_page(self):
        setup_layout = QVBoxLayout()

        self.address_box = ServerConfigurator("Server", see_server_info=True)
        self.address_box.ip = self.config.get("ip", "127.0.0.1")
        self.address_box.port = self.config.get("port", 7979)
        self.address_box.address_button.clicked.connect(self.create_client)
        self.server_signal.connect(self.update_server_info)

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
                self.client.name = name
                self.client.connection.send(pickle.dumps(("info", self._name)))

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        log.info("closing window")
        if self.client is not None:
            self.client.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
