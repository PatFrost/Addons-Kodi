
import os
import re
import json
import time
from datetime import timedelta
from traceback import print_exc
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui

from decimal import Decimal, DefaultContext

def divide(a, b):
    return DefaultContext.divide(Decimal(a),  Decimal(b))

# get skin zoom on starpup
SKIN_ZOOM = "".join(re.findall("<skinzoom.*?>(.*?)</skinzoom>",
    open(xbmc.translatePath("special://profile/guisettings.xml")).read())) or "0"
if SKIN_ZOOM != "0":
    xbmcgui.Dialog().notification('Add-on Service - Mouse Event', "Doesn't work correctly with zoom skin. (%s)" % SKIN_ZOOM, xbmcgui.NOTIFICATION_WARNING, 3000)
SKIN_ZOOM = divide(SKIN_ZOOM, 100)


def log(msg, lvl=xbmc.LOGNOTICE):
    xbmc.log('Mouse Event - Skin Utils: {}'.format(msg), lvl)


def onInterfaceSettings(monitor=xbmc.Monitor()):
    zoom = ""
    while xbmc.getCondVisibility('Window.IsActive(interfacesettings)'):
        if xbmc.getCondVisibility('Integer.IsEqual(System.CurrentControlId,-74) + String.Contains(System.CurrentControl,$LOCALIZE[20109])'):
            #xbmcgui.Dialog().notification('Add-on Service - Mouse Event', "Doesn't work correctly with zoom skin.", xbmcgui.NOTIFICATION_WARNING, 3000)
            #monitor.waitForAbort(3)
            scc = xbmc.getInfoLabel("System.CurrentControl")
            if " %" in scc:
                zoom = scc
            monitor.waitForAbort(.1)
    if " %" in zoom:
        new_zoom = divide(zoom.split()[2].strip("("), 100)
        if new_zoom != SKIN_ZOOM:
            log("{} - Zoom changed {}% to {}%".format(xbmc.getSkinDir(), SKIN_ZOOM, new_zoom))
            globals().update({"SKIN_ZOOM": new_zoom})


class DICT(dict):
    # Don't raises a KeyError -> https://docs.python.org/2/reference/datamodel.html#object.__missing__
    def __missing__(self, key):
        if key.startswith("skin."):
            # Probably a new skin added! rescan.
            self.update(get_skins_info())
            return self.get(key) or DICT()
        elif key in ["width", "height"]:
            return 1
        return DICT()

def get_skins_info():
    results = json.loads(xbmc.executeJSONRPC(
        '{"jsonrpc": "2.0", "id": 1, "method": "Addons.GetAddons", \
        "params": {"type": "xbmc.gui.skin", "enabled": "all", \
        "properties": ["name", "path", "broken"]}}'
        )).get("result", {}).get("addons", [])
    skins = DICT()
    for skin in results:
        # if skin["broken"]: continue
        # get/add resolution of skin
        try:
            for res in ET.parse(os.path.join(skin["path"], "addon.xml")).findall("extension/res"):
                res = res.attrib
                if res: skin[res["aspect"]] = res
        except:
            print_exc()
        skins[skin['addonid']] = skin
    return skins

SKINS = get_skins_info()

def get_skin_res(skin, aspect):
    return SKINS[skin][aspect]

def get_current_skin_res():
    return get_skin_res(xbmc.getSkinDir(), xbmc.getInfoLabel("Skin.AspectRatio"))


if (__name__ == "__main__"):
    st = time.clock()
    log(json.dumps(SKINS, sort_keys=True, indent=2))
    log(get_current_skin_res())
    log(get_skin_res("skin.dummy", "21:9"))
    log(str(timedelta(0, (time.clock() - st), 0)))
