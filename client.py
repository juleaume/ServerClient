import socket
import threading

from utils import Messenger


class Client(Messenger):
    def __init__(self, ip=None, port=None, signal=None):
        super(Client, self).__init__(ip, port, signal)
        self.sock = socket.socket()
        self._connected = False
        self.reading_thread = None

    def connect(self):
        if self.address == (None, None):
            raise ValueError
        self.sock.connect(self.address)
        self._connected = True
        print("connected!")

    def run(self):
        self.reading_thread = threading.Thread(target=self._run)
        self.reading_thread.start()

    def _run(self):
        while self._connected:
            self.message = self.sock.recv(4096)

    def send_message(self, message):
        try:
            self.sock.send(message)
        except ConnectionResetError:
            print("Connection failed")


if __name__ == '__main__':
    client = Client("127.0.0.1", 7878)
    client.connect()
    client.run()
