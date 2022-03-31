import socket


class Messenger:
    def __init__(self, ip, port, signal=None):
        self._ip = ip
        self._port = port
        self.signal = signal
        self._last_message = b''
        self._fresh = True

    @property
    def address(self):
        return self._ip, self._port

    @address.setter
    def address(self, value):
        self._ip, self._port = value

    @property
    def message(self) -> bytes:
        self._fresh = False
        return self._last_message

    @message.setter
    def message(self, value):
        print(f"Got message: {value}")
        self._fresh = True
        self._last_message = value
        if self.signal is not None:
            self.signal.emit()

    def send_message(self, message: bytes):
        raise NotImplemented


def get_available_hosts():
    *_, ips = socket.gethostbyname_ex(socket.gethostname())
    return ["", "127.0.0.1"] + ips
