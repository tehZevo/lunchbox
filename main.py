import mido
from mido import Message
#https://mido.readthedocs.io/en/stable/ports/index.html#callbacks

PROGRAMMER_MODE = 1
LIVE_MODE = 0

print(mido.get_input_names())
print(mido.get_output_names())

def print_message(message):
    print(message)
    
port = mido.open_input("MIDIIN2 (LPX MIDI) 3", callback=print_message)
outport = mido.open_output("MIDIOUT2 (LPX MIDI) 4")
port.callback = print_message

#TODO: send sysex to LP to turn it into programmer mode
enter_programmer_mode = Message("sysex", data=[0, 32, 41, 2, 12, 14, PROGRAMMER_MODE])

#TODO: auto exit prog mode on sigint

outport.send(enter_programmer_mode)

import time
while True:
    time.sleep(1)