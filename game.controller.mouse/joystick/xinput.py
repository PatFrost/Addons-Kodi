"""
based on jaraco.input
https://github.com/jaraco/jaraco.input/blob/master/jaraco/input/win32/xinput.py
"""


import time
from math import sqrt
from threading import Timer
from operator import attrgetter

from xinput_h import *
#from dinput import get_devices
from winmm import getJoyNames
from event import EventDispatcher


def setTriggerDeadzone(value, value2):
    if value < XINPUT_GAMEPAD_TRIGGER_THRESHOLD:
        value = 0.0
    else:
        value = (value/255.0)
        # value -= XINPUT_GAMEPAD_TRIGGER_THRESHOLD
    # value *= 1.0 / (255.0 - XINPUT_GAMEPAD_TRIGGER_THRESHOLD)
    if value2 < XINPUT_GAMEPAD_TRIGGER_THRESHOLD:
        value2 = 0.0
    else:
        value2 = (value2/255.0)
        # value2 -= XINPUT_GAMEPAD_TRIGGER_THRESHOLD
    # value2 *= 1.0 / (255.0 - XINPUT_GAMEPAD_TRIGGER_THRESHOLD)
    return value, value2

def setThumbStickDeadzone(X, Y, INPUT_DEADZONE):
    # http://msdn.microsoft.com/en-gb/library/windows/desktop/ee417001%28v=vs.85%29.aspx#dead_zone
    # determine how far the controller is pushed
    magnitude = sqrt(X*X + Y*Y)

    # check if the controller is outside a circular dead zone
    if (magnitude > INPUT_DEADZONE):
        # determine the direction the controller is pushed
        normalizedX = X / magnitude
        normalizedY = Y / magnitude

        # clip the magnitude at its expected maximum value
        magnitude = min(32767.0, magnitude)

        # adjust magnitude relative to the end of the dead zone
        magnitude -= INPUT_DEADZONE

        # normalize the magnitude with respect to its expected range
        # giving a magnitude value of 0.0 to 1.0
        normMagnitude = magnitude / (32767.0 - INPUT_DEADZONE)

        # Y is negated because xbox controllers have an opposite sign from
        # the 'standard controller' recommendations.
        return (normalizedX * normMagnitude, -normalizedY * normMagnitude)
    else:
        # if the controller is in the deadzone zero out the magnitude
        return (0.0, 0.0)

def get_names():
    return getJoyNames()
    #names = [d.name for d in reversed(get_devices())]
    #names = [d.name for d in get_devices()]
    #return names
DEVICE_NAMES = get_names()
DEVICE_COUNT = len(DEVICE_NAMES)


