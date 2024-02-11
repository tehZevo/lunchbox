import mido
from mido import Message

from lunchbox import Lunchbox

H_STEP = 1
V_STEP = 4
#middle c is 60
ROOT = 60 - 12
VEL_SCALE = 0.5
PAD_OCTAVE_OFFSETS = [-1, 1]

#starting at C when untransposed
lights = [
    [0, 0, 255],
    [0, 0, 255]
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

def release(x, y, pad=0):
    note = xy_to_note(x, y, pad)
    print("pad", pad, "released", note)
    out_port.send(Message("note_on", note=note, velocity=0))

def polytouch(x, y, value, pad=0):
    pass
    # lunch.light(x, y, value, value, value, pad=pad)
    # print("pad", pad, "polytouch", x, y, value)




in_devices = [
    "MIDIIN2 (LPX MIDI) 4",
    "MIDIIN4 (LPX MIDI) 6",
]
out_devices = [
    "MIDIOUT2 (LPX MIDI) 5",
    "MIDIOUT4 (LPX MIDI) 7",
]

lunch = Lunchbox(in_devices, out_devices, press, release, polytouch)
lunch.list_devices()
lunch.connect()

out_port = mido.open_output(MIDO_DEVICE)

lunch.wait()