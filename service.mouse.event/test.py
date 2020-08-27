# -*- coding: utf-8 -*-

import os
import re
import sys
import time
from datetime import timedelta
from traceback import print_exc
from collections import namedtuple

import mouse
from resources.lib.geometry import *

STEP_WAIT = 1

try:
    import xbmc
    import xbmcgui
    import skin_utils
    waitForAbort = xbmc.Monitor().waitForAbort # return False or True
    STEP_WAIT *= 5
    ACTIONS_MOUSE = range(xbmcgui.ACTION_MOUSE_START, xbmcgui.ACTION_MOUSE_END+1)
    KEY_JOYSTICK_BUTTONS = range(xbmcgui.KEY_JOYSTICK_BUTTON_A, xbmcgui.KEY_JOYSTICK_BUTTON_GUIDE+1)
except:
    xbmc = None
    waitForAbort = time.sleep # return None

RESOURCES = sys.path[0].replace("\\", "/")+"/resources/"
IMG_DIR   = RESOURCES + "skins/media/"

from decimal import Decimal, DefaultContext

def divide(a, b):
    return DefaultContext.divide(Decimal(a),  Decimal(b))

def isdigitfloat(value):
    value = "0{}0".format(value.lstrip("-"))
    return not [1 for s in value.split(".", 1) if not s.isdigit()]

def time_took(st):
    return str(timedelta(0, (time.clock() - st), 0))

def notif(line1, line2):
    if xbmc:
        xbmcgui.Dialog().notification(line1, line2, xbmcgui.NOTIFICATION_INFO, 3000)
    print "{}: {}".format(line1, line2)

def argb_to_hex(argb=None):
    """
    Convert a 4-tuple of integers, suitable for use in an ``argb()``
    color quadruplet, to a normalized hexadecimal value for that color.

    Examples:

    >>> argb_to_hex((255, 255, 255, 255))
    'ffffffff'
    >>> argb_to_hex((255, 0, 0, 128))
    'ff000080'

    """
    return '%02X%02X%02X%02X' % argb
def random_color():
    return argb_to_hex(tuple([random.randint(0, 255) for i in range(4)]))


