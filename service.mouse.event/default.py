
from traceback import print_exc
from decimal import Decimal, DefaultContext

import xbmc
import xbmcgui
from xbmcaddon import Addon

ADDON = Addon("service.mouse.event")
SETTING = ADDON.getSetting

import mouse
from resources.lib import skin_utils


def divide(a, b):
    return DefaultContext.divide(Decimal(a),  Decimal(b))


class Service(xbmc.Monitor):
    def __init__(self):
        xbmc.Monitor.__init__(self)

        self.kodi_window = mouse.KodiResolution()

        self.oldpos = None
        self.oldskin = None
        self.isAlive = False

        self.windowsid = {}

    def start(self):
        if self.isAlive:
            return
        self.isAlive = True
        while not self.abortRequested():
            if not xbmc.getCondVisibility('System.GetBool(Input.EnableMouse) + Window.IsActive(Pointer.xml)'):
                if self.waitForAbort(.5):
                    break
                continue

            try:
                self.set_mouse_position()
            except:
                print_exc()
            skin_utils.onInterfaceSettings(self)
            self.debugInfo()

            if self.waitForAbort(.1): # Sleep/wait for abort for 100 milliseconds
                break # Abort was requested while waiting. We should exit

    def set_mouse_position(self):
        #transform mouse coords to kodi coords
        # get mouse position
        pt_x, pt_y = mouse.get_position()
        if self.oldpos == (pt_x, pt_y):
            return
        self.oldpos = (pt_x, pt_y)
        # get kodi coords
        fullscreen = xbmc.getCondVisibility('!String.IsEqual(System.ScreenMode,windowed)')
        k_left, k_top, k_width, k_height = self.kodi_window.get_position(fullscreen)
        # get/set skin resoluton
        self.skin = skin_utils.get_current_skin_res()
        if self.skin != self.oldskin:
            self.windowsid = {}
        self.oldskin = self.skin
        # get scaling
        scalex = divide(self.skin["width"],  k_width)
        scaley = divide(self.skin["height"], k_height)
        # now transform to kodi
        posx = (pt_x - k_left) * scalex
        posy = (pt_y - k_top) * scaley

        if skin_utils.SKIN_ZOOM:
            posx -= posx*skin_utils.SKIN_ZOOM
            posy -= posy*skin_utils.SKIN_ZOOM
        self.set_properties(posx, posy)

    def set_properties(self, posx, posy):
        xbmc.executebuiltin('SetProperty(MousePosX,%i,home)' % posx)
        xbmc.executebuiltin('SetProperty(MousePosY,%i,home)' % posy)

    def onNotification(self, sender, method, data):
        #xbmc.log("Monitor.onNotification: sender=%s - method=%s - data=%s" %(sender, method, data), xbmc.LOGNOTICE)
        pass

    def debugInfo(self):
        visible = 'Window.IsActive(Pointer.xml) + String.IsEqual(Window(home).Property(service.mouse.event.debug),true)'
        if xbmc.getCondVisibility('System.HasModalDialog'):
            wid = xbmcgui.getCurrentWindowDialogId()
        else:
            visible += ' + !System.HasModalDialog'
            wid = xbmcgui.getCurrentWindowId()
        #if SETTING("debug") == "false":
        #    xbmc.executebuiltin('ClearProperty(service.mouse.event.debug,home)')
        #else:
        xbmc.executebuiltin('SetProperty(service.mouse.event.debug,%s,home)' % SETTING("debug"))
        if self.windowsid.get(wid) is None:
            window = xbmcgui.Window(wid)
            label = 'Add-on Mouse Event (x:$INFO[Window(home).Property(MousePosX)], y:$INFO[Window(home).Property(MousePosY)])'
            debugLabels = [xbmcgui.ControlLabel(2, 2, int(self.skin["width"]), 50, label, alignment=0x00000006, textColor='0xFF000000'),
                           xbmcgui.ControlLabel(0, 0, int(self.skin["width"]), 50, label, alignment=0x00000006)]
            window.addControls(debugLabels)
            for label in debugLabels:
                label.setVisibleCondition(visible)
            self.windowsid[wid] = (window, debugLabels)
            

if (__name__ == "__main__"):
    Service().start()
