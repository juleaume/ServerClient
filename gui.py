import socket
import sys

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, \
    QGroupBox, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, \
    QTextEdit, QCheckBox

from client import Client
from server import Server
from utils import get_available_hosts, Messenger, log


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

        s_ip, s_port, s_create, s_message, s_send_button, s_history = \
            self._create_box("Server", QComboBox)
        c_ip, c_port, c_connect, c_message, c_send_button, c_history = \
            self._create_box("Client")

        s_create.clicked.connect(
            lambda: self.create_server(
                s_ip.currentText(), int(s_port.text()), s_history, s_message)
        )
        c_connect.clicked.connect(
            lambda: self.create_client(
                c_ip.text(), int(c_port.text()), c_history, c_message)
        )

        def send_and_place(endpoint: Messenger, message: QLineEdit,
                           dialog: QTextEdit):
            msg = message.text()
            if msg:
                if not self.agnostic:
                    signed_msg = f"[{endpoint.name}] {msg}"
                else:
                    signed_msg = msg
                endpoint.send_message(signed_msg)
                t = dialog.toPlainText()
                t = f"{t}{signed_msg}\n"
                dialog.setText(t)
                message.setText('')

        s_send_button.clicked.connect(
            lambda: send_and_place(self.server, s_message, s_history))
        c_send_button.clicked.connect(
            lambda: send_and_place(self.client, c_message, c_history))

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

    def create_server(self, ip, port, messages, text_box):
        self.server = Server(ip, port, self.server_message)
        self.set_agnostic()
        if self.name and not self.agnostic:
            self.server.name = self.name
        self.server.run()
        self.server_message.connect(
            lambda: self._update_text(messages, self.server)
        )
        text_box.setEnabled(True)  # open text box even if no one is
        # listening, the sending will fail anyway

    def create_client(self, ip, port, messages, text_box):
        self.client = Client(ip, port, self.client_message)
        self.set_agnostic()
        if self.name and not self.agnostic:
            self.client.name = self.name
        self.client_message.connect(
            lambda: self._update_text(messages, self.client)
        )
        self.client.connect()
        self.client.run()
        text_box.setEnabled(self.client.connected)  # only open the text
        # box if the client is connected to a server

    @staticmethod
    def _update_text(box: QTextEdit, endpoint: Messenger):
        t = box.toPlainText()
        message = f"{t}{endpoint.message.decode()}"
        box.setText(message)

    def _create_box(self, name: str, ip_type=QLineEdit):
        group_box = QGroupBox(name)
        layout = QVBoxLayout()
        group_box.setLayout(layout)
        ip_layout = QHBoxLayout()
        ip_label = QLabel("IP")
        ip_layout.addWidget(ip_label, 1, Qt.AlignRight)
        if ip_type == QLineEdit:
            ip_selector = QLineEdit("127.0.0.1")
            address_button = QPushButton("Connect")
            ip_selector.returnPressed.connect(address_button.click)
        else:
            ip_selector = QComboBox()
            ip_selector.addItems(get_available_hosts())
            address_button = QPushButton("Create")

        ip_layout.addWidget(ip_selector, 2, Qt.AlignLeft)
        layout.addLayout(ip_layout)

        port_layout = QHBoxLayout()
        port_label = QLabel("Port")
        port_layout.addWidget(port_label, 1, Qt.AlignRight)
        port_selector = QLineEdit("7878")
        port_selector.returnPressed.connect(address_button.click)
        port_layout.addWidget(port_selector, 2, Qt.AlignLeft)
        layout.addLayout(port_layout)

        layout.addWidget(address_button)

        message_box = TextShow()
        layout.addWidget(message_box)
        text_layout = QHBoxLayout()
        text_box = QLineEdit()
        text_box.setEnabled(False)
        text_layout.addWidget(text_box, 2)
        send_button = QPushButton("↲")
        text_layout.addWidget(send_button, 1, Qt.AlignBottom)

        text_box.returnPressed.connect(send_button.click)

        layout.addLayout(text_layout)

        self.layout.addWidget(group_box)

        return ip_selector, port_selector, \
               address_button, text_box, send_button, message_box

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