class GuiPixels:
    PIXEL_IMG = IMG_DIR+"picker-white2.png"
    def __init__(self):
        res = mouse.get_desktop_res()
        self.kodi_rect = Rect(res.left, res.top, res.right, res.bottom)
        self.kodi_window = mouse.KodiResolution()
        self.get_mouse_position()
        self.controls = []
        if xbmc:
            if xbmc.getCondVisibility('System.HasModalDialog'):
                self.wid = xbmcgui.getCurrentWindowDialogId()
            else:
                self.wid = xbmcgui.getCurrentWindowId()
            self.window = xbmcgui.Window(self.wid)
            #print "getResolution(%r)" % self.window.getResolution()

    def add(self, x, y, wh=10, colordiffuse='0xFFFF0000', transform=True):
        if xbmc:
            if transform:
                # getinfolabel too slow
                #x, y = xbmc.getInfoLabel('$INFO[Window(home).Property(MousePosX)],$INFO[Window(home).Property(MousePosY)]').split(",")
                #x, y = self.get_mouse_position(x, y)
                x, y = self.transformToKodi(x, y)
            diff = Decimal(wh/2.0)
            ctrl = xbmcgui.ControlImage(int(x-diff), int(y-diff), wh, wh, self.PIXEL_IMG, 0, colordiffuse)
            self.window.addControl(ctrl)
            self.controls.append(ctrl)
        return (int(x), int(y))

    def remove(self):
        if self.controls and xbmc:
            if waitForAbort(1):
                return
            try:
                #self.controls.reverse()
                self.window.removeControls(self.controls)
                self.controls = []
            except: pass#print_exc()

    def transformToKodi(self, pt_x, pt_y):
        if xbmc:
            # now transform to kodi
            posx = (pt_x - self.k_left) * self.scalex
            posy = (pt_y - self.k_top) * self.scaley
            
            if skin_utils.SKIN_ZOOM:
                posx -= posx*skin_utils.SKIN_ZOOM
                posy -= posy*skin_utils.SKIN_ZOOM
            return (posx, posy)
        return pt_x, pt_y

    def get_mouse_position(self, x=0, y=0):
        #transform mouse coords to kodi coords
        # get mouse position
        pt_x, pt_y = x, y #mouse.get_position()
        if xbmc:
            # get kodi coords
            fullscreen = xbmc.getCondVisibility('!String.IsEqual(System.ScreenMode,windowed)')
            self.k_left, self.k_top, self.k_width, self.k_height = self.kodi_window.get_position(fullscreen)
            self.kodi_rect = Rect(self.k_left, self.k_top, self.k_width, self.k_height)
            # get/set skin resoluton
            self.skin = skin_utils.get_current_skin_res()
            # get scaling
            self.scalex = divide(self.skin["width"],  self.k_width)
            self.scaley = divide(self.skin["height"], self.k_height)
            # now transform to kodi
            posx = (pt_x - self.k_left) * self.scalex
            posy = (pt_y - self.k_top) * self.scaley
            #return (posx, posy)
            #return self.transformToKodi(pt_x, pt_y)

    def setAnimation(self):
        closewith = 1 if len(self.controls) > 2 else 0
        for s_ctrl, e_ctrl in pairwise(self.controls, closewith):
            x1, y1 = s_ctrl.getPosition()
            x2, y2 = e_ctrl.getPosition()
            w, h   = s_ctrl.getWidth(), s_ctrl.getHeight()
            diff   = (w/2.0) # for center of control
            line   = Line(x1+diff, y1+diff, x2+diff, y2+diff)
            endline = "%i,%i,%i,%i" % (x1, y1, round(line.distance)+w, w)
            anims = [('conditional', 'condition=true effect=rotate center=auto end=%s time=500' % str(line.angle)),
                     ('conditional', 'condition=true effect=zoom tween=linear end=%s time=2000' % (endline))]
            s_ctrl.setAnimations(anims)
            #xbmc.log("setAnimations({})".format(anims), xbmc.LOGNOTICE)

PIXELS = GuiPixels()

