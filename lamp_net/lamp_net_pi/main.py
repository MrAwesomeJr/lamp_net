import lamp_pi
import neopixel
import board

server_address = ("54.254.195.195", 38282)
pixels = neopixel.NeoPixel(board.D12, 50, brightness=1, auto_write = False)

pi = lamp_pi.Pi(server_address, pixels)
pi.run()