from lunchbox import Lunchbox

H_STEP = 1
V_STEP = 4

def xy_to_note(x, y):
    x = max(0, min(x, 7))
    y = max(0, min(y, 7))
    return x * H_STEP + y * V_STEP

def press(x, y, velocity, pad=0):
    note = xy_to_note(x, y)
    print("pad", pad, "pressed", note, velocity)

def release(x, y, pad=0):
    note = xy_to_note(x, y)
    print("pad", pad, "released", note)

def polytouch(x, y, value, pad=0):
    pass
    # lunch.light(x, y, value, value, value, pad=pad)
    # print("pad", pad, "polytouch", x, y, value)


in_devices = [
    "MIDIIN2 (LPX MIDI) 1",
    "MIDIIN4 (LPX MIDI) 3",
]
out_devices = [
    "MIDIOUT2 (LPX MIDI) 2",
    "MIDIOUT4 (LPX MIDI) 4",
]

lunch = Lunchbox(in_devices, out_devices, press, release, polytouch)
lunch.list_devices()
lunch.connect()

lunch.wait()