import socket
import threading


def ip_to_str(address):
    # expect address to be a tuple of (ip, port)
    return f'{address[0]}:{address[1]}'


def str_to_ip(string_address):
    # expect string_address to be in format given by ip_to_str()
    return tuple(string_address.split(":"))


def double_ip_to_str(public_address, private_address):
    return f'{ip_to_str(public_address)}|{ip_to_str(private_address)}'


def str_to_double_ip(string_addresses):
    addresses = string_addresses.split("|")
    return str_to_ip(addresses[0]), str_to_ip(addresses[1])


class P2P:
    def async_accept(self, local_address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(local_address)
        sock.listen(1)
        sock.settimeout(5)
        while not self.stop_connecting.is_set():
            try:
                self.connection = sock.accept()
            except socket.timeout:
                continue
            else:
                self.stop_connecting.set()

    def async_connect(self, local_address, client_address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.bind(local_address)
        while not self.stop_connecting.is_set():
            try:
                sock.connect(client_address)
            except socket.error:
                continue
            else:
                self.connection = Connection((sock, client_address))
                self.stop_connecting.set()

    def connect_p2p(self, local_pub_address, local_priv_address, peer_pub_address, peer_priv_address):
        # p2p mostly possible thanks to https://github.com/dwoz/python-nat-hole-punching/blob/master/tcp_client.py
        # https://en.wikipedia.org/wiki/TCP_hole_punching describes the bs that's NAT port predictability.
        # To summarize: it isn't.

        self.stop_connecting = threading.Event()
        self.connection = None

        threads = [
            threading.Thread(target=self.async_accept, args=(local_priv_address)),
            threading.Thread(target=self.async_accept, args=(local_pub_address)),
            threading.Thread(target=self.async_connect, args=(local_priv_address, peer_pub_address)),
            threading.Thread(target=self.async_connect, args=(local_priv_address, peer_priv_address))
        ]

        for thread in threads:
            thread.start()

        while not self.stop_connecting:
            pass

        return self.connection


class Connection:
    def __init__(self, accept, connected=True):
        self.socket = accept[0]
        self.address = accept[1]
        self.connected = connected

    def connect(self):
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
        try:
            self.socket.send(str(msg).encode())
        except ConnectionResetError:
            self.connected = False

    def recv(self, buffer_size=1024):
        msg = b''
        try:
            msg = self.socket.recv(buffer_size)
        except BlockingIOError:
            return False
        except ConnectionResetError:
            self.connected = False
            return False

        if msg == b'':
            self.connected = False
            return False
        else:
            return msg.decode()
