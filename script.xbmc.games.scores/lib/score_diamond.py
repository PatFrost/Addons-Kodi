
import json
from gamesdb import addScore
fpath = r"C:\Documents and Settings\Frost\Application Data\XBMC\userdata\addon_data\script.game.diamond\scores.json"
s_json = open( fpath ).read()
scores = json.loads( s_json )
for score in scores:
    #score[u'Frost', 266818, u'Medium', u'2012-09-22']
    s = {
        "strNickName": score[ 0 ],
        "score": score[ 1 ],
        "strMode": score[ 2 ],
        "strDate": score[ 3 ],
        "strGameId": "script.game.diamond",
        }
    print addScore( s )