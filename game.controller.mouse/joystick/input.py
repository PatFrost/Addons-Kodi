
import time
import ctypes
from ctypes import byref, c_long, Structure
from platform import release

GetLastError = ctypes.windll.kernel32.GetLastError
WinError = ctypes.WinError

GetSystemMetrics = ctypes.windll.user32.GetSystemMetrics
SetProcessDPIAware = ctypes.windll.user32.SetProcessDPIAware

mouse_event = ctypes.windll.user32.mouse_event
GetCursorPos = ctypes.windll.user32.GetCursorPos
SetCursorPos = ctypes.windll.user32.SetCursorPos

keybd_event = ctypes.windll.user32.keybd_event
GetKeyState = ctypes.windll.user32.GetKeyState

# http://msdn.microsoft.com/en-us/library/windows/desktop/ms646273(v=vs.85).aspx
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_LEFTCLICK = MOUSEEVENTF_LEFTDOWN + MOUSEEVENTF_LEFTUP
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_RIGHTCLICK = MOUSEEVENTF_RIGHTDOWN + MOUSEEVENTF_RIGHTUP
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_MIDDLECLICK = MOUSEEVENTF_MIDDLEDOWN + MOUSEEVENTF_MIDDLEUP
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100
MOUSEEVENTF_XCLICK = MOUSEEVENTF_XDOWN + MOUSEEVENTF_XUP

MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x01000

WHEEL_DELTA = 120

#https://msdn.microsoft.com/en-us/library/windows/desktop/dd375731(v=vs.85).aspx
VK_BACK = 0x08   # BACKSPACE key
VK_RETURN = 0x0D # ENTER key
VK_ESCAPE = 0x1B # ESC key
VK_LWIN = 0x5B   # Left Windows key (Natural keyboard)
VK_APPS = 0x5D   # Applications key (Natural keyboard)

VK_LEFT = 0x25  # LEFT ARROW key
VK_UP = 0x26    # UP ARROW key
VK_RIGHT = 0x27 # RIGHT ARROW key
VK_DOWN = 0x28  # DOWN ARROW key

CHATPAD_X1 = VK_F23 = 0x86
CHATPAD_X2 = VK_F24 = 0x87

VK_MASK = 32768


class POINT(Structure):
    _fields_ = [("x", c_long),
                ("y", c_long)]

if float(release().replace("NT", "7")) >= 8.1:
    #On Windows 8.1 and/or 10. I am not getting the correct resolution from either ctypes or tk.
    #Other people are having this same problem for ctypes: getsystemmetrics returns wrong screen size
    #To get the correct full resolution of a high DPI monitor on windows 8.1+, one must call SetProcessDPIAware
    SetProcessDPIAware()


def get_desktop_res():
    """Returns the width and height of the screen as a two-integer tuple.

    Returns:
      (width, height) tuple of the screen size, in pixels.
    """
    return (GetSystemMetrics(0), GetSystemMetrics(1))


_width, _height = get_desktop_res()
def sendEvent(event, x, y, dwData=0):
    convertedX = 65536 * x // _width + 1
    convertedY = 65536 * y // _height + 1
    mouse_event(event,
                c_long(convertedX),
                c_long(convertedY),
                dwData, 0)

    if GetLastError() != 0:
        raise WinError()

def getPosition():
    """Returns the current xy coordinates of the mouse cursor as a two-integer
    tuple by calling the GetCursorPos() win32 function.

    Returns:
      (x, y) tuple of the current xy coordinates of the mouse cursor.
    """
    cursor = POINT()
    GetCursorPos(byref(cursor))
    return (cursor.x, cursor.y)

def setPosition(x, y):
    SetCursorPos(int(x), int(y))

def pressButton(button, x=0, y=0):
    if button == 'left':
        sendEvent(MOUSEEVENTF_LEFTDOWN, x, y)
    elif button == 'middle':
        sendEvent(MOUSEEVENTF_MIDDLEDOWN, x, y)
    elif button == 'right':
        sendEvent(MOUSEEVENTF_RIGHTDOWN, x, y)
    elif button == 'x':
        sendEvent(MOUSEEVENTF_XDOWN, x, y)

def releaseButton(button, x=0, y=0):
    if button == 'left':
        sendEvent(MOUSEEVENTF_LEFTUP, x, y)
    elif button == 'middle':
        sendEvent(MOUSEEVENTF_MIDDLEUP, x, y)
    elif button == 'right':
        sendEvent(MOUSEEVENTF_RIGHTUP, x, y)
    elif button == 'x':
        sendEvent(MOUSEEVENTF_XUP, x, y)

def clickButton(button, x=0, y=0):
    if button == 'left':
        sendEvent(MOUSEEVENTF_LEFTCLICK, x, y)
    elif button == 'middle':
        sendEvent(MOUSEEVENTF_MIDDLECLICK, x, y)
    elif button == 'right':
        sendEvent(MOUSEEVENTF_RIGHTCLICK, x, y)
    elif button == 'x':
        sendEvent(MOUSEEVENTF_XCLICK, x, y)

def scroll(clicks, x=None, y=None):
    startx, starty = getPosition()
    width, height = get_desktop_res()

    if x is None:
        x = startx
    else:
        x = max(min(int(x), (width-1)), 0)

    if y is None:
        y = starty
    else:
        y = max(min(int(y), (height-1)), 0)

    sendEvent(MOUSEEVENTF_WHEEL, x, y, dwData=int(WHEEL_DELTA*clicks))


def keyDown(key):
    # press key
    keybd_event(key, 0, 1, 0)

def keyUp(key):
    # release key
    keybd_event(key, 0, 2, 0)

def pressKey(key, speed=1):
    # click key
    vk = None
    if key == "left": vk = VK_LEFT
    elif key == "up": vk = VK_UP
    elif key == "right": vk = VK_RIGHT
    elif key == "down": vk = VK_DOWN
    elif key == "back": vk = VK_BACK
    elif key == "enter": vk = VK_RETURN
    elif key == "escape": vk = VK_ESCAPE
    elif key == "apps": vk = VK_APPS
    elif key == "win": vk = VK_LWIN
    if vk is not None:
        keyDown(vk)
        time.sleep(0.05/speed)
        keyUp(vk)

from winkey import VIRTUAL_KEY
HEX = sorted(VIRTUAL_KEY.keys())
def getKey():
    key = None
    while key is None:
        for vk in HEX:
            if GetKeyState(vk) & VK_MASK:
                key = (hex(vk), VIRTUAL_KEY[vk])
                break
        time.sleep(.015)
    return key

# require chatpad for xbox one
def getX1State():
    return (GetKeyState(CHATPAD_X1) & VK_MASK)

def getX2State():
    return (GetKeyState(CHATPAD_X2) & VK_MASK)


def x1_x2_test(event):
    # need a thread or Timer
    while True:
        if getX1State():
            if event(("X1", "pressed")):
                print("stop called")
                break
            time.sleep(.1)
        if getX2State():
            if event(("X2", "pressed")):
                print("stop called")
                break
            time.sleep(.1)
        time.sleep(.015)


if __name__ == '__main__':
    c = 0
    def p(e):
        global c
        if c >= 4:
            return 1
        print(e)
        c += 1
    x1_x2_test(p)

    # pressKey("enter")
    # time.sleep(1)
    # pressKey("up")
    # time.sleep(1)
    # pressKey("up")
    # time.sleep(1)

    # scroll(25)
    # time.sleep(2)
    # scroll(-25)
