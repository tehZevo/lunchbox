from lunchbox import Lunchbox

def press(x, y, velocity, pad=0):
    lunch.light(x, y, "#00fF00", pad=pad)
    print("pad", pad, "pressed", x, y, velocity)

def release(x, y, pad=0):
    lunch.light(x, y, 0, 0, 0, pad=pad)
    print("pad", pad, "released", x, y)

def polytouch(x, y, value, pad=0):
    #lunch.light(x, y, value, value, value, pad=pad)
    print("pad", pad, "polytouch", x, y, value)


lunch = Lunchbox(press, release, polytouch)
lunch.list_devices()
# lunch.connect(
#     in_devices = [
#         "MIDIIN2 (LPX MIDI) 4",
#         "MIDIIN4 (LPX MIDI) 6",
#     ],
#     out_devices = [
#         "MIDIOUT2 (LPX MIDI) 5",
#         "MIDIOUT4 (LPX MIDI) 7",
#     ]
# )

lunch.autodetect()

# for r in range(4):
#     for g in range(4):
#         for b in range(4):
#             bx = b % 2
#             by = b // 2
#             x = r + bx * 4
#             y = g + by * 4
#             print(r, g, b, x, y)
#             r2 = r / 4 * 255
#             g2 = g / 4 * 255
#             b2 = b / 4 * 255
#             lunch.light(x, y, r2, g2, b2)
# 
# #light up logo
# lunch.light(8, 8, 0, 255, 0)

lunch.wait()