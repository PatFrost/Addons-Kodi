
import sys
import json

from joystick import *

# for test move mouse with ThumbStick
#import input


def getCoordinates(posx, posy, area=None, offset=None):
    if area is not None:
        acx, acy = [(c/2.0) for c in area]
        posx *= acx
        posy *= acy
    if offset is not None:
        posx += offset[0]
        posy += offset[1]
    return posx, posy


def sample_first_joystick():
    print("sample_first_joystick")
    """
    Grab 1st available Gamepad, logging changes to the screen.
    L & R analogue triggers set the vibration motor speed.
    ThumbStick to move mouse
    """
    # hotkeys for multiple buttons pressed
    # id based on xinput_h.KBUTTONS.keys
    combinations = {
        "Hot 1": [1, 2, 3, 0],
        "Hot 2": [1, 5, 3],
        "Start Kodi": [4, 5, 14],
        }
    joysticks = get_joysticks(combinations)
    joys_count = len(joysticks)

    if not joys_count:
        sys.exit(0)

    globals().update(count_changed=False)
    def _thread_joysticks_count():
        if check_joysticks_count(joys_count) != 0:
            globals().update(count_changed=True)
        else:
            timer_thread = Timer(5, _thread_joysticks_count, ())
            timer_thread.start()
    timer_thread = Timer(1, _thread_joysticks_count, ())
    timer_thread.start()

    # for test move mouse with ThumbStick
    coord = input.get_desktop_res()
    offset = [(c/2.0) for c in coord]
    area = (200, 200)

    def onCombo(name):
        print("hotkeys", name, combinations[name])

    def onButton(button, pressed):
        print('button', button, pressed)

    def onAxis(axis, value):
        print('axis', axis, value)
        if axis == "LeftTrigger":
            joy.setVibration(value, 0)
        elif axis == "RightTrigger":
            joy.setVibration(0, value)
        else:
            dx, dy = value
            x, y = getCoordinates(dx, dy, area, offset)
            input.setPosition(x, y)

    for j in joysticks:
        j.on_axis = onAxis
        j.on_button = onButton
        j.on_combinations = onCombo
        print json.dumps(j.information(), sort_keys=True, indent=2)
        print "-"*60

    # main loop
    while True:
        for joy in joysticks:
            joy.dispatch_events()
            time.sleep(.01)

        if count_changed:
            break

    try: timer_thread.cancel()
    except: pass
    if count_changed:
        print("New device connected or disconnected!")
        sample_first_joystick()


def sample_mouse_joystick():
    print("sample_mouse_joystick")
    """
    Grab 1st available Gamepad, logging changes to the screen.
    L & R analogue triggers sroll up or down.
    ThumbStick to move mouse
    """
    # for test move mouse with ThumbStick
    coord = input.get_desktop_res()
    offset = [(c/2.0) for c in coord]
    speed = 10.0
    startx = starty = None #input.getPosition()
    globals().update(startx=startx, starty=starty)

    joysticks = get_joysticks(onMouse=True)
    joys_count = len(joysticks)

    if not joys_count:
        sys.exit(0)

    globals().update(count_changed=False)
    def _thread_joysticks_count():
        if check_joysticks_count(joys_count) != 0:
            globals().update(count_changed=True)
        else:
            timer_thread = Timer(5, _thread_joysticks_count, ())
            timer_thread.start()
    timer_thread = Timer(1, _thread_joysticks_count, ())
    timer_thread.start()

    joy = joysticks[0]

    @joy.event
    def on_button(button, pressed):
        kid, d = button
        if not pressed:
            if d["name"] == "a":
                input.releaseButton("left")
            elif d["name"] == "b":
                input.releaseButton("right")
        elif pressed:
            if d["name"] == "a":
                input.pressButton("left")
            elif d["name"] == "b":
                input.pressButton("right")
            elif d["name"] in ["leftbumper", "leftthumb"]:
                input.clickButton("left")
            elif d["name"] in ["rightbumper", "rightthumb"]:
                input.clickButton("right")
            elif d["name"] == "y":
                input.clickButton("middle")
            elif d["name"] == "x":
                input.clickButton("x")
            elif d["name"] == "start":
                input.pressKey("enter")
            elif d["name"] == "back":
                input.pressKey("back")
            elif d["name"] == "up":
                input.pressKey("up")
            elif d["name"] == "down":
                input.pressKey("down")
            elif d["name"] == "left":
                input.pressKey("left")
            elif d["name"] == "right":
                input.pressKey("right")

    @joy.event
    def on_axis(axis, value):
        if axis == "LeftTrigger":
            input.scroll(value*2)
        elif axis == "RightTrigger":
            input.scroll(value*-2)
        else:
            dx, dy = value
            x, y = (dx*speed, dy*speed)
            global startx, starty
            if startx == starty == None:
                startx, starty = input.getPosition()
            startx = max(min(int(startx+x), coord[0]), 0)
            starty = max(min(int(starty+y), coord[1]), 0)
            input.setPosition(startx, starty)

    # main loop
    while True:
        joy.dispatch_events()
        time.sleep(.01)

        if count_changed:
            break

    try: timer_thread.cancel()
    except: pass
    if count_changed:
        print("New device connected or disconnected!")
        sample_mouse_joystick()

if __name__ == "__main__":
    #sample_mouse_joystick()
    sample_first_joystick()
