import socket

from utils import Messenger, log


class Server(Messenger):
    def __init__(self, ip="", port=7878, signal=None):
        super(Server, self).__init__(ip, port, signal)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection = None
        self._sock.bind(self.address)
        self._sock.listen()

    def _run(self):
        log.info(f"Server running, listening connections @ {self.address}")
        self.connection, addr = self._sock.accept()
        log.info(f"Entering connection from {addr}")
        self.connected = True
        self.connection.settimeout(1)
        if not self.agnostic:
            self.send_message(
                f"<Welcome to {self.name} server>"
            )
        while self.connected:
            try:
                self.message = self.connection.recv(4096)
                if self.message == b'':
                    self.connected = False
            except socket.timeout:
                pass

    def closing_statement(self):
        self.send_message(f"<{self.name} has closed the chat>")

    def __str__(self):
        return "Server"


if __name__ == '__main__':
    server = Server()
    server.run()