class Free(xbmcgui.WindowXMLDialog):
    def __new__(cls,  *args, **kwargs):
        dskin = "Default.{}".format(PIXELS.skin["folder"])
        if not os.path.exists(RESOURCES+"skins/"+dskin):
            dskin = "Default"
        return super(Free, cls).__new__(cls, "script-mouse-test.xml", sys.path[0], dskin)

    def __init__(self, *args, **kwargs):
        super(Free, self).__init__()
        
        PIXELS.window = self
        self.color = random_color()
        #self.amount1 = self.amount2 = 0
        self.lines = []
        self.colorlines = []
        self.locked = False
        self.animationbykodi = kwargs.get("animationbykodi")
        self.track_mouse = kwargs.get("trackmouse")
        self.track_added = False

        if self.animationbykodi or self.track_mouse:
            PIXELS.PIXEL_IMG = IMG_DIR+"picker-white.png"

        #self.testfunction = kwargs.get("testfunction")
            
    def onInit(self):
        self.setProperty('current.color', self.color)
        
        self.list_control = self.getControl(9002)
        self.time_control = self.getControl(150)
        self.anim_control = self.getControl(151)
        self.eline_control = self.getControl(152)
        self.joypointer = self.getControl(2000)
        #self.setJoyPosition(*self.joypointer.getPosition())

        # if self.track_mouse:
            # self.addTrackMouse()
        # if self.testfunction:
            # exec self.testfunction
        
        # *****NEW START HERE*****
        # set listitem
        choices = [("Circle", "circle"),
                   ("Circle[CR]1/2", "circle"),
                   ("Polygon", "polygon"),
                   ("Star", "star"),
                   ("Kodi[CR]Text", "text"),
                   (xbmc.getInfoLabel("$LOCALIZE[156]"), "free"),
                   #(xbmc.getInfoLabel("$LOCALIZE[156][CR]Anim by[CR]Kodi"), "free"),
                   ("Track[CR]Mouse", "track")]

        self.listitems = [xbmcgui.ListItem(*c) for c in choices]
        self.list_control.reset()
        self.list_control.addItems(self.listitems)
        self.list_control.selectItem(6)
        self.listitems[6].select(1)
        self.setProperty('current.style', "track")
        self.addTrackMouse()
        self.setFocusId(9002)
        
        # default value for options
        self.peak_or_vertex_count = 8
        self.circle_extent = 360
        self.radius1 = 200
        self.radius2 = 75
        self.angle = 45
        self.max_radius = int(PIXELS.skin["height"])/2

        control = namedtuple('control', 'edit progress')
        edit = namedtuple('edit', 'ctrl min max')
        progress = namedtuple('progress', 'ctrl property')
        self.edits = {
            101: control(edit(self.getControl(101), 1, 1000),            progress(self.getControl(102), "progress102.color")), # peak/vertex: range 2...????
            111: control(edit(self.getControl(111), 1, self.max_radius), progress(self.getControl(112), "progress112.color")), # radius: range 2...max_radius
            121: control(edit(self.getControl(121), 1, self.max_radius), progress(self.getControl(122), "progress122.color")), # radius 2: range 2...max_radius
            131: control(edit(self.getControl(131), -360, 360),          progress(self.getControl(132), "progress132.color")), # angle: range -360...360
            141: control(edit(self.getControl(141), -360, 360),          progress(self.getControl(142), "progress142.color")), # extent: range -360...360
            }
        self.edits_id = self.edits.keys()
        # xbmc.log("{}".format(self.edits), xbmc.LOGNOTICE)
        for i in self.edits_id: #range(102, 143, 10):
            self.getControl(i+1).setPercent(1)

    def setJoyPosition(self, x, y):
        self.joypointer.setPosition(int(x), int(y))
        self.setProperty('JoyPosX', str(int(x)))
        self.setProperty('JoyPosY', str(int(y)))

    def onFocus(self, controlID):
        pass

    def sendClick(self, controlID):
        try: self.onClick(controlID)
        except: print_exc()

    def onClick(self, controlID):
        # if self.track_added:
            # return

        if not self.track_added and controlID == 21:
            if PIXELS.controls:
                PIXELS.window.removeControl(PIXELS.controls[-1])
                del PIXELS.controls[-1]

        elif controlID == 9002:
            pos = self.list_control.getSelectedPosition()
            item = self.list_control.getListItem(pos)
            if item.isSelected():
                item.select(0)
                self.setProperty('current.style', "")
            else:
                style = item.getLabel2()
                self.setProperty('current.style', style)
                for i, li in enumerate(self.listitems):
                    li.select((i == pos))
                pvc = {"polygon": "Vertex count:", "star": "Peak count:"}.get(style)
                if pvc: self.edits[101].edit.ctrl.setLabel(pvc)

        elif controlID in self.edits_id:
            edit = self.edits[controlID].edit
            value = edit.ctrl.getText()
            if not value:
                return
            if not isdigitfloat(value):
                fake = map(ord, value)
                value = str(sum(fake)/len(fake))
                edit.ctrl.setText(value)

            if "." not in value: value += ".0"
            pct = float(value)*100.0/edit.max
            if float(value) < edit.min:
                edit.ctrl.setText(str(edit.min))
                pct = edit.min*100.0/edit.max
            elif float(value) > edit.max:
                edit.ctrl.setText(str(edit.max))
                pct = 100.0

            progress = self.edits[controlID].progress
            if pct < 0: # or "-" in value:
                self.setProperty(progress.property, "red")
                progress.ctrl.setPercent(int(str(int(pct)).strip("-")))
            else:
                self.setProperty(progress.property, "white")
                progress.ctrl.setPercent(int(pct))

    def addTrackMouse(self):
        x = divide(PIXELS.skin["width"], 2)
        y = divide(PIXELS.skin["height"], 2)
        PIXELS.add(x, y, colordiffuse=random_color(), transform=False)
        self.track_ctrl = PIXELS.controls[-1]
        self.track_x1, self.track_y1 = self.track_ctrl.getPosition()
        self.track_w, self.track_h   = self.track_ctrl.getWidth(), self.track_ctrl.getHeight()
        self.track_diff  = (self.track_w/2.0) # for center of control
        self.track_added = True
        # fake first use
        self.onTrackMouse()
        
    def onTrackMouse(self):
        x2, y2 = map(float, PIXELS.transformToKodi(*mouse.get_position()))
        line   = Line(self.track_x1+self.track_diff, self.track_y1+self.track_diff, x2+self.track_diff, y2+self.track_diff)
        endline = "%i,%i,%i,%i" % (self.track_x1, self.track_y1, round(line.distance)+self.track_w, self.track_w)
        anims = [('conditional', 'condition=true effect=rotate center=auto end=%s time=0' % str(line.angle)),
                 ('conditional', 'condition=true effect=zoom tween=linear end=%s time=0' % (endline))]
        self.track_ctrl.setAnimations(anims)
        self.track_ctrl.setColorDiffuse(random_color())

    def onAction(self, action):
        if self.track_added and action == xbmcgui.ACTION_MOUSE_MOVE:
            self.onTrackMouse()
        #self.amount1, self.amount2 = action.getAmount1(), action.getAmount2()

        if self.locked:# or self.track_added:
            if action == xbmcgui.ACTION_PREVIOUS_MENU:
                self.close()
            return

        if action in ACTIONS_MOUSE:
            self.onMouseAction(action)
        elif action == xbmcgui.ACTION_PREVIOUS_MENU:
            self.close()
        else:
            buttonCode = action.getButtonCode()
            #xbmc.log("onAction(id={}, bcode={}, amount=({},{}))".format(action.getId(), buttonCode, self.amount1, self.amount2), xbmc.LOGNOTICE)
            if not buttonCode: return
            if buttonCode in KEY_JOYSTICK_BUTTONS:
                self.onJoystickAction(buttonCode)
            else:
                self.onKeyboardAction((buttonCode & 0xFF))

    def onMouseAction(self, action):
        if action == xbmcgui.ACTION_MOUSE_MIDDLE_CLICK:
            #PIXELS.remove()
            #self.lines = []
            #self.colorlines = []
            self.drawLines()
        elif action == xbmcgui.ACTION_MOUSE_LEFT_CLICK:
            if xbmc.getCondVisibility("ControlGroup(9000).HasFocus | Control.HasFocus(9001) | Control.HasFocus(8999)"):
                return
            pos = mouse.get_position()
            pt_x, pt_y = PIXELS.add(*pos, colordiffuse=self.color)
            self.lines += [pt_x, pt_y]
            self.colorlines.append(self.color)
        #elif action == xbmcgui.ACTION_MOUSE_RIGHT_CLICK: # hmmm!  right_click auto close window, if container not exists
        #    self.drawLines()
        elif action in [xbmcgui.ACTION_MOUSE_WHEEL_DOWN, xbmcgui.ACTION_MOUSE_WHEEL_UP]:
            self.color = random_color()
            self.setProperty('current.color', self.color)

    def onJoystickAction(self, buttonCode, step=11):
        # https://github.com/xbmc/xbmc/blob/f303c86db9a8bb11dd27983dca64235ad3f95a55/xbmc/input/Key.h#L78
        pt_x, pt_y = self.joypointer.getPosition() # mouse.get_position()
        
        if buttonCode == xbmcgui.KEY_JOYSTICK_BUTTON_BACK:
            # close window
            self.close()
        elif buttonCode == xbmcgui.KEY_JOYSTICK_BUTTON_START:
            # remove pixels
            PIXELS.remove()
            self.lines = []
            self.colorlines = []
        elif buttonCode == xbmcgui.KEY_JOYSTICK_BUTTON_B:
            # draw lines
            self.drawLines()
        elif buttonCode == xbmcgui.KEY_JOYSTICK_BUTTON_X:
            # add pixel to click coords
            pt_x, pt_y = PIXELS.add(pt_x, pt_y, colordiffuse=self.color, transform=False)
            self.lines += [pt_x, pt_y]
            self.colorlines.append(self.color)
        elif buttonCode in [xbmcgui.KEY_JOYSTICK_BUTTON_A, xbmcgui.KEY_JOYSTICK_BUTTON_Y]:
            # random color
            self.color = random_color()
            self.setProperty('current.color', self.color)

        elif buttonCode == xbmcgui.KEY_JOYSTICK_BUTTON_LEFT_THUMB_STICK_UP:
            pt_y = max(pt_y-step, 0)
            self.setJoyPosition(pt_x, pt_y)
        elif buttonCode == xbmcgui.KEY_JOYSTICK_BUTTON_LEFT_THUMB_STICK_DOWN:
            pt_y = min(pt_y+step, int(PIXELS.skin["height"]))
            self.setJoyPosition(pt_x, pt_y)
        elif buttonCode == xbmcgui.KEY_JOYSTICK_BUTTON_LEFT_THUMB_STICK_LEFT:
            pt_x = max(pt_x-step, 0)
            self.setJoyPosition(pt_x, pt_y)
        elif buttonCode == xbmcgui.KEY_JOYSTICK_BUTTON_LEFT_THUMB_STICK_RIGHT:
            pt_x = min(pt_x+step, int(PIXELS.skin["width"]))
            self.setJoyPosition(pt_x, pt_y)
            #mouse.move(pt_x, pt_y) # not work :)

    def onKeyboardAction(self, actionID):
        # keyboard action
        if (actionID == ord('Z')): # Z was pressed, CLEAR LAST CONTROL
            self.sendClick(21)
        elif (actionID == ord('X')): # X was pressed, CLEAR ALL CONTROLS
            PIXELS.remove()
            self.lines = []
            self.colorlines = []

    def drawLines(self):
        if self.animationbykodi:
            PIXELS.setAnimation()
            return
        if len(self.lines) > 4:
            self.locked = True
            try:
                lines = all_points_to_line(self.lines)
                #i = 0
                for c, line in enumerate(lines):
                    color = self.colorlines[c]
                    for pos in line:
                        #mouse.move(*pos)
                        #if i in lwait:
                            #time.sleep(wait)
                        if waitForAbort(.001):
                            break
                        #i += 1
                        PIXELS.add(*pos, colordiffuse=color, transform=False)
                        self.setJoyPosition(*pos)
            except:
                print_exc()
            self.lines = []
            self.colorlines = []
            self.locked = False

def testCircle(radius, extent=None, center=(0, 0), duration=1.0, endswithline=False):
    cy = center[1] + (radius/2)
    circ = Circle(center[0], int(cy), radius, extent)
    circ.removeDouble()
    coords = circ.coords

    totals = len(coords)
    wait = max(.001, duration/(totals+1.0))
    lwait = range(0, totals+1, STEP_WAIT)

    #color = random_color()
    st = time.clock()
    for i, pos in enumerate(coords):
        mouse.move(*pos)
        if i in lwait:
            #time.sleep(wait)
            if waitForAbort(wait):
                break
        PIXELS.add(*pos, colordiffuse=random_color())
    
    half = ""
    if endswithline:
        lines = all_points_to_line(coords[-1]+coords[1])

        t2 = sum([len(l) for l in lines])
        wait = max(.001, duration/(t2+1.0))
        lwait = range(0, t2+1, STEP_WAIT)
        totals += t2

        st = time.clock()
        i = 0
        for line in lines:
            for pos in line:
                mouse.move(*pos)
                if i in lwait:
                    #time.sleep(wait)
                    if waitForAbort(wait):
                        break
                i += 1
                PIXELS.add(*pos, colordiffuse=random_color())
        half = "Half "
        
    notif('Mouse Event - Test %sCircle' % half, "{} points took {}".format(totals, time_took(st)))

