import mido
from mido import Message
#https://mido.readthedocs.io/en/stable/ports/index.html#callbacks
#https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/downloads/Launchpad%20X%20-%20Programmers%20Reference%20Manual.pdf

PROGRAMMER_MODE = 1
LIVE_MODE = 0

print(mido.get_input_names())
print(mido.get_output_names())

def press(x, y, velocity):
    print("pressed", x, y, velocity)

def release(x, y):
    print("released", x, y)

def polytouch(x, y, value):
    print("polytouch", x, y, value)

def note_to_xy(note):
    x = (note % 10) - 1
    y = (note // 10) - 1
    return x, y

def handle_message(message):
    # print(message)
    if message.type == "note_on":
        x, y = note_to_xy(message.note)
        if message.velocity > 0:
            press(x, y, message.velocity)
        else:
            release(x, y)
    if message.type == "polytouch":
        x, y = note_to_xy(message.note)
        polytouch(x, y, message.value)
    if message.type == "control_change":
        x, y = note_to_xy(message.control)
        if message.value > 0:
            press(x, y, message.value)
        else:
            release(x, y)
        
    
port = mido.open_input("MIDIIN2 (LPX MIDI) 3", callback=handle_message)
outport = mido.open_output("MIDIOUT2 (LPX MIDI) 4")
# port.callback = print_message

#TODO: send sysex to LP to turn it into programmer mode
enter_programmer_mode = Message("sysex", data=[0, 32, 41, 2, 12, 14, PROGRAMMER_MODE])

#TODO: auto exit prog mode on sigint

outport.send(enter_programmer_mode)

import time
while True:
    time.sleep(1)