# -*- coding: utf-8 -*-

# List public names
__all__ = ['get_desktop_res', 'move', 'get_position', 'KodiResolution']

import time
import ctypes
from platform import release


if float(release()) >= 8.1:
    #On Windows 8.1 and/or 10. I am not getting the correct resolution from either ctypes or tk.
    #Other people are having this same problem for ctypes: getsystemmetrics returns wrong screen size
    #To get the correct full resolution of a high DPI monitor on windows 8.1+, one must call SetProcessDPIAware
    ctypes.windll.user32.SetProcessDPIAware()


FindWindow = ctypes.windll.user32.FindWindowW
mouse_event = ctypes.windll.user32.mouse_event
GetCursorPos = ctypes.windll.user32.GetCursorPos
SetCursorPos = ctypes.windll.user32.SetCursorPos
GetClientRect = ctypes.windll.user32.GetClientRect
ClientToScreen = ctypes.windll.user32.ClientToScreen
GetSystemMetrics = ctypes.windll.user32.GetSystemMetrics

MOUSEEVENTF_MOVE = 0x0001     # Movement occurred.
MOUSEEVENTF_ABSOLUTE = 0x8000 # The dx and dy parameters contain normalized absolute coordinates.
ABSOLUTE_MOVE = MOUSEEVENTF_MOVE + MOUSEEVENTF_ABSOLUTE

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long),
                ("y", ctypes.c_long)]

class RECT(ctypes.Structure):
    _fields_ = [('left',   ctypes.c_long),
                ('top',    ctypes.c_long),
                ('right',  ctypes.c_long),
                ('bottom', ctypes.c_long)]


def get_desktop_res():
    return RECT(0, 0, GetSystemMetrics(0), GetSystemMetrics(1))

def get_position():
    point = POINT()
    GetCursorPos(ctypes.byref(point))
    return point.x, point.y

def move(x, y, absolute=False):
    if absolute:
        res = get_desktop_res()
        x *= 65536.0 / res.right #convert to absolute coordinates
        y *= 65536.0 / res.bottom
        mouse_event(ABSOLUTE_MOVE, int(x), int(y), 0, 0)
    else:
        SetCursorPos(int(x), int(y))


class KodiResolution(object):
    def __init__(self):
        self.hwnd = FindWindow(u"Kodi", None) # Window handle
        #print "Kodi position on desktop"
        #print "left={}, top={}, width={}, height={}".format(*self.get_position())

    def get_position(self, fullscreen=False):
        # get_position is REQUIRED
        """Returns tuple of 4 numbers: (x, y)s of top-left and width-height of client"""
        if not self.hwnd:
            return (0, 0, 1, 1)

        desktop_res = get_desktop_res()
        if fullscreen:
            return desktop_res.left, desktop_res.top, desktop_res.right, desktop_res.bottom

        rect1 = RECT()
        rect2 = RECT()
        GetClientRect(self.hwnd, ctypes.pointer(rect1))
        ClientToScreen(self.hwnd, ctypes.pointer(rect2))

        if rect2.left < 0 > rect2.top and rect1.right == rect1.bottom == 0:
            return desktop_res.left, desktop_res.top, desktop_res.right, desktop_res.bottom

        return rect2.left, rect2.top, rect1.right, rect1.bottom



def slide(x, y, absolute=False, duration=0, steps=125):
    # steps = movements per second. default: 125
    if not duration:
        move(x, y, absolute)
    else:
        start_x, start_y = get_position()

        dx = x - start_x
        dy = y - start_y

        duration /= 1000.0

        if dx == dy == 0:
            time.sleep((duration/2.0) or 1)

        else:
            steps = max(1.0, float(int(duration*float(steps))))
            wait = duration/(steps+1.0)
            for i in range(int(steps)+1):
                x = start_x + dx*i/steps
                y = start_y + dy*i/steps
                move(x, y, absolute)
                time.sleep(wait)

if __name__ == '__main__':
    desktop_res = get_desktop_res()
    # print desktop_res.left, desktop_res.top, desktop_res.right, desktop_res.bottom
    # print

    # kodi_window = KodiResolution()
    # print kodi_window.get_position()
    # print

    from datetime import timedelta
    start_x, start_y = get_position()
    #move(0, 0)
    st = time.clock()
    slide(50, 50,    duration=1000, steps=360)
    time.sleep(1)
    slide(1500, 700,    duration=3000, steps=360)
    #slide(1550, 850, duration=1000)
    #slide(50, 850,   duration=1000)
    #slide(1550, 50,  duration=1000)
    print str(timedelta(0, (time.clock() - st), 0))
    print get_position()
