import time

import mido
from mido import Message

#https://mido.readthedocs.io/en/stable/ports/index.html#callbacks
#https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/downloads/Launchpad%20X%20-%20Programmers%20Reference%20Manual.pdf

PROGRAMMER_MODE = 1
LIVE_MODE = 0

LIGHT_SYSEX = [0, 32, 41, 2, 12, 3]
RGB_LIGHT_TYPE = 3

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
    return Message("sysex", data=[*LIGHT_SYSEX, RGB_LIGHT_TYPE, index, r, g, b])


class Lunchbox:
    #TODO: add parameter for list of device names, otherwise autodetect
    def __init__(self, in_devices=[], out_devices=[], on_press=lambda x, y, vel:None, on_release=lambda x, y:None, on_polytouch=lambda x, y, val:None):
        self.in_devices = in_devices
        self.out_devices = out_devices
        self.on_press = on_press
        self.on_release = on_release
        self.on_polytouch = on_polytouch
        self.in_ports = []
        self.out_ports = []
    
    def light(self, x, y, r, g, b, pad=0):
        x = max(0, min(x, 8))
        y = max(0, min(y, 8))
        message = light_message(x, y, r, g, b)
        self.out_ports[pad].send(message)
        
    def handle_message(self, message, pad):
        print(pad)
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
    
    def connect_to_pad(self, in_device, out_device, pad):
        in_port = mido.open_input(in_device, callback=lambda message: self.handle_message(message, pad))
        out_port = mido.open_output(out_device)
        
        enter_programmer_mode = Message("sysex", data=[0, 32, 41, 2, 12, 14, PROGRAMMER_MODE])
        #TODO: auto exit prog mode on sigint
        out_port.send(enter_programmer_mode)
        
        return in_port, out_port
        
    def connect(self):
        #TODO: search for all launchpads and autoconnect
        for pad, (in_device, out_device) in enumerate(zip(self.in_devices, self.out_devices)):
            in_port, out_port = self.connect_to_pad(in_device, out_device, pad)
            self.in_ports.append(in_port)
            self.out_ports.append(out_port)
        
    def wait(self):
        while True:
            time.sleep(1)
