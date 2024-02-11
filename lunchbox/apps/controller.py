import mido
from mido import Message

from lunchbox import Lunchbox

#TODO: cli args

H_STEP = 1
V_STEP = 4
#middle c is 60
ROOT = 60 - 12 - 4
VEL_SCALE = 0.5
PAD_OCTAVE_OFFSETS = [-1, 1]
# 
# IN_DEVICES = [
#     "MIDIIN2 (LPX MIDI) 4",
#     "MIDIIN4 (LPX MIDI) 6",
# ]
# OUT_DEVICES = [
#     "MIDIOUT2 (LPX MIDI) 5",
#     "MIDIOUT4 (LPX MIDI) 7",
# ]

COLOR_ROOT = "#00FF00"
COLOR_OFF = "#000000"
COLOR_MAJOR = "#0000FF"
COLOR_WHITE = "#220500"

#starting at C when untransposed
lights = [
    #C C# D D#
    COLOR_ROOT, COLOR_OFF, COLOR_WHITE, COLOR_OFF,
    #E F F#
    COLOR_MAJOR, COLOR_WHITE, COLOR_OFF,
    #G G# A A# B
    COLOR_MAJOR, COLOR_OFF, COLOR_WHITE, COLOR_OFF, COLOR_WHITE
]


MIDO_DEVICE = "lunchbox 3"

def xy_to_note(x, y, pad):
    x = max(0, min(x, 7))
    y = max(0, min(y, 7))
    note = x * H_STEP + y * V_STEP + ROOT
    #adjust octave based on pad
    note = note + 12 * PAD_OCTAVE_OFFSETS[pad]
    return note

def press(x, y, velocity, pad=0):
    note = xy_to_note(x, y, pad)
    print("pad", pad, "pressed", note, velocity)
    velocity = int((1 - VEL_SCALE) * 127) + int(velocity * VEL_SCALE)
    out_port.send(Message("note_on", note=note, velocity=velocity))
    for pad in range(len(lunch.out_ports)):
        for x, y in get_all_xy(note, pad):
            lunch.light(x, y, "#FFFFFF", pad=pad)

def release(x, y, pad=0):
    note = xy_to_note(x, y, pad)
    #TODO: press all notes that match
    print("pad", pad, "released", note)
    out_port.send(Message("note_on", note=note, velocity=0))
    for pad in range(len(IN_DEVICES)):
        for x, y in get_all_xy(note, pad):
            lunch.light(x, y, get_natural_color(x, y, pad), pad=pad)
    # lunch.light(x, y, get_natural_color(x, y, pad), pad=pad)

def polytouch(x, y, value, pad=0):
    pass
    # lunch.light(x, y, value, value, value, pad=pad)
    # print("pad", pad, "polytouch", x, y, value)
    
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
    color = lights[note]
    return color

def reset_lights():
    for x in range(8):
        for y in range(8):
            for pad in range(len(lunch.out_ports)):
                lunch.light(x, y, get_natural_color(x, y, pad), pad=pad)




lunch = Lunchbox(press, release, polytouch)
lunch.list_devices()
lunch.autodetect()

out_port = mido.open_output(MIDO_DEVICE)
reset_lights()

lunch.wait()