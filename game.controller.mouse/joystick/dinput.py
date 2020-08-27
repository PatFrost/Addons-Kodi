
__all__ = ["get_devices"]

from ctypes import oledll, windll, Structure
from ctypes import byref, c_int, c_uint, c_uint16, c_uint32, c_void_p, c_wchar
from ctypes import c_ubyte, c_ulong, c_ushort, POINTER, WINFUNCTYPE, HRESULT

DirectInput8Create = oledll.dinput8.DirectInput8Create
GetModuleHandleW = windll.kernel32.GetModuleHandleW

DIRECTINPUT_VERSION = 0x0800
DIEDFL_ATTACHEDONLY = 0x00000001
DI8DEVCLASS_GAMECTRL = 4
MAX_PATH = 260

LPVOID = c_void_p
WORD = c_uint16
DWORD = c_uint32
LPDWORD = POINTER(DWORD)
BOOL = c_int
WCHAR = c_wchar
UINT = c_uint
HWND = c_uint32
HANDLE = LPVOID
TCHAR = WCHAR * MAX_PATH

class GUID(Structure):
    _fields_ = [('Data1', c_ulong),
                ('Data2', c_ushort),
                ('Data3', c_ushort),
                ('Data4', c_ubyte*8)]

    def __init__(self, l, w1, w2, b1, b2, b3, b4, b5, b6, b7, b8):
        self.Data1 = l
        self.Data2 = w1
        self.Data3 = w2
        self.Data4[:] = (b1, b2, b3, b4, b5, b6, b7, b8)

    def __repr__(self):
        b1, b2, b3, b4, b5, b6, b7, b8 = self.Data4
        return 'GUID(%x, %x, %x, %x, %x, %x, %x, %x, %x, %x, %x)' % (
            self.Data1, self.Data2, self.Data3,
            b1, b2, b3, b4, b5, b6, b7, b8)

LPGUID = POINTER(GUID)
REFIID = POINTER(GUID)

class METHOD(object):
    '''COM method.'''
    def __init__(self, restype, *args):
        self.restype = restype
        self.argtypes = args

    def get_field(self):
        return WINFUNCTYPE(self.restype, *self.argtypes)

class STDMETHOD(METHOD):
    '''COM method with HRESULT return value.'''
    def __init__(self, *args):
        super(STDMETHOD, self).__init__(HRESULT, *args)

class COMMethodInstance(object):
    '''Binds a COM interface method.'''
    def __init__(self, name, i, method):
        self.name = name
        self.i = i
        self.method = method

    def __get__(self, obj, tp):
        if obj is not None:
            return lambda *args: \
                self.method.get_field()(self.i, self.name)(obj, *args)
        raise AttributeError()

class COMInterface(Structure):
    '''Dummy struct to serve as the type of all COM pointers.'''
    _fields_ = [('lpVtbl', c_void_p)]

class InterfaceMetaclass(type(POINTER(COMInterface))):
    '''Creates COM interface pointers.'''
    def __new__(cls, name, bases, dct):
        methods = []
        for base in bases[::-1]:
            methods.extend(base.__dict__.get('_methods_', ()))
        methods.extend(dct.get('_methods_', ()))

        for i, (n, method) in enumerate(methods):
            dct[n] = COMMethodInstance(n, i, method)

        dct['_type_'] = COMInterface

        return super(InterfaceMetaclass, cls).__new__(cls, name, bases, dct)

class Interface(POINTER(COMInterface)):
    '''Base COM interface pointer.'''
    __metaclass__ = InterfaceMetaclass

class IUnknown(Interface):
    _methods_ = [('QueryInterface', STDMETHOD(REFIID, c_void_p)),
                 ('AddRef', METHOD(c_int)),
                 ('Release', METHOD(c_int))]



class DIDEVICEINSTANCE(Structure):
    _fields_ = (('dwSize', DWORD),
                ('guidInstance', GUID),
                ('guidProduct', GUID),
                ('dwDevType', DWORD),
                ('tszInstanceName', TCHAR),
                ('tszProductName', TCHAR),
                ('guidFFDriver', GUID),
                ('wUsagePage', WORD),
                ('wUsage', WORD))
LPDIDEVICEINSTANCE = POINTER(DIDEVICEINSTANCE)
LPDIENUMDEVICESCALLBACK = WINFUNCTYPE(BOOL, LPDIDEVICEINSTANCE, LPVOID)

class DIDEVICEOBJECTINSTANCE(Structure):
    _fields_ = (('dwSize', DWORD),
                ('guidType', GUID),
                ('dwOfs', DWORD),
                ('dwType', DWORD),
                ('dwFlags', DWORD),
                ('tszName', TCHAR),
                ('dwFFMaxForce', DWORD),
                ('dwFFForceResolution', DWORD),
                ('wCollectionNumber', WORD),
                ('wDesignatorIndex', WORD),
                ('wUsagePage', WORD),
                ('wUsage', WORD),
                ('dwDimension', DWORD),
                ('wExponent', WORD),
                ('wReportId', WORD))
LPDIDEVICEOBJECTINSTANCE = POINTER(DIDEVICEOBJECTINSTANCE)
LPDIENUMDEVICEOBJECTSCALLBACK = WINFUNCTYPE(BOOL, LPDIDEVICEOBJECTINSTANCE, LPVOID)

class DIDEVICEOBJECTDATA(Structure):
    _fields_ = (('dwOfs', DWORD),
                ('dwData', DWORD),
                ('dwTimeStamp', DWORD),
                ('dwSequence', DWORD),
                ('uAppData', POINTER(UINT)))
LPDIDEVICEOBJECTDATA = POINTER(DIDEVICEOBJECTDATA)

class DIOBJECTDATAFORMAT(Structure):
    _fields_ = (('pguid', POINTER(GUID)),
                ('dwOfs', DWORD),
                ('dwType', DWORD),
                ('dwFlags', DWORD))
    __slots__ = [n for n, t in _fields_]
LPDIOBJECTDATAFORMAT = POINTER(DIOBJECTDATAFORMAT)

class DIDATAFORMAT(Structure):
    _fields_ = (('dwSize', DWORD),
                ('dwObjSize', DWORD),
                ('dwFlags', DWORD),
                ('dwDataSize', DWORD),
                ('dwNumObjs', DWORD),
                ('rgodf', LPDIOBJECTDATAFORMAT))
    __slots__ = [n for n, t in _fields_]
LPDIDATAFORMAT = POINTER(DIDATAFORMAT)

class DIPROPHEADER(Structure):
    _fields_ = (('dwSize', DWORD),
                ('dwHeaderSize', DWORD),
                ('dwObj', DWORD),
                ('dwHow', DWORD))
LPDIPROPHEADER = POINTER(DIPROPHEADER)

class IDirectInputDevice8(IUnknown):
    _methods_ = [
        ('GetCapabilities', STDMETHOD()),
        ('EnumObjects', STDMETHOD(LPDIENUMDEVICEOBJECTSCALLBACK, LPVOID, DWORD)),
        ('GetProperty', STDMETHOD()),
        ('SetProperty', STDMETHOD(LPVOID, LPDIPROPHEADER)),
        ('Acquire', STDMETHOD()),
        ('Unacquire', STDMETHOD()),
        ('GetDeviceState', STDMETHOD()),
        ('GetDeviceData', STDMETHOD(DWORD, LPDIDEVICEOBJECTDATA, LPDWORD, DWORD)),
        ('SetDataFormat', STDMETHOD(LPDIDATAFORMAT)),
        ('SetEventNotification', STDMETHOD(HANDLE)),
        ('SetCooperativeLevel', STDMETHOD(HWND, DWORD)),
        ('GetObjectInfo', STDMETHOD()),
        ('GetDeviceInfo', STDMETHOD()),
        ('RunControlPanel', STDMETHOD()),
        ('Initialize', STDMETHOD()),
        ('CreateEffect', STDMETHOD()),
        ('EnumEffects', STDMETHOD()),
        ('GetEffectInfo', STDMETHOD()),
        ('GetForceFeedbackState', STDMETHOD()),
        ('SendForceFeedbackCommand', STDMETHOD()),
        ('EnumCreatedEffectObjects', STDMETHOD()),
        ('Escape', STDMETHOD()),
        ('Poll', STDMETHOD()),
        ('SendDeviceData', STDMETHOD()),
        ('EnumEffectsInFile', STDMETHOD()),
        ('WriteEffectToFile', STDMETHOD()),
        ('BuildActionMap', STDMETHOD()),
        ('SetActionMap', STDMETHOD()),
        ('GetImageInfo', STDMETHOD())]

class IDirectInput8(IUnknown):
    _methods_ = [
        ('CreateDevice', STDMETHOD(POINTER(GUID), POINTER(IDirectInputDevice8), c_void_p)),
        ('EnumDevices', STDMETHOD(DWORD, LPDIENUMDEVICESCALLBACK, LPVOID, DWORD)),
        ('GetDeviceStatus', STDMETHOD()),
        ('RunControlPanel', STDMETHOD()),
        ('Initialize', STDMETHOD()),
        ('FindDevice', STDMETHOD()),
        ('EnumDevicesBySemantics', STDMETHOD()),
        ('ConfigureDevices',  STDMETHOD())]

IID_IDirectInput8W = GUID(0xBF798031, 0x483A, 0x4DA2,
                          0xAA, 0x99, 0x5D, 0x64,
                          0xED, 0x36, 0x97, 0x00)

DirectInput8Create.argtypes = \
    (c_void_p, DWORD, LPGUID, c_void_p, c_void_p)


class DirectInputDevice(object):
    def __init__(self, device):
        self.device = device
        self.name = self.device.tszInstanceName
        self.name2 = self.device.tszProductName
        self.manufacturer = "Microsoft" if "Xbox" in self.name else ""

        for f, v in DIDEVICEINSTANCE._fields_:
            print(f, getattr(self.device, f))
        print


idinput = IDirectInput8()
def set_idinput():
    DirectInput8Create(GetModuleHandleW(None),
                       DIRECTINPUT_VERSION,
                       IID_IDirectInput8W,
                       byref(idinput),
                       None)
set_idinput()
DEVICE = IDirectInputDevice8()
def get_devices():
    devices = []
    def _device_enum(device_instance, arg):
        #DEVICE = IDirectInputDevice8()
        idinput.CreateDevice(device_instance.contents.guidInstance,
                             byref(DEVICE),
                             None)
        devices.append(DirectInputDevice(device_instance.contents))
        return 1

    idinput.EnumDevices(DI8DEVCLASS_GAMECTRL,
                        LPDIENUMDEVICESCALLBACK(_device_enum),
                        None,
                        DIEDFL_ATTACHEDONLY)
    return devices

if __name__ == "__main__":
    import time
    from datetime import timedelta
    st = time.clock()
    names = [d.name for d in get_devices()]#*4
    print str(timedelta(0, (time.clock() - st), 0))
    print names
    