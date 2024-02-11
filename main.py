import time

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

class Lunchbox:
    def __init__(self, on_press=lambda x, y, vel:None, on_release=lambda x, y:None, on_polytouch=lambda x, y, val:None):
        #TODO: make these support a pad number
        self.on_press = on_press
        self.on_release = on_release
        self.on_polytouch = on_polytouch
        
    def handle_message(self, message):
        # print(message)
        if message.type == "note_on":
            x, y = note_to_xy(message.note)
            if message.velocity > 0:
                self.on_press(x, y, message.velocity)
            else:
                self.on_release(x, y)
        if message.type == "polytouch":
            x, y = note_to_xy(message.note)
            self.on_polytouch(x, y, message.value)
        if message.type == "control_change":
            x, y = note_to_xy(message.control)
            if message.value > 0:
                self.on_press(x, y, message.value)
            else:
                self.on_release(x, y)
                
    def connect(self):
        #TODO: search for all launchpads and autoconnect
        self.inport = mido.open_input("MIDIIN2 (LPX MIDI) 3", callback=lambda message: self.handle_message(message))
        self.outport = mido.open_output("MIDIOUT2 (LPX MIDI) 4")
        
        enter_programmer_mode = Message("sysex", data=[0, 32, 41, 2, 12, 14, PROGRAMMER_MODE])
        #TODO: auto exit prog mode on sigint
        self.outport.send(enter_programmer_mode)
        
    def wait(self):
        while True:
            time.sleep(1)

lunch = Lunchbox(press, release, polytouch)
lunch.connect()
lunch.wait()