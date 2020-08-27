
import os
import sys
from threading import Timer
from traceback import print_exc

import xbmc
import xbmcgui
from xbmcaddon import Addon

from lib.samremote import KEY_CODES, SamRemote, setVolume
from lib.services import *

ADDON = Addon("script.samsung.remote")

def parseSendKeys(args):
    send_keys = []
    if args:
        try:
            for arg in args.replace("&amp;", "&").replace(";", ",").split(","):
                send_keys += [dict([a.split("=") for a in arg.split("&")])]
        except:
            print_exc()
            send_keys = []
    #print send_keys
    return send_keys

def sendKeys(sendkeys):
    KEYS = KEY_CODES.keys()
    sr = SamRemote()
    for key in sendkeys:
        k, w = key.get("sendkey"), key.get("wait")
        if str(w).isdigit(): w = int(w)/1000.0
        if str(k) in KEYS:
            # send key and sleep
            sr.sendKey(k, w)
        elif key.get("sendtext"):
            # send key and sleep
            sr.sendText(key["sendtext"], w)
        else:
            print "Invalid: samsung.remote.send(%r)" % key
    # close remote
    sr.close()

def dialogSelectSetItem(item):
    cmd = "Control.Move(3,%i)" % int(item)
    xbmc.executebuiltin(cmd)
    xbmc.log("Dialog.Select."+cmd, xbmc.LOGINFO)

def fullRemote(addSearch=True):
    xbmc.executebuiltin("Skin.ToggleSetting(sam_full_remote)")
    try:
        KEYS, CHOICES = [], []
        for k, v in sorted(KEY_CODES.items(), key=lambda v: v[1][0]):
            CHOICES.append("".join(["[B]", v[0], "[/B]  [COLOR=66FFFFFF](", v[1], ")[/COLOR]"]))
            KEYS.append(k)
        if addSearch:
            CHOICES += [xbmc.getLocalizedString(16017)]

        selectItem = 0
        while (selectItem != -1):
            Timer(0.5, dialogSelectSetItem, [selectItem]).start()
            selectItem = selected = xbmcgui.Dialog().select('XBMC Samsung TV Remote', CHOICES)
            if selected == -1: break

            if selected >= len(KEYS):
                #get text from keyboard
                kb = xbmc.Keyboard("", xbmc.getLocalizedString(16017))
                kb.doModal()
                if kb.isConfirmed():
                    text = kb.getText()
                    # get connection
                    sr = SamRemote()
                    # send key and sleep 1 second
                    sr.sendText(text, 1)
                    # close remote
                    sr.close()
            else:
                # get connection
                #xbmc.executebuiltin("ActivateWindow(busydialog)")
                sr = SamRemote()
                #xbmc.executebuiltin("Dialog.Close(busydialog,true)")
                # send key and sleep 1 second
                sr.sendKey(KEYS[selected], 1)
                # close remote
                sr.close()
    except:
        print_exc()
    xbmc.executebuiltin("Skin.Reset(sam_full_remote)")


class DialogRemote(xbmcgui.WindowXMLDialog):
    CONTAINER_ID          = range(1149, 1160+1)
    CONTROLS_EDIT_ID      = [1163, 1164]
    CONTAINER_SERVICES_ID = 159

    def __init__(self, *args, **kwargs):
        self.lock      = False
        self.listitems = []
        self.services  = loadServices()

    def onInit(self):
        self.addServices()

    def addServices(self):
        self.listitems = []
        try:
            self.control_services = self.getControl(self.CONTAINER_SERVICES_ID)
            self.control_services.reset()
            for service in self.services:
                try:
                    listitem = xbmcgui.ListItem(service["title"], "", service["icon"], service["icon"])
                    listitem.setProperty("sendkeys", service["sendkeys"])
                    self.listitems.append(listitem)
                except:
                    print ("service:", service)
                    print_exc()
            self.control_services.addItems(self.listitems)
        except:
            print_exc()

    def onClick(self, controlID):
        try:
            if controlID == self.CONTAINER_SERVICES_ID: controlID += 1000
            if not self.lock and controlID in self.CONTAINER_ID:
                sendkeys = xbmc.getInfoLabel("Container(%i).ListItem.Property(sendkeys)" % int(controlID-1000))
                if sendkeys.lower() == "fullremote":
                    return fullRemote(False)
                self.lock = True
                #xbmcgui.Dialog().ok(xbmc.getInfoLabel("Container(%i).ListItem.Label" % int(controlID-1000)), sendkeys)

                send_text = []
                if "KEY_DTV_SIGNAL" in sendkeys:
                    #get text from keyboard
                    kb = xbmc.Keyboard("", xbmc.getLocalizedString(16017))
                    kb.doModal()
                    if kb.isConfirmed():
                        text = kb.getText()
                        # first add clean text and send search text
                        send_text = [{"sendtext": "", "wait": 2000}, {"sendtext": text, "wait": 1000}]

                send_keys = parseSendKeys(sendkeys)
                if send_keys: sendKeys(send_keys + send_text)

            elif controlID in self.CONTROLS_EDIT_ID:
                text = self.getControl(int(controlID-1000)).getText()
                send = [{"sendkey": "KEY_DTV_SIGNAL", "wait": 3000}, {"sendtext": "", "wait": 2000}]
                if text: send += [{"sendtext": text, "wait": 1000}]
                sendKeys(send)
        except:
            print_exc()
        self.lock = False

    def onContextMenu(self):
        #if not bool(self.listitems) and not xbmc.getCondVisibility("Control.HasFocus(159)"):
        #    return
        try:
            pos   = self.control_services.getSelectedPosition()
            title = xbmc.getInfoLabel("Container(159).ListItem.Label").decode("utf-8")
            choices = map(xbmc.getLocalizedString, [13332, 13333, 117, 118, 748, 13511, 20462, 222])
            choices[4] += "  [COLOR=FF999999](KEY_[B]?????[/B])[/COLOR]"
            #choices = ["Up", "Down", "Delete", "Rename", "Edit Keys", "Choose Art", "Add Service", "Cancel"]
            selected = xbmcgui.Dialog().select(title, choices)

            if selected in [0, 1]:
                # move up/down service
                item = self.services[pos]
                services = move_item_list(self.services, item, ("up","down")[selected])
                if self.services != services:
                    self.services = services
                    self.addServices()
                    self.control_services.selectItem(self.services.index(item))
                    ok = saveServices(self.services)

            elif selected == 2:
                # delete service
                del self.listitems[pos]
                del self.services[pos]
                ok = saveServices(self.services)
                self.control_services.removeItem(pos)
                if pos >= len(self.services): pos -= 1
                self.control_services.selectItem(pos)

            elif selected == 3:
                # rename service title
                kb = xbmc.Keyboard(title, xbmc.getLocalizedString(16008))
                kb.doModal()
                if kb.isConfirmed():
                    text = kb.getText()
                    self.listitems[pos].setLabel(text)
                    self.services[pos]["title"] = text
                    ok = saveServices(self.services)

            elif selected == 4:
                # edit service send key(s)
                new_sendkeys = "sendkey=KEY_?????&amp;wait=250"
                str_sendkeys = xbmc.getInfoLabel("Container(159).ListItem.Property(sendkeys)")
                sendkeys = ["sendkey={0}&wait={1}".format(*s.values()) for s in parseSendKeys(str_sendkeys)] or [new_sendkeys]
                more     = [xbmc.getLocalizedString(22082), xbmc.getLocalizedString(190), xbmc.getLocalizedString(222)]
                heading = u"".join([title, u": [COLOR=FF999999]", xbmc.getLocalizedString(748), u"[/COLOR] "])
                selectItem = 0
                while (selectItem != -1):
                    Timer(0.5, dialogSelectSetItem, [selectItem]).start()
                    selectItem = selected = xbmcgui.Dialog().select(heading, sendkeys + more)
                    if (selected == -1) or (selected > len(sendkeys)+1):
                        break
                    if selected == len(sendkeys):
                        # more...
                        sendkeys.append(new_sendkeys)
                    elif selected == len(sendkeys)+1:
                        # save
                        keys = ";".join(sendkeys)
                        self.listitems[pos].setProperty("sendkeys", keys)
                        self.services[pos]["sendkeys"] = keys
                        ok = saveServices(self.services)
                        break
                    else:
                        # edit send keys
                        kb = xbmc.Keyboard(sendkeys[selected], heading + str(selected+1))
                        kb.doModal()
                        if kb.isConfirmed():
                            sendkeys[selected] = kb.getText()
                            if not sendkeys[selected]:
                                del sendkeys[selected]

            elif selected == 5:
                # choose art of service
                cur_art = xbmc.getInfoLabel("Container(159).ListItem.Icon")
                art = xbmcgui.Dialog().browse(1, xbmc.getLocalizedString(1030), 'files', '.gif|.jpg|.png', True, False, os.path.dirname(cur_art)+"/")
                if art and os.path.isfile(art) and art != cur_art:
                    self.listitems[pos].setIconImage(art)
                    self.listitems[pos].setThumbnailImage(art)
                    self.services[pos]["icon"] = art
                    ok = saveServices(self.services)

            elif selected == 6:
                # add new service
                self.services.append({"title": "New Empty Service", "icon": "iRemote/Images/etc_feedback.png", "sendkeys": ""})
                ok = saveServices(self.services)
                self.addServices()
                self.control_services.selectItem(len(self.services)-1)
                xbmc.sleep(300)
                xbmc.executebuiltin("Action(ContextMenu)")
        except:
            print_exc()

    def onFocus(self, controlID):
        pass

    def onAction(self, action):
        actionID = action.getId()
        if actionID == 117 and bool(self.listitems) and xbmc.getCondVisibility("Control.HasFocus(159)"):
            self.onContextMenu()

        if actionID in [9, 10]:#, 92]: don't use 92, allow container onback
            self._close_dialog()

        if actionID == 92:
            #print "action(%r)" % actionID
            if xbmc.getCondVisibility("Control.HasFocus(160)"):
                self._close_dialog()
            else:
                try:
                    self.getControl(160)
                    self.setFocusId(160)
                except:
                    self._close_dialog()

    def _close_dialog(self):
        self.close()

def main():
    try:
        args = ",".join(sys.argv[1:])
        #print sys.argv
        send_keys = parseSendKeys(args)
        if send_keys:
            sendKeys(send_keys)

        else:
            remote_xml = ADDON.getSetting("remote")
            if remote_xml != "FullRemote.xml":
                try:
                    w = DialogRemote(remote_xml, ADDON.getAddonInfo("path"))
                    w.doModal()
                    del w
                except:
                    print_exc()
                    remote_xml = "FullRemote.xml"

            if remote_xml == "FullRemote.xml":
                fullRemote()
    except:
        print locals()
        print_exc()

if __name__ == "__main__":
    main()
