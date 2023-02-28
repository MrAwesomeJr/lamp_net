import socket
from functions import *
import re
import neopixel
import board


class Pi:
    def __init__(self, server_address, pixels):
        self.server_address = server_address
        self.pixels = pixels
        self.pixels.auto_write = False
        self.client_pub_address = ""
        self.client_priv_address = ""
        self.priv_address = ""
        self.pub_address = ""
        self.client = None

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(True)
        self.server = Connection((sock, self.server_address), connected=False)

        while True:
            self.connect_server()
            self.client_pub_address, self.client_priv_address = str_to_double_ip(self.server.recv())

            while self.client == None:
                self.connect_client()
            self.client.send(f'{self.pixels.n}|{self.pixels.pixel_order}')

            while self.client.connected:
                data = self.client.recv()
                # split data into led strip information
                data = re.findall("."*6, data)

                for index, led in enumerate(data):
                    data[index] = re.findall("."*2, led)
                    data[index] = map(lambda x: int(x, 16), led)
                    self.pixels[index] = data[index]

                self.pixels.show()

            self.pixels.fill((0, 0, 0))

    def connect_server(self):
        while not self.server.connected:
            self.server.connect()
            self.priv_address = self.server.socket.getsockname()
            self.server.send(ip_to_str(self.priv_address))
            self.pub_address = self.server.recv()

    def connect_client(self):
        self.client = P2P.connect_p2p(self.pub_address, self.priv_address, self.client_pub_address, self.client_priv_address)