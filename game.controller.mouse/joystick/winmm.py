
from _winreg import OpenKey, QueryValueEx, HKEY_CURRENT_USER
from ctypes import windll, pointer, sizeof, Structure
from ctypes.wintypes import WORD, UINT, DWORD, WCHAR as TCHAR

# http://msdn.microsoft.com/en-us/library/windows/desktop/dd757116(v=vs.85).aspx

joyGetDevCaps = windll.winmm.joyGetDevCapsW
# joyGetNumDevs = windll.winmm.joyGetNumDevs
# joyGetPos = windll.winmm.joyGetPos
# joyGetPosEx = windll.winmm.joyGetPosEx


JOYERR_NOERROR = 0
MAXPNAMELEN = 32
MAX_JOYSTICKOEMVXDNAME = 260


class JOYCAPS(Structure):
    _fields_ = [('wMid', WORD),
                ('wPid', WORD),
                ('szPname', TCHAR * MAXPNAMELEN),
                ('wXmin', UINT),
                ('wXmax', UINT),
                ('wYmin', UINT),
                ('wYmax', UINT),
                ('wZmin', UINT),
                ('wZmax', UINT),
                ('wNumButtons', UINT),
                ('wPeriodMin', UINT),
                ('wPeriodMax', UINT),
                ('wRmin', UINT),
                ('wRmax', UINT),
                ('wUmin', UINT),
                ('wUmax', UINT),
                ('wVmin', UINT),
                ('wVmax', UINT),
                ('wCaps', UINT),
                ('wMaxAxes', UINT),
                ('wNumAxes', UINT),
                ('wMaxButtons', UINT),
                ('szRegKey', TCHAR * MAXPNAMELEN),
                ('szOEMVxD', TCHAR * MAX_JOYSTICKOEMVXDNAME)]
CBJCJOYCAPS = sizeof(JOYCAPS)

C = "System\\CurrentControlSet\\Control\\Media"
MR = C + "Resources\\Joystick\\%s\\CurrentJoystickSettings" # % 'DINPUT.DLL'
MP = C + "Properties\\PrivateProperties\\Joystick\\OEM\\%s"


def getJoyNames(num_devs=15):
    joy_names = {}
    for joyId in range(num_devs):
        # Get device capabilities.
        caps = JOYCAPS()
        if joyGetDevCaps(joyId, pointer(caps), CBJCJOYCAPS) != JOYERR_NOERROR:
            # not connected...
            continue

        for f, v in JOYCAPS._fields_:
            print(f, getattr(caps, f))

        # set temp name
        joy_names[joyId] = "Joystick %i" % (joyId + 1)

        key = None
        key2 = None
        if caps.szRegKey:
            # Fetch the name from registry.
            try:
                key = OpenKey(HKEY_CURRENT_USER, MR % caps.szRegKey)
                if key:
                    oem = QueryValueEx(key, "Joystick%iOEMName" % (joyId + 1))
                    print oem
                    if oem:
                        key2 = OpenKey(HKEY_CURRENT_USER, MP % (oem[0]))
                if key2:
                    oem = QueryValueEx(key2, "OEMName")
                    print oem
                    joy_names[joyId] = oem[0]
            except: # WindowsError:
                pass
        if hasattr(key, "Close"):
            key.Close()
        if hasattr(key2, "Close"):
            key2.Close()
        print

    return joy_names

if __name__ == "__main__":
    import time
    from datetime import timedelta
    st = time.clock()
    names = getJoyNames()
    print str(timedelta(0, (time.clock() - st), 0))
    print names
