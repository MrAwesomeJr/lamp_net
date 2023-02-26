import lamp_server

my_address = ("0.0.0.0", 38282)
pi_address = ("61.244.128.52", 0)

server = lamp_server.Server(my_address, pi_address)
server.run()