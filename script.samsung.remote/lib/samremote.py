
import re
import uuid
import socket
from httplib import HTTP
from base64 import b64encode
from traceback import print_exc
from time import sleep as wait

from keymaps import KEY_CODES


# constants
try:
    from xbmcaddon import Addon
    SETTING = Addon("script.samsung.remote").getSetting
    TV_IP   = SETTING("tvip")
    TV_PORT = int(SETTING("tvport"))
    TV_APP  = "iphone.%s.iapp.samsung" % SETTING("tvmodel")
except:
    TV_IP   = "192.168.0.114"                                  # IP Address of TV
    TV_PORT = 55000                                            # Port Address of TV (default: 55000)
    TV_APP  = "iphone.UN40F5500.iapp.samsung"                  # Might need changing to match your TV type

MY_APP  = "iphone.kodi.iapp.samsung"                           # What the iPhone app reports
REMOTE  = "Kodi Remote"                                        # What gets reported when it asks for permission/also shows in General->Wireless Remote Control menu
MY_IP   = socket.gethostbyname(socket.gethostname())           # Doesn't seem to be really used
MY_MAC  = ":".join(re.findall("..", "%012X" % uuid.getnode())) # Used for the access control/validation, but not after that AFAIK

# encoded constants
B64_SRC    = b64encode(MY_IP)
B64_MAC    = b64encode(MY_MAC)
B64_REMOTE = b64encode(REMOTE)

messagepart1  = chr(0x64) + chr(0x00)
messagepart1 += chr(len(B64_SRC))    + chr(0x00) + B64_SRC
messagepart1 += chr(len(B64_MAC))    + chr(0x00) + B64_MAC
messagepart1 += chr(len(B64_REMOTE)) + chr(0x00) + B64_REMOTE
messagepart2  = chr(0xc8) + chr(0x00)

part1 = chr(0x00) + chr(len(MY_APP)) + chr(0x00) + MY_APP + chr(len(messagepart1)) + chr(0x00) + messagepart1
part2 = chr(0x00) + chr(len(MY_APP)) + chr(0x00) + MY_APP + chr(len(messagepart2)) + chr(0x00) + messagepart2


DEFAULT_TIMEOUT = socket.getdefaulttimeout()

def setVolume(volume):
    volume = int(volume)
    if volume > 100: volume = 100
    elif volume < 0: volume = 0
    
    soap = '<?xml version="1.0" encoding="utf-8"?><s:Envelope xmlns:ns0="urn:schemas-upnp-org:service:RenderingControl:1" ' \
           's:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">' \
           '<s:Body><ns0:SetVolume><InstanceID>0</InstanceID><Channel>Master</Channel>' \
           '<DesiredVolume>%i</DesiredVolume>' \
           '</ns0:SetVolume></s:Body></s:Envelope>' % volume

    conn = HTTP(TV_IP, 7676)
    conn.putrequest('POST', '/smp_16_')
    conn.putheader('Host', TV_IP)
    conn.putheader('Content-Length', len(soap))
    conn.putheader('User-Agent', 'Twisted PageGetter')
    conn.putheader('SOAPACTION', '"urn:schemas-upnp-org:service:RenderingControl:1#SetVolume"')
    conn.putheader('content-type', 'text/xml ;charset="utf-8"')
    conn.putheader('connection', 'close')
    conn.endheaders()
    conn.send(soap)
    statuscode, statusmessage, header = conn.getreply()
    response = conn.getfile().read()
    conn.close()
    #print statuscode, statusmessage, header
    # print response
    print "samsung.remote.setVolume(%r)" % volume

class SamRemote:
    def __init__(self):
        self.sock = None
        try:
            socket.setdefaulttimeout(3)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #self.sock.settimeout(3)
            # connect to tv
            self.sock.connect((TV_IP, TV_PORT))
            # send part1 and part2
            for part in [part1, part2]:
                self.sock.send(part)
                wait(.25)
        except:
            print_exc()
            self.close()

    def close(self):
        socket.setdefaulttimeout(DEFAULT_TIMEOUT)
        try:
            self.sock.close()
            wait(.1)
        except:
            print_exc()
        self.sock = None

    def sendKey(self, key, ts=None):
        if not self.sock: return
        print "samsung.remote.sendKey(%s,%r)" % (key, ts)
        try:
            messagepart3 = chr(0x00) + chr(0x00) + chr(0x00) + chr(len(b64encode(key))) + chr(0x00) + b64encode(key)
            part3 = chr(0x00) + chr(len(TV_APP)) + chr(0x00) + TV_APP + chr(len(messagepart3)) + chr(0x00) + messagepart3
            self.sock.send(part3)
        except:
            print_exc()
        if ts is not None:
            wait(ts)

    def sendText(self, txt, ts=None):
        if not self.sock: return
        print "samsung.remote.sendText(%s,%r)" % (txt, ts)
        try:
            messagepart3 = chr(0x01) + chr(0x00) + chr(len(b64encode(txt))) + chr(0x00) + b64encode(txt)
            part3 = chr(0x01) + chr(len(MY_APP)) + chr(0x00) + MY_APP + chr(len(messagepart3)) + chr(0x00) + messagepart3
            self.sock.send(part3)
        except:
            print_exc()
        if ts is not None:
            wait(ts)

if __name__ == "__main__":
    sr = SamRemote()

    #sr.sendText("google.ca",5)
    #sr.sendKey("KEY_CAPTION",1)

    # KEY_WEBBROWSER = [("KEY_CONTENTS",5)] + [("KEY_LEFT",1.25)]*5 + [("KEY_ENTER",5)] + [("KEY_EXIT", None)]
    # for k,s in KEY_WEBBROWSER:
        # sr.sendKey(k, s)

    # go to ztele hd
    # sr.sendKey("KEY_EXT20",.5)
    sr.sendKey("KEY_6",.5)
    sr.sendKey("KEY_4",.5)
    sr.sendKey("KEY_3",.5)
    # sr.sendKey("KEY_ENTER")

    sr.close()
    #setVolume(10)
