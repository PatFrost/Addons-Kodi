
# Modules general
import os
import sys
import time
import random
from threading import Timer
from traceback import print_exc
from datetime import date, timedelta
from urlparse import parse_qsl as parse_params

# Modules XBMC
import xbmc
import xbmcgui
from xbmcaddon import Addon


# constants
ADDON = Addon("script.game.diamond")
ADDON_ID = ADDON.getAddonInfo("id")
ADDON_DIR = ADDON.getAddonInfo("path")
GAME_ID = ADDON_ID # required, used in gamesdb::scrores
TODAY = date.today()

# Modules Custom
import gamesdb # from module script.xbmc.games.scores
import gemsutils as utils
from animations import * # constants animation


# constants
# PY_SCORES = Addon("script.xbmc.games.scores").getAddonInfo("path")
# PY_SCORES = os.path.join(PY_SCORES, "default.py")
# PY_SCORES_ARGV = ["default.py", GAME_ID]

GEMS_DIR = os.path.join(ADDON_DIR, "resources", "skins", "Default", "media", "gems")
GEM_IMG = os.path.join(GEMS_DIR, "gem{}b.png")
DYNAMITE_GEM = os.path.join(GEMS_DIR, "dynamite{}.png")

WAV_DIR = os.path.join(ADDON_DIR, "resources", "skins", "Default", "sounds")
BAD_SWAP_WAV = os.path.join(WAV_DIR, "badswap.wav")
DIAMOND_WAV = os.path.join(WAV_DIR, "diamond.wav")
BOMB_WAV = os.path.join(WAV_DIR, "boom.wav")

# Language = ADDON.getLocalizedString # ADDON strings
# LangXBMC = xbmc.getLocalizedString # XBMC strings


# https://github.com/xbmc/xbmc/blob/master/xbmc/input/Key.h
CLOSE_DIALOG = [
    xbmcgui.ACTION_PARENT_DIR,
    xbmcgui.ACTION_PREVIOUS_MENU,
    xbmcgui.ACTION_NAV_BACK,
    # xbmcgui.ACTION_CONTEXT_MENU,
    ]

def playSound(snd):
    xbmc.playSFX(snd)

