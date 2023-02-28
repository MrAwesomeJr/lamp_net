import socket
import threading
from functions import *


class Server:
    def __init__(self, my_address, pi_address):
        self.my_address = my_address
        self.pi_address = pi_address
        self.pi = None
        self.client = None
        self.stop = threading.Event()
        self.connect_pi_thread = threading.Thread(target=self.connect_pi)

        self.pi_address_string = ""
        self.client_address_string = ""

    def run(self):
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.listener_socket.bind(self.my_address)
        self.listener_socket.listen()
        self.connect_pi_thread.run()

        while True:
            if self.pi.connected:
                self.listener_socket.setblocking(False)
                try:
                    self.client = Connection(self.listener_socket.accept())
                except BlockingIOError:
                    continue

                # the server only needs to handle one request at a time because the pi can only accept one request at a time anyways
                client_priv_address = str_to_ip(self.client.recv())
                self.client_address_string = double_ip_to_str(self.client.address, client_priv_address)
                self.client.send(ip_to_str(self.client.address))

                self.client.send(self.pi_address_string)
                self.pi.send(self.client_address_string)
                self.client.disconnect()

    def connect_pi(self):
        while not self.stop.is_set():
            # assume first connection from pi server's address is correct
            # if pi server disconnects wait for reconnect
            while self.pi == None or not self.pi.connected:
                self.listener_socket.setblocking(True)
                self.pi = Connection(self.listener_socket.accept())

                # verify pi is the correct ip
                if self.pi_address[1] == 0 and self.pi.address[0] != self.pi_address[0]:
                    self.pi.disconnect()
                    continue
                elif self.pi.address != self.pi_address:
                    self.pi.disconnect()
                    continue

                pi_priv_address = str_to_ip(self.pi.recv())
                self.pi_address_string = double_ip_to_str(self.pi.address, pi_priv_address)
                self.pi.send(ip_to_str(self.pi.address))
