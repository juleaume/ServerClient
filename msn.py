import sys
from typing import Union

from PyQt5 import QtGui
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QApplication

from client import Client
from gui import MessageBox
from utils import log


class Window(QMainWindow):
    client_signal = pyqtSignal()
    agnostic = False

    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Messenger")
        self.client_box = MessageBox(self, "MSN")
        self.setCentralWidget(self.client_box)
        self.client = None  # type: Union[None, Client]
        self.client_box.address_button.clicked.connect(self.create_client)
        self.show()

    def create_client(self):
        self.client = Client(
            self.client_box.ip, self.client_box.port, self.client_signal
        )
        self.client_box.connect(self.client)
        self.client_signal.connect(self.client_box.update_text)
        self.client.connect()
        self.client.run()
        self.client_box.user_text_message_box.setEnabled(self.client.connected)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        log.info("closing window")
        if self.client is not None:
            self.client.stop()
            del self.client


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    sys.exit(app.exec())
