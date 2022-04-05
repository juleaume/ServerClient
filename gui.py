import sys
from typing import Union

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, \
    QGroupBox, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, \
    QTextEdit, QCheckBox

from client import Client
from server import Server
from utils import get_available_hosts, log


class MessageBox(QGroupBox):
    def __init__(self, parent, name, ip_type=QLineEdit):
        super().__init__(name)
        self.parent = parent  # type: Window
        self.endpoint = None  # type: Union[None, Server, Client]
        layout = QVBoxLayout()
        self.setLayout(layout)
        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP")
        ip_layout.addWidget(ip_label, 1, Qt.AlignRight)
        if ip_type == QLineEdit:
            self.ip_selector = QLineEdit("127.0.0.1")
            self.address_button = QPushButton("Connect")
            self.ip_selector.returnPressed.connect(self.address_button.click)
        else:
            self.ip_selector = QComboBox()
            self.ip_selector.addItems(get_available_hosts())
            self.address_button = QPushButton("Create")

        ip_layout.addWidget(self.ip_selector, 2, Qt.AlignLeft)
        layout.addLayout(ip_layout)

        port_layout = QHBoxLayout()
        port_label = QLabel("Port")
        port_layout.addWidget(port_label, 1, Qt.AlignRight)
        self.port_selector = QLineEdit("7878")
        self.port_selector.returnPressed.connect(self.address_button.click)
        port_layout.addWidget(self.port_selector, 2, Qt.AlignLeft)
        layout.addLayout(port_layout)

        layout.addWidget(self.address_button)

        self.text_history_box = TextShow()
        layout.addWidget(self.text_history_box)
        text_layout = QHBoxLayout()
        self.user_text_message_box = QLineEdit()
        self.user_text_message_box.setEnabled(False)
        text_layout.addWidget(self.user_text_message_box, 2)
        self.send_button = QPushButton("↲")
        self.send_button.clicked.connect(self._send_and_place)
        text_layout.addWidget(self.send_button, 1, Qt.AlignBottom)

        self.user_text_message_box.returnPressed.connect(self.send_button.click)

        layout.addLayout(text_layout)

    def _send_and_place(self):
        if self.endpoint is None:
            log.error("Not connected")
            return
        msg = self.user_text_message_box.text()
        if msg:
            if not self.parent.agnostic:
                signed_msg = f"[{self.endpoint.name}] {msg}"
            else:
                signed_msg = msg
            self.endpoint.send_message(signed_msg)
            t = self.text_history_box.toPlainText()
            t = f"{t}{signed_msg}\n"
            self.text_history_box.setText(t)
            self.user_text_message_box.setText('')

    def update_text(self):
        if self.endpoint is not None:
            t = self.text_history_box.toPlainText()
            message = f"{t}{self.endpoint.message.decode()}"
            self.text_history_box.setText(message)
        else:
            log.error("Endpoint is not connected")

    def connect(self, endpoint):
        self.endpoint = endpoint

    @property
    def ip(self):
        if isinstance(self.ip_selector, QComboBox):
            return self.ip_selector.currentText()
        else:
            return self.ip_selector.text()

    @property
    def port(self):
        return int(self.port_selector.text())


class TextShow(QTextEdit):
    enter_pressed = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(TextShow, self).__init__(*args, **kwargs)

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        e.ignore()


class Window(QMainWindow):
    server_message = pyqtSignal()
    client_message = pyqtSignal()

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

        self.server_box = MessageBox(self, "Server", QComboBox)
        self.layout.addWidget(self.server_box)

        self.client_box = MessageBox(self, "Client")
        self.layout.addWidget(self.client_box)

        self.server_box.address_button.clicked.connect(self.create_server)
        self.client_box.address_button.clicked.connect(self.create_client)

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
                    f"<{former_name} is now {self.server.name}>"
                )
            if self.client is not None:
                former_name = self.client.name
                self.client.name = self.name
                self.client.send_message(
                    f"<{former_name} is now {self.client.name}>"
                )

    def create_server(self):
        self.server = Server(
            self.server_box.ip, self.server_box.port, self.server_message
        )
        self.set_agnostic()
        self.server_box.connect(self.server)
        if self.name and not self.agnostic:
            self.server.name = self.name
        self.server.run()
        self.server_message.connect(self.server_box.update_text)
        self.server_box.user_text_message_box.setEnabled(True)  # open text box even
        # if no one is listening, the sending will fail anyway

    def create_client(self):
        self.client = Client(
            self.client_box.ip, self.client_box.port, self.client_message
        )
        self.set_agnostic()
        self.client_box.connect(self.client)
        if self.name and not self.agnostic:
            self.client.name = self.name
        self.client_message.connect(self.client_box.update_text)
        self.client.connect()
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
