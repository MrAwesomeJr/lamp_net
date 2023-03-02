# lamp_net

designed to be used with my specific setup of a Raspberry Pi 4B 8GB connected to an ALITOVE 12mm 50 LED WS2811 strip, though should work most setups that supports the neopixel library (entirely untested)

It's a 3-way system that uses an intermediate server to faciliate peer2peer networking, then directly sends data from the client to the raspberry pi, in order to remotely update lights. TCP hole punching is used to peer2peer through NATs, because... well, really, it was just a learning experience. I wanted the pseudo-argument of "low latency". There are probably a lot of better ways to do this than the way I picked, such as:
  - including a buffer system
  - using UDP hole punching instead of TCP (has a higher success rate)
  - uploading code (low latency, jitter and bandwidth)
  - adding a message protocol (to prevent accidents from reading sockets at bad times)

dependencies: neopixel board

for any end user being told to use this repository by someone with a LED setup (probably me), the only relevant package to be installed is the lamp_net_client library. This isn't on PyPi (nor am i bothered to go through the pains of uploading it there) so you'll have to install/update it manually, but that shouldn't be too hard considering you've made it to this page.

todo:
  - add support for RGBW
  - allow client to add pixels in RGB or RBG independent of what setting the pi is on
  - fully (or at least correctly) implement adafruit_pixelbuf.PixelBuf (https://github.com/adafruit/Adafruit_CircuitPython_Pixelbuf/blob/dafbe8b7b19fcdbde7ff93f1cede4a0f5e1b0ec3/adafruit_pixelbuf.py#L31)
  - fix tcp connections not realizing when the endpoint is dead (usually through keyboardinterrupt)
