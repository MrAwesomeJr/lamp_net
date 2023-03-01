import socket
import threading
from functions import *
import logging


class Server:
    def __init__(self, my_address, pi_address):
        self.my_address = my_address
        self.pi_address = pi_address
        self.pi = None
        self.client = None

        self.pi_address_string = ""
        self.client_address_string = ""

        self.logger = logging.getLogger(__name__)

    def run(self):
        self.listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        self.listener_socket.bind(self.my_address)
        self.listener_socket.listen()
        self.logger.info(f"Listening from {ip_to_str(self.listener_socket.getsockname())}")

        self.listener_socket.setblocking(False)
        while True:
            if self.pi == None or not self.pi.connected:
                self.connect_pi()
            try:
                self.client = Connection(self.listener_socket.accept())
            except BlockingIOError:
                continue
            else:
                # the server only needs to handle one request at a time because the pi can only accept one request at a time anyways
                client_priv_address = str_to_ip(self.client.recv())
                self.logger.info(f"Client's addresses are {multiple_ip_to_str([self.client.address, client_priv_address])}")
                self.client_address_string = multiple_ip_to_str([self.client.address, client_priv_address])
                self.client.send(ip_to_str(self.client.address))

                self.client.send(self.pi_address_string)
                self.pi.send(self.client_address_string)
                self.client.disconnect()
                self.logger.info("Connection with client closed")

    def connect_pi(self):
        # assume first connection from pi server's address is correct
        # if pi server disconnects wait for reconnect
        self.logger.info("Connecting Pi")
        while self.pi == None or not self.pi.connected:
            try:
                self.pi = Connection(self.listener_socket.accept())
            except BlockingIOError:
                pass
            else:
                # verify pi is the correct ip
                if self.pi_address[0] == self.pi.address[0]:
                    if self.pi_address[1] != 0 and self.pi_address[1] != self.pi.address[1]:
                        self.pi.disconnect()
                else:
                    self.pi.disconnect()


        pi_priv_address = str_to_ip(self.pi.recv())
        self.logger.info(f"Pi addresses are {multiple_ip_to_str([self.pi.address, pi_priv_address])}")
        self.pi_address_string = multiple_ip_to_str([self.pi.address, pi_priv_address])
        self.pi.send(ip_to_str(self.pi.address))
