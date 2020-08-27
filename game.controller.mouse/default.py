# -*- coding: utf-8 -*-

import sys
import json
import time
from traceback import print_exc

import xbmc
import xbmcgui
from xbmcaddon import Addon

from joystick import *

#ADDON_DIR = sys.path[0]
ADDON = Addon()
ADDON_DIR = ADDON.getAddonInfo("path")
LangXBMC  = xbmc.getLocalizedString
LangADDON = ADDON.getLocalizedString

MONITOR = xbmc.Monitor()


# https://github.com/xbmc/xbmc/blob/master/xbmc/input/Key.h
CLOSE_WINDOW = [#xbmcgui.ACTION_PARENT_DIR,
                #xbmcgui.ACTION_PREVIOUS_MENU,
                xbmcgui.ACTION_NAV_BACK]

ACTION_MOVES = [xbmcgui.ACTION_MOVE_LEFT,
                xbmcgui.ACTION_MOVE_RIGHT, 
                xbmcgui.ACTION_MOVE_UP,
                xbmcgui.ACTION_MOVE_DOWN,
                xbmcgui.ACTION_MOUSE_MOVE]


def log(msg, lvl=xbmc.LOGNOTICE):
    xbmc.log('JOYSTICK MOUSE: {}'.format(msg), lvl)

def getAddonDetails(addonid):
    data = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "Addons.GetAddonDetails",
        "params": {"addonid": addonid, "properties": ["enabled"]}
        })
    details = json.loads(xbmc.executeJSONRPC(data))
    #log(json.dumps(details, sort_keys=True, indent=2))
    return details.get("result", {}).get("addon", {})

def setAddonEnabled(addonid, enabled):
    data = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "Addons.SetAddonEnabled",
        "params": {"addonid": addonid, "enabled": enabled}
        })
    statut = json.loads(xbmc.executeJSONRPC(data))
    #log(json.dumps(statut, sort_keys=True, indent=2))
    return statut.get("result") == "OK"

def getCoordinates(posx, posy, area=None, offset=None):
    if area is not None:
        acx, acy = [(c/2.0) for c in area]
        posx *= acx
        posy *= acy
    if offset is not None:
        posx += offset[0]
        posy += offset[1]
    return posx, posy


class Gamepad(xbmcgui.WindowXML):
    def __new__(cls):
        return super(Gamepad, cls).__new__(cls, "script-gamepad.xml", ADDON_DIR)

    def __init__(self):
        super(Gamepad, self).__init__()
        self.stop = False
        self.joy = None

        self.joysticks = get_joysticks()
        self.joys_count = len(self.joysticks)
        if self.joys_count == 1:
                self.joy = self.joysticks[0]
        elif self.joys_count > 1:
            choices = sorted(DEVICE_NAMES.items())
            selected = xbmcgui.Dialog().select(LangADDON(30099),
                                               [n for i, n in choices])
            if selected >= 0:
                self.joy = self.joysticks[choices[selected][0]]
        else:
            self.joy = None

    def onButton(self, button, pressed):
        kid, d = button
        self.setProperty("button.{}".format(d["name"]), str(pressed))

    def onAxis(self, axis, value):
        try:
            if axis == "LeftTrigger":
                self.setProperty("lefttrigger", ("0", "1")[value > 0])
                self.leftTriggerControl.setPosition(0, int(20*value))
                self.joy.setVibration(value, 0)
            elif axis == "RightTrigger":
                self.setProperty("righttrigger", ("0", "1")[value > 0])
                self.rightTriggerControl.setPosition(0, int(20*value))
                self.joy.setVibration(0, value)
            else:
                dx, dy = value
                self.setProperty(axis, ("0", "1")[dx != 0.0 or dy != 0.0])
                self.controlGroup.setPosition(int(200*dx), int(75*dy))
        except:
            print_exc()

    def onInit(self):
        if self.joy is None:
            xbmcgui.Dialog().notification(LangADDON(30100), LangADDON(30101),
                                          xbmcgui.NOTIFICATION_ERROR, 5000)
            self.close()
        else:
            self.start()

    def start(self):
        try:
            self.setContainer()

            self.controlGroup = self.getControl(100)
            self.leftTriggerControl = self.getControl(101)
            self.rightTriggerControl = self.getControl(102)

            self.joy.on_button = self.onButton
            self.joy.on_axis = self.onAxis

            info = self.joy.capabilities #information()
            self.setProperty("joystick.name", info["name"])
            # try: self.setProperty("battery.level", str(info["battery"]["level"]))
            # except: pass

            bat_info_added = False
            # main loop
            while not self.stop:
                self.joy.dispatch_events()
                #time.sleep(.01)
                if MONITOR.waitForAbort(.01):
                    break
                if not bat_info_added:
                    b = self.joy.capabilities.get("battery", {})
                    if b.get("level") is not None:
                        self.setProperty("battery.level", str(b["level"]))
                        self.setProperty("battery.type", str(b["type"]))
                        self.setProperty("battery.percent", str(b["percent"]))
                        bat_info_added = True
        except:
            print_exc()

    def setContainer(self):
        self.container150 = self.getControl(150)
        self.container151 = self.getControl(151)
        self.container152 = self.getControl(152)
        order = [15,  4,  6, 12, 13, 11, 10, 8, 17, 18, 19, 20,
                 16,  5,  7,  0,  1,  2,  3, 9, 21, 22, 23, 24,
                 25, 14, 26]
        self.listitems = []
        for kid in order:
            item = KBUTTONS[kid]
            l = xbmcgui.ListItem("")
            l.setProperty('kid', str(kid))
            l.setProperty('gamepad.bname', LangADDON(item["msgctxt"]))
            l.setArt({'icon': 'icons/{}.png'.format(item["name"])})
            self.listitems.append(l)
            
        self.container150.reset()
        self.container150.addItems(self.listitems[:12])

        self.container151.reset()
        self.container151.addItems(self.listitems[12:24])

        self.container152.reset()
        self.container152.addItems(self.listitems[24:])
        self.container152.selectItem(1)

    def onFocus(self, controlID):
        pass

    def sendClick(self, controlID):
        self.onClick(controlID)

    def onClick(self, controlID):
        try:
            if controlID in [150, 151, 152]:
                li = self.getControl(controlID).getSelectedItem()
                kid = int(li.getProperty('kid'))
                bname = li.getProperty('gamepad.bname')
                clabel = li.getLabel()
                choice = [LangADDON(30047), LangADDON(30048)]
                if controlID == 152:
                    choice += [LangADDON(30046)]
                if clabel:
                    choice += [LangXBMC(13334)]
                    
                selected = xbmcgui.Dialog().select(bname, choice)
                if clabel and len(choice) == 3 and selected == 2:
                    selected += 1
                    
                if selected == 0:
                    # keyboard action
                    newkey = self.selectKey(bname)
                    if newkey is not None:
                        li.setLabel(newkey[1])
                elif selected == 1:
                    # mouse action
                    choice = [LangADDON(i) for i in range(30049, 30058)]
                    m = xbmcgui.Dialog().select(LangADDON(30047), choice)
                    if m == 0:
                        c = None
                        if kid in [17, 18, 19, 20]:
                            c = self.container150
                        elif kid in [21, 22, 23, 24]:
                            c = self.container151
                        if c is not None:
                            m = choice[m]
                            for i in range(8, 12):
                                c.getListItem(i).setLabel(m)
                    elif m >= 1:
                        li.setLabel(choice[m])
                elif selected == 2:
                    # custom action
                    xbmcgui.Dialog().ok(LangADDON(30046), LangADDON(30045))
                    kb = xbmc.Keyboard(clabel, bname)
                    kb.doModal()
                    if kb.isConfirmed():
                        cmd = kb.getText()
                        li.setLabel(cmd)
                elif selected == 3:
                    # edit label
                    kb = xbmc.Keyboard(clabel, LangXBMC(1029))
                    kb.doModal()
                    if kb.isConfirmed():
                        label = kb.getText()
                        li.setLabel(label)
        except:
            print_exc()
                
    def onAction(self, action):
        if action in CLOSE_WINDOW:
            self._close()
        elif action in ACTION_MOVES:
            try:
                if xbmc.getCondVisibility("Control.HasFocus(150)"):
                    pos = self.container150.getSelectedPosition()
                    self.container151.selectItem(pos)
                elif xbmc.getCondVisibility("Control.HasFocus(151)"):
                    pos = self.container151.getSelectedPosition()
                    self.container150.selectItem(pos)
            except:
                print_exc()
        #elif action == xbmcgui.ACTION_CONTEXT_MENU:
        #    xbmcgui.Dialog().contextmenu(["Default Settings", "Cancel"])
        else:
            # kodi keyboard action
            buttonCode = action.getButtonCode()
            if buttonCode:
                self.onKeyboardAction((buttonCode & 0xFF))

    def onKeyboardAction(self, actionID):
        # keyboard action
        if (actionID == ord('H')): # H was pressed, get hint
            self.sendClick(6)
        elif (actionID == ord('P')): # P was pressed, pause game
            self.sendClick(11)
        elif (actionID == ord('W')): # W was pressed, show scores
            self.sendClick(10)

    def _close(self):
        self.stop = True
        xbmc.sleep(500)
        self.close()

    def selectKey(self, heading=""):
        self.key = None
        self.stop_get_key = False
        def getKey():
            HEX = sorted(input.VIRTUAL_KEY.keys())
            while self.key is None:
                for vk in HEX:
                    if input.GetKeyState(vk) & input.VK_MASK:
                        self.key = (hex(vk), input.VIRTUAL_KEY[vk])
                        break
                #time.sleep(.015)
                if MONITOR.waitForAbort(.015):
                    break
                if self.stop_get_key:
                    self.key = None
                    break

            xbmc.executebuiltin("Dialog.Close(okdialog)")
            #xbmcgui.Dialog().ok(heading, str(self.key[0]), self.key[1])

        Timer(.5, getKey, ()).start()
        xbmcgui.Dialog().ok(heading, "Appuyer sur le bouton auquel vous souhaitez attribuer cette fonction.")
        self.stop_get_key = True
        return self.key


g = Gamepad()
g.doModal()
del g

"""
if xbmc.getCondVisibility('system.getbool(input.enablemouse)'):
    # mouse active
    ok = True
    addonid = 'peripheral.joystick'
    peripheral_joystick_enabled = getAddonDetails(addonid).get('enabled', False)
    if peripheral_joystick_enabled:
        # desactive, pas supporter avec ce mode
        ok = setAddonEnabled(addonid, False)
    if ok:
        # Eeny, meeny, miny, moe,
        # Catch a tiger by the toe.
        # If he hollers, let him go,
        # Eeny, meeny, miny, moe.
        import sample
        log("sample_mouse_joystick")
        sample.sample_mouse_joystick()
        #log("sample_first_joystick")
        #sample.sample_first_joystick()

    if peripheral_joystick_enabled:
        ok = setAddonEnabled(addonid, True)
"""