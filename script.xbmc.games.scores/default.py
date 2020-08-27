
import sys
sys.path.append(sys.path[0]+"/lib")

import xbmc
xbmc.log("{}".format(sys.argv), xbmc.LOGNOTICE)

# parse argv
GAME_ID = None
try: GAME_ID = sys.argv[1]
except: pass
if GAME_ID is None:
    from xbmcgui import Dialog
    from gamesdb import getGames
    games = getGames()
    selected = Dialog().select("Select Game", [t for t, i, g in games])
    if selected >= 0:
        GAME_ID = games[selected][2]
    # else:
        # sys.exit()

if GAME_ID:
    from scores import Main
    Main()
