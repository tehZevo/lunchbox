import time

import mido
from mido import Message
#https://mido.readthedocs.io/en/stable/ports/index.html#callbacks
#https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/downloads/Launchpad%20X%20-%20Programmers%20Reference%20Manual.pdf

from lunchbox import Lunchbox

print(mido.get_input_names())
print(mido.get_output_names())

def press(x, y, velocity):
    print("pressed", x, y, velocity)

def release(x, y):
    print("released", x, y)

def polytouch(x, y, value):
    print("polytouch", x, y, value)


in_device = "MIDIIN2 (LPX MIDI) 3"
out_device = "MIDIOUT2 (LPX MIDI) 4"

lunch = Lunchbox([in_device], [out_device], press, release, polytouch)
lunch.list_devices()
lunch.connect()
lunch.wait()