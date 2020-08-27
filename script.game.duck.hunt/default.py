
# Modules general
import os
import sys
import time
import random
from traceback import print_exc
from threading import Lock, Thread, Timer
from datetime import date, timedelta

# Modules XBMC
import xbmc
import xbmcgui
import xbmcvfs
from xbmcaddon import Addon


# constants
ADDON     = Addon( "script.game.duck.hunt" )
ADDON_ID  = ADDON.getAddonInfo( "id" )
ADDON_DIR = ADDON.getAddonInfo( "path" )

# Modules Custom
GAME_ID = ADDON_ID
import gamesdb # from module script.xbmc.games.scores
from sprites import *


# https://raw.github.com/xbmc/xbmc/master/xbmc/input/Key.h
ACTION_PARENT_DIR    =   9
ACTION_PREVIOUS_MENU =  10
ACTION_SHOW_INFO     =  11
ACTION_PAUSE         =  12
ACTION_NAV_BACK      =  92
ACTION_MOUSE_MOVE    = 107
ACTION_CONTEXT_MENU  = 117
ACTION_BUILT_IN      = 122
CLOSE_GAME           = [ ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK, ACTION_CONTEXT_MENU ]


def SFX( wav ):
    if ADDON.getSetting( "playsfx" ) == "false": return
    xbmc.playSFX( os.path.join( ADDON_DIR, "resources", "sounds", wav ) )


def getSpritesDir():
    def _samepath( p1, p2 ):
        return ( os.path.normcase( os.path.abspath( p1 ) ) == os.path.normcase( os.path.abspath( p2 ) ) )

    SPRITES_DIR = ""
    if _samepath( ADDON_DIR, xbmc.translatePath( "special://home/addons/%s/" % ADDON_ID ) ):
        SPRITES_DIR = "special://home/addons/%s/resources/sprites/" % ADDON_ID

    elif _samepath( ADDON_DIR, xbmc.translatePath( "special://xbmc/addons/%s/" % ADDON_ID ) ):
        SPRITES_DIR = "special://xbmc/addons/%s/resources/sprites/" % ADDON_ID

    if not SPRITES_DIR or not xbmcvfs.exists( SPRITES_DIR ):
        SPRITES_DIR = os.path.join( ADDON_DIR, "resources", "sprites" )
    return SPRITES_DIR
SPRITES_DIR  = getSpritesDir()
SPRITES_DOG  = SPRITES_DIR + "dog/"
SPRITES_PROP = "SetProperty(sprites_dir,%s)" % SPRITES_DIR


if hasattr( xbmcgui, "getMousePosition" ):
    getMousePosition = xbmcgui.getMousePosition
else:
    skinWidth, skinHeight = 1280, 720
    def getMousePosition( win ):
        #action.getAmount1-2 VS xbmcgui.getMousePosition
        point_x, point_y = 0, 0
        try:
            #transform the amounts coordinates to this window's coordinates
            #but is not real, if g_guiSkinzoom = (CSettingInt*)g_guiSettings.GetSetting("lookandfeel.skinzoom");
            #for info see https://github.com/xbmc/xbmc/blob/master/xbmc/guilib/GraphicContext.cpp#L568
            point_x = win.amount1 * skinWidth  / float( win.getWidth() )
            point_y = win.amount2 * skinHeight / float( win.getHeight() )
        except:
            print locals()
            print_exc()
        return int( point_x ), int( point_y )



class hunt( xbmcgui.WindowXML ):
    def __init__( self, *args, **kwargs ):
        self.amount1      = kwargs[ "amount1" ]
        self.amount2      = kwargs[ "amount2" ]
        self.gamemode     = kwargs[ "gamemode" ]
        self.hiscore      = kwargs[ "hiscore" ]
        self.update_score = None
        self.score        = 0
        self.perfect      = 0
        self.start_time   = 0
        self.gamestarted  = 0
        self.paused       = False
        self.bird_1_stop  = 0
        self.bird_2_stop  = 0
        self.bird_3_stop  = 0
        self.shooted      = []

    def onInit( self ):
        try:
            xbmc.executebuiltin( SPRITES_PROP )
            self.setProperty( "hiscore", self.hiscore )
            #
            self.cartridge = self.getControl( 150 )
            self.cartridge.addItem( xbmcgui.ListItem( "0", "0" ) )
            #
            self.skeet    = self.getControl( 2000 )
            self.skeetBtn = self.getControl( 2001 )
            #
            self.bird_1          = self.getControl( 100 )
            self.bird_1_width    = self.bird_1.getWidth()
            self.bird_1_height   = self.bird_1.getHeight()
            self.bird_1_setImage = self.getControl( 101 ).setImage
            #
            self.bird_2          = self.getControl( 200 )
            self.bird_2_width    = self.bird_2.getWidth()
            self.bird_2_height   = self.bird_2.getHeight()
            self.bird_2_setImage = self.getControl( 201 ).setImage
            #
            self.bird_3          = self.getControl( 300 )
            self.bird_3_width    = self.bird_3.getWidth()
            self.bird_3_height   = self.bird_3.getHeight()
            self.bird_3_setImage = self.getControl( 301 ).setImage
            #
            self.flying_height = int( ( self.getControl( 1 ).getHeight() - self.bird_1_height ) / 4 * 3 )
            self.flying_width  = self.getControl( 1 ).getWidth()
            self.screensplit   = getSplitScreen( 0, 0, self.flying_width, self.flying_height )
            # pointer
            self.pointer = self.getControl( 1000 )
            self.setPointer()
            #
            self.startGame()
        except:
            print locals()
            print_exc()

    def onFocus( self, controlID ):
        pass

    def wait( self, ms, min=0.001, xtime=time ):
        # ms:   10+
        # min:  0.001s with time module
        # min:  1ms with xbmc module
        # xtime: time/xbmc
        t, s = time.time(), ( ms / 1000.0 )
        while self.gamestarted and s > time.time() - t:
            xtime.sleep( min )

    def timer( self ):
        if self.gamestarted and not xbmc.abortRequested:
            td = timedelta( seconds=( time.time() - self.start_time ) )
            self.setProperty( "time", str( td ).lstrip( "0:" ).split( "." )[ 0 ] or "0" )
            self._stop_timer()
            self.timer_thread = Timer( 1, self.timer, () )
            self.timer_thread.start()

    def _stop_timer( self ):
        try: self.timer_thread.cancel()
        except: pass

    def fire( self ):
        SFX( "gun_shotgun2.WAV" )
        self.setProperty( "fire", "1" )
        xbmc.sleep( 310 )
        self.setProperty( "fire", "" )

    def addBullet( self, bullets=0 ):
        bullets = bullets or int( float( ADDON.getSetting( "bullets" ) ) )
        self.cartridge.reset()
        self.cartridge.addItems( [ xbmcgui.ListItem( str( i ), "[CR]".join( list( str( i ) ) ) ) for i in range( 1, bullets+1 ) ] )
        self.cartridge.selectItem( bullets-1 )

    def onClick( self, controlID ):
        try:
            Thread( target=self.fire ).start()
            if not self.paused and controlID in [ 102, 202, 302, 299 ]:
                self.setFocusId( 299 )
                bulletID = int( self.cartridge.getSelectedItem().getLabel() or "0" )
                if bulletID == 1:
                    self.cartridge.reset()
                    self.cartridge.addItem( xbmcgui.ListItem( "0", "0" ) )

                if bulletID < 1 or not self.gamestarted:
                    return

                if controlID == 299:
                    self.birdHasFear = True
                    #return

                if controlID == 102 and self.gamemode < 4:
                    # stop bird 1
                    self.bird_1_stop = 1

                if controlID == 202 and 2 <= self.gamemode <= 3:
                    # stop bird 2
                    self.bird_2_stop = 1

                if controlID == 302 and self.gamemode == 3:
                    # stop bird 2
                    self.bird_3_stop = 1

        except:
            print locals()
            print_exc()

    def levelUp( self ):
        shooted = sum( self.shooted )
        if hasNextRound( self.gamestarted, shooted ):
            if shooted in [ 10, 12 ]:
                # is perfect add +10000 pts
                if int( self.cartridge.getSelectedItem().getLabel() or "0" ) - int( float( ADDON.getSetting( "bullets" ) ) ) == ( -10, -12 )[ self.gamemode == 3 ]:
                    self.perfect += 1
                    perfect_pts = ( 10000 * self.perfect )
                    self.setProperty( "perfect", str( perfect_pts ) )
                    self.wait( 2000, 1, xbmc )
                    self.score += perfect_pts
                    self.setProperty( "score", str( self.score ) )
                # add bonus pts
                bonus = getPTS( self.gamestarted, BONUS )
                self.setProperty( "bonus", str( bonus ) )
                self.wait( 2000, 1, xbmc )
                self.score += bonus
                self.setProperty( "score", str( self.score ) )

            self.gamestarted += 1
            self.setProperty( "levelup", str( self.gamestarted ) )
            self.wait( 2000, 1, xbmc )
            self.setProperty( "gamelevel", str( self.gamestarted ) )

            self.wait( 2000, 1, xbmc )
            self.setProperty( "levelup", "" )
            self.setProperty( "perfect", "" )
            self.setProperty( "bonus", "" )

            return True

    def startGame( self ):
        if not self.gamestarted:
            if self.gamemode == 4:
                self.startGameC()
            else:
                self.startGameABX()


    def startGameABX( self ):
        self.setFocusId( 299 )

        self.gamestarted = 1
        self.score       = 0

        if self.gamemode == 2: self.setProperty( "ongameb", "1" )
        if self.gamemode == 3: self.setProperty( "ongamex", "1" )
        self.setProperty( "onnextlevel", "1" )
        self.setProperty( "gamestarted", "1" )
        self.setProperty( "gamelevel", "1" )
        self.setProperty( "score", "0" )
        self.setProperty( "time", "0" )

        # start intro
        self.bird_1.setEnabled( 0 )
        self.bird_2.setEnabled( 0 )
        self.wait( 2000, 1, xbmc )
        SFX( "bigdog.wav" )
        self.wait( 2000, 1, xbmc )
        self.setProperty( "levelup", str( self.gamestarted ) )
        self.wait( 4000, 1, xbmc )
        self.setProperty( "onnextlevel", "" )
        self.setProperty( "levelup", "" )
        self.setProperty( "bonus", "" )
        self.bird_1.setEnabled( 1 )
        self.bird_2.setEnabled( 1 )
        # end intro
        
        self.bird_1.setPosition( -self.bird_1_width, 0 )
        self.bird_2.setPosition( -self.bird_2_width, 0 )
        self.bird_3.setPosition( -self.bird_3_width, 0 )

        self.start_time = time.time()
        self.timer()

        self.commonLock  = Lock()
        self.game_thread = Thread( target=self.onGameABX )
        self.game_thread.start()

    def onGameABX( self ):
        try:
            random.shuffle( self.screensplit )
            wait = 2000.0 / float( self.flying_width + ( self.bird_2_width * 2 ) ) / 1000.0
            step = 1
            dummy_race = [ ( None, None ) ] * 360 #int( 0.35 / wait )

            self.commonLock.acquire()
            while self.gamestarted:
                self.waitPaused()
                self.clearList()
                self.addBullet()
                self.shooted = []

                for i in range( ( 10, 5, 4 )[ self.gamemode - 1 ] ):
                    if not self.gamestarted: break
                    self.waitPaused()
                    self.setFocusId( 299 )

                    self.birdHasFear = False
                    self.setProperty( "bird_escape", "" )

                    self.bird_1_stop = 0
                    bird_1_pts, bird_1_flying, bird_1_shot, bird_1_dropped, bird_1_catched = self.getBirdInfo()
                    hide_race14 = ( "bird1" not in bird_1_flying and "bird3" not in bird_1_flying )
                    hide_race15 = ( "bird2" not in bird_1_flying and "bird3" not in bird_1_flying )
                    b1x1, b1y1 = -self.bird_1_width, random.randrange( 0, self.flying_height )
                    self.bird_1.setPosition( b1x1, b1y1 )
                    self.bird_1_setImage( bird_1_flying )
                    self.setProperty( "flying1_direction", "right" )
                    self.setProperty( "dog_bird1_pull", "" )
                    self.setProperty( "bird1_pts", "" )

                    self.bird_2_stop = 0
                    if self.gamemode > 1:
                        bird_2_pts, bird_2_flying, bird_2_shot, bird_2_dropped, bird_2_catched = self.getBirdInfo()
                        hide_race24 = ( "bird1" not in bird_2_flying and "bird3" not in bird_2_flying )
                        hide_race25 = ( "bird2" not in bird_2_flying and "bird3" not in bird_2_flying )
                        b2x1, b2y1 = self.flying_width, random.randrange( 0, self.flying_height )
                        self.bird_2.setPosition( b2x1, b2y1 )
                        self.bird_2_setImage( bird_2_flying )
                        self.setProperty( "flying2_direction", "left" )
                        self.setProperty( "dog_bird2_pull", "" )
                        self.setProperty( "bird2_pts", "" )
                    
                    self.bird_3_stop = 0
                    if self.gamemode > 2:
                        bird_3_pts, bird_3_flying, bird_3_shot, bird_3_dropped, bird_3_catched = self.getBirdInfo()
                        hide_race34 = ( "bird1" not in bird_3_flying and "bird3" not in bird_3_flying )
                        hide_race35 = ( "bird3" not in bird_3_flying and "bird3" not in bird_3_flying )
                        bird_3_reverse = random.choice( [ False, True ] )
                        b3x1 = ( -self.bird_1_width, self.flying_width )[ bird_3_reverse ]
                        b3y1 = random.randrange( 0, self.flying_height )
                        self.bird_3.setPosition( b3x1, b3y1 )
                        self.bird_3_setImage( bird_3_flying )
                        self.setProperty( "flying3_direction", ( "right", "left" )[ bird_3_reverse ] )
                        self.setProperty( "dog_bird3_pull", "" )
                        self.setProperty( "bird3_pts", "" )
                    
                    race1 = []
                    race2 = []
                    race3 = []
                    race1_count = 0 # max: 7
                    race2_count = 0 # max: 7
                    race3_count = 0 # max: 7
                    if self.gamemode < 2: race2_count = 8
                    if self.gamemode < 3: race3_count = 8

                    birds_catched = []

                    SFX( "Duck1.wav" )
                    while self.gamestarted:
                        self.waitPaused()
                        self.setFocusId( 299 )

                        if not race1 and race1_count <= 7:
                            race1 = self.getRace( b1x1, b1y1, step, race1_count )
                            if   race1_count == 4 and hide_race14: race1 = []
                            elif race1_count == 5 and hide_race15: race1 = []
                            race1_count += 1

                        if race1:
                            b1x1, b1y1 = race1.pop( 0 )
                            try: x2, y2 = race1[ -1 ]
                            except: x2, y2 = b1x1, b1y1

                            if ( b1x1 and b1y1 ) is not None:
                                if bird_1_shot:
                                    flying1_direction = ( "right", "left" )[ b1x1 > x2 ]
                                    if b1y1 > y2+self.bird_1_height: flying1_direction = "top_" + flying1_direction
                                    if y2 > b1y1+self.bird_1_height: flying1_direction = "bottom_" + flying1_direction
                                    self.setProperty( "flying1_direction", flying1_direction )

                                self.bird_1.setPosition( b1x1, b1y1 )
                            if self.birdHasFear and race1_count < 7: race1 = []
                            
                            if self.bird_1_stop and bird_1_shot:
                                self.setProperty( "flying1_direction", flying1_direction.replace( "top_", "" ).replace( "bottom_", "" ) )
                                self.bird_1_setImage( bird_1_shot )
                                race1_count = 7
                                # dummy race for wait 500
                                race1 = dummy_race[ :: ]
                                self.shooted.append( 1 )
                                self.addItem( xbmcgui.ListItem( str( len( self.shooted ) ), "1", bird_1_shot ) )
                                bird_1_shot = None
                                birds_catched.append( bird_1_catched )

                        elif bird_1_dropped and self.bird_1_stop and race1_count >= 7:
                            self.score += bird_1_pts
                            self.setProperty( "score", str( self.score ) )
                            self.setProperty( "bird1_pts", str( bird_1_pts ) )
                            self.bird_1_setImage( bird_1_dropped )
                            bird_1_dropped = None
                            race1 = []

                        elif bird_1_flying and not self.bird_1_stop and race1_count >= 7:
                            self.shooted.append( 0 )
                            self.addItem( xbmcgui.ListItem( str( len( self.shooted ) ), "0", bird_1_flying ) )
                            bird_1_flying = None
                        
                        if self.gamemode > 1:
                            if not race2 and race2_count <= 7 and race1_count > 1:
                                race2 = self.getRace( b2x1, b2y1, step, race2_count, True )
                                if   race2_count == 4 and hide_race24: race2 = []
                                elif race2_count == 5 and hide_race25: race2 = []
                                race2_count += 1

                            if race2:
                                b2x1, b2y1 = race2.pop( 0 )
                                try: x2, y2 = race2[ -1 ]
                                except: x2, y2 = b2x1, b2y1

                                if ( b2x1 and b2y1 ) is not None:
                                    if bird_2_shot:
                                        flying2_direction = ( "right", "left" )[ b2x1 > x2 ]
                                        if b2y1 > y2+self.bird_2_height: flying2_direction = "top_" + flying2_direction
                                        if y2 > b2y1+self.bird_2_height: flying2_direction = "bottom_" + flying2_direction
                                        self.setProperty( "flying2_direction", flying2_direction )

                                    self.bird_2.setPosition( b2x1, b2y1 )
                                if self.birdHasFear and race2_count < 7: race2 = []
                            
                                if self.bird_2_stop and bird_2_shot:
                                    self.setProperty( "flying2_direction", flying2_direction.replace( "top_", "" ).replace( "bottom_", "" ) )
                                    self.bird_2_setImage( bird_2_shot )
                                    race2_count = 7
                                    # dummy race for wait 500
                                    race2 = dummy_race[ :: ]
                                    self.shooted.append( 1 )
                                    self.addItem( xbmcgui.ListItem( str( len( self.shooted ) ), "1", bird_2_shot ) )
                                    bird_2_shot = None
                                    birds_catched.append( bird_2_catched )

                            elif bird_2_dropped and self.bird_2_stop and race2_count >= 7:
                                self.score += bird_2_pts
                                self.setProperty( "score", str( self.score ) )
                                self.setProperty( "bird2_pts", str( bird_2_pts ) )
                                self.bird_2_setImage( bird_2_dropped )
                                bird_2_dropped = None
                                race2 = []
                                
                            elif bird_2_flying and not self.bird_2_stop and race2_count >= 7:
                                self.shooted.append( 0 )
                                self.addItem( xbmcgui.ListItem( str( len( self.shooted ) ), "0", bird_2_flying ) )
                                bird_2_flying = None

                        if self.gamemode > 2:
                            if not race3 and race3_count <= 7 and race2_count > 1:
                                race3 = self.getRace( b3x1, b3y1, step, race3_count, bird_3_reverse )
                                if   race3_count == 4 and hide_race34: race3 = []
                                elif race3_count == 5 and hide_race35: race3 = []
                                race3_count += 1

                            if race3:
                                b3x1, b3y1 = race3.pop( 0 )
                                try: x2, y2 = race3[ -1 ]
                                except: x2, y2 = b3x1, b3y1

                                if ( b3x1 and b3y1 ) is not None:
                                    if bird_3_shot:
                                        flying3_direction = ( "right", "left" )[ b3x1 > x2 ]
                                        if b3y1 > y2+self.bird_3_height: flying3_direction = "top_" + flying3_direction
                                        if y2 > b3y1+self.bird_3_height: flying3_direction = "bottom_" + flying3_direction
                                        self.setProperty( "flying3_direction", flying3_direction )

                                    self.bird_3.setPosition( b3x1, b3y1 )
                                if self.birdHasFear and race3_count < 7: race3 = []
                            
                                if self.bird_3_stop and bird_3_shot:
                                    self.setProperty( "flying3_direction", flying3_direction.replace( "top_", "" ).replace( "bottom_", "" ) )
                                    self.bird_3_setImage( bird_3_shot )
                                    race3_count = 7
                                    # dummy race for wait 500
                                    race3 = dummy_race[ :: ]
                                    self.shooted.append( 1 )
                                    self.addItem( xbmcgui.ListItem( str( len( self.shooted ) ), "1", bird_3_shot ) )
                                    bird_3_shot = None
                                    birds_catched.append( bird_3_catched )

                            elif bird_3_dropped and self.bird_3_stop and race3_count >= 7:
                                self.score += bird_3_pts
                                self.setProperty( "score", str( self.score ) )
                                self.setProperty( "bird3_pts", str( bird_3_pts ) )
                                self.bird_3_setImage( bird_3_dropped )
                                bird_3_dropped = None
                                race3 = []
                                
                            elif bird_3_flying and not self.bird_3_stop and race3_count >= 7:
                                self.shooted.append( 0 )
                                self.addItem( xbmcgui.ListItem( str( len( self.shooted ) ), "0", bird_3_flying ) )
                                bird_3_flying = None

                        if self.birdHasFear: self.birdHasFear = False
                        if race1_count > 7 and race2_count > 7 and race3_count > 7: break
                        time.sleep( wait ) # same min = 1ms (.001) on win32

                    for i in range( 1, 4 ): self.setProperty( "bird_%i_catched" % ( i + 1 ), "" )
                    if xbmc.getCondVisibility( "IsEmpty(Window.Property(dog_pulled))" ):
                        n_birds = len( birds_catched )
                        self.wait( 1000, 1, xbmc )
                        if not n_birds:
                            self.setProperty( "bird_escape", "1" )
                            SFX( "07_laugh.wav" )
                        else:
                            self.setProperty( "dog_bird%i_pull" % n_birds, "1" )
                            for i, catched in enumerate( birds_catched ):
                                self.setProperty( "bird_%i_catched" % ( i + 1 ), SPRITES_DOG + catched )
                        self.wait( 2000, 1, xbmc )

                    self.wait( 1000 )
                    self.setProperty( "bird_escape", "" )
                    self.setProperty( "dog_bird1_pull", "" )
                    self.setProperty( "dog_bird2_pull", "" )
                    self.setProperty( "dog_bird3_pull", "" )
                self.wait( 1000 )
                if self.gamestarted and not self.levelUp():
                    break
            self.setProperty( "gameover", "1" )
            self.wait( 1200 )
        except SystemExit:
            self.gamestarted = 0
        except:
            print locals()
            print_exc()

        if not xbmc.abortRequested:
            if self.gamestarted:
                self.addScore()
            self.stopGame()

    def getBirdInfo( self ):
        random.shuffle( BIRDS )
        bird = random.choice( BIRDS )
        return getPTS( self.gamestarted, bird ), bird[ "flying" ], bird[ "shot" ], bird[ "dropped" ], bird[ "catch" ]

    def getRace( self, x1, y1, step, race=0, reverse=False ):
        slide = []
        if race <=3:
            x, y, w, h = self.screensplit[ race ]
            x2, y2 = randomPosition( x, y, w, h )
            slide = getSlideCoords( x1, y1, x2, y2, step )
        elif race == 4:
            slide = Circle( x1, y1, int( y1 / 2.0 ) ).coords
            if reverse: slide = slide[ ::-1 ]
        elif race == 5:
            slide = Circle( x1, y1, -int( ( self.flying_height - y1 ) / 2.0 ) ).coords
            if reverse: slide = slide[ ::-1 ]
        elif race == 6:
            x2 = self.flying_width
            if reverse: x2 = -self.bird_2_width
            slide = getSlideCoords( x1, y1, x2, y1, step )

        return slide

    def startGameC( self ):
        self.commonLock  = Lock()
        self.game_thread = Thread( target=self.onGameC )
        self.game_thread.setDaemon( True )
        self.game_thread.start()

    def onGameC( self ):
        try:
            self.setFocusId( 299 )

            self.gamestarted = 1
            self.score       = 0

            self.setProperty( "ongamec", "1" )
            self.setProperty( "gamelevel", "1" )
            self.setProperty( "score", "0" )
            self.setProperty( "time", "0" )

            self.start_time = time.time()
            self.timer()

            self.commonLock.acquire()
            while self.gamestarted:
                self.waitPaused()
                self.clearList()
                self.addBullet()
                self.shooted = []
                pts = getPTS( self.gamestarted, DISC )
                self.wait( 1000, 1, xbmc )

                for i in range( 10 ):
                    if not self.gamestarted: break
                    self.waitPaused()
                    #self.addBullet( 3 )
                    self.setProperty( "skeet_pts", "" )
                    self.skeetBtn.setSelected( 0 )
                    SFX( "15_skeet_1.wav" )
                    pts_added = False

                    CIRCLE = Circle( 592, 1220, random.randrange( 490, 610, 10 ), step=2 )
                    for coord in random.choice( [ CIRCLE.coords, CIRCLE.coords[ ::-1 ] ] ):
                        if not self.gamestarted: break
                        self.waitPaused()
                        if coord[ 1 ] > 720: continue
                        self.skeet.setPosition( *map( int, coord ) )
                        xbmc.sleep( 3 )

                        if not pts_added and self.skeetBtn.isSelected():
                            pts_added = True
                            self.score += pts
                            self.setProperty( "skeet_pts", str( pts ) )
                            self.setProperty( "score", str( self.score ) )
                            self.addItem( xbmcgui.ListItem( str( i ), "1", "special://xbmc/media/icon32x32.png" ) )
                            self.shooted.append( 1 )
                            self.setFocusId( 299 )

                    if not self.skeetBtn.isSelected():
                        self.addItem( xbmcgui.ListItem( str( i ), "0", "special://xbmc/media/icon32x32.png" ) )
                        self.shooted.append( 0 )
                    self.wait( 1000, 1, xbmc )

                self.wait( 1000, 1, xbmc )
                if self.gamestarted and not self.levelUp():
                    break
            self.setProperty( "gameover", "1" )
            self.wait( 1200 )
        except SystemExit:
            self.gamestarted = 0
        except:
            print locals()
            print_exc()

        if not xbmc.abortRequested:
            if self.gamestarted:
                self.addScore()
            self.stopGame()

    def addScore( self ):
        try:
            current_score = self.getProperty( "score" ) or xbmc.getInfoLabel( 'Container(50).Property(score)' )
            if current_score > "0":
                # new score
                self.update_score = {
                    "strNickName":   "",
                    "score":         int( current_score ),
                    "level":         int( self.getProperty( "gamelevel" ) or xbmc.getInfoLabel( 'Container(50).Property(gamelevel)' ) ),
                    "perfect":       int( self.perfect ),
                    "strMode":       "Game " + ( "A", "B", "X", "C" )[ self.gamemode - 1 ],
                    "strTimePlayed": str( self.getProperty( "time" ) or xbmc.getInfoLabel( 'Container(50).Property(time)' ) ),
                    "strDate":       str( date.today() ),
                    "strGameId":     ADDON_ID,
                    }
        except:
            print locals()
            print_exc()

    def waitPaused( self ):
        while self.paused and self.gamestarted:
            self.wait( 500, 1, xbmc )

    def pause( self ):
        self.paused = not self.paused
        self.setProperty( "paused", "" )
        if self.paused:
            self.setProperty( "paused", "1" )

    def setPointer( self ):
        self.pointer.setPosition( *getMousePosition( self ) )

    def onAction( self, action ):
        if xbmc.abortRequested:
            self.gamestarted = 0
        try:
            if action == ACTION_BUILT_IN and self.gamestarted:
                xbmc.sleep( 10 )
                # close all dialog, because xbmc freeze
                #if xbmc.getCondVisibility( 'Window.IsVisible(shutdownmenu)' ):
                xbmc.executebuiltin( 'Dialog.Close(all,true)' )
                #print "Window.IsVisible(shutdownmenu) -> Dialog.Close(shutdownmenu)"

            if action == ACTION_MOUSE_MOVE:
                #amount used if not xbmcgui hasattr getMousePosition
                self.amount1 = action.getAmount1()
                self.amount2 = action.getAmount2()
                self.setPointer()

            elif action == ACTION_PAUSE and self.gamestarted:
                SFX( "11_pauze.wav" )
                self.pause()

            elif action in CLOSE_GAME:
                self.stopGame()

            else:
                # keyboard action
                buttonCode = action.getButtonCode()
                if not buttonCode: return
                self.onKeyboardAction( ( buttonCode & 0xFF ) )
        except:
            print locals()
            print_exc()

    def onKeyboardAction( self, keyID ):
        #print "keyboard action (%r,%r,%s)" % ( keyID, ord( keyID ), chr( keyID ) )
        if keyID == 137: # end was pressed, stop game
            self.stopGame()

    def releaseLock( self ):
        try: self.commonLock.release()
        except: pass

    def stopGame( self ):
        self.gamestarted = 0
        if self.paused: self.pause()
        self._stop_timer()
        self.releaseLock()
        try:
            while self.game_thread.isAlive():
                self.game_thread.join( 0 )
                time.sleep( 0.02 )
        except: pass
        xbmc.sleep( 1000 )
        self.close()