class Joystick(EventDispatcher):
    """
    Joystick

    A stateful wrapper, using pyglet event model, that binds to one
    XInput device and dispatches events when states change.

    Gamepad that were tested:
     - Xbox ONE for Windows Wireless controller.
     - Logitech F310 Wired controller.

    Params:
      combinations : [opt] dict. hotkeys for multiple buttons pressed
                                 id based on xinput_h.KBUTTONS.keys

      onMouse : [opt] bool - False (default)
      onMouse : [opt] bool - True = D'ont wait dwPacketNumber change
                                    for axis, is good for move cursor.

    Example:
      controller_one = Joystick(0)

      joy_mouse = Joystick(0, onMouse=True)

      hotkeys = {
        "Hot 1": [1, 2, 3, 0],
        "Hot 2": [1, 5, 3],
        "Start Kodi": [4, 5, 14],
        }
      controller_hotkeys = Joystick(0, combinations=hotkeys)
    """

    @staticmethod
    def enumerate_devices(combinations={}, onMouse=False):
        "Returns the devices that are connected"
        devices = []
        for i in range(MAX_DEVICES):
            d = Joystick(i, combinations, onMouse)
            if d.isConnected():
                devices.append(d)
        return devices

    def __init__(self, device_number, combinations, onMouse):
        # if DEVICE_COUNT >= device_number+1:
            # name = DEVICE_NAMES[device_number]
        # elif DEVICE_COUNT == device_number:
            # name = DEVICE_NAMES[device_number-1]
        # else:
            # name = "Controller %i" % (device_number+1)
        name = DEVICE_NAMES.get(device_number,
                                "Joystick %i" % (device_number+1))

        battery_info = XINPUT_BATTERY_INFORMATION()
        capabilities = {"name": name, "device": device_number}

        buttons = set()
        last_state = None
        received_packets = 0
        missed_packets = 0

        values = vars()
        values.pop('self')
        self.__dict__.update(values)

        map(self.register_event_type, ['on_axis',
                                       'on_button',
                                       'on_combinations',
                                       'on_missed_packet',
                                       'on_state_changed'])

        super(Joystick, self).__init__()

        state = self.getState(True)
        self.ex = state is not None
        if not self.ex:
            state = self.getState(False)
        self.last_state = state
        self.getCapabilities()

    def getKeystroke(self):
        keystroke = XINPUT_KEYSTROKE()
        res = XInputGetKeystroke(XUSER_INDEX_ANY,
                                 XINPUT_FLAG_KEYBOARD,
                                 pointer(keystroke))
        if res == ERROR_SUCCESS:
            for f, v in XINPUT_KEYSTROKE._fields_:
                if f == "VirtualKey":
                    print(f, hex(getattr(keystroke, f)))
                else:
                    print(f, getattr(keystroke, f))
            print "-"*50
        # elif res == ERROR_EMPTY:
            # print("No new gamepad keystrokes.")
        # else:
            # print res

    def getState(self, ex=True):
        "Get the state of the controller represented by this object"
        state = XINPUT_STATE()
        if ex:
            res = XInputGetStateEx(self.device_number, byref(state))
        else:
            res = XInputGetState(self.device_number, byref(state))
        if res == ERROR_SUCCESS:
            #self.getKeystroke()
            return state
        else:
            return None # (device is not connected)

    def isConnected(self):
        connected = self.last_state is not None
        #connected = self.setVibration(0, 0)
        if connected:
            if self.battery_info.BatteryType == BATTERY_TYPE_DISCONNECTED:
                self.getBatteryInfo()
        return connected

    def getCapabilities(self):
        cap = XINPUT_CAPABILITIES()
        res = XInputGetCapabilities(self.device_number,
                                    XINPUT_FLAG_GAMEPAD,
                                    pointer(cap))
        c = {}
        c["type"] = ("Other", "Game")[cap.Type]
        c["subtype"] = ("Other", "Gamepad")[cap.SubType == 1]
        if cap.SubType == 1 and cap.Type == 0:
            c["type"] = "Game"
        c["flags"] = 0 #cap.Flags

        b = {}
        wb = cap.Gamepad.wButtons
        for button, (bitmask, kid) in sorted(WBUTTONS.items()):
            b[KBUTTONS[kid]["name"]] = (wb & bitmask == bitmask)
        b["guide"] = b["guide"] or self.ex
        c["buttons"] = b

        g = cap.Gamepad
        b = {}
        for a, t in AXIS_FIELDS:
            t = getattr(g, a)
            b[a[1:].lower()] = (t == (-64, 255)[a.startswith("b")])
        c["axis"] = b

        c["vibration"] = {"low": cap.Vibration.wLeftMotorSpeed == 255,
                          "high": cap.Vibration.wRightMotorSpeed == 255}

        self.capabilities.update(c)

    def information(self):
        return self.capabilities

    def getBatteryInfo(self):
        "return battery level and type"
        bat_info = XINPUT_BATTERY_INFORMATION()
        XInputGetBatInfo(self.device_number,      # Index of the gamer associated with the device
                         BATTERY_DEVTYPE_GAMEPAD, # Which device on this user index
                         pointer(bat_info))

        if self.battery_info.BatteryLevel != bat_info.BatteryLevel:
            self.battery_info = bat_info
            b = {"level": bat_info.BatteryLevel, "type": bat_info.BatteryType,
                 "percent": (0, 33, 75, 100)[bat_info.BatteryLevel]}
            self.capabilities.update(battery=b)

    def setVibration(self, leftmotor, rightmotor, timeoff=0):
        "Control the speed of both motors seperately"
        rumble = XINPUT_VIBRATION(max(min(int(leftmotor*65535), 65535), 0),
                                  max(min(int(rightmotor*65535), 65535), 0))
        ok = XInputSetState(self.device_number, byref(rumble)) == ERROR_SUCCESS
        if ok and (0 < timeoff > 2):
            time.sleep(timeoff)
            XInputSetState(self.device_number, byref(XINPUT_VIBRATION(0, 0)))
        return ok

    def dispatch_events(self):
        "The main event loop for a joystick"
        state = self.getState(True)
        if state is not None:
            if self.onMouse or state.dwPacketNumber != self.last_state.dwPacketNumber:
                # state has changed, handle the change
                self.update_packet_count(state)
                self.handle_changed_state(state)
                self.last_state = state

    def update_packet_count(self, state):
        "Keep track of received and missed packets for performance tuning"
        self.received_packets += 1
        missed_packets = state.dwPacketNumber-self.last_state.dwPacketNumber-1
        if missed_packets:
            self.dispatch_event('on_missed_packet', missed_packets)
        self.missed_packets += missed_packets

    def handle_changed_state(self, state):
        "Dispatch various events as a result of the state changing"
        self.dispatch_event('on_state_changed', state)
        self.dispatchState(state)
        if self.battery_info.BatteryType == BATTERY_TYPE_DISCONNECTED:
            self.getBatteryInfo()

    def rapidThumb(self, dx, dy, speed=1.5):
        right = dx > 0.5
        left = dx < -0.5
        up = dy > 0.5
        down = dy < -0.5
        if right or left:
            dx *= speed
        if up or down:
            dy *= speed
        return (dx, dy)

    def dispatchState(self, state):
        g1 = state.Gamepad
        g2 = self.last_state.Gamepad

        # on_axis
        if self.onMouse or g1.sThumbLX != g2.sThumbLX or g1.sThumbLY != g2.sThumbLY:
            nl1 = setThumbStickDeadzone(g1.sThumbLX, g1.sThumbLY, XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE)
            nl2 = setThumbStickDeadzone(g2.sThumbLX, g2.sThumbLY, XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE)
            if self.onMouse:
                nl1 = self.rapidThumb(*nl1)
            if (nl1 != nl2):
                self.dispatch_event('on_axis', 'LeftThumbStick', nl1)
        if self.onMouse or g1.sThumbRX != g2.sThumbRX or g1.sThumbRY != g2.sThumbRY:
            nr1 = setThumbStickDeadzone(g1.sThumbRX, g1.sThumbRY, XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE)
            nr2 = setThumbStickDeadzone(g2.sThumbRX, g2.sThumbRY, XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE)
            if self.onMouse:
                nr1 = self.rapidThumb(*nr1)
            if (nr1 != nr2):
                self.dispatch_event('on_axis', 'RightThumbStick', nr1)

        if g1.bLeftTrigger != g2.bLeftTrigger:
            nt1, nt2 = setTriggerDeadzone(g1.bLeftTrigger, g2.bLeftTrigger)
            if (nt1 != nt2):
                self.dispatch_event('on_axis', 'LeftTrigger', nt1)
        if g1.bRightTrigger != g2.bRightTrigger:
            nt1, nt2 = setTriggerDeadzone(g1.bRightTrigger, g2.bRightTrigger)
            if (nt1 != nt2):
                self.dispatch_event('on_axis', 'RightTrigger', nt1)

        # on_button
        current = g1.wButtons
        last = g2.wButtons
        for button, (bitmask, kid) in WBUTTONS.items():
            if current & bitmask:
                # don't repeat, if axis moved
                if kid not in self.buttons:
                    self.dispatch_event('on_button', (kid, KBUTTONS[kid]), 1)
                    self.buttons.add(kid)
            elif last & bitmask:
                self.dispatch_event('on_button', (kid, KBUTTONS[kid]), 0)
                #if kid in self.buttons: self.buttons.remove(kid)
                self.buttons.discard(kid)

        # combinations or hotkeys
        for name, k in self.combinations.items():
            if not set(k).difference(self.buttons):
                self.dispatch_event('on_combinations', name)

    # stub methods for event handlers
    def on_state_changed(self, state):
        pass

    def on_axis(self, axis, value):
        pass

    def on_button(self, button, pressed):
        pass

    def on_combinations(self, name):
        pass

    def on_missed_packet(self, number):
        pass


def get_joysticks(combinations={}, onMouse=False):
    joysticks = Joystick.enumerate_devices(combinations, onMouse)
    #device_numbers = list(map(attrgetter('device_number'), joysticks))
    print('Found %i device(s)' % len(joysticks))
    return joysticks

def check_joysticks_count(old_count=0):
    # need a thread or Timer
    names = get_names()
    globals().update({"DEVICE_NAMES": names, "DEVICE_COUNT": len(names)})

    if DEVICE_COUNT > old_count:
        return 1  # new device connected
    elif DEVICE_COUNT < old_count:
        return -1  # device disconnected
    else:
        return 0 # is same
