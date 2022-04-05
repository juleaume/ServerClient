import socket

from utils import Messenger, log


class MultipointServer(Messenger):
    def __init__(self, ip, port, signal=None):
        super(MultipointServer, self).__init__(ip, port, signal)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection_pool = list()
        self._sock.bind(self.address)
        self._sock.listen()
        self.first_connection = True
        self.connected = True

    def start(self):
        while self.connected:
            log.info("spawning new listener")
            connection, address = self._sock.accept()
            log.info(f"new connection from {address}")
            connection.settimeout(.5)
            connection.send(f"<Welcome to the server>\n".encode())
            self.connection_pool.append(connection)
            if self.first_connection:
                self.first_connection = False
                self.run()

    def _run(self):
        while self.connected:
            for connection in self.connection_pool:  # type:socket.socket
                try:
                    message = connection.recv(4096)
                    if message:
                        self.message = message
                    else:
                        raise ConnectionAbortedError
                    self._send_to_all(connection)
                    if self.signal is not None:
                        self.signal.emit()
                except socket.timeout:
                    # going to the next connection endpoint
                    continue
                except (ConnectionAbortedError, ConnectionResetError):
                    log.info(
                        f"[{self}] Someone disconnected, removing agent"
                    )
                    self.connection_pool.remove(connection)

    def _send_to_all(self, sender: socket.socket):
        for connection in self.connection_pool:  # type: socket.socket
            if not connection == sender:
                connection.send(self.message)

    def __str__(self):
        return "Multipoint Server"


if __name__ == '__main__':
    server = MultipointServer("", 7979)
    server.start()
