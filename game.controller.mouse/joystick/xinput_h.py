
import platform
from ctypes import windll, Structure, POINTER
from ctypes import c_ubyte, byref, pointer, sizeof
from ctypes.wintypes import DWORD, SHORT, UINT, WCHAR, WORD, LPVOID


#xinput = windll.xinput9_1_0
xinput = windll.xinput1_3
XInputGetState = xinput.XInputGetState
XInputSetState = xinput.XInputSetState

# XInput 1.3 and older functions
XInputEnable = xinput.XInputEnable
XInputGetBatInfo = xinput.XInputGetBatteryInformation
XInputGetKeystroke = xinput.XInputGetKeystroke
XInputGetCapabilities = xinput.XInputGetCapabilities
XInputGetDSoundAudioDeviceGuids = xinput.XInputGetDSoundAudioDeviceGuids

# XInput 1.3 undocumented functions
XINPUT1_3 = windll.LoadLibrary("xinput1_3")
XInputGetStateEx = XINPUT1_3[100]
XInputGetStateEx.argtypes = [DWORD, LPVOID]
XInputGetStateEx.restype = DWORD
XInputWaitForGuideButton = XINPUT1_3[101]
XInputWaitForGuideButton.argtypes = [DWORD, DWORD, LPVOID]
XInputWaitForGuideButton.restype = DWORD
XInputCancelGuideButtonWait = XINPUT1_3[102]
XInputCancelGuideButtonWait.argtypes = [DWORD]
XInputCancelGuideButtonWait.restype = DWORD
XInputPowerOffController = XINPUT1_3[103]
XInputPowerOffController.argtypes = [DWORD]
XInputPowerOffController.restype = DWORD

# XInput 1.4 functions
# XInputGetAudioDeviceIds = windll.xinput1_4.XInputGetAudioDeviceIds

# XInput 1.4 undocumented functions
# XINPUT1_4 = windll.LoadLibrary("xinput1_4")
# XInputGetBaseBusInformation = XINPUT1_4[104]
# XInputGetBaseBusInformation.argtypes = [DWORD, LPVOID]
# XInputGetBaseBusInformation.restype = DWORD
# XInputGetCapabilitiesEx = XINPUT1_4[108]
# XInputGetCapabilitiesEx.argtypes = [DWORD, DWORD, DWORD, LPVOID]
# XInputGetCapabilitiesEx.restype = DWORD

# Version 9_1_0 has no extra exports


ERROR_DEVICE_NOT_CONNECTED = 1167 # The device is not connected.
ERROR_SUCCESS = 0 # The operation completed successfully.
ERROR_EMPTY = 4306 # no new keys have been pressed (XInputGetKeystroke)

XUSER_INDEX_ANY = 0x000000FF # (XInputGetKeystroke)
MAX_DEVICES = 4

# Codes returned for the gamepad keystroke
VK_PAD_A = 0x5800
VK_PAD_B = 0x5801
VK_PAD_X = 0x5802
VK_PAD_Y = 0x5803
VK_PAD_RSHOULDER = 0x5804
VK_PAD_LSHOULDER = 0x5805
VK_PAD_LTRIGGER = 0x5806
VK_PAD_RTRIGGER  =  0x5807

VK_PAD_DPAD_UP = 0x5810
VK_PAD_DPAD_DOWN = 0x5811
VK_PAD_DPAD_LEFT = 0x5812
VK_PAD_DPAD_RIGHT = 0x5813
VK_PAD_START = 0x5814
VK_PAD_BACK = 0x5815
VK_PAD_LTHUMB_PRESS = 0x5816
VK_PAD_RTHUMB_PRESS = 0x5817

VK_PAD_LTHUMB_UP = 0x5820
VK_PAD_LTHUMB_DOWN = 0x5821
VK_PAD_LTHUMB_RIGHT = 0x5822
VK_PAD_LTHUMB_LEFT = 0x5823
VK_PAD_LTHUMB_UPLEFT = 0x5824
VK_PAD_LTHUMB_UPRIGHT = 0x5825
VK_PAD_LTHUMB_DOWNRIGHT = 0x5826
VK_PAD_LTHUMB_DOWNLEFT = 0x5827

VK_PAD_RTHUMB_UP = 0x5830
VK_PAD_RTHUMB_DOWN = 0x5831
VK_PAD_RTHUMB_RIGHT = 0x5832
VK_PAD_RTHUMB_LEFT = 0x5833
VK_PAD_RTHUMB_UPLEFT = 0x5834
VK_PAD_RTHUMB_UPRIGHT = 0x5835
VK_PAD_RTHUMB_DOWNRIGHT = 0x5836
VK_PAD_RTHUMB_DOWNLEFT = 0x5837

# Flags used in XINPUT_KEYSTROKE
XINPUT_KEYSTROKE_KEYDOWN = 0x0001 # The key was pressed. 
XINPUT_KEYSTROKE_KEYUP  = 0x0002  # The key was released. 
XINPUT_KEYSTROKE_REPEAT = 0x0004  # A repeat of a held key. 


# wButtons
#    "Bitmask of the device digital buttons, as follows.
# A set bit indicates that the corresponding button is pressed.
# And last int = id used by kodi
WBUTTONS = {"XINPUT_GAMEPAD_DPAD_UP": (0x0001, 10),
            "XINPUT_GAMEPAD_DPAD_DOWN": (0x0002, 12),
            "XINPUT_GAMEPAD_DPAD_LEFT": (0x0004, 13),
            "XINPUT_GAMEPAD_DPAD_RIGHT": (0x0008, 11),
            "XINPUT_GAMEPAD_START": (0x0010, 7),
            "XINPUT_GAMEPAD_BACK": (0x0020, 6),
            "XINPUT_GAMEPAD_LEFT_THUMB": (0x0040, 8),
            "XINPUT_GAMEPAD_RIGHT_THUMB": (0x0080, 9),
            "XINPUT_GAMEPAD_LEFT_SHOULDER": (0x0100, 4),
            "XINPUT_GAMEPAD_RIGHT_SHOULDER": (0x0200, 5),
            "XINPUT_GAMEPAD_GUIDE": (0x0400, 14), # Undocumented
            "XINPUT_GAMEPAD_A": (0x1000, 0),
            "XINPUT_GAMEPAD_B": (0x2000, 1),
            "XINPUT_GAMEPAD_X": (0x4000, 2),
            "XINPUT_GAMEPAD_Y": (0x8000, 3)}

# kodi buttons map: id, name, msgctxt->(strings.po) and kj->(key.h)
# https://github.com/xbmc/xbmc/blob/master/xbmc/input/Key.h#L78
KBUTTONS = {0:  {"kj": 284, "msgctxt": 30001, "name": "a"},
            1:  {"kj": 285, "msgctxt": 30002, "name": "b"},
            2:  {"kj": 286, "msgctxt": 30003, "name": "x"},
            3:  {"kj": 287, "msgctxt": 30004, "name": "y"},
            4:  {"kj": 288, "msgctxt": 30014, "name": "leftbumper"},
            5:  {"kj": 289, "msgctxt": 30015, "name": "rightbumper"},
            6:  {"kj": 303, "msgctxt": 30006, "name": "back"},
            7:  {"kj": 302, "msgctxt": 30005, "name": "start"},
            8:  {"kj": 292, "msgctxt": 30008, "name": "leftthumb"},
            9:  {"kj": 293, "msgctxt": 30009, "name": "rightthumb"},
            10: {"kj": 298, "msgctxt": 30010, "name": "up"},
            11: {"kj": 301, "msgctxt": 30012, "name": "right"},
            12: {"kj": 299, "msgctxt": 30011, "name": "down"},
            13: {"kj": 300, "msgctxt": 30013, "name": "left"},
            14: {"kj": 308, "msgctxt": 30007, "name": "guide"},

            15: {"kj": 290, "msgctxt": 30016, "name": "lefttrigger"},
            16: {"kj": 291, "msgctxt": 30017, "name": "righttrigger"},
            17: {"kj": 305, "msgctxt": 30018, "name": "leftthumbdown"},
            18: {"kj": 306, "msgctxt": 30019, "name": "leftthumbleft"},
            19: {"kj": 307, "msgctxt": 30020, "name": "leftthumbright"},
            20: {"kj": 304, "msgctxt": 30021, "name": "leftthumbup"},
            21: {"kj": 295, "msgctxt": 30022, "name": "rightthumbdown"},
            22: {"kj": 296, "msgctxt": 30023, "name": "rightthumbleft"},
            23: {"kj": 297, "msgctxt": 30024, "name": "rightthumbright"},
            24: {"kj": 294, "msgctxt": 30025, "name": "rightthumbup"},
            25: {"kj": 0x1, "msgctxt": 30028, "name": "x1"}, # chatpad
            26: {"kj": 0x2, "msgctxt": 30027, "name": "x2"}, # chatpad
            }

# Gamepad Dead Zone
XINPUT_GAMEPAD_LEFT_THUMB_DEADZONE = 7849
XINPUT_GAMEPAD_RIGHT_THUMB_DEADZONE = 8689
XINPUT_GAMEPAD_TRIGGER_THRESHOLD = 30
XBOX_ONE_TRIGGER_MAX = 1023 # not used
XBOX_ONE_TRIGGER_DEADZONE = 120 # not used

# https://msdn.microsoft.com/en-us/library/windows/desktop/microsoft.directx_sdk.reference.xinput_capabilities(v=vs.85).aspx
XINPUT_OTHER_GAMEPAD = 0x0
XINPUT_DEVTYPE_GAMEPAD = 0x01

