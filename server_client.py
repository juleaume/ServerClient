import socket
import sys

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, \
    QVBoxLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QCheckBox, \
    QComboBox

from client import Client
from gui import MessageBox, ServerConfigurator
from server import Server
from utils import log


class Window(QMainWindow):
    server_message_signal = pyqtSignal()
    client_message_signal = pyqtSignal()

    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Server Client")
        self.server = None
        self.client = None
        self.name = ""

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)

        settings_box = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        settings_box.setLayout(settings_layout)

        agnostic_layout = QHBoxLayout()
        agnostic_label = QLabel("Agnostic")
        self.agnostic_checkbox = QCheckBox()
        self.agnostic_checkbox.clicked.connect(self.set_agnostic)
        agnostic_layout.addWidget(agnostic_label)
        agnostic_layout.addWidget(self.agnostic_checkbox, 1, Qt.AlignLeft)
        settings_layout.addLayout(agnostic_layout)

        username_label = QLabel("Username")
        self.username_entry = QLineEdit()
        self.username_entry.returnPressed.connect(self.set_username)
        set_username_button = QPushButton("set username")
        set_username_button.clicked.connect(self.set_username)
        # self.username_entry.textChanged.connect(self.set_username)
        username_layout = QHBoxLayout()
        username_layout.addWidget(username_label, 1, Qt.AlignTop)
        username_layout.addWidget(self.username_entry, 1, Qt.AlignTop)
        username_layout.addWidget(set_username_button, 1, Qt.AlignTop)
        settings_layout.addLayout(username_layout)

        self.layout.addWidget(settings_box)

        self.server_settings = ServerConfigurator("Server", QComboBox)
        self.layout.addWidget(self.server_settings)
        self.server_box = MessageBox(self, "Server")
        self.layout.addWidget(self.server_box)

        self.client_settings = ServerConfigurator("Client")
        self.layout.addWidget(self.client_settings)
        self.client_box = MessageBox(self, "Client")
        self.layout.addWidget(self.client_box)

        self.server_settings.address_button.clicked.connect(self.create_server)
        self.client_settings.address_button.clicked.connect(self.create_client)

        self.show()

    @property
    def agnostic(self):
        return self.agnostic_checkbox.isChecked()

    def set_agnostic(self):
        value = self.agnostic_checkbox.isChecked()
        self.username_entry.setEnabled(not value)
        if self.server is not None:
            self.server.agnostic = value
        if self.client is not None:
            self.client.agnostic = value

    def set_username(self):
        if not self.agnostic:
            self.name = self.username_entry.text()
            log.info(f"Username set to {self.name}")
            if self.server is not None:
                former_name = self.server.name
                self.server.name = self.name
                self.server.send_message(
                    f"<{former_name} is now {self.server.name}>\n"
                )
            if self.client is not None:
                former_name = self.client.name
                self.client.name = self.name
                self.client.send_message(
                    f"<{former_name} is now {self.client.name}>\n"
                )

    def create_server(self):
        self.server = Server(
            self.server_settings.ip, self.server_settings.port,
            self.server_message_signal
        )
        self.set_agnostic()
        self.server_box.connect(self.server)
        if self.name and not self.agnostic:
            self.server.name = self.name
        self.server.run()
        self.server_message_signal.connect(self.server_box.update_text)
        self.server_box.user_text_message_box.setEnabled(True)  # open text box even
        # if no one is listening, the sending will fail anyway

    def create_client(self):
        self.client = Client(
            self.client_settings.ip, self.client_settings.port,
            self.client_message_signal
        )
        self.set_agnostic()
        if self.name and not self.agnostic:
            self.client.name = self.name
        try:
            self.client.connect()
        except (socket.timeout, ConnectionError):
            del self.client
            return
        self.client_box.connect(self.client)
        self.client_message_signal.connect(self.client_box.update_text)
        self.client.run()
        self.client_box.user_text_message_box.setEnabled(self.client.connected)
        # only open the  text box if the client is connected to a server

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        log.info("closing window")
        if self.client is not None:
            self.client.stop()
            del self.client
        if self.server is not None:
            self.server.stop()
            del self.server


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
