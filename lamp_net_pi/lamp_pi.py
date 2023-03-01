import socket
from functions import *
import re
import neopixel
import board
import logging


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

        self.logger = logging.getLogger(__name__)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        sock.setblocking(True)
        self.server = Connection((sock, self.server_address), connected=False)

        while True:
            self.connect_server()
            self.logger.info(f"Connected server at {ip_to_str(self.server_address)}")
            self.client_pub_address, self.client_priv_address = str_to_multiple_ip(self.server.recv())
            self.logger.info(f"Client's addresses are {multiple_ip_to_str([self.client_pub_address, self.client_priv_address])}")

            while self.client == None or not self.client.connected:
                self.connect_client()
            self.client.send(f'{self.pixels.n}|{self.pixels.byteorder}')

            while self.client.connected:
                data = self.client.recv()
                # split data into led strip information
                data = re.findall("."*6, data)

                for index, led in enumerate(data):
                    data[index] = re.findall("."*2, led)
                    for subindex, led_color in enumerate(data[index]):
                        data[index][subindex] = int(led_color, 16)
                    data[index] = list(data[index])
                    self.pixels[index] = data[index]

                self.pixels.show()

            self.logger.info("Client disconnected, resetting")

            self.pixels.fill((0, 0, 0))

    def connect_server(self):
        while not self.server.connected:
            self.server.connect()
            self.priv_address = self.server.socket.getsockname()
            self.server.send(ip_to_str(self.priv_address))
            self.pub_address = str_to_ip(self.server.recv())

    def connect_client(self):
        self.logger.info("Attempting P2P connection")
        self.client = P2P().connect_p2p(self.pub_address, self.priv_address, self.client_pub_address, self.client_priv_address)
        self.logger.info("P2P connection success!")