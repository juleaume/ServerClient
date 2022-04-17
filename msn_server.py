import pickle
import socket
import sys

from utils import Messenger, log


class MultipointServer(Messenger):
    def __init__(self, ip, port, signal=None, name=None):
        super(MultipointServer, self).__init__(ip, port, signal)
        if name is not None:
            self.name = name
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.connection_pool = list()
        self._sock.bind(self.address)
        self._sock.listen()
        self.first_connection = True
        self.connected = True
        self._info = {self._sock: self.name}

    def start(self):
        while self.connected:
            log.info("spawning new listener")
            connection, address = self._sock.accept()
            log.info(f"new connection from {address}")
            connection.settimeout(.5)
            self.connection_pool.append(connection)
            if self.first_connection:
                self.first_connection = False
                self.run()

    @property
    def info(self):
        return self._info

    def send_info(self, connection: socket.socket):
        connection.send(
            pickle.dumps(
                ("info", list(self.info.values())
                 )
            )
        )  # only send the names of the connected

    def update_info(self, client, info, remove=False):
        if remove and client in self._info.keys():
            del self._info[client]
        else:
            self._info[client] = info
        # check-up
        for connected in list(self._info.keys()):  # make a copy of the list
            if connected not in self.connection_pool and \
                    not connected == self._sock:
                del self._info[connected]
        for connection in self.connection_pool:  # type: socket.socket
            self.send_info(connection)

    def _run(self):
        while self.connected:
            for connection in self.connection_pool:  # type:socket.socket
                try:
                    received = connection.recv(4096)
                    if received:
                        command, value = pickle.loads(received)
                        if command == "info":
                            self.update_info(
                                connection, value, value == "remove"
                            )
                        elif command == "message":
                            self.message = value
                            self._send_to_all(connection)
                            if self.signal is not None:
                                self.signal.emit()
                    else:
                        raise ConnectionAbortedError

                except socket.timeout:
                    # going to the next connection endpoint
                    continue
                except ConnectionError:
                    log.info(
                        f"[{self}] Someone disconnected, removing agent"
                    )
                    self.connection_pool.remove(connection)

    def _send_to_all(self, sender: socket.socket):
        for connection in self.connection_pool:  # type: socket.socket
            if not connection == sender:
                connection.send(self.message)

    def __str__(self):
        return self.name


def main():
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = None
    server = MultipointServer("", 7979, name=name)
    server.start()


if __name__ == '__main__':
    main()