def testPolygon(vertex_count, radius, center=(0, 0), angle=0, duration=1.0):
    points = create_polygon(vertex_count, radius, center, angle)
    lines = all_points_to_line(points)

    totals = sum([len(l) for l in lines])
    wait = max(.001, duration/(totals+1.0))
    lwait = range(0, totals+1, STEP_WAIT)

    st = time.clock()
    i = 0
    for line in lines:
        color = random_color()
        for pos in line:
            mouse.move(*pos)
            if i in lwait:
                #time.sleep(wait)
                if waitForAbort(wait):
                    break
            i += 1
            PIXELS.add(*pos, colordiffuse=color)

    notif('Mouse Event - Test Polygon', "{} points took {}".format(totals, time_took(st)))
    
def testStar(peak_count, radius1, radius2, center=(0, 0), angle=0, duration=1.0):
    points = create_star(peak_count, radius1, radius2, center, angle)
    lines = all_points_to_line(points)

    totals = sum([len(l) for l in lines])
    wait = max(.001, duration/(totals+1.0))
    lwait = range(0, totals+1, STEP_WAIT)

    st = time.clock()
    i = 0
    for line in lines:
        color = random_color()
        for pos in line:
            mouse.move(*pos)
            if i in lwait:
                #time.sleep(wait)
                if waitForAbort(wait):
                    break
            i += 1
            PIXELS.add(*pos, colordiffuse=color)

    notif('Mouse Event - Test Star', "{} points took {}".format(totals, time_took(st)))

