import socket
from lamp_net_client.functions import *
import logging
import time


class Pixels:
    def __init__(self, n, byte_order, pi, auto_write=True):
        self._pixels = [(0, 0, 0) for i in n]
        self.byte_order = byte_order
        self.n = n
        self.pi = pi
        self._brightness = 1
        self.auto_write = auto_write

        self.current_index = 0

        self.logger = logging.getLogger(__name__)

    def fill(self, color):
        self._pixels = [color for i in self.n]

        if self.auto_write:
            self.show()

    def __getitem__(self, item):
        return self._pixels[item]

    def __setitem__(self, key, value):
        if isinstance(value, list):
            bright_values = []
            for i in value:
                bright_values.append(tuple(map(lambda x: x*self.brightness, i)))
            self._pixels[key] = bright_values
        else:
            self._pixels[key] = list(map(lambda x: x*self.brightness, value))

        if self.auto_write:
            self.show()

    def __iter__(self):
        self.current_index = 0
        return self._pixels

    def __next__(self):
        if self.current_index <= self.n:
            return_value = self._pixels[self.current_index]
            self.current_index += 1
            return return_value
        else:
            raise StopIteration

    def __len__(self):
        return len(self._pixels)

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value: float):
        value = min(max(value, 0.0), 1.0)
        change = value - self._brightness
        if -0.001 < change < 0.001:
            return

        self._brightness = value

    def show(self):
        hex_pixels = self._pixels
        for index, pixel in enumerate(hex_pixels):
            hex_pixels[index] = map(lambda x: f'{int(x*self._brightness):0<2x}', pixel)
        string_pixels = map(lambda x: "".join(x), hex_pixels)
        msg = "".join(string_pixels)
        self.pi.send(msg)

        # technically not required but the pi can't handle so many frames
        # the lights run at around 200-250 fps max so the buffer fills
        time.sleep(0.005)


class Client:
    def __init__(self):
        self.server = None
        self.pi = None
        self.pixels = None
        self.priv_address = ""
        self.pub_address = ""
        self.pi_priv_address = ""
        self.pi_pub_address = ""

        self.logger = logging.getLogger(__name__)

    def connect(self, server_address):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.server = Connection((sock, server_address), connected=False)

        self.server.connect()
        self.logger.info(f"Connected server at {ip_to_str(server_address)}")
        self.priv_address = self.server.socket.getsockname()
        self.server.send(ip_to_str(self.priv_address))
        self.pub_address = str_to_ip(self.server.recv())
        self.logger.info(f"My addresses are {multiple_ip_to_str([self.pub_address, self.priv_address])}")
        self.pi_pub_address, self.pi_priv_address = str_to_multiple_ip(self.server.recv())
        self.logger.info(f"The Pi's addresses are {multiple_ip_to_str([self.pi_pub_address, self.pi_priv_address])}")

        self.logger.info("Attempting P2P connection")
        self.pi = P2P().connect_p2p(self.pub_address, self.priv_address, self.pi_pub_address, self.pi_priv_address)
        self.logger.info("P2P connection success!")

        # receive f'{self.pixels.n}|{self.pixels.byte_order}' from lamp_net_pi/lamp_pi.py
        pixel_params = self.pi.recv().split("|")
        self.logger.info(f"Pixel parameters recieved {pixel_params}")
        self.pixels = Pixels(pixel_params[0], pixel_params[1], self.pi)