XINPUT_DEVSUBTYPE_GAMEPAD = 0x01
XINPUT_DEVSUBTYPE_UNKNOWN = 0x00
XINPUT_DEVSUBTYPE_WHEEL = 0x02
XINPUT_DEVSUBTYPE_ARCADE_STICK = 0x03
XINPUT_DEVSUBTYPE_FLIGHT_STICK = 0x04
XINPUT_DEVSUBTYPE_DANCE_PAD = 0x05
XINPUT_DEVSUBTYPE_GUITAR = 0x06
XINPUT_DEVSUBTYPE_GUITAR_ALTERNATE = 0x07
XINPUT_DEVSUBTYPE_DRUM_KIT = 0x08
XINPUT_DEVSUBTYPE_GUITAR_BASS = 0x0B
XINPUT_DEVSUBTYPE_ARCADE_PAD = 0x13

XINPUT_CAPS_VOICE_SUPPORTED = 0x0004
XINPUT_CAPS_FFB_SUPPORTED = 0x0001
XINPUT_CAPS_WIRELESS = 0x0002
XINPUT_CAPS_PMD_SUPPORTED = 0x0008
XINPUT_CAPS_NO_NAVIGATION = 0x0010

XINPUT_FLAG_GAMEPAD = 0x00000001
XINPUT_FLAG_KEYBOARD = 0x00000002

# Devices that support batteries
BATTERY_DEVTYPE_GAMEPAD = 0x00
BATTERY_DEVTYPE_HEADSET = 0x01

# The type of battery.
# BatteryType will be one of the following values.
BATTERY_TYPE_DISCONNECTED = 0x00 # The device is not connected.
BATTERY_TYPE_WIRED = 0x01        # The device is a wired device and does not
BATTERY_TYPE_ALKALINE = 0x02     # The device has an alkaline battery.
BATTERY_TYPE_NIMH = 0x03         # The device has a nickel metal hydride battery.
BATTERY_TYPE_UNKNOWN = 0xFF      # The device has an unknown battery type.

# The charge state of the battery.
# This value is only valid for wireless devices with a known battery type.
# BatteryLevel will be one of the following values.
BATTERY_LEVEL_EMPTY = 0x00
BATTERY_LEVEL_LOW = 0x01
BATTERY_LEVEL_MEDIUM = 0x02
BATTERY_LEVEL_FULL = 0x03

# http://msdn.microsoft.com/en-gb/library/windows/desktop/ee417001%28v=vs.85%29.aspx
class XINPUT_GAMEPAD(Structure):
    _fields_ = [('wButtons', WORD),
                ('bLeftTrigger', c_ubyte),
                ('bRightTrigger', c_ubyte),
                ('sThumbLX', SHORT),
                ('sThumbLY', SHORT),
                ('sThumbRX', SHORT),
                ('sThumbRY', SHORT)]
# used on function dispatch_axis_events (outdated)
AXIS_FIELDS = [(a, sizeof(t)) for a, t in XINPUT_GAMEPAD._fields_[1:]]

class XINPUT_STATE(Structure):
    _fields_ = [('dwPacketNumber', DWORD),
                ('Gamepad', XINPUT_GAMEPAD)]

# Speed of the motors. Valid values are in the range 0 to 65,535.
# Zero signifies no motor use 65,535 signifies 100 percent motor use.
class XINPUT_VIBRATION(Structure):
    _fields_ = [("wLeftMotorSpeed", WORD),
                ("wRightMotorSpeed", WORD)]

# Set up function argument types and return type
XInputSetState.argtypes = [UINT, POINTER(XINPUT_VIBRATION)]
XInputSetState.restype = UINT

class XINPUT_CAPABILITIES(Structure):
    _fields_ = [('Type', c_ubyte),
                ('SubType', c_ubyte),
                ('Flags', WORD),
                ('Gamepad', XINPUT_GAMEPAD),
                ('Vibration', XINPUT_VIBRATION)]

# Windows 8+ (XInput 1.4), DirectX SDK (XInput 1.3)
class XINPUT_BATTERY_INFORMATION(Structure):
    _fields_ = [('BatteryType', c_ubyte),
                ('BatteryLevel', c_ubyte)]

# Remarks
# Wireless controllers are not considered active upon system
# startup, and calls to any of the XInput functions before a
# wireless controller is made active return ERROR_DEVICE_NOT_CONNECTED.
# Game titles must examine the return code and be prepared to handle
# this condition. Wired controllers are automatically activated when
# they are inserted. Wireless controllers are activated when the user
# presses the START or Xbox Guide button to power on the controller.
class XINPUT_KEYSTROKE(Structure):
    _fields_ = [('VirtualKey', WORD),
                ('Unicode', WCHAR),
                ('Flags', WORD),
                ('UserIndex', c_ubyte),
                ('HidCode', c_ubyte)]

# https://msdn.microsoft.com/en-us/library/windows/desktop/aa373931(v=vs.85).aspx
class GUID(Structure):
    _fields_ = [("Data1", DWORD),
                ("Data2", WORD),
                ("Data3", WORD),
                ("Data4", c_ubyte*8)]
