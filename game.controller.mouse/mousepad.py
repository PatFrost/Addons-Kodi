
import time
from traceback import print_exc

from joystick import *

class MousePad:
    def __init__(self):
        self.stop = False
        
        # for move mouse with ThumbStick
        self.coord = input.get_desktop_res()
        self.offset = [(c/2.0) for c in self.coord]
        self.speed = 10.0
        self.startx = self.starty = None #input.getPosition()

        self.joys_count = 0
        self.count_changed = False
        
        self.run()

    def _thread_joysticks_count(self):
        try:
            if check_joysticks_count(self.joys_count) != 0:
                self.count_changed = True
            else:
                if not self.stop:
                    self.thread1 = Timer(5, self._thread_joysticks_count, ())
                    self.thread1.start()
        except:
            print_exc()

    def run(self):
        self.joysticks = get_joysticks(onMouse=True)
        self.joys_count = len(self.joysticks)

        # setup events
        for j in self.joysticks:
            j.on_axis = self.onAxis
            j.on_button = self.onButton
            j.on_combinations = self.onCombo

        self.thread1 = Timer(1, self._thread_joysticks_count, ())
        self.thread1.start()
        self.thread2 = Timer(1, self.onChatpad, ())
        self.thread2.start()
        
        # main loop
        try:
            joy = self.joysticks[0]
            while not self.stop:
                #for joy in self.joysticks:
                joy.dispatch_events()
                time.sleep(.01)

                if self.count_changed:
                    break
        except:
            print_exc()
            self.stop = True

        try: self.thread1.cancel()
        except: pass
        try: self.thread2.cancel()
        except: pass

        if not self.stop and self.count_changed:
            print("New device connected or disconnected!")
            self.run()

    def onCombo(self, name):
        print("hotkeys", name)#, combinations[name])

    def onChatpad(self):
        # need a thread or Timer
        while not self.stop:
            if input.getX1State():
                for j in self.joysticks:
                    j.setVibration(1, 0)
                print(("X1", "pressed"))
                time.sleep(.1)
            if input.getX2State():
                for j in self.joysticks:
                    j.setVibration(0, 1)
                print(("X2", "pressed"))
                time.sleep(.1)
            time.sleep(.015)

    def onButton(self, button, pressed):
        kid, d = button
        try:
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
        except:
            print_exc()

    def onAxis(self, axis, value):
        try:
            if axis == "LeftTrigger":
                input.scroll(value*1.5)
            elif axis == "RightTrigger":
                input.scroll(value*-1.5)
            else:
                # thumbstick move mouse
                dx, dy = value
                x, y = (dx*self.speed, dy*self.speed)
                if self.startx == self.starty == None:
                    self.startx, self.starty = input.getPosition()
                self.startx = max(min(int(self.startx+x), self.coord[0]), 0)
                self.starty = max(min(int(self.starty+y), self.coord[1]), 0)
                input.setPosition(self.startx, self.starty)
        except:
            print_exc()

MousePad()
