import mido
from mido import Message

import yaml

from lunchbox import Lunchbox

try:
    with open("controller-config.yml") as f:
        config = yaml.safe_load(f)
except:
    config = {}

H_STEP = config.get("h_step", 1)
V_STEP = config.get("v_step", 4)
X_OFFSET = config.get("x_offset", 4)
Y_OFFSET = config.get("x_offset", 3)
#middle c is 60
ROOT = config.get("root", 24) #octave 3
VEL_SCALE = config.get("vel_scale", 1.0)
#can be int or list
PAD_OCTAVE_OFFSETS = config.get("pad_octave_offsets", 1) #[-1, 1]

COLOR_ROOT = "#00FF00"
COLOR_OFF = "#000000"
COLOR_MAJOR = "#0000FF"
COLOR_WHITE = "#330500"
#starting at C when untransposed
COLORS = config.get("colors", [
    #C C# D D#
    COLOR_ROOT, COLOR_OFF, COLOR_WHITE, COLOR_OFF,
    #E F F#
    COLOR_MAJOR, COLOR_WHITE, COLOR_OFF,
    #G G# A A# B
    COLOR_MAJOR, COLOR_OFF, COLOR_WHITE, COLOR_OFF, COLOR_WHITE
])

#TODO: flag for toggling each of: background colors, press colors, and velocity sensitive colors
#TODO: transpose
transpose = 0

OUTPUT_DEVICE = config.get("output_device", "loopMIDI Port")
AUTODETECT = config.get("autodetect", True)
IN_DEVICES = config.get("in_devices", [])
OUT_DEVICES = config.get("out_devices", [])

def xy_to_note(x, y, pad):
    #TODO: test offsets
    x = max(0, min(x, 7))
    x += X_OFFSET
    y = max(0, min(y, 7))
    y += Y_OFFSET
    
    note = x * H_STEP + y * V_STEP + ROOT
    note = note + transpose
    #adjust octave based on pad
    note = note + 12 * PAD_OCTAVE_OFFSETS[pad]
    return note

#TODO: per-pad transpose
#TODO: reset to configured transpose
def press_top_button(button, pad):
    global transpose
    print("Top button", button, "pressed")
    #octave up/down
    if button == 0:
        print(f"transpose + 12 ({transpose})")
        transpose += 12
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 1:
        print(f"transpose - 12 ({transpose})")
        transpose -= 12
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 2:
        print(f"transpose - 1({transpose})")
        transpose -= 1
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 3:
        print(f"transpose + 1 ({transpose})")
        transpose += 1
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 4:
        print(f"transpose reset ({transpose})")
        transpose = 0
        lunch.light(button, 8, "#FFFFFF", pad=pad)

def press_right_button(button, pad):
    print("Right button", button, "pressed")

def release_top_button(button, pad):
    print("Top button", button, "released")
    if button >= 0 and button < 5:
        lunch.light(button, 8, "#000000", pad=pad)

def release_right_button(button, pad):
    print("Right button", button, "released")

def press(x, y, velocity, pad=0):
    if x == 8:
        press_right_button(y, pad)
        return
    if y == 8:
        press_top_button(x, pad)
        return
    note = xy_to_note(x, y, pad)
    print("pad", pad, "pressed", note, velocity)
    velocity = int((1 - VEL_SCALE) * 127) + int(velocity * VEL_SCALE)
    out_port.send(Message("note_on", note=note, velocity=velocity))
    for pad in range(len(lunch.out_ports)):
        for x, y in get_all_xy(note, pad):
            lunch.light(x, y, "#FFFFFF", pad=pad)

def release(x, y, pad=0):
    if x == 8:
        release_right_button(y, pad)
        return
    if y == 8:
        release_top_button(x, pad)
        return
    note = xy_to_note(x, y, pad)
    #TODO: press all notes that match
    print("pad", pad, "released", note)
    out_port.send(Message("note_on", note=note, velocity=0))
    for pad in range(len(lunch.out_ports)):
        for x, y in get_all_xy(note, pad):
            lunch.light(x, y, get_natural_color(x, y, pad), pad=pad)

def polytouch(x, y, value, pad=0):
    note = xy_to_note(x, y, pad)
    for pad in range(len(lunch.out_ports)):
        for x, y in get_all_xy(note, pad):
            lunch.light(x, y, value, value, value, pad=pad)
    
def get_all_xy(note, pad):
    xy = []
    for x in range(8):
        for y in range(8):
            n = xy_to_note(x, y, pad)
            if n == note:
                xy.append((x, y))
    return xy

def get_natural_color(x, y, pad):
    note = xy_to_note(x, y, pad)
    note = note % 12
    color = COLORS[note]
    return color

def reset_lights():
    for x in range(8):
        for y in range(8):
            for pad in range(len(lunch.out_ports)):
                lunch.light(x, y, get_natural_color(x, y, pad), pad=pad)

lunch = None
out_port = None

def main():
    global PAD_OCTAVE_OFFSETS, lunch, out_port
    
    lunch = Lunchbox(press, release, polytouch)
    print("Availalable midi devices:")
    lunch.list_devices()
    
    if AUTODETECT:
        lunch.autodetect()
    else:
        lunch.connect(IN_DEVICES, OUT_DEVICES)
    
    if len(lunch.connected_devices) == 0:
        print("No devices connected to Lunchbox, exiting.")
        exit(0)

    #TODO: test
    if type(PAD_OCTAVE_OFFSETS) == int:
        PAD_OCTAVE_OFFSETS = [PAD_OCTAVE_OFFSETS * i for i in range(len(lunch.out_ports))]

    out_port = mido.open_output(OUTPUT_DEVICE)
    reset_lights()

    lunch.wait()

if __name__ == "__main__":
    main()