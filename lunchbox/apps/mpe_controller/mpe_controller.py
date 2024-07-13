from collections import defaultdict
from dataclasses import dataclass
import time
from uuid import uuid4
import math

import mido
from mido import Message
import yaml

from lunchbox import Lunchbox, find_device

try:
    with open("mpe-controller-config.yml") as f:
        config = yaml.safe_load(f)
except:
    config = {}

DEBUG = False

MIN_MPE_CHANNEL = 1
MAX_MPE_CHANNEL = 15
#TODO: config
BEND_TIME = 1/4. #1/4 of a second

TET = 24

PITCH_BEND = False

#TODO: find_or_create_touch that increments mpe channel

#TODO: microtonality (round to nearest 12tet, then calculate pitch bend offset)

@dataclass
class Touch:
    id: str
    pad: int
    start_x: int
    start_y: int
    cur_x: int
    cur_y: int
    note: int
    channel: int
    released: bool
    release_time: float
    pitch_bend: float

    def new(pad, x, y, note, channel):
        id = str(uuid4())
        return Touch(id, pad, x, y, x, y, note, channel, False, 0, 0)

next_mpe_channel = MIN_MPE_CHANNEL
touches = []

#TODO: pass in delta time or something idk
last_time = time.time()
def update_touches():
    global last_time
    dt = time.time() - last_time
    last_time = time.time()
    
    for touch in touches.copy():
        if PITCH_BEND:
            target_bend = touch.cur_x - touch.start_x
            touch.pitch_bend += (target_bend - touch.pitch_bend) * 0.3 #TODO: config
            if touch.pitch_bend != 0:
                #TODO: only send one pitch bend per channel
                #TODO: config
                pitch = int(touch.pitch_bend * 8192 / 48.) #TODO: or something like that
                print(pitch)
                out_port.send(Message("pitchwheel", channel=touch.channel, pitch=pitch))
        if touch.released:
            touch.release_time += dt
        if touch.release_time > BEND_TIME:
            remove_touch(touch)

#find the first touch (or None) at the given x, y and pad
def find_touch(pad, x, y):
    found = [n for n in touches if n.pad == pad and n.cur_x == x and n.cur_y == y]
    if len(found) > 0:
        return found[0]
    
    return None

#find all touches left/right 1 x of the given x, y
def find_touch_bend(pad, x, y):
    found = [n for n in touches if n.pad == pad and abs(n.cur_x - x) == 1 and n.cur_y == y]
    return found

#remove touch with the same id
def remove_touch(touch):
    global touches
    touches = [t for t in touches if not (t.id == touch.id)]

H_STEP = config.get("h_step", 1)
V_STEP = config.get("v_step", 4)
X_OFFSET = config.get("x_offset", 0)
Y_OFFSET = config.get("y_offset", 0)
#middle c is 60
ROOT = config.get("root", 24) #octave 3
VEL_SCALE = config.get("vel_scale", 1.0)
VISUALIZER = config.get("visualizer", False)
#can be int or list
PAD_OCTAVE_OFFSETS = config.get("pad_octave_offsets", 1)
SPLIT_MODE = config.get("split_mode", 0)

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


def xy_to_note(x, y, pad):
    orig_x = x
    x = max(0, min(x, 7))
    x += X_OFFSET
    y = max(0, min(y, 7))
    y += Y_OFFSET
    
    if SPLIT_MODE > 0:
        x = x % 4
    
    note = x * H_STEP + y * V_STEP + ROOT
    if SPLIT_MODE > 0 and orig_x >= 4:
        note = note + TET * SPLIT_MODE
    note = note + transpose
    #adjust octave based on pad
    note = note + TET * PAD_OCTAVE_OFFSETS[pad]
    return note

#TODO: per-pad transpose
#TODO: reset to configured transpose
def press_top_button(button, pad):
    global transpose
    if DEBUG:
        print("Top button", button, "pressed")
    #octave up/down
    if button == 0:
        transpose += TET
        print(f"Transpose + {TET} ({transpose})")
        lunch.light(button, 8, "#FFFFFF", pad=pad)
    elif button == 1:
        transpose -= TET
        print(f"Transpose - {TET} ({transpose})")
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

def press_right_button(button, pad):
    if DEBUG:
        print("Right button", button, "pressed")

def release_top_button(button, pad):
    if DEBUG:
        print("Top button", button, "released")
    if button >= 0 and button < 5:
        lunch.light(button, 8, "#000000", pad=pad)

def release_right_button(button, pad):
    if DEBUG:
        print("Right button", button, "released")

def calc_microtonal(source_note, tet):
    #convert note in arbitrary tet to pitch
    pitch = 440 * 2 ** (source_note / tet)
    #convert pitch to nearest 12 tet
    target_note = math.log2(pitch / 440) * 12
    remainder = target_note % 1
    target_note = math.floor(target_note)

    return target_note, remainder

def send_microtonal_note(source_note, tet, velocity, channel):
    target_note, remainder = calc_microtonal(source_note, tet)
    print("og note:", source_note, "new note:", target_note, "remainder:", remainder)

    bend = math.floor(remainder / 48. * 8192)
    #pitch bend the remainder (??)
    out_port.send(Message("pitchwheel", channel=channel, pitch=bend))
    out_port.send(Message("note_on", note=target_note, velocity=velocity, channel=channel))

def release_microtonal_note(source_note, tet, channel):
    target_note, _ = calc_microtonal(source_note, tet)
    out_port.send(Message("note_off", note=target_note, channel=channel))

def press(x, y, velocity, pad=0):
    global next_mpe_channel
    if x == 8:
        press_right_button(y, pad)
        return
    if y == 8:
        press_top_button(x, pad)
        return
    note = xy_to_note(x, y, pad)
    print(note)
    if DEBUG:
        print("pad", pad, "pressed", note, velocity)

    if PITCH_BEND:
        touches_to_bend = find_touch_bend(pad, x, y)
        if len(touches_to_bend) > 0:
            for touch in touches_to_bend:
                touch.cur_x = x
                touch.cur_y = y
            return
        
    velocity = int((1 - VEL_SCALE) * 127) + int(velocity * VEL_SCALE)
    found_touch = find_touch(pad, x, y)
    if found_touch is not None:
        #end the found touch and start a new one
        remove_touch(found_touch)
    

    #create touch
    touch = Touch.new(pad, x, y, note, next_mpe_channel)
    next_mpe_channel += 1
    if next_mpe_channel > MAX_MPE_CHANNEL:
        next_mpe_channel = MIN_MPE_CHANNEL
    touches.append(touch)

    send_microtonal_note(touch.note, TET, velocity, touch.channel)
    #reset pitch for this channel too
    #out_port.send(Message("pitchwheel", channel=touch.channel, pitch=0))
    #out_port.send(Message("note_on", note=touch.note, velocity=velocity, channel=touch.channel))
    
    for pad in range(len(lunch.out_ports)):
        for x, y in get_all_xy(touch.note, pad):
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
    touch = find_touch(pad, x, y)
    if touch is None:
        print("no touch found at", x, y, "... how did we get here?")
        return
    touch.released = True
    #out_port.send(Message("note_on", note=touch.note, velocity=0, channel=touch.channel))
    release_microtonal_note(touch.note, TET, touch.channel)
    for pad in range(len(lunch.out_ports)):
        for x, y in get_all_xy(touch.note, pad):
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
    note = (note - transpose) % TET
    #color = COLORS[note % len(COLORS)] #TODO: readdress to support arbitrary TET
    color = "#000000" if note >= len(COLORS) else COLORS[note]
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
    update_touches()

def main():
    global PAD_OCTAVE_OFFSETS, lunch, out_port

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

    print("Opening output device...")
    out_port = mido.open_output(find_device(mido.get_output_names(), OUTPUT_DEVICE))
    
    feedback_port = None
    if FEEDBACK_DEVICE is not None:
        print("Opening feedback device...")
        feedback_port = mido.open_input(find_device(mido.get_input_names(), FEEDBACK_DEVICE), callback=lambda message: handle_feedback_message(message))
        
    reset_lights()
    
    print("Ready!")
    lunch.wait()

if __name__ == "__main__":
    main()
