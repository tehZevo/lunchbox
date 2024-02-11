import sys
import signal
import re
import time
import traceback

import mido
from mido import Message

#https://mido.readthedocs.io/en/stable/ports/index.html#callbacks
#https://fael-downloads-prod.focusrite.com/customer/prod/s3fs-public/downloads/Launchpad%20X%20-%20Programmers%20Reference%20Manual.pdf

PROGRAMMER_MODE = 1
LIVE_MODE = 0

LIGHT_SYSEX = [0, 32, 41, 2, 12, 3]
RGB_LIGHT_TYPE = 3

MIDI_MATCH = [r"MIDI(IN|OUT)\d+ \(LPX MIDI\)", r"Launchpad X:"]

def should_autodetect_device(name):
    return any([re.match(pattern, name) for pattern in MIDI_MATCH])

def hex_to_rgb(hex):
    hex = hex.lstrip('#')
    return tuple(int(hex[i:i+2], 16) for i in (0, 2, 4))

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
    def __init__(self, on_press=lambda x, y, vel:None, on_release=lambda x, y:None, on_polytouch=lambda x, y, val:None):
        self.on_press = on_press
        self.on_release = on_release
        self.on_polytouch = on_polytouch
        self.in_ports = []
        self.out_ports = []
        self.connected_devices = []
    
    def light(self, x, y, r, g=None, b=None, pad=0):
        #assume hex
        if g is None:
            r, g, b = hex_to_rgb(r)
        x = max(0, min(x, 8))
        y = max(0, min(y, 8))
        message = light_message(x, y, r, g, b)
        self.out_ports[pad].send(message)
        
    def handle_message(self, message, pad):
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
        if len(mido.get_input_names()) == 0:
            print("<none>")
        for device in mido.get_input_names():
            print("-", device)
        
        print("Output devices:")
        if len(mido.get_output_names()) == 0:
            print("<none>")
        for device in mido.get_output_names():
            print("-", device)
    
    def list_connected_devices(self):
        print("Connected devices:")
        if len(self.connected_devices) == 0:
            print("<none>")
            return
            
        for in_device, out_device in self.connected_devices:
            print(f"- in: '{in_device}', out: '{out_device}'")
        
    
    def connect_to_pad(self, in_device, out_device, pad):
        in_port = mido.open_input(in_device, callback=lambda message: self.handle_message(message, pad))
        try:
            out_port = mido.open_output(out_device)
        except:
            traceback.print_exc()
            in_port.close()
            raise ValueError("Failed to fully connect to device.")
        
        enter_programmer_mode = Message("sysex", data=[0, 32, 41, 2, 12, 14, PROGRAMMER_MODE])
        out_port.send(enter_programmer_mode)
        
        self.in_ports.append(in_port)
        self.out_ports.append(out_port)
        self.connected_devices.append({
            "in": in_device,
            "out": out_device
        })
    
    def live_mode(self, pad):
        enter_live_mode = Message("sysex", data=[0, 32, 41, 2, 12, 14, LIVE_MODE])
        self.out_ports[pad].send(enter_live_mode)
        
    def connect(self, in_devices, out_devices):
        for pad, (in_device, out_device) in enumerate(zip(in_devices, out_devices)):
            self.connect_to_pad(in_device, out_device, pad)
    
    def autodetect(self):
        #idk if this will always work, but its worth a try
        in_names = [name for name in mido.get_input_names() if should_autodetect_device(name)]
        out_names = [name for name in mido.get_output_names() if should_autodetect_device(name)]
        in_out_pairs = list(zip(in_names, out_names))
        #try to connect to each device, store successes in our devices
        pads = 0
        for in_name, out_name in in_out_pairs:
            #try to connect to each pad pair
            try:
                self.connect_to_pad(in_name, out_name, pads)
                print(f"Connected to '{in_name}' / '{out_name}'")
                pads += 1
            except ValueError:
                print(f"Unable to connect to pad with input '{in_name}' and output '{out_name}'")
                
    
    def wait(self):
        #reset pads on sigint
        def signal_handler(sig, frame):
            for pad in range(len(self.out_ports)):
                self.live_mode(pad)
            sys.exit(0)
            #TODO: fix double ctrl c requirement
        
        signal.signal(signal.SIGINT, signal_handler)
        
        while True:
            time.sleep(1)
