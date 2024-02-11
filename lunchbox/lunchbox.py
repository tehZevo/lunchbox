import time

import mido
from mido import Message

PROGRAMMER_MODE = 1
LIVE_MODE = 0

def note_to_xy(note):
    x = (note % 10) - 1
    y = (note // 10) - 1
    return x, y

def xy_to_note(x, y):
    return (y + 1) * 10 + (x + 1)

def round_color(x):
    return int(max(0, min(x / 255, 1) * 127))
    
def light_message(x, y, r, g, b):
    r = round_color(r)
    g = round_color(g)
    b = round_color(b)
    index = xy_to_note(x, y)
    LIGHT_SYSEX = [0, 32, 41, 2, 12, 3]
    RGB_LIGHT_TYPE = 3
    return Message("sysex", data=[*LIGHT_SYSEX, RGB_LIGHT_TYPE, index, r, g, b])


class Lunchbox:
    #TODO: add parameter for list of device names, otherwise autodetect
    def __init__(self, in_devices=[], out_devices=[], on_press=lambda x, y, vel:None, on_release=lambda x, y:None, on_polytouch=lambda x, y, val:None):
        self.in_devices = in_devices
        self.out_devices = out_devices
        #TODO: make these support a pad number
        self.on_press = on_press
        self.on_release = on_release
        self.on_polytouch = on_polytouch
    
    def light(self, x, y, r, g, b, pad=0):
        x = max(0, min(x, 8))
        y = max(0, min(y, 8))
        message = light_message(x, y, r, g, b)
        self.outport.send(message)
        
    def handle_message(self, message, pad):
        # print(message)
        if message.type == "note_on":
            x, y = note_to_xy(message.note)
            if message.velocity > 0:
                self.on_press(x, y, message.velocity, pad=pad)
            else:
                self.on_release(x, y, pad=pad)
        if message.type == "polytouch":
            x, y = note_to_xy(message.note)
            self.on_polytouch(x, y, message.value, pad=pad)
        if message.type == "control_change":
            x, y = note_to_xy(message.control)
            if message.value > 0:
                self.on_press(x, y, message.value, pad=pad)
            else:
                self.on_release(x, y, pad=pad)
    
    def list_devices(self):
        print("Input devices:")
        for device in mido.get_input_names():
            print("-", device)
        
        print("Output devices:")
        for device in mido.get_output_names():
            print("-", device)
    
    def connect(self):
        #TODO: search for all launchpads and autoconnect
        in_device = self.in_devices[0]
        out_device = self.out_devices[0]
        pad = 0 #TODO: remove hardcoded pad number
        #TODO: support multiple devices here
        self.inport = mido.open_input(in_device, callback=lambda message: self.handle_message(message, pad))
        self.outport = mido.open_output(out_device)
        
        enter_programmer_mode = Message("sysex", data=[0, 32, 41, 2, 12, 14, PROGRAMMER_MODE])
        #TODO: auto exit prog mode on sigint
        self.outport.send(enter_programmer_mode)
        
    def wait(self):
        while True:
            time.sleep(1)
