import socket
import sys
import threading
import logging

log = logging.Logger("PASC")
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
handler.setFormatter(
    logging.Formatter("%(levelname)s: %(thread)s: %(asctime)s: %(message)s")
)
log.addHandler(handler)


class Messenger:
    def __init__(self, ip, port, signal=None):
        self._ip = ip
        self._port = port
        self.signal = signal
        self._connected = False
        self._last_message = b''
        self._name = socket.gethostname()
        self._agnostic = False
        self.reading_thread = None  # type: threading.Thread
        self._connection = None  # type: socket.socket

    @property
    def address(self):
        return self._ip, self._port

    @address.setter
    def address(self, value):
        self._ip, self._port = value

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def message(self) -> bytes:
        return self._last_message

    @message.setter
    def message(self, value):
        log.info(f"[{self}] Got message: {value}")
        self._last_message = value
        if self.signal is not None:
            self.signal.emit()

    @property
    def connected(self):
        return self._connected

    @connected.setter
    def connected(self, value):
        if value:
            log.info(f"[{self}] connected")
        else:
            log.info(f"[{self}] disconnected")
        self._connected = value

    @property
    def connection(self) -> socket.socket:
        return self._connection

    @connection.setter
    def connection(self, value):
        self._connection = value

    @property
    def agnostic(self):
        return self._agnostic

    @agnostic.setter
    def agnostic(self, value):
        if value:
            log.info(f"[{self}] is now agnostic")
        else:
            log.info(f"[{self}] is no longer agnostic")
        self._agnostic = value

    def run(self):
        self.reading_thread = threading.Thread(
            target=self._run, name=f"{self}"
        )
        self.reading_thread.start()

    def stop(self):
        if not self._agnostic:
            self.closing_statement()
        self.connected = False
        self.reading_thread.join()

    def closing_statement(self):
        pass

    def send_message(self, message: str):
        if self.connected:
            try:
                self.connection.send(f"{message}\n".encode())
            except ConnectionResetError:
                log.warning(f"[{self}] Connection failed")
            except AttributeError:
                log.warning(f"[{self}] Sending failed, not connected")
        else:
            log.warning(f"[{self}] Not connected")

    def _run(self):
        raise NotImplemented


def get_available_hosts():
    *_, ips = socket.gethostbyname_ex(socket.gethostname())
    return ["", "127.0.0.1"] + ips
