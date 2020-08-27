
import os
import json
from traceback import print_exc

try:
    import xbmc
    import xbmcgui
    import xbmcvfs
    from xbmcaddon import Addon
    ADDON = Addon("script.samsung.remote")
    # set cached filename
    profile     = ADDON.getAddonInfo('profile')
    C_FILENAME  = xbmc.translatePath(profile + 'services.json')
    OPEN_FILE   = xbmcvfs.File
    path_exists = xbmcvfs.exists
    if not path_exists(profile): xbmcvfs.mkdir(profile)
except:
    C_FILENAME  = 'services.json'
    OPEN_FILE   = open
    path_exists = os.path.exists

DEFAULT_SERVICES = [
  {
    "title": "Smart Hub",
    "icon": "smarthub3.png",
    "sendkeys": "sendkey=KEY_CONTENTS&amp;wait=250"
  },
  {
    "title": "3D",
    "icon": "icon_3d.png",
    "sendkeys": "sendkey=KEY_PANNEL_CHDOWN&amp;wait=250"
  },
  {
    "title": "HDMI",
    "icon": "icon_hdmi.png",
    "sendkeys": "sendkey=KEY_HDMI&amp;wait=250",
  },
  {
    "title": "Web Browser",
    "icon": "iRemote/Images/internet_tv.png",
    "sendkeys": "sendkey=KEY_CONVERGENCE&amp;wait=250"
  },
  # {
    # "title": "PC (HDMI 3/DVI)",
    # "icon": "iRemote/Images/pcinput.png",
    # "sendkeys": "sendkey=KEY_AUTO_ARC_PIP_RIGHT_BOTTOM&amp;wait=250"
  # }, 
  {
    "title": "PC/Kodi (HDMI 2)",
    "icon": "iRemote/Images/pcinput.png",
    "sendkeys": "sendkey=KEY_AUTO_ARC_PIP_WIDE&amp;wait=250"
  }, 
  {
    "icon": "Universal_remote_side.png", 
    "sendkeys": "fullremote", 
    "title": "Full Remote"
  },
  # {
    # "title": "Raspberry Pi (HDMI 2)",
    # "icon": "Rasp_turn_around.gif",
    # "sendkeys": "sendkey=KEY_AUTO_ARC_PIP_WIDE&amp;wait=250"
  # }, 
  {
    "icon": "../../../../channels/z_big.png", 
    "sendkeys": "sendkey=KEY_EXT20&wait=250;sendkey=KEY_6&wait=500;sendkey=KEY_4&wait=500;sendkey=KEY_3&wait=500;sendkey=KEY_ENTER&wait=250", 
    "title": "Ztélé HD"
  }
]


def loadServices():
    services = []
    try:
        if path_exists(C_FILENAME):
            f = OPEN_FILE(C_FILENAME)
            b = f.read().strip("\x00")
            f.close()
            services = json.loads(b)
    except:
        print_exc()
    return services or DEFAULT_SERVICES

def saveServices(services):
    ok = False
    try:
        b = json.dumps(services, sort_keys=True, indent=2)
        f = OPEN_FILE(C_FILENAME, "w")
        f.write(b)
        f.close()
        ok = True
    except:
        print_exc()
    return ok

def move_item_list(iterable, item, move="up"):
    try:
        copied_list = iterable[:]
        i_old = copied_list.index(item)
        i_new = i_old + (1, -1)[move == "up"]
        max = len(copied_list)
        if i_new == -1: i_new = max
        elif i_new >= max: i_new = 0
        copied_list.insert(i_new, copied_list.pop(i_old))
        return copied_list
    except:
        print_exc()
        return iterable

def selectCustomService():
    from threading import Timer
    def dialogSelectSetItem(item):
        cmd = "Control.Move(3,%i)" % int(item)
        xbmc.executebuiltin(cmd)
        xbmc.log("Dialog.Select."+cmd, xbmc.LOGINFO)

    services = loadServices()
    choices = [s["title"] for s in services]

    # selectItem = 0
    # try: 
        # selectItem = choices.index(ADDON.getSetting("custom_name"))
        # choices[selectItem] = "[COLOR=selected]%s[/COLOR]" % choices[selectItem]
    # except:
        # print_exc()
    # Timer(0.3, dialogSelectSetItem, [selectItem]).start()

    selected = xbmcgui.Dialog().select("Select your custom source", choices)
    if selected != -1:
        ADDON.setSetting("ended_source", "Custom")
        ADDON.setSetting("custom_name", services[selected]["title"])
        ADDON.setSetting("custom_source", services[selected]["sendkeys"])


if __name__ == "__main__":
    selectCustomService()
    
    # l = DEFAULT_SERVICES #[1,2,3,4,5,6,7,8,9,0]
    # services = move_item_list(l, l[0], "down")

    # print json.dumps( DEFAULT_SERVICES, sort_keys=True, indent=2 )
    # print json.dumps( services, sort_keys=True, indent=2 )
    # print DEFAULT_SERVICES == services
    
    
