import lamp_net_client
import time
import logging

# logging.getLogger()
# logging.basicConfig(level=logging.INFO)

client = lamp_net_client.Client()
client.connect(("54.254.195.195", 38282))

client.pixels.brightness = 0.1

# times are in seconds
timeout = 20*60
sleep_time = 0.1
minimum = 0
maximum = 255
pixel_count = 50
loop_size = 1200
# quadratic size is kind of arbitrary

quadratic_size = loop_size / 30

values = []
for pixel in range(0, loop_size):
    # at the point where r is 255, g should be 0
    # and then r = 254, either b or g should be 1
    # total at any given point is 255
    # b has to loop around the back
    r = -(((pixel)/quadratic_size)**2) + maximum
    if r <= 0:
        r = -(((pixel - int(loop_size))/quadratic_size)**2) + maximum
    g = -(((pixel - int(loop_size/3))/quadratic_size)**2) + maximum
    b = -(((pixel - int(loop_size*2/3))/quadratic_size)**2) + maximum

    # clamp values
    r = max(min(int(r), maximum), minimum)
    g = max(min(int(g), maximum), minimum)
    b = max(min(int(b), maximum), minimum)

    values.append((g, r, b))

print("loop_size:",loop_size)
print("sleep_time",sleep_time)
print("timeout",timeout)

start_time = time.perf_counter()
while timeout >= (time.perf_counter() - start_time):
    for frame in range(0, loop_size):
        client.pixels[:] = values[:pixel_count]
        client.pixels.show()
        values.append(values[0])
        values.pop(0)
        if sleep_time > 0:
            time.sleep(sleep_time)

client.pixels.fill((0, 0, 0))

