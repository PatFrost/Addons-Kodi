
import xbmc
import xbmcgui
from xbmcaddon import Addon

ADDON      = Addon("script.samsung.remote")
ADDON_NAME = ADDON.getAddonInfo( "name" )

def getSam():
    TV_MODEL = ADDON.getSetting("tvmodel")
    TV_NAME  = ADDON.getSetting("tvname")
    TV_IP    = ADDON.getSetting("tvip")

    DEVICES = DEVICE = None
    if TV_IP and ADDON.getSetting("manualsam") == "true":
        DEVICE = {TV_IP: [TV_NAME, TV_MODEL]}
        
    elif TV_IP:
        from lib.samdevices import getSamDevices
        DEVICES = getSamDevices()
        DEVICE  = DEVICES.get(TV_IP)
        DEVICES = sorted(DEVICES.items())

    if not DEVICE:
        # notify user for device is off or ip changed!
        l2 = "" if not DEVICES else "This device is auto detected!"
        l3 = "" if not DEVICES else ["%s (%s) @ %s" % (v[0], v[1], k) for k, v in DEVICES][0]
        if not xbmcgui.Dialog().yesno("Samsung Remote - Kodi Events", "Sam IP '%s' changed or your device is off!" % TV_IP, l2, l3, "Open Setting", TV_IP if TV_IP else "Pass"):
            ADDON.openSettings()
            xbmc.sleep(1000)
            while xbmc.getCondVisibility("Window.IsVisible(addonsettings)"):
                xbmc.sleep(1000)
            TV_IP = ADDON.getSetting("tvip")
            DEVICES = DEVICE = None
            if TV_IP and ADDON.getSetting("manualsam") == "true":
                DEVICE = {TV_IP: [TV_NAME, TV_MODEL]}
            elif TV_IP:
                from lib.samdevices import getSamDevices
                DEVICES = getSamDevices()
                DEVICE  = DEVICES.get(TV_IP)
                DEVICES = sorted(DEVICES.items())
        elif TV_IP:
            DEVICE = {TV_IP: [TV_NAME, TV_MODEL]}

    import default
    from default import parseSendKeys, sendKeys
    
    return parseSendKeys, sendKeys, DEVICE

SOURCES = {
    'HDMI 1': 'KEY_EXT20',
    'HDMI 2': 'KEY_AUTO_ARC_PIP_WIDE',
    'HDMI 3': 'KEY_AUTO_ARC_PIP_RIGHT_BOTTOM',
    'HDMI (Switch HDMI Input)': 'KEY_HDMI',
    'Component 1': 'KEY_COMPONENT1',
    'Av 1': 'KEY_AV1',
    'TV': 'KEY_TV',
    }

class service:
    def __init__(self):
        self.parseSendKeys, self.sendKeys, self.DEVICE = getSam()
        self.onKodiStartup()
        self.Player = kodiPlayer(main=self)

        while not xbmc.abortRequested:
            xbmc.sleep(1000)
            if xbmc.getCondVisibility("Window.IsVisible(addonsettings) + SubString(Control.GetLabel(20),%s)" % ADDON_NAME):
                # Fake on settings changed
                while xbmc.getCondVisibility("Window.IsVisible(addonsettings)"):
                    xbmc.sleep(1000)
                self.parseSendKeys, self.sendKeys, self.DEVICE = getSam()

        del self.Player
        self.onKodiStopped()

    def onKodiStartup(self):
        if not self.DEVICE: return
        if ADDON.getSetting("enabled") == "false": return

        send_keys = []
        # on startup set source
        if ADDON.getSetting("activate_source") == "true":
            kodi_source = SOURCES.get(ADDON.getSetting("kodi_source"))
            if kodi_source:
                send_keys += [{"sendkey": kodi_source, "wait": 300}]

        # add volume values
        send_keys += self.getVolumeKeys("vol_on_startup")

        if send_keys:
            self.sendKeys(send_keys)


    def onKodiStopped(self):
        if not self.DEVICE: return
        if ADDON.getSetting("enabled") == "false": return
        
        # add volume values
        send_keys = self.getVolumeKeys("vol_on_ended")

        # on stopped go back source
        if ADDON.getSetting("inactive_source") == "true":
            ended_source = ADDON.getSetting("ended_source")
            if ended_source == "Custom":
                send_keys += self.parseSendKeys(ADDON.getSetting("custom_source"))
            else:
                back_source = SOURCES.get(ended_source)
                if back_source:
                    send_keys += [{"sendkey": back_source, "wait": 300}]

        if send_keys:
            self.sendKeys(send_keys)

    def getVolumeKeys(self, setting):
        vol = ADDON.getSetting(setting)
        try: return [{"sendkey": ("KEY_VOLUP", "KEY_VOLDOWN")["-" in vol], "wait": 300}] * int(vol.strip("-"))
        except: return []
                
class kodiPlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        xbmc.Player.__init__(self)
        self.main = kwargs["main"]

    def onPlayBackStarted(self):
        if self.main.DEVICE and ADDON.getSetting("enabled") == "true":
            send_keys = []
            # refresh source
            if ADDON.getSetting("refresh_kodi_source") == "true":
                kodi_source = SOURCES.get(ADDON.getSetting("kodi_source"))
                xbmc.sleep(600)
                if self.isPlayingVideo() and kodi_source:
                    send_keys += [{"sendkey": kodi_source, "wait": 300}]

            # add volume values
            send_keys += self.main.getVolumeKeys("vol_on_playback_started")

            if send_keys:
                self.main.sendKeys(send_keys)

    def onPlayBackStopped(self):
        if self.main.DEVICE and ADDON.getSetting("enabled") == "true":
            # add volume values
            send_keys = self.main.getVolumeKeys("vol_on_playback_ended")
            if send_keys:
                self.main.sendKeys(send_keys)

    def onPlayBackEnded(self):
        self.onPlayBackStopped()


service()
