from collections import defaultdict

import mido
from mido import Message
import yaml

from lunchbox import Lunchbox, find_device


try:
    with open("controller-config.yml") as f:
        config = yaml.safe_load(f)
except:
    config = {}

DEBUG = False

H_STEP = config.get("h_step", 1)
V_STEP = config.get("v_step", 4)
X_OFFSET = config.get("x_offset", 0)
Y_OFFSET = config.get("y_offset", 0)
#middle c is 60
ROOT = config.get("root", 24) #octave 3
VEL_CENTER = config.get("vel_center", 80)
VISUALIZER = config.get("visualizer", False)
#can be int or list
PAD_OCTAVE_OFFSETS = config.get("pad_octave_offsets", 1)
SPLIT_MODE = config.get("split_mode", 0)

SENSITIVITIES = [0, 0.25, 0.5, 1]
cur_sensitivity = 1

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
    # "#00000" for _ in range(12)
])

#TODO: flag for toggling each of: background colors, press colors, and polytouch sensitive colors
transpose = 0

OUTPUT_DEVICE = config.get("output_device", "loopMIDI Port")
FEEDBACK_DEVICE = config.get("feedback_device", None)
AUTODETECT = config.get("autodetect", True)
IN_DEVICES = config.get("in_devices", [])
OUT_DEVICES = config.get("out_devices", [])

pad_channels = []

def xy_to_note(x, y, pad):
    orig_x = x
    #TODO: test offsets
    x = max(0, min(x, 7))
    x += X_OFFSET
    y = max(0, min(y, 7))
    y += Y_OFFSET
    
    if SPLIT_MODE > 0:
        x = x % 4
    
    note = x * H_STEP + y * V_STEP + ROOT
    if SPLIT_MODE > 0 and orig_x >= 4:
        note = note + 12 * SPLIT_MODE
    note = note + transpose
    #adjust octave based on pad
    note = note + 12 * PAD_OCTAVE_OFFSETS[pad]
    return note

def set_pad_channel(pad, channel):
    pc = pad_channels[pad]
    if channel in pc:
        pc.remove(channel)
    else:
        pc.add(channel)
    #reset lights
    for i in range(8):
        lunch.light(8, i, "#000000", pad=pad)
    #set channel light from top down
    for c in pc:
        lunch.light(8, 7 - c, "#FFFFFF", pad=pad)

    print(f"Pad {pad} changed to channels {pc}")

#TODO: per-pad transpose
#TODO: reset to configured transpose
def press_top_button(button, pad):
    global transpose, cur_sensitivity
    
    if DEBUG:
        print("Top button", button, "pressed")
    #octave up/down
    if button == 0:
        transpose += 12
        print(f"Transpose + 12 ({transpose})")
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 1:
        transpose -= 12
        print(f"Transpose - 12 ({transpose})")
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 2:
        transpose -= 1
        print(f"Transpose - 1({transpose})")
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 3:
        transpose += 1
        print(f"Transpose + 1 ({transpose})")
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 4:
        transpose = 0
        print(f"Transpose reset ({transpose})")
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 7:
        cur_sensitivity += 1
        if cur_sensitivity >= len(SENSITIVITIES):
            cur_sensitivity = 0
        print(f"Sensitivity changed to {SENSITIVITIES[cur_sensitivity]}")
        lunch.light(button, 8, "#FFFFFF", pad=pad)

def press_right_button(button, pad):
    if DEBUG:
        print("Right button", button, "pressed")
    set_pad_channel(pad, 7 - button)

def release_top_button(button, pad):
    if DEBUG:
        print("Top button", button, "released")
    if button >= 0 and button < 5:
        lunch.light(button, 8, "#000000", pad=pad)
    if button == 7:
        update_sense_lights()

def release_right_button(button, pad):
    if DEBUG:
        print("Right button", button, "released")

def update_sense_lights():
    #TODO: make global/config
    sens_lights = [0, 32, 64, 127]
    sens_l = sens_lights[cur_sensitivity]
    lunch.light(7, 8, sens_l, sens_l, sens_l, pad=0)
    lunch.light(7, 8, sens_l, sens_l, sens_l, pad=1)

#calculate velocity based on center value in config and current sensitivity
def calc_velocity(input_velocity):
    sens = SENSITIVITIES[cur_sensitivity]
    vel_float = input_velocity / 127.
    vel_min = VEL_CENTER + (0 - VEL_CENTER) * sens
    vel_max = VEL_CENTER + (127 - VEL_CENTER) * sens
    velocity = int(vel_min + (vel_max - vel_min) * vel_float)

    return velocity

def press(x, y, velocity, pad=0):
    if x == 8:
        press_right_button(y, pad)
        return
    if y == 8:
        press_top_button(x, pad)
        return
    note = xy_to_note(x, y, pad)
    if DEBUG:
        print("pad", pad, "pressed", note, velocity)
    velocity = calc_velocity(velocity)
    for c in pad_channels[pad]:
        out_port.send(Message("note_on", note=note, velocity=velocity, channel=c))
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
    if DEBUG:
        print("pad", pad, "released", note)
    for c in pad_channels[pad]:
        out_port.send(Message("note_on", note=note, velocity=0, channel=c))
    for pad in range(len(lunch.out_ports)):
        for x, y in get_all_xy(note, pad):
            lunch.light(x, y, get_natural_color(x, y, pad), pad=pad)

def polytouch(x, y, value, pad=0):
    note = xy_to_note(x, y, pad)
    for pad in range(len(lunch.out_ports)):
        for x, y in get_all_xy(note, pad):
            pass
            # lunch.light(x, y, value, value, value, pad=pad)

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
    note = (note - transpose) % 12
    color = COLORS[note]
    return color

def reset_lights():
    for x in range(8):
        for y in range(8):
            for pad in range(len(lunch.out_ports)):
                lunch.light(x, y, get_natural_color(x, y, pad), pad=pad)

lunch = None
out_port = None

def feedback_press(note):
    #light up x/y that should be pressed
    for pad in range(len(lunch.connected_devices)):
        for x, y in get_all_xy(note, pad):
            lunch.light(x, y, "#FFFFFF", pad=pad)
            
def feedback_release(note):
    #reset lights of x/y that should be released
    for pad in range(len(lunch.connected_devices)):
        for x, y in get_all_xy(note, pad):
            color = get_natural_color(x, y, pad)
            lunch.light(x, y, color, pad=pad)

def handle_feedback_message(message):
    if message.type == "note_on":
        if message.velocity > 0:
            feedback_press(message.note)
        else:
            feedback_release(note)
    if message.type == "note_off":
        feedback_release(message.note)

counter = 0
def update(lunch):
    pass
    # global counter
    # counter += 1
    # print("hi", counter)

def main():
    global PAD_OCTAVE_OFFSETS, lunch, out_port, pad_channels

    lunch = Lunchbox(press, release, polytouch, visualizer=VISUALIZER, update_function=update)
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

    pad_channels = [set() for _ in lunch.connected_devices]
    for pad, _ in enumerate(pad_channels):
        set_pad_channel(pad, 0)
    
    print("Opening output device...")
    out_port = mido.open_output(find_device(mido.get_output_names(), OUTPUT_DEVICE))
    
    feedback_port = None
    if FEEDBACK_DEVICE is not None:
        print("Opening feedback device...")
        feedback_port = mido.open_input(find_device(mido.get_input_names(), FEEDBACK_DEVICE), callback=lambda message: handle_feedback_message(message))
        
    reset_lights()
    update_sense_lights()
    
    print("Ready!")
    lunch.wait()

if __name__ == "__main__":
    main()