def testStarAnimated(peak_count, radius1, radius2, center=(0, 0), angle=0, duration=1.0):
    points = create_star(peak_count, radius1, radius2, center, angle)
    totals = len(points)/2
    st = time.clock()
    for pos in zip(points[::2], points[1::2]):
        color = random_color()
        mouse.move(*pos)
        if waitForAbort(.25):
            break
        pos = map(Decimal, pos)
        PIXELS.add(*pos, colordiffuse=color)
    PIXELS.setAnimation()
    notif('Mouse Event - Test Star', "{} points took {}".format(totals, time_took(st)))
    waitForAbort(5)

def testKodiText(radius=88, center=(0, 0), duration=1.0):
    center = PIXELS.kodi_rect.center
    # o points
    o_points = create_polygon(16, radius, (center[0]-100, center[1]), 0)
    # d points 
    d_points  = create_polygon(6, radius, (center[0]+100, center[1]), 30)
    db_points = border(d_points)[2:-2]
    # i points
    i_points  = border(list(db_points), 35)[2:-2]
    ii_points = list(i_points)
    ii_points[1] -= radius/2.0
    ii_points[3] -= radius*2.5
    # resize barre of d
    db_points[1] -= radius
    # barre of K
    k_points  = border(list(db_points), -520)[2:-2]
    k1_points = list(k_points)
    middle    = (k1_points[-1] - k1_points[1])/2.2
    bottom    = k1_points[-1]
    k1_points[0]  += radius*1.5
    k1_points[-1] -= middle
    k2_points      = list(k1_points)
    k2_points[1]   = bottom
    k2_points[-1] -= radius/4.0

    kodi = [(k2_points, random_color(), 20),
            (k1_points, random_color(), 20),
            (k_points,  random_color(), 22),
            (o_points,  random_color(), 20),
            (d_points,  random_color(), 20),
            (db_points, random_color(), 22),
            (i_points,  random_color(), 20),
            (ii_points, random_color(), 22)]
    random.shuffle(kodi)
    st = time.clock()
    _totals = 0
    for points, color, size in kodi:
        lines = all_points_to_line(points)

        totals = sum([len(l) for l in lines])
        _totals += totals 
        wait = max(.001, duration/(totals+1.0))
        lwait = range(0, totals+1, STEP_WAIT)

        i = 0
        for line in lines:
            color = random_color()
            for pos in line:
                mouse.move(*pos)
                if i in lwait:
                    if waitForAbort(wait):
                        break
                i += 1
                PIXELS.add(*pos, wh=size, colordiffuse=color)

    notif('Mouse Event - Test Kodi Text', "{} points took {}".format(_totals, time_took(st)))
    

if (__name__ == "__main__"):
    #m_pos = mouse.get_position()
    w = Free()
    w.doModal()
    del w
    #mouse.move(*m_pos)

