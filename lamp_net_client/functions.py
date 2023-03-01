import socket
import threading
import struct
import logging


def ip_to_str(address):
    # expect address to be a tuple of (ip, port)
    return f'{address[0]}:{address[1]}'


def str_to_ip(string_address):
    # expect string_address to be in format given by ip_to_str()
    address = tuple(string_address.split(":"))
    address = (address[0], int(address[1]))
    return address


def multiple_ip_to_str(ips):
    for index, ip in enumerate(ips):
        ips[index] = ip_to_str(ip)
    return "|".join(ips)


def str_to_multiple_ip(string_ips):
    ips = string_ips.split("|")
    for index, ip in enumerate(ips):
        ips[index] = str_to_ip(ip)
    return ips


class P2P:
    def __init__(self):
        self.stop_connecting = threading.Event()
        self.connection = None

        self.logger = logging.getLogger(__name__)

    def async_accept(self, local_address):
        self.logger.info(f"Attempting async accept from {local_address}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(("0.0.0.0", local_address[1]))
        sock.listen(1)
        sock.settimeout(5)
        while not self.stop_connecting.is_set():
            try:
                self.connection = Connection(sock.accept())
            except socket.timeout:
                continue
            else:
                self.logger.info(f"Async accept success from {local_address}")
                self.stop_connecting.set()

    def async_connect(self, local_address, client_address):
        self.logger.info(f"Attempting async connect from {local_address} to {client_address}")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(("0.0.0.0", local_address[1]))
        while not self.stop_connecting.is_set():
            try:
                sock.connect(client_address)
            except socket.error:
                continue
            else:
                self.logger.info(f"Async connect success from {local_address} to {client_address}")
                self.connection = Connection((sock, client_address))
                self.stop_connecting.set()

    def connect_p2p(self, local_pub_address, local_priv_address, peer_pub_address, peer_priv_address):
        # p2p mostly possible thanks to https://github.com/dwoz/python-nat-hole-punching/blob/master/tcp_client.py
        # https://en.wikipedia.org/wiki/TCP_hole_punching describes the bs that's NAT port predictability.
        # To summarize: it isn't.

        self.stop_connecting = threading.Event()
        self.connection = None

        threads = [
            threading.Thread(target=self.async_accept, args=(local_priv_address,)),
            threading.Thread(target=self.async_accept, args=(local_pub_address,)),
            threading.Thread(target=self.async_connect, args=(local_priv_address, peer_pub_address)),
            threading.Thread(target=self.async_connect, args=(local_priv_address, peer_priv_address))
        ]

        for thread in threads:
            thread.daemon = True
            thread.start()
        self.logger.info("All async threads started")

        while not self.stop_connecting.is_set():
            pass

        return self.connection


class Connection:
    def __init__(self, accept, connected=True):
        self.socket = accept[0]
        self.address = accept[1]
        self.connected = connected

        self.logger = logging.getLogger(__name__)

    def connect(self):
        self.logger.info(f"connect to {self.address}")
        while not self.connected:
            try:
                self.socket.connect(self.address)
                self.connected = True
            except ConnectionRefusedError:
                pass

    def disconnect(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.connected = False

    def send(self, msg):
        self.logger.info(f"Sending to {ip_to_str(self.address)}: {msg}")
        try:
            data = struct.pack('>I', len(msg)) + msg.encode()
            self.socket.send(data)
        except ConnectionResetError:
            self.connected = False

    def recv(self):
        length = b''
        data = b''
        while length == b'':
            try:
                length = self.socket.recv(4)
            except BlockingIOError:
                continue
            except ConnectionResetError:
                self.connected = False
                return False

        msg_length = struct.unpack('>I', length)[0]

        while len(data) < msg_length:
            packet = self.socket.recv(msg_length - len(data))
            if not packet:
                return False
            data += packet

        self.logger.info(f"Recieved from {ip_to_str(self.address)}: {data.decode()}")
        return data.decode()
