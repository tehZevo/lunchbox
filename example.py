import time

import mido
from mido import Message
#https://mido.readthedocs.io/en/stable/ports/index.html#callbacks
#https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/downloads/Launchpad%20X%20-%20Programmers%20Reference%20Manual.pdf

from lunchbox import Lunchbox

print(mido.get_input_names())
print(mido.get_output_names())

def press(x, y, velocity, pad=0):
    print("pad", pad, "pressed", x, y, velocity)

def release(x, y, pad=0):
    print("pad", pad, "released", x, y)

def polytouch(x, y, value, pad=0):
    print("pad", pad, "polytouch", x, y, value)


in_device = "MIDIIN2 (LPX MIDI) 3"
out_device = "MIDIOUT2 (LPX MIDI) 4"

lunch = Lunchbox([in_device], [out_device], press, release, polytouch)
lunch.list_devices()
lunch.connect()

for r in range(4):
    for g in range(4):
        for b in range(4):
            bx = b % 2
            by = b // 2
            x = r + bx * 4
            y = g + by * 4
            print(r, g, b, x, y)
            r2 = r / 4 * 255
            g2 = g / 4 * 255
            b2 = b / 4 * 255
            lunch.light(x, y, r2, g2, b2)

#light up logo
lunch.light(8, 8, 0, 255, 0)

lunch.wait()