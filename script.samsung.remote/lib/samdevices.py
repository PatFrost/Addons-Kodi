
import time
import socket
from re import findall
from urllib import urlopen
from StringIO import StringIO
from httplib import HTTPResponse
from datetime import timedelta

DEFAULT_TIMEOUT = socket.getdefaulttimeout()

def timeTook(tc):
    return str(timedelta(0, (time.clock() - tc)))

class SSDPResponse(object):
    class _FakeSocket(StringIO):
        def makefile(self, *args, **kw):
            return self

    def __init__(self, response):
        r = HTTPResponse(self._FakeSocket(response))
        r.begin()
        self.location = r.getheader("location")
        self.usn      = r.getheader("usn")
        self.st       = r.getheader("st")
        self.cache    = r.getheader("cache-control").split("=")[1]
        try: r.close()
        except: pass

    def __repr__(self):
        return "<SSDPResponse({location}, {st}, {usn})>".format(**self.__dict__)

def discover(service, timeout=2, retries=1):
    tc = time.clock()
    group = ("239.255.255.250", 1900)
    message = "\r\n".join([
        'M-SEARCH * HTTP/1.1',
        'HOST: {0}:{1}'.format(*group),
        'MAN: "ssdp:discover"',
        'ST: {0}'.format(service),
        'MX: 3','',''])
    socket.setdefaulttimeout(timeout)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(message, group)
    responses = {}
    while True:
        try:
            response = SSDPResponse(sock.recv(1024))
            responses[response.location] = response
        except socket.timeout:
            break
    try: sock.close()
    except: pass
    socket.setdefaulttimeout(DEFAULT_TIMEOUT)
    print "discover(%r, timeout=%i, retries=%i) took %s" % (service, timeout, retries, timeTook(tc))
    if retries and not responses:
        return discover(service, timeout, retries-1)
    return responses.values()

def getSamDevices():
    tc = time.clock()
    tvips = {}
    ssdpModes = ['urn:samsung.com:device:RemoteControlReceiver:1', 'ssdp:all', 'urn:samsung.com:service:MultiScreenService:1']
    for ssdpMode in ssdpModes:
        if tvips: break
        for device in discover(ssdpMode):
            if "samsung" in device.usn.lower():
                tvip = device.location.split("/")[2].split(":")[0]
                if tvip not in tvips:
                    #print device.location
                    sock = urlopen(device.location)
                    tvxml = sock.read()
                    sock.close()
                    tvips[tvip] = [
                        "".join(findall("<friendlyName>(.*?)</friendlyName>", tvxml)),
                        "".join(findall("<modelName>(.*?)</modelName>", tvxml)),
                        ]
    print "getSamDevices(%r) took %s" % (tvips, timeTook(tc))
    return tvips


def selectDevice():
    import xbmc
    from xbmcgui import Dialog
    from xbmcaddon import Addon
    ADDON = Addon("script.samsung.remote")
    xbmc.executebuiltin('ActivateWindow(busydialog)')
    tv_devices = sorted(getSamDevices().items())
    choices = ["%s (%s) @ %s" % (v[0], v[1], k) for k, v in tv_devices] + ["Manual", "Cancel"]
    xbmc.executebuiltin('Dialog.Close(busydialog,true)')
    selected = Dialog().select("Select your Samsung device", choices)
    device = None
    if selected >= 0 and selected < len(tv_devices):
        # auto and selected
        device = tv_devices[selected]
        ADDON.setSetting("autosam", "$LOCALIZE[13416]")
        ADDON.setSetting("manualsam", "false")
        ADDON.setSetting("tvmodel", device[1][1])
        ADDON.setSetting("tvname", device[1][0])
        ADDON.setSetting("tvip", device[0])

    elif selected == len(tv_devices):
        # manual
        ADDON.setSetting("autosam", "$LOCALIZE[413]")
        ADDON.setSetting("manualsam", "true")
        xbmc.sleep(500)
        xbmc.executebuiltin('Action(Down)')

    #if device:
    #    tvip, name, model = device[0], device[1][0], device[1][1]
    #    Dialog().ok("Samsung device", tvip, name, model)


if __name__ == '__main__':
    selectDevice()