class Diamond(xbmcgui.WindowXMLDialog):
    def __new__(cls):
        return super(Diamond, cls).__new__(cls, "script-diamond.xml", ADDON_DIR)

    def __init__(self):
        super(Diamond, self).__init__()

        self.time_allowed = (60*5) # 5min
        self.time_left = self.time_allowed
        self.color_time_progress = timedelta(seconds=60)
        
        self.current_score = 0
        self.next_bomb = 5000
        self.help_pts = 300
        self.blanked = 0
        
        self.controls_hint = []
        self.control_added = []
        self.selected = []
        self.gems_id = []
        self.gems = []
        
        self.paused = False
        self.lock = False
        self._stop = True
        
        self.mode = ""
        self.username = ""

    def onInit(self):
        self.setProperty("color_progress", "white")
        
        self.mode_ids = [7, 8, 9, 10]
        self.mode_dict = {7: u"Easy", 8: u"Medium", 9: u"Hard", 10: u"Expert"}
        self.help_dict = {7: 250, 8: 500, 9: 750, 10: 1000}

        self.container = self.getControl(50)
        self.container.reset()

        self.help_button = self.getControl(6)
        self.help_button.setEnabled(0)
        
        self.pause_button = self.getControl(11)

        self.progress_bar = self.getControl(666)

        rcl = parse_params(self.getProperty("required_container_layout"))
        self.rcl = dict([(k, int(v)) for k, v in rcl])
        
        # setattr gemControl, simply for fast research

    def gemControl(self, gem_pos):
        return self.getControl(100+gem_pos)

    def addPTSControl(self, label, gem_pos):
        ctrl = self.gemControl(gem_pos)
        x, y = ctrl.getPosition()
        w, h = ctrl.getWidth(), ctrl.getHeight()
        # print (self.rcl["x"]+x, self.rcl["y"]+y, w, h, label)

        lbl = xbmcgui.ControlLabel(self.rcl["x"]+x, self.rcl["y"]+y, w, h, label, "font13_title", alignment=0x00000002+0x00000004)
        self.addControl(lbl)

        # st = int(gem_pos/8)*self.rcl["h"]#80
        lbl.setAnimations(
            [('conditional', ANIM_PTS_OUT_SCREEN.format(int(gem_pos/8)*self.rcl["h"], SCREEN_HEIGHT))] \
            + ANIM_PTS_CONTROL
            )
        self.control_added.append(lbl)

    def remPTSControl(self):
        if self.control_added:
            try:
                self.removeControls(self.control_added)
            except:
                for ctrl in self.control_added:
                    try:
                        self.removeControl(ctrl)
                    except:
                        pass
            self.control_added = []

    def onFocus(self, controlID):
        pass

    def timer(self):
        if self._stop:
            return None
        try:
            percent = ((self.time_left * 100.0) / self.time_allowed)
            if percent < 0:   percent = 0
            elif percent > 100: percent = 100

            self.progress_bar.setPercent(int(percent))

            self._stop_timer_thread()
            if self.time_left > 0:
                self.timer_thread = Timer(1, self.timer, ())
                self.timer_thread.start()

            if not self.paused:
                if self.time_left < 0: self.time_left = 0
                td = timedelta(seconds=self.time_left)
                self.setContainerProperty("time_left", str(td).lstrip("0:").split(".")[0])
                self.setProperty("color_progress", ("white", "red")[td < self.color_time_progress])
                self.time_left -= 1
                self.game_statut()
        except:
            print_exc()

    def _stop_timer_thread(self):
        try: self.timer_thread.cancel()
        except: pass

    def _stop_game(self, clear_list=True):
        self.blanked = 0
        self.current_score = 0
        self.next_bomb = 5000
        self.help_pts = 300
        self.selected = []
        self.gems_id  = []
        self.gems     = []
        self.paused = False
        self.lock  = False
        self._stop = True
        
        self._stop_timer_thread()
        self.setContainerProperty("time_left", "")
        try:
            self.help_button.setEnabled(0)
        except:
            print_exc()
        try:
            self.progress_bar.setPercent(1)
        except:
            print_exc()
        try:
            if clear_list:
                self.container.reset()
        except:
            print_exc()
        xbmc.sleep(500)

    def game_statut(self):
        self.help_button.setEnabled(self.current_score >= self.help_pts)
        if self.time_left > 0 and self.blanked >= 64:
            # you win, add time to score
            self.current_score += int(self.time_left * 10)
            self.setContainerProperty("current_score", str(self.current_score))
            current_score = self.current_score
            mode = self.mode
            self._stop_game(False)
            # enter name
            self.setContainerProperty("winning", "1")
            kb = xbmc.Keyboard(self.username, "Score {} - Enter username".format(current_score))
            kb.doModal()
            if kb.isConfirmed():
                username = kb.getText()
                if bool(username):
                    self.username = username
                    score = {
                        "strNickName": username,
                        "score":       current_score,
                        "strMode":     mode,
                        "strDate":     str(TODAY),
                        "strGameId":   ADDON_ID,
                        }
                    OK, idScore = gamesdb.addScore(score)
                    # self.sendClick(10)

            self.mode = ""
            self.remPTSControl()

        elif self.time_left <= 0:
            # you lose
            self._stop_game(False)
            self.setContainerProperty("lose", "1")
            self.mode = ""
            self.remPTSControl()

    def move_gems(self, _sleep=True):
        # get dropping gems (GOOD METHODE)
        drop_gems = {}
        for col in range(0, 8)[::-1]:
            while True:
                has_empty = False
                for i in range(col, col+64, 8)[::-1]:
                    drop = False
                    move_i = i-8
                    if move_i < 0 and self.gems[i] == 0:
                        self.gems[i] = random.choice(self.gems_id)
                        # print "{}, new gem: {}".format(i, self.gems[i])
                        drop = True

                    if self.gems[i] == 0:
                        self.gems[i] = self.gems[move_i]
                        self.gems[move_i] = 0
                        drop = True

                    if drop:
                        drop_gems[i] = drop_gems.get(i, 0) + 69 # pas certain, doit etre 80

                    if self.gems[i] == 0:
                        has_empty = True

                if not has_empty:
                    break

        bomb_index = None
        if drop_gems and self.current_score >= self.next_bomb:
            self.next_bomb += 5000
            bomb_index = random.choice(range(64))

        # now drop gems
        drop_gems = sorted(drop_gems.items(), reverse=True)
        pw = range(0, len(drop_gems)+1, 3)
        ipw = 0
        for i, posy in drop_gems:
            li = self.container.getListItem(i)
            li.setLabel2(str(self.gems[i]))
            li.setProperty("gem_vs_gem", "")
            #
            image = GEM_IMG.format(self.gems[i])
            if bool(li.getProperty("dynamite")):
                li.setProperty("dynamite", "1")
                image = DYNAMITE_GEM.format(self.gems[i])
            #
            c = self.gemControl(i)
            c.setImage(image)
            c.setAnimations([('conditional', ANIM_DROP_GEM.format(posy))])
            #
            if ipw in pw:
                playSound(DIAMOND_WAV)
            ipw += 1

        if bomb_index is not None:
            while True:
                li = self.container.getListItem(bomb_index)
                if not bool(li.getProperty("dynamite")):
                    li.setProperty("dynamite", "1")
                    self.gemControl(bomb_index).setImage(DYNAMITE_GEM.format(self.gems[bomb_index]))
                    break
                bomb_index = random.choice(range(64))

        # sleep
        if _sleep:
            time.sleep(.5)
            # re-add sleeping time in time left
            self.time_left += .5

    def sendClick(self, controlID):
        try: self.onClick(controlID)
        except: print_exc()

    def onClick(self, controlID):
        try:
            if controlID == 11:
                # pause game
                self.paused = not self.paused
                self.pause_button.setSelected(self.paused)

            elif controlID == 20:
                # show scores
                if self.mode:
                    self.sendClick(11)
                xbmc.executebuiltin("RunScript(script.xbmc.games.scores,{})".format(ADDON_ID))
                # sys.argv = PY_SCORES_ARGV
                # execfile(PY_SCORES)

            elif controlID == 6:
                # help, get hints
                if self._stop or self.lock or self.paused or self.current_score <= self.help_pts:
                    return None
                hint = utils.get_hint(self.gems[:])
                if hint is not None:
                    self.current_score -= self.help_pts
                    self.setContainerProperty("current_score", str(self.current_score))
                    
                    self.gemControl(hint[0]).setAnimations(ANIM_HINT)
                    # xbmc.sleep(100)
                    self.gemControl(hint[1]).setAnimations(ANIM_HINT)
                    h1 = self.container.getListItem(hint[0])
                    h2 = self.container.getListItem(hint[1])
                    self.controls_hint += [hint[0], hint[1]]
                    # h1.setProperty("hint_1", "1")
                    # h2.setProperty("hint_2", "1")
                    # self.controls_hint += [h1, h2]

                    self.container.selectItem(hint[1])
                    # self.setFocusId(50)
                else:
                    xbmcgui.Dialog().notification("KoDiamond", "No Hint Found! :(", xbmcgui.NOTIFICATION_ERROR, 2000)
                    self.gems[-8:] = [0]*8
                    self.move_gems()

                    rem_gems = utils.get_match_gems(self.gems)
                    if not rem_gems:
                        self.sendClick(6)
                    else:
                        self.selected = rem_gems[:3]
                        self.container.selectItem(self.selected[0])
                        self.sendClick(50)

            elif controlID == 50:
                if self._stop or self.lock or self.paused:
                    return None
                self.lock = True
                if len(self.selected) == 3:
                    self.selected = self.selected[:2]
                else:
                    pos = self.container.getSelectedPosition()
                    if pos not in self.selected:
                        self.selected.append(pos)
                    elif pos in self.selected:
                        self.gemControl(pos).setAnimations([]) # reset rotate animation
                        self.container.getListItem(pos).select(0)
                        self.selected = []
                        self.lock = False
                        return None

                if len(self.selected) == 2:
                    # swap gems
                    self.remPTSControl()
                    a, b = self.selected[0], self.selected[1]

                    # get direction to move selected gems
                    ok = True
                    if (a + 1) == b:
                        anim_a, anim_b = ANIM_SWAP_RIGHT
                    elif (a - 1) == b:
                        anim_a, anim_b = ANIM_SWAP_LEFT
                    elif (a + 8) == b:
                        anim_a, anim_b = ANIM_SWAP_DOWN
                    elif (a - 8) == b:
                        anim_a, anim_b = ANIM_SWAP_UP
                    else:
                        ok = False

                    if not ok: # not good selected
                        playSound(BAD_SWAP_WAV)
                        self.selected = [a]
                        self.lock = False
                        return None

                    # first move gems
                    li_a = self.container.getListItem(a)
                    li_b = self.container.getListItem(b)
                    gem_a = int(li_a.getLabel2())
                    gem_b = int(li_b.getLabel2())
                    # print (gem_a, gem_b), self.gems
                    self.gems[a] = gem_b
                    self.gems[b] = gem_a
                    # print self.gems

                    li_a.setLabel2(str(gem_b))
                    li_b.setLabel2(str(gem_a))
                    self.gemControl(a).setAnimations([('conditional', anim_a)])
                    self.gemControl(b).setAnimations([('conditional', anim_b)])

                    # sleep
                    time.sleep(.6)
                    # re-add sleeping time in time left
                    self.time_left += .6

                    for i in self.selected:
                        li = self.container.getListItem(i)
                        li.select(0)
                    self.selected = []
                    # for li in self.controls_hint:
                    #     li.setProperty("hint_1", "")
                    #     li.setProperty("hint_2", "")
                    for i in self.controls_hint:
                        self.gemControl(i).setAnimations([])
                        self.container.getListItem(i)
                    self.controls_hint = []

                    # check match gems
                    rem_gems = utils.get_match_gems(self.gems)
                    if not rem_gems:
                        playSound(BAD_SWAP_WAV)
                        # replace gems selected, not match found
                        li_a.setLabel2(str(gem_a))
                        li_b.setLabel2(str(gem_b))
                        self.gemControl(a).setAnimations([('conditional', anim_a.replace(" end=", " start="))])
                        self.gemControl(b).setAnimations([('conditional', anim_b.replace(" end=", " start="))])
                        self.gems[a] = gem_a
                        self.gems[b] = gem_b
                    else:
                        ca = self.gemControl(a)
                        cb = self.gemControl(b)
                        ca.setImage(GEM_IMG.format(gem_b))
                        cb.setImage(GEM_IMG.format(gem_a))
                        ca.setAnimations(ANIM_STOP_SWAP)
                        cb.setAnimations(ANIM_STOP_SWAP)
                        if bool(li_a.getProperty("dynamite")):
                            rem_gems.append(a)
                        if bool(li_b.getProperty("dynamite")):
                            rem_gems.append(b)
                        while True:
                            # check form (+, L , T) for bonus scores and time
                            PLUS = utils.has_plus(rem_gems)
                            L = utils.has_L(rem_gems)
                            T = utils.has_T(rem_gems)
                            # add bonus time
                            self.time_left += len(rem_gems)/3
                            self.time_left += len(PLUS)+(len(T)*0.75)+(len(L)*0.5)
                            # set bonus score
                            self.current_score += (len(PLUS)*1000)+(len(T)*750)+(len(L)*500)

                            explosion = []
                            # Set gem vs gem
                            while True:
                                pos = rem_gems[0]
                                li = self.container.getListItem(pos)
                                li.setProperty("gem_vs_gem", "1")
                                self.gemControl(pos).setAnimations(ANIM_ZOOM_OUT)
                                # set current score
                                gem_id = li.getLabel2()
                                pts = int(gem_id) * 25
                                str_pts = "[COLOR=blue][B]{}[/B][/COLOR]".format(pts)
                                if pos in L: str_pts = "[COLOR=red][B]500[/B][/COLOR]"
                                if pos in T: str_pts = "[COLOR=silver][B]750[/B][/COLOR]"
                                if pos in PLUS: str_pts = "[COLOR=gold][B]1000[/B][/COLOR]"
                                self.addPTSControl(str_pts, pos)
                                self.current_score += pts
                                self.setContainerProperty("current_score", str(self.current_score))
                                # add extra bonus time .33 for id 7
                                if gem_id == "7": self.time_left += 0.333333333333
                                # add extra bonus time .55 for id 8
                                if gem_id == "8": self.time_left += 0.555555555555
                                # set blanked
                                if li.getProperty("blanked") != "1":
                                    li.setProperty("blanked", "1")
                                    self.blanked += 1

                                self.gems[pos] = 0
                                del rem_gems[0]

                                if bool(li.getProperty("dynamite")):
                                    li.setProperty("dynamite", "")
                                    self.current_score += 1000
                                    new_explosion = utils.get_explosion(pos)
                                    new_rem_gems = []
                                    for i in rem_gems:
                                        if i not in new_explosion:
                                            new_rem_gems.append(i)
                                    rem_gems = new_explosion + new_rem_gems
                                    explosion += new_explosion
                                    playSound(BOMB_WAV)

                                if pos in explosion:
                                    self.gemControl(pos).setImage("explosion.gif")

                                if not rem_gems:
                                    break

                            #if explosion:
                            #    playSound(BOMB_WAV)

                            # sleep
                            time.sleep(1)
                            # re-add sleeping time in time left
                            self.time_left += 1

                            # now add new gems
                            if not self.gems_id:
                                break

                            self.move_gems()

                            rem_gems = utils.get_match_gems(self.gems)

                            if not rem_gems:
                                break

                    self.game_statut()
                else:
                    self.gemControl(pos).setAnimations(ANIM_FIRST_SELECTED)
                    li = self.container.getListItem(pos)
                    li.select(1)
                self.lock = False

            elif controlID in self.mode_ids:
                if not self.getControl(controlID).isSelected():
                    self._stop_game()
                    for i in self.mode_ids:
                        self.getControl(i).setEnabled(1)
                else:
                    for i in self.mode_ids:
                        self.getControl(i).setEnabled(i == controlID)
                    self.pause_button.setSelected(0)
                    self.paused = False

                    self.mode = self.mode_dict.get(controlID) or ""
                    self.help_pts = self.help_dict.get(controlID) or 250
                    self.lock = False
                    self._stop = False
                    self.blanked = 0
                    self.current_score = 0
                    self.next_bomb = 5000
                    self.setContainerProperty("lose", "")
                    self.setContainerProperty("winning", "")
                    self.setContainerProperty("current_score", "0")
                    self.setContainerProperty("help_pts", str(self.help_pts))

                    hi_score = 0
                    try:
                        scores = gamesdb.getScores(ADDON_ID, 1, 1)
                        for score in scores:
                            if score["strMode"] == self.mode:
                                hi_score = score["score"]
                    except:
                        print_exc()
                    self.setContainerProperty("hi_score", str(hi_score))

                    self.time_left = self.time_allowed

                    self.gems_id = range(1, (controlID - 1))
                    random.shuffle(self.gems_id)
                    self.gems = [0]*64
                    self.remPTSControl()
                    self.container.reset()
                    for pos in range(64):
                        self.gemControl(pos).setImage("")
                        li = xbmcgui.ListItem("", "0")
                        self.container.addItem(li)

                    self.move_gems(False)
                    time.sleep(1)

                    # remove match gems on start new game
                    while True:
                        rem_gems = utils.get_match_gems(self.gems)
                        if not rem_gems: break

                        for pos in rem_gems:
                            self.gems[pos] = 0
                        self.move_gems(False)

                    pos = random.choice(range(64))
                    self.container.selectItem(pos)

                    for s in ["1", "2", "3", "GO!"]:
                        time.sleep(.5)
                        self.setContainerProperty("countdown", s)
                        time.sleep(.75)
                        self.setContainerProperty("countdown", "")

                    self.setFocusId(50)
                    self.timer()
        except:
            self.lock = False
            print_exc()

    def onAction(self, action):
        if action in CLOSE_DIALOG:
            self._close_dialog()
        else:
            # keyboard action
            buttonCode = action.getButtonCode()
            if buttonCode:
                self.onKeyboardAction((buttonCode & 0xFF))
            #xbmc.log("onAction(id={} bcode={})".format(action.getId(), buttonCode), xbmc.LOGNOTICE)

    def onKeyboardAction(self, actionID):
        # keyboard action
        if (actionID == ord('H')): # H was pressed, get hint
            self.sendClick(6)
        elif (actionID == ord('P')): # P was pressed, pause game
            self.sendClick(11)
        elif (actionID == ord('W')): # W was pressed, show scores
            self.sendClick(10)

    def _close_dialog(self):
        self._stop_game()
        self.close()


wd = Diamond()
wd.doModal()
del wd
