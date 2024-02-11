import time

import mido
from mido import Message

PROGRAMMER_MODE = 1
LIVE_MODE = 0

def note_to_xy(note):
    x = (note % 10) - 1
    y = (note // 10) - 1
    return x, y

class Lunchbox:
    #TODO: add parameter for list of device names, otherwise autodetect
    def __init__(self, in_devices=[], out_devices=[], on_press=lambda x, y, vel:None, on_release=lambda x, y:None, on_polytouch=lambda x, y, val:None):
        self.in_devices = in_devices
        self.out_devices = out_devices
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
        #TODO: support multiple devices here
        self.inport = mido.open_input(in_device, callback=lambda message: self.handle_message(message))
        self.outport = mido.open_output(out_device)
        
        enter_programmer_mode = Message("sysex", data=[0, 32, 41, 2, 12, 14, PROGRAMMER_MODE])
        #TODO: auto exit prog mode on sigint
        self.outport.send(enter_programmer_mode)
        
    def wait(self):
        while True:
            time.sleep(1)
