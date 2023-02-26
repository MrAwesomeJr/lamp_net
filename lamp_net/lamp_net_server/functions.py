import socket


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


class Connection:
    def __init__(self, accept):
        self.socket = accept[0]
        self.address = accept[1]
        self.connected = True

    def connect(self):
        if not self.connected:
            self.socket.connect(self.address)
            self.connected = True

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
