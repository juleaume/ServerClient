import socket

from utils import Messenger


class Client(Messenger):
    def __init__(self, ip=None, port=None, signal=None):
        super(Client, self).__init__(ip, port, signal)
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection.settimeout(2)

    def connect(self):
        if self.address == (None, None):
            print("No address used")
        try:
            print(f"Trying to connect to {self.address}")
            self.connection.settimeout(10)
            self.connection.connect(self.address)
            self.connection.settimeout(2)
            self.connected = True
            if not self.agnostic:
                self.send_message(
                    f"<{self.name} has entered the chat>"
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
        print(f"{self} stops listening")

    def closing_statement(self):
        self.send_message(f"<{self.name} has left the chat>")

    def __str__(self):
        return "Client"


if __name__ == '__main__':
    client = Client("127.0.0.1", 7878)
    client.connect()
    client.run()
