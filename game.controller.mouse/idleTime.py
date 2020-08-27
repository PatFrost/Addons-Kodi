
import time
from ctypes import Structure, windll, c_uint, sizeof, byref

GetTickCount = windll.kernel32.GetTickCount
GetLastInputInfo = windll.user32.GetLastInputInfo

class LASTINPUTINFO(Structure):
    _fields_ = [('cbSize', c_uint),
                ('dwTime', c_uint)]
lastInputInfo = LASTINPUTINFO()
lastInputInfo.cbSize = sizeof(lastInputInfo)

def get_idle_duration():
    GetLastInputInfo(byref(lastInputInfo)) 
    millis = GetTickCount() - lastInputInfo.dwTime
    return millis / 1000.0


min = 60*.25
while True:
    d = get_idle_duration()
    print d, lastInputInfo.cbSize
    if d >= min:
        windll.user32.mouse_event(1, 1, 1, 0, 0)
        print "stop", d
        break
    time.sleep(.1)
