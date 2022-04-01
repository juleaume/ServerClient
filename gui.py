import sys

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, \
    QGroupBox, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, \
    QTextEdit

from client import Client
from server import Server
from utils import get_available_hosts, Messenger


class TextEdit(QTextEdit):
    enter_pressed = pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(TextEdit, self).__init__(*args, **kwargs)

    def keyPressEvent(self, e: QtGui.QKeyEvent) -> None:
        if e.key() == Qt.Key.Key_Return:
            self.enter_pressed.emit()
            e.accept()
        else:
            super().keyPressEvent(e)


class Window(QMainWindow):
    server_message = pyqtSignal()
    client_message = pyqtSignal()

    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Server Client")
        self.server = None
        self.client = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout()
        self.central_widget.setLayout(self.layout)

        s_ip, s_port, s_button, s_msg, s_send = self._create_box(
            "Server", QComboBox)
        c_ip, c_port, c_button, c_msg, c_send = self._create_box("Client")

        s_button.clicked.connect(
            lambda: self.create_server(
                s_ip.currentText(), int(s_port.text()), s_msg)
        )
        c_button.clicked.connect(
            lambda: self.create_client(c_ip.text(), int(c_port.text()), c_msg))

        s_send.clicked.connect(
            lambda: self.send_message(self.server, s_msg)
        )
        c_send.clicked.connect(
            lambda: self.send_message(self.client, c_msg)
        )

        self.show()

    def send_message(self, endpoint: Messenger, box: QTextEdit):
        endpoint.send_message(
            self._get_last_line(box).encode())
        t = box.toPlainText()
        t += '\n>'
        box.setText(t)

    def create_server(self, ip, port, message_box):
        self.server = Server(ip, port, self.server_message)
        self.server.run()
        self.server_message.connect(
            lambda: self._update_text(message_box, self.server)
        )
        message_box.setEnabled(True)  # open text box even if no one is
        # listening, the sending will fail anyway

    def create_client(self, ip, port, message_box):
        self.client = Client(ip, port, self.client_message)
        self.client_message.connect(
            lambda: self._update_text(message_box, self.client)
        )
        self.client.connect()
        self.client.run()
        message_box.setEnabled(self.client.connected)  # only open the text
        # box if the client is connected to a server

    @staticmethod
    def _update_text(box: QTextEdit, endpoint: Messenger):
        t = box.toPlainText()[:-1]
        message = f"{t}<{endpoint.message.decode()}\n>"
        box.setText(message)

    @staticmethod
    def _get_last_line(box: QTextEdit) -> str:
        t = box.toPlainText()
        return t.splitlines()[-1][1:]

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

        text_layout = QHBoxLayout()
        text_box = TextEdit('>')
        text_box.setEnabled(False)
        text_layout.addWidget(text_box, 2)
        send_button = QPushButton("↲")
        text_layout.addWidget(send_button, 1, Qt.AlignBottom)

        def click_and_place():
            send_button.click()
            cursor = text_box.textCursor()
            cursor.setPosition(len(text_box.toPlainText()))
            text_box.setTextCursor(cursor)

        text_box.enter_pressed.connect(click_and_place)

        layout.addLayout(text_layout)

        self.layout.addWidget(group_box)

        return ip_selector, port_selector, \
               address_button, text_box, send_button

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        print("closing window")
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