class duck( xbmcgui.WindowXML ):
    def __init__( self, *args, **kwargs ):
        self.username = ""
        self.setListItems()
        self.setHiScores()
        self.isStarted = False

    def setListItems( self ):
        self.listitems = [
            xbmcgui.ListItem( "GAME A   1 DUCK" ),
            xbmcgui.ListItem( "GAME B   2 DUCKS" ),
            xbmcgui.ListItem( "GAME X   3 DUCKS" ),
            xbmcgui.ListItem( "GAME C   CLAY SHOOTING" ),
            xbmcgui.ListItem( "SCORES" ),
            xbmcgui.ListItem( xbmc.getLocalizedString( 5 ) ),
            xbmcgui.ListItem( xbmc.getLocalizedString( 13009 ) ),
            xbmcgui.ListItem( "INSTRUCTIONS" )
            ]

    def onInit( self ):
        try:
            if not self.isStarted:
                self.isStarted = True
                xbmc.executebuiltin( SPRITES_PROP )
                # add menu
                self.mainMenu = self.getControl( 9000 )
                self.mainMenu.addItems( self.listitems )
                self.setFocus( self.mainMenu )
                #
                self.infoMenu = self.getControl( 250 )
                #
                self.getControl( 150 ).reset()
                bullets = 3 #int( float( ADDON.getSetting( "bullets" ) ) )
                self.getControl( 150 ).addItems( [ xbmcgui.ListItem( str( i ), "[CR]".join( list( str( i ) ) ) ) for i in range( 1, bullets+1 ) ] )
                self.getControl( 150 ).selectItem( bullets-1 )
                # pointer
                self.pointer = self.getControl( 1000 )
                #amount used if not xbmcgui hasattr getMousePosition
                self.amount1, self.amount2 = int( round( self.getWidth() / 2.0 ) ), int( round( self.getHeight() / 2.0 ) )
                #
                SFX( "17_start_game.wav" )
            #
            self.setPointer()
        except:
            print locals()
            print_exc()

    def setHiScores( self, reset=False ):
        try:
            if reset:
                pos = self.mainMenu.getSelectedPosition()
                self.setListItems()
                self.mainMenu.reset()
                self.mainMenu.addItems( self.listitems )
                self.mainMenu.selectItem( pos )
                self.setFocus( self.mainMenu )

            i_mode = { "Game A": 0, "Game B": 1, "Game X": 2, "Game C": 3 }
            self.scores = gamesdb.getScores( ADDON_ID, 1, 1 )
            for score in self.scores:
                li = self.listitems[ i_mode[ score[ "strMode" ] ] ]
                li.setLabel2( str( score[ "score" ] ) )
                if score[ "strAvatar" ]: li.setIconImage( score[ "strAvatar" ] )
                li.setProperty( "name",       score[ "strNickName" ] )
                li.setProperty( "idUser",     str( score[ "idUser" ] ) )
                li.setProperty( "idScore",    str( score[ "idScore" ] ) )
                li.setProperty( "score",      str( score[ "score" ] ) )
                li.setProperty( "level",      str( score[ "level" ]    or "" ) )
                li.setProperty( "perfect",    str( score[ "perfect" ]  or "" ) )
                li.setProperty( "mode",       score[ "strMode" ]       or "" )
                li.setProperty( "timeplayed", score[ "strTimePlayed" ] or "" )
                li.setProperty( "date",       score[ "strDate" ]       or "" )
                li.setProperty( "online",     str( score[ "online" ]   or "" ) )
        except:
            print locals()
            print_exc()

    def onFocus( self, controlID ):
        pass

    def fire( self ):
        SFX( "gun_shotgun2.WAV" )
        self.setProperty( "fire", "1" )
        xbmc.executebuiltin( "control.move(150,-1)" )
        xbmc.sleep( 310 )
        self.setProperty( "fire", "" )

    def onClick( self, controlID ):
        try:
            Thread( target=self.fire ).start()
            if controlID == 9000:
                selected = self.mainMenu.getSelectedPosition()

                if 0 <= selected <= 3:
                    hiscore = self.mainMenu.getSelectedItem().getLabel2()
                    h = hunt( "script-duckhunt.xml", ADDON_DIR, gamemode=( selected + 1 ), hiscore=hiscore, amount1=self.amount1, amount2=self.amount2 )
                    h.doModal()
                    update_score = h.update_score
                    self.amount1, self.amount2 = h.amount1, h.amount2
                    del h
                    self.setPointer()
                    SFX( "17_start_game.wav" )
                    if update_score:
                        self.updateScore( update_score )

                elif selected == 4:
                    xbmc.executebuiltin( "RunScript(script.xbmc.games.scores,%s)" % ADDON_ID )

                elif selected == 5:
                    ADDON.openSettings()

                elif selected == 6:
                    self._close_game()

                elif selected == 7:
                    self.info()
        except:
            print locals()
            print_exc()

    def updateScore( self, score ):
        # update score
        xbmc.sleep( 500 )
        kb = xbmc.Keyboard( self.username, xbmc.getLocalizedString( 1019 ) )
        kb.doModal()
        if kb.isConfirmed():
            username = kb.getText()
            if bool( username ):
                self.username = username
                score[ "strNickName" ] = self.username
                OK, idScore = gamesdb.addScore( score )
                if idScore > -1: self.setHiScores( True )

    def info( self ):
        self.infoMenu.reset()
        # line 1
        for label in [ "Duck", "Rounds[CR]1 - 5", "Rounds[CR]6 - 10", "Rounds[CR]11 - 15", "Rounds[CR]16 - 20", "Rounds[CR]21 - 99" ]:
            self.infoMenu.addItem( xbmcgui.ListItem( label ) )

        # line 2, 3, 4
        for bird in [ BLACK_BIRD, BLUE_BIRD, RED_BIRD ]:
            self.infoMenu.addItem( xbmcgui.ListItem( "", "", bird[ "flying" ] ) )
            for pts in [ "pts1", "pts2", "pts3", "pts4", "pts5" ]:
                self.infoMenu.addItem( xbmcgui.ListItem( str( bird[ pts ] ) ) )

        # line 5
        self.infoMenu.addItem( xbmcgui.ListItem( "Discs" ) )
        for pts in [ "pts1", "pts2", "pts3", "pts4", "pts5" ]:
            self.infoMenu.addItem( xbmcgui.ListItem( str( DISC[ pts ] ) ) )

        # line 6
        self.infoMenu.addItem( xbmcgui.ListItem( "Bonus" ) )
        for pts in [ "pts1", "pts2", "pts3", "pts4", "pts5" ]:
            self.infoMenu.addItem( xbmcgui.ListItem( str( BONUS[ pts ] ) ) )
        self.setFocusId( 9001 )

    def resetInfo( self ):
        self.infoMenu.reset()
        xbmc.sleep( 1000 )
        self.setFocusId( 9000 )

    def setPointer( self ):
        self.pointer.setPosition( *getMousePosition( self ) )

    def onAction( self, action ):
        try:
            if action == ACTION_MOUSE_MOVE:
                #amount used if not xbmcgui hasattr getMousePosition
                self.amount1 = action.getAmount1()
                self.amount2 = action.getAmount2()
                self.setPointer()

            elif action == ACTION_SHOW_INFO:
                if self.infoMenu.size():
                    self.resetInfo()
                else:
                    self.info()

            elif action in CLOSE_GAME:
                if self.infoMenu.size():
                    self.resetInfo()
                else:
                    self._close_game()
        except:
            print locals()
            print_exc()

    def _close_game( self ):
        self.close()


if __name__ == '__main__':
    #xbmc.executebuiltin( "Skin.SetString(addon-pointer,%s)" % os.path.join( ADDON_DIR, "resources", "skins", "Default", "media", "pointer-hunt.gif" ) )
    #xbmc.executebuiltin( "Skin.SetBool(addon-pointer-centered)" )
    try:
        w = duck( "script-duckhunt-main.xml", ADDON_DIR )
        w.doModal()
        del w
    except:
        print_exc()
    #xbmc.executebuiltin( "Skin.Reset(addon-pointer-centered)" )
    #xbmc.executebuiltin( "Skin.Reset(addon-pointer)" )
