import socket

from utils import Messenger


class Client(Messenger):
    def __init__(self, ip=None, port=None, signal=None):
        super(Client, self).__init__(ip, port, signal)
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection.settimeout(1)

    def connect(self):
        if self.address == (None, None):
            print("No address used")
        try:
            print(f"Trying to connect to {self.address}")
            self.connection.connect(self.address)
            self.connected = True
            self.send_message(
                f"<{socket.gethostname()} has entered the chat>".encode()
            )
        except (ConnectionRefusedError, socket.timeout):
            print("Could not reach host")

    def _run(self):
        while self.connected:
            try:
                self.message = self.connection.recv(4096)
                if self.message == b'':
                    self.connected = False
            except socket.timeout:
                pass

    def __str__(self):
        return "Client"


if __name__ == '__main__':
    client = Client("127.0.0.1", 7878)
    client.connect()
    client.run()
