import socket
import threading

from utils import Messenger


class Server(Messenger):
    def __init__(self, ip="", port=7878, signal=None):
        super(Server, self).__init__(ip, port, signal)
        self._is_open = True
        self.reading_thread = None
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection = None
        self._sock.bind(self.address)
        self._sock.listen(1)

    def run(self):
        self.reading_thread = threading.Thread(
            target=self._run, name="receiving thread"
        )
        self.reading_thread.start()

    def stop(self):
        self._is_open = False
        self.connection.settimeout(.1)
        self.reading_thread.join()

    def _run(self):
        print(f"Server running, listening connections @ {self.address}")
        self.connection, addr = self._sock.accept()
        print(f"Connection accepted! from {addr}")
        while self._is_open:
            self.message = self.connection.recv(4096)

    def send_message(self, message):
        try:
            self.connection.send(message)
        except ConnectionResetError:
            print("Connection failed")
        except AttributeError:
            print("Sending failed, not connected")


if __name__ == '__main__':
    server = Server()
    server.run()
