
import os
import time
import random
from datetime import timedelta
from traceback import print_exc
from threading import Thread, Timer

import xbmc
import xbmcgui
import xbmcvfs
from xbmcaddon import Addon

ADDON      = Addon( "script.game.the.walking.dead" )
ADDON_ID   = ADDON.getAddonInfo( 'id' )
ADDON_NAME = ADDON.getAddonInfo( 'name' )
ADDON_DIR  = ADDON.getAddonInfo( 'path' ).decode( 'utf-8' )
ADDON_DATA = xbmc.translatePath( ADDON.getAddonInfo( 'profile' ) ).decode( 'utf-8' )
LangXBMC   = xbmc.getLocalizedString  # XBMC strings

from resources.lib.episodes import *
from resources.lib.game import *

winsound = None
try: import winsound
except: pass


# https://github.com/xbmc/xbmc/blob/master/xbmc/input/Key.h
ACTION_MOVE_LEFT      =   1
ACTION_MOVE_RIGHT     =   2
ACTION_MOVE_UP        =   3
ACTION_MOVE_DOWN      =   4
ACTION_PARENT_DIR     =   9
ACTION_PREVIOUS_MENU  =  10
ACTION_SHOW_INFO      =  11
ACTION_QUEUE_ITEM     =  34
ACTION_NAV_BACK       =  92
ACTION_CONTEXT_MENU   = 117
CLOSE_WINDOW          = [ ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK ]
CLOSE_DIALOG          = [ ACTION_SHOW_INFO, ACTION_CONTEXT_MENU ] + CLOSE_WINDOW


def getSpritesDir():
    def _samepath( p1, p2 ):
        return ( os.path.normcase( os.path.abspath( p1 ) ) == os.path.normcase( os.path.abspath( p2 ) ) )

    SPRITES_DIR = ""
    if _samepath( ADDON_DIR, xbmc.translatePath( "special://home/addons/%s/" % ADDON_ID ) ):
        SPRITES_DIR = "special://home/addons/%s/resources/characters/" % ADDON_ID

    elif _samepath( ADDON_DIR, xbmc.translatePath( "special://xbmc/addons/%s/" % ADDON_ID ) ):
        SPRITES_DIR = "special://xbmc/addons/%s/resources/characters/" % ADDON_ID

    if not SPRITES_DIR or not xbmcvfs.exists( SPRITES_DIR ):
        SPRITES_DIR = os.path.join( ADDON_DIR, "resources", "characters" ) + os.sep

    return SPRITES_DIR
# set our characters dir
SPRITES_DIR  = getSpritesDir()
SPRITES_PROP = "SetProperty(sprites_dir,%s)" % SPRITES_DIR

# set our sprites images
BOX_IMAGES    = [ "barbed.png", "box1.png", "box2.png", "box3.png", "box4.png" ]
WEAPON_IMAGES = [ "gator-machete.png", "balle.png", "colt.png" ]
FOOD_IMAGE    = [ "arm.png", "heart.png" ]

WALKER_IMAGE  = os.path.join( SPRITES_DIR, "walker.png" )
WALKER_IMAGE2 = os.path.join( SPRITES_DIR, "walker-eat.png" )


# set our fanart and tune
def getUserFanartAndTune():
    F, T = "", "http://www.televisiontunes.com/song/download/22529" #"http://www.televisiontunes.com/download.php?f=Walking_Dead"
    s_json = xbmc.executeJSONRPC( '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties": ["art", "fanart", "file"] }, "id": 1}' )
    if ( '"label":"%s"' % ADDON_NAME ) in s_json:
        for tvshow in reversed( json.loads( unicode( s_json, 'utf-8', errors='ignore' ) )[ "result" ].get( 'tvshows' ) or [] ):
            if tvshow[ "label" ] == ADDON_NAME:
                F = tvshow.get( "art", {} ).get( "fanart" ) or tvshow.get( "fanart" ) or ""
                if xbmcvfs.exists( tvshow[ "file" ] + "theme.mp3" ):
                    T = tvshow[ "file" ] + "theme.mp3"
                break
    return F, T
FANART, TUNE = getUserFanartAndTune()


def IsTrue( strBool ):
    return str( strBool ).lower() in [ "1", "true" ]


def time_took( t ):
    return str( timedelta( seconds=( time.time() - t ) ) )


def playTune():
    if not TUNE: return
    playlist = xbmc.PlayList( xbmc.PLAYLIST_MUSIC )
    playlist.clear()
    playlist.add( TUNE )
    xbmc.Player().play( playlist, windowed=True )
    xbmc.executebuiltin( "PlayerControl(RepeatAll)" )


def SFX( wav ):
    if ADDON.getSetting( "playsfx" ) == "false": return
    wav = os.path.join( ADDON_DIR, "resources", "sounds", wav )
    # played = 0
    # if winsound and xbmc.getCondVisibility( "Player.Playing" ):
        # try:
            # winsound.PlaySound( wav, winsound.SND_ASYNC )
            # played = 1
        # except:
            # pass
    # if not played:
    xbmc.playSFX( wav, False )


def getGlobals():
    return globals()

from resources.lib.dialogs import editor, info, selectChapter


class Dead( xbmcgui.WindowXML ):
    def __init__( self, *args, **kwargs ):
        self.started  = False
        self.chapters = Episode1()
        self.setVariables()

    def onInit( self ):
        xbmc.executebuiltin( SPRITES_PROP )
        xbmc.executebuiltin( "SetProperty(fanart,%s)" % FANART )
        playTune()

        self.setProperties()
        self.list_control_game     = self.getControl( 150 )
        self.list_control_peoples  = self.getControl( 250 )
        self.list_control_weapons  = self.getControl( 350 )
        self.list_control_bullets  = self.getControl( 1150 )
        self.control_show_grid     = self.getControl( 31 )
        self.control_critical_zone = self.getControl( 41 )

        if not self.started:
            self.started = True
            self.clearList()
            self.addBullets()

            #ADDON.setSetting( "FirstTimeRun", "false" )
            if not IsTrue( ADDON.getSetting( "FirstTimeRun" ) ):
                self.onClick( 81 )# info()
            
    def setProperties( self ):
        try: mt = str( self.game[ "move_total" ] ) or "0"
        except: mt = "0"
        xbmc.executebuiltin( "SetProperty(move_total,%s)" % mt )
        xbmc.executebuiltin( "SetProperty(move_count,%s)" % str( self.move_count ) )

    def addBullets( self, bullets=6 ):
        if self.list_control_bullets.size() == bullets:
            return
        self.list_control_bullets.reset()
        if bullets:
            listitems = [ xbmcgui.ListItem( str( i ), "[CR]".join( list( str( i ) ) ) ) for i in range( 1, bullets+1 ) ]
            self.list_control_bullets.addItems( listitems )
            self.list_control_bullets.selectItem( bullets-1 )

    def setContainerPeoples( self ):
        listitems = []
        self.list_control_peoples.reset()
        try:
            if self.game:
                for people in self.game[ "peoples" ]:
                    PEOPLE_IMGAGE = os.path.join( PEOPLES_DIR, people[ "image" ] )
                    li = xbmcgui.ListItem( people[ "name" ], people[ "statut" ].lower(), PEOPLE_IMGAGE )
                    listitems.append( li )
        except:
            print_exc()
        if listitems:
            self.list_control_peoples.addItems( listitems )

    def setContainerWeapons( self ):
        listitems = []
        self.list_control_weapons.reset()
        try:
            if self.game:
                # weapons : [ "gator-machete.png", "balle.png", "colt.png" ]
                for item in sorted( set( self.game[ "weapons" ] ) ):
                    if item == "balle.png": continue
                    li = xbmcgui.ListItem( item[ :-4 ], "", item )
                    listitems.append( li )

                self.game[ "weapons" ].sort()
                if self.game[ "weapons" ].count( "colt.png" ):
                    self.addBullets( self.game[ "weapons" ].count( "balle.png" ) )
                    if not self.list_control_bullets.size(): self.game[ "current_weapon" ] = ""

                if not self.game[ "current_weapon" ] and "gator-machete.png" in self.game[ "weapons" ]:
                    self.game[ "current_weapon" ] = "gator-machete"
                xbmc.executebuiltin( "SetProperty(current_weapon,%s)" % self.game[ "current_weapon" ] )
                if "machete" in self.game[ "current_weapon" ]: self.list_control_bullets.reset()
        except:
            print_exc()
        if listitems:
            self.list_control_weapons.addItems( listitems )

    def setVariables( self ):
        self.gameLocked      = False
        self.listitems       = []

        self.fire_position   = -1
        self.player_position = -1
        self.walker_position = []
        self.max_walkers     = 0
        self.move_count      = 0 # reseted on each chapter

        self.player          = {}
        self.people          = {}

    def setGame( self, chapter=1 ):
        self.list_control_game.reset()
        if chapter > len( self.chapters ):
            xbmc.executebuiltin( "ClearProperty(chapter)" )
            xbmc.executebuiltin( "SetProperty(ToBeContinued,1)" )
            xbmc.executebuiltin( "AlarmClock(ToBeContinued,ClearProperty(ToBeContinued),00:30,true)" )
            xbmc.executebuiltin( "SetFocus(1)" ) #self.setFocusId( 7000 )
            return

        self.list_control_game.setEnabled( 0 )
        xbmc.executebuiltin( "SetProperty(chapter,%i)" % chapter )

        self.setVariables()
        self.setProperties()
        self.setContainerPeoples()
        self.setContainerWeapons()

        self.grid = self.chapters.getChapter( chapter )
        for count, id in enumerate( self.grid ):
            listitem = xbmcgui.ListItem( str( count ) )
            listitem.setProperty( "sprites_dir", SPRITES_DIR ) 
            self.listitems.append( listitem )
            if id == 0: continue

            if id == PLAYER_ID:
                self.player_position = count
                self.player = self.game.getPlayer()
                listitem.setProperty( "player", os.path.join( PEOPLES_DIR, self.player[ "image" ] ) )

            elif id == WALKER_ID:
                listitem.setProperty( "walker", "1" )
                self.walker_position += [ count ]
                self.max_walkers     += 1

            elif id == FOOD_ID:
                listitem.setProperty( "food", random.choice( FOOD_IMAGE ) )

            elif id == BOX_ID:
                listitem.setProperty( "box", random.choice( BOX_IMAGES ) )

            elif id == WEAPON_ID:
                listitem.setProperty( "item", random.choice( WEAPON_IMAGES[ :chapter ] ) )

        # set self.critical_zone and self.safe_zone same time.
        self.setCriticalZone()

        # add people in safe zone, if possible
        if self.grid.count( 0 ) and chapter > 1:
            # get people
            self.people = self.game.getPeople()
            if self.people:
                safe = list( self.safe_zone.difference( set( range( self.player_position - 15, self.player_position + 15 ) ) ) )
                if safe:
                    random.shuffle( safe )
                    pos = random.choice( safe )

                    PEOPLE_IMGAGE = os.path.join( PEOPLES_DIR, self.people[ "image" ] )
                    self.listitems[ pos ].setProperty( "people", PEOPLE_IMGAGE )
                    self.grid[ pos ] = PEOPLE_ID

        self.list_control_game.setEnabled( 1 )
        self.list_control_game.addItems( self.listitems )
        self.list_control_game.selectItem( self.player_position )
        self.setFocusId( 150 )

    def setCriticalZone( self ):
        #st = time.time()
        # Get Critical Zone
        self.safe_zone = set()
        self.critical_zone = self.getCriticalZone()
        for i, li in enumerate( self.listitems ):
            li.setProperty( "criticalzone", ( "", "1" )[ i in self.critical_zone ] )
            li.setProperty( "safezone", "" )
            if self.grid[ i ] == NONE_ID and i not in self.critical_zone:
                li.setProperty( "safezone", "1" )
                self.safe_zone.add( i )
        #print time_took( st )

    def getCriticalZone( self ):
        critical_zone = set()
        exclude = [ NONE_ID, PLAYER_ID ] # empty, player
        #include = [ FOOD_ID, BOX_ID, WEAPON_ID, PEOPLE_ID ] # food, box or item or people
        for pos in self.walker_position:
            row = []
            column = []
            if self.grid[ pos ] == WALKER_ID:
                temp_row = []
                d = int( str( "%02d" % pos )[ 0 ] + "0" )
                for i in [ ( d + e ) for e in range( 10 ) ]:
                    temp_row.append( i )
                    if i > pos and self.grid[ i ] not in exclude: #in include:
                        break
                for i in temp_row[ ::-1 ]:
                    row.append( i )
                    if i < pos and self.grid[ i ] not in exclude: #in include:
                        break

                temp_column = []
                d = int( str( "%02d" % pos )[ 1 ] )
                for i in [ ( d + e ) for e in range( 0, 100, 10 ) ]:
                    temp_column.append( i )
                    if i > pos and self.grid[ i ] not in exclude: #in include:
                        break
                for i in temp_column[ ::-1 ]:
                    column.append( i )
                    if i < pos and self.grid[ i ] not in exclude: #in include:
                        break

            elif self.grid[ pos ] == WALKER_EAT_ID:
                for i in [ 10, -10, -1, 1 ]:
                    if i in [ -1, 1 ] and str( "%02d" % pos )[ 0 ] != str( "%02d" % ( pos + i ) )[ 0 ]: # not same row
                        continue
                    if ( 0 <= ( pos + i ) <= 99 ):# and ( self.grid[ pos + i ] == NONE_ID ):
                        critical_zone.add( pos + i )

            if row or column:
                critical_zone.update( row + column )

        #print ( "critical_zone", critical_zone )
        return critical_zone

    def onFocus( self, controlID ):
        pass

    def onClick( self, controlID ):
        if controlID == 250:
            # change player is people selected alive
            pos = self.list_control_peoples.getSelectedPosition()
            if self.game[ "peoples" ][ pos ][ "statut" ] == u'Alive':
                self.game[ "player" ] = pos
                self.player = self.game.getPlayer()
                self.listitems[ self.player_position ].setProperty( "player", os.path.join( PEOPLES_DIR, self.player[ "image" ] ) )
                self.list_control_game.selectItem( self.player_position )
                self.setFocusId( 150 )

        elif controlID == 350:
            # change weapon
            self.game[ "current_weapon" ] = self.list_control_weapons.getSelectedItem().getLabel()
            xbmc.executebuiltin( "SetProperty(current_weapon,%s)" % self.game[ "current_weapon" ] )
            self.setContainerWeapons()
            self.setFocusId( 7000 )

        elif controlID == 7000:
            self.onFire()

        elif controlID == 11:
            # start walking
            while True:
                self.game_name, selected = selectChapter()
                if selected >= 0:
                    # before set game, load saved game
                    self.game = Game( self.game_name )
                    if self.game[ "game_over" ]:
                        xbmcgui.Dialog().ok( ADDON_NAME, "This game is over!", "Select a new game or clear settings." )
                        selected = self.game[ "chapter" ] + 1

                    if selected > self.game[ "chapter" ]:
                        xbmc.sleep( 1000 )
                        continue

                    self.chapter = selected
                    self.control_show_grid.setSelected( self.game[ "showgrid" ] )
                    self.control_critical_zone.setSelected( self.game[ "criticalzone" ] )
                    self.setGame( self.chapter )
                break

        elif controlID == 61:
            editor()
            
        elif controlID == 81:
            self.setFocusId( 7000 )
            info()
            self.setFocusId( 81 )
            
        elif controlID in [ 71, 202 ]:
            if xbmc.getCondVisibility( "!Player.Playing" ): playTune()
            else: xbmc.executebuiltin( "PlayerControl(Stop)" )
        
    def onFire( self ):
        try:
            swing = True
            if self.player_position < 0:
                if xbmc.getCondVisibility( "!SubString(window.property(current_weapon),machete)" ):
                    xbmc.executebuiltin( "control.move(1150,-1)" )
                    SFX( "gun_shotgun2.WAV" )
                    return
                
            if self.player_position > 0:
                ride = []
                direction = xbmc.getInfoLabel( "window.property(weapon_direction)" )
                if direction == u"onup":
                    i = int( str( "%02d" % self.player_position )[ 1 ] )
                    ride = range( i, self.player_position + 10, 10 )[ ::-1 ]

                elif direction == u"ondown":
                    ride = range( self.player_position, 100, 10 )

                elif direction == u"onleft":
                    d = int( str( "%02d" % self.player_position )[ 0 ] ) * 10
                    ride = range( d, self.player_position + 1 )[ ::-1 ]

                elif direction == u"onright":
                    d = int( str( "%02d" % self.player_position )[ 0 ] ) * 10 + 10
                    if d > 100: d = 100
                    ride = range( self.player_position, d )
                
                if not self.list_control_bullets.size():
                    ride = ride[ :2 ]

                else: #if self.game[ "weapons" ].count( "balle.png" ):
                    SFX( "gun_shotgun2.WAV" )
                    del self.game[ "weapons" ][ self.game[ "weapons" ].index( "balle.png" ) ]
                    bullets = self.game[ "weapons" ].count( "balle.png" )
                    if not bullets: self.setContainerWeapons()
                    else: self.addBullets( bullets )
                    swing = False

                self.fire_position = -1
                xbmc.executebuiltin( "SetProperty(onfire,1)" )
                pos = 0
                for pos in ride:
                    self.fire_position = pos
                    self.listitems[ pos ].setProperty( "onfire", "1" )
                    time.sleep( .15 )
                    if self.grid[ pos ] == BOX_ID: break
                    if self.grid[ pos ] in [ WALKER_ID, WALKER_EAT_ID ]:
                        time.sleep( .5 )
                        break
                    self.listitems[ pos ].setProperty( "onfire", "" )
                self.listitems[ pos ].setProperty( "onfire", "" )
                xbmc.executebuiltin( "ClearProperty(onfire)" )
            self.fire_position = -1

            if swing:
                xbmc.sleep( 100 )
                SFX( "SwingMachete.wav" )
        except:
            pass
        
    def move( self, pos=0 ):
        temp_pos = self.player_position + pos
        if self.grid[ temp_pos ] in [ FOOD_ID, BOX_ID ]: # box
            if 0 <= ( temp_pos + pos ) <= 99:
                # check line limit, if pos == -1 or 1
                if pos in [ -1, 1 ] and str( "%02d" % temp_pos )[ 0 ] != str( "%02d" % ( temp_pos + pos ) )[ 0 ]: # not same row
                    pos = 0
                if self.grid[ temp_pos + pos ] in [ WALKER_ID, WALKER_EAT_ID, BOX_ID, WEAPON_ID, PEOPLE_ID ]: # box vs walker or walker eat or box or item
                    pos = 0
                if self.grid[ temp_pos ] == FOOD_ID and self.grid[ temp_pos + pos ] == FOOD_ID: # food vs food
                    pos = 0

                if self.grid[ temp_pos ] == BOX_ID and self.grid[ temp_pos + pos ] == FOOD_ID: # box vs food
                    # move food before box
                    if 0 <= ( temp_pos + pos + pos ) <= 99:
                        # check line limit, if pos == -1 or 1
                        if pos in [ -1, 1 ] and str( "%02d" % temp_pos )[ 0 ] != str( "%02d" % ( temp_pos + pos + pos ) )[ 0 ]: # not same row
                            pos = 0
                        if self.grid[ temp_pos + pos + pos ] > NONE_ID: # box vs food vs X
                            pos = 0

                        # move food
                        if pos != 0:
                            img = self.listitems[ temp_pos + pos ].getProperty( "food" )
                            self.listitems[ temp_pos + pos + pos ].setProperty( "food", img )
                            self.listitems[ temp_pos + pos ].setProperty( "food", "" )
                            self.grid[ temp_pos + pos + pos ] = self.grid[ temp_pos + pos ]

                # move box or food
                if pos != 0:
                    property = ( "box", "food" )[ self.grid[ temp_pos ] == FOOD_ID ]
                    img = self.listitems[ temp_pos ].getProperty( property )
                    self.listitems[ temp_pos + pos ].setProperty( property, img )
                    self.listitems[ temp_pos ].setProperty( property, "" )
                    self.grid[ temp_pos + pos ] = self.grid[ temp_pos ]
            else:
                pos = 0

        return self.player_position + pos

    def onGame( self, actionID ):
        #self.gameover = False
        self.gameLocked = True

        new_pos = self.player_position
        self.grid[ new_pos ] = 0

        if actionID == ACTION_MOVE_UP and ( self.player_position - 10 >= 0 ):
            xbmc.executebuiltin( "SetProperty(weapon_direction,onup)" )
            new_pos = self.move( -10 )

        elif actionID == ACTION_MOVE_DOWN and ( self.player_position + 10 <= 99 ):
            xbmc.executebuiltin( "SetProperty(weapon_direction,ondown)" )
            new_pos = self.move( 10 )

        elif actionID == ACTION_MOVE_LEFT and ( self.player_position - 1  >= 0 ):
            xbmc.executebuiltin( "SetProperty(weapon_direction,onleft)" )
            if str( "%02d" % self.player_position )[ 0 ] == str( "%02d" % ( self.player_position - 1 ) )[ 0 ]:
                new_pos = self.move( -1 )

        elif actionID == ACTION_MOVE_RIGHT and ( self.player_position + 1 <= 99 ):
            xbmc.executebuiltin( "SetProperty(weapon_direction,onright)" )
            if str( "%02d" % self.player_position )[ 0 ] == str( "%02d" % ( self.player_position + 1 ) )[ 0 ]:
                new_pos = self.move( 1 )

        # grab items !
        if self.grid[ new_pos ] == WEAPON_ID:
            item = self.listitems[ new_pos ].getProperty( "item" )
            self.listitems[ new_pos ].setProperty( "item", "" )
            self.game[ "weapons" ].append( item )
            self.setContainerWeapons()

        if self.grid[ new_pos ] == PEOPLE_ID:
            self.grid[ new_pos ] = 0
            #people = self.listitems[ new_pos ].getProperty( "people" )
            self.listitems[ new_pos ].setProperty( "people", "" )
            #name = self.peoples_added[ -1 ][ "name" ]
            #self.listpeoples.append( xbmcgui.ListItem( name, "alive", people ) )
            self.people[ "statut" ] = u'Alive'
            self.game[ "peoples" ].append( self.people )
            self.setContainerPeoples()

        # move player
        if self.player_position != new_pos:
            pimg = self.listitems[ self.player_position ].getProperty( "player" )
            self.listitems[ self.player_position ].setProperty( "player", "" )
            self.listitems[ new_pos ].setProperty( "player", pimg )

        self.grid[ new_pos ] = PLAYER_ID
        self.list_control_game.selectItem( new_pos )
        self.setFocusId( 150 )

        # if new pos == current player pos, pass
        if self.player_position == new_pos:
            self.gameLocked = False
            return
        self.player_position = new_pos

        self.move_count += 1 # reseted on each chapter
        self.game[ "move_total" ] += 1
        self.setProperties()
        self.setCriticalZone()

        # now walker turn :)
        position = self.player_position
        # get direct ride, if player in criticalzone or food added in self.critical_zone
        ride = bool( self.listitems[ position ].getProperty( "criticalzone" ) )
        if not ride:
            for count, i in enumerate( self.grid ):
               if i == FOOD_ID and count in self.critical_zone:
                    position = count
                    ride = True
                    break
        #
        self.list_control_game.setEnabled( 0 )
        self.setFocusId( 7000 ) # control of current weapon used
        has_spleep = False
        if ride:
            # total walker
            walkers = len( self.walker_position )
            for pos in sorted( self.walker_position ):
                ride = []
                # get walker direct ride
                if str( "%02d" % pos )[ 0 ] == str( "%02d" % position )[ 0 ]: # same row
                    ride = range( pos, position + 1 ) or range( position, pos + 1 )[ ::-1 ]

                elif str( "%02d" % pos )[ 1 ] == str( "%02d" % position )[ 1 ]: # same column
                    ride = range( pos, position + 10, 10 ) or range( position, pos + 10, 10 )[ ::-1 ]

                # if more one walker, reset ride if self.grid position is 1, 2, 4, 6
                if ride and walkers > 1:
                    for i in ride:
                        if i == pos: continue
                        if self.grid[ i ] in [ WALKER_ID, WALKER_EAT_ID, BOX_ID, WEAPON_ID ]:
                            ride = []
                            break

                if ride:
                    SFX( "Zombie Short Low Growl.wav" )
                    # now move walker
                    time.sleep( .5 )
                    old_pos = pos
                    for pos2 in ride:
                        if old_pos == pos2: continue
                        #
                        if self.grid[ pos2 ] == FOOD_ID:
                            self.listitems[ pos2 ].setProperty( "food", "" )
                        #
                        walker = ( "1", "2" )[ self.grid[ pos2 ] in [ FOOD_ID, PLAYER_ID ] ]
                        walker = ( walker, "" )[ self.fire_position in [ old_pos, pos2 ] ]
                        self.listitems[ old_pos ].setProperty( "walker", "" )
                        self.listitems[ pos2 ].setProperty( "walker", walker )
                        #
                        if walker == "":
                            del self.walker_position[ self.walker_position.index( old_pos ) ]
                        else:
                            self.grid[ pos2 ] = int( walker or NONE_ID )
                            self.walker_position[ self.walker_position.index( old_pos ) ] = pos2
                        #
                        self.grid[ old_pos ] = NONE_ID
                        old_pos = pos2
                        #
                        self.setCriticalZone()
                        if walker == "":
                            break
                        time.sleep( 1 )
                        has_spleep = True

                    # player dead
                    if not self.grid.count( PLAYER_ID ):
                        #self.gameover = True
                        break
        #else:
        #if not self.gameover:
        if self.grid.count( PLAYER_ID ):
            # check for walker vs food or not
            while True:
                eat = False
                # move walker, case by case
                for pos in sorted( self.walker_position ):
                    if eat: break
                    #
                    #walker = "1"
                    #for id_prop, prop in [ [ PLAYER_ID, "player" ], [ PEOPLE_ID, "people" ], [ FOOD_ID, "food" ] ]: # player or people or food
                    #    if eat: break
                    has_people = self.people and self.grid.count( PEOPLE_ID )
                    for i in [ 10, -10, -1, 1 ]:
                        pos2 = pos + i
                        if i in [ -1, 1 ] and str( "%02d" % pos )[ 0 ] != str( "%02d" % ( pos2 ) )[ 0 ]: # not same row
                            continue
                        #
                        if ( 0 <= ( pos2 ) <= 99 ) and ( self.grid[ pos2 ] in [ PLAYER_ID, PEOPLE_ID, FOOD_ID ] ): # walker vs player or people or food
                            if   self.grid[ pos2 ] == PLAYER_ID: prop = "player"
                            elif self.grid[ pos2 ] == PEOPLE_ID: prop = "people"
                            elif self.grid[ pos2 ] == FOOD_ID:   prop = "food"
                            eat = True
                        #
                        #if eat:
                            if not has_spleep: time.sleep( .75 )
                            has_spleep = False

                            self.listitems[ pos ].setProperty( "walker", "" )
                            walker = ( "2", "" )[ self.fire_position in [ pos, pos2 ] ] # trop facile
                            self.listitems[ pos2 ].setProperty( "walker", walker )
                            #
                            if walker == "":
                                del self.walker_position[ self.walker_position.index( pos ) ]
                            else:
                                SFX( "Zombie Short Low Growl.wav" )
                                self.listitems[ pos2 ].setProperty( prop, "" )
                                self.grid[ pos2 ] = WALKER_EAT_ID #int( walker or NONE_ID )
                                self.walker_position[ self.walker_position.index( pos ) ] = pos2
                            #
                            self.grid[ pos ]  = NONE_ID
                            self.setCriticalZone()

                            #if self.people and prop == "people": #id_prop == PEOPLE_ID:
                            if has_people and not self.grid.count( PEOPLE_ID ):
                                self.people[ "statut" ] = u'Dead'
                                self.game[ "peoples" ].append( self.people )
                                self.setContainerPeoples()

                            # player dead
                            #if id_prop == PLAYER_ID:
                            #if not self.grid.count( PLAYER_ID ):
                            #    self.gameover = True
                                
                            break
                        #if walker == "":
                        #    break
                if not eat:
                    break

        self.setCriticalZone()
        self.gameLocked = False
        self.list_control_game.setEnabled( 1 )

        #if self.gameover:
        if not self.grid.count( PLAYER_ID ):
            xbmc.executebuiltin( "ClearProperty(chapter)" )
            # set dead statut for other people
            #if self.game[ "player" ] > 0:
            self.game[ "peoples" ][ self.game[ "player" ] ][ "statut" ] = u'Dead'
            deadname = " ".join( [ self.player[ "name" ], LangXBMC( 21402 ), LangXBMC( 21897 ).lower(), "..." ] )
            self.game[ "player" ] = 0
            self.setContainerPeoples()
            self.player = self.game.getPlayer()
            
            reset = 1 
            if self.game[ "game_over" ]: # or not self.player:
                xbmcgui.Dialog().ok( ADDON_NAME, "[COLOR=red][B]GAME OVER![/B][/COLOR]", "", deadname )

            elif xbmcgui.Dialog().yesno( ADDON_NAME, "[COLOR=red][B]Your walking was stopped here![/B][/COLOR]", "", deadname, LangXBMC( 13009 ), "Retry" ):
                self.setGame( self.chapter )
                reset = 0

            if reset:
                self.resetGame()

        else:
            self.list_control_game.selectItem( self.player_position )
            self.setFocusId( 150 )

            #if not 1:walkers and 3:foods and 6:weapons and 7:peoples : chapter up +1
            if not ( self.grid.count( WALKER_ID ) + self.grid.count( WEAPON_ID ) + self.grid.count( PEOPLE_ID ) ):# + self.grid.count( FOOD_ID )
                self.chapter += 1
                if self.chapter > int( ADDON.getSetting( self.game_name ) or "0" ):
                    ADDON.setSetting( self.game_name, str( self.chapter ) )
                    self.game[ "chapter" ] = self.chapter
                
                # before set game, update game
                self.game[ "showgrid" ]     = self.control_show_grid.isSelected()
                self.game[ "criticalzone" ] = self.control_critical_zone.isSelected()
                self.game.saveGame()

                self.setGame( self.chapter )

            # add new walker if food exists
            elif self.grid.count( FOOD_ID ) and not ( self.grid.count( WALKER_ID ) + self.grid.count( WALKER_EAT_ID ) ):
                Timer( 1, self.addRandomWalker, () ).start()

    def resetGame( self ):
        try:
            self.game = None
            self.list_control_game.reset()
            xbmc.executebuiltin( "ClearProperty(chapter)" )
            self.setVariables()
            self.setProperties()
            xbmc.executebuiltin( "SetFocus(9000)" )
        except:
            print_exc()
    
    def addRandomWalker( self ):
        #print "add new walker, food exists!"
        if self.grid.count( WALKER_ID ) < self.max_walkers:
            excludes = range( self.player_position - 15, self.player_position + 15 )
            while True: #for i in range( 100 ):
                i = random.randint( 0, 99 )
                if self.grid[ i ] == NONE_ID and i not in excludes:
                    self.listitems[ i ].setProperty( "walker", "1" )
                    self.walker_position.append( i )
                    self.grid[ i ] = WALKER_ID
                    break
        self.setCriticalZone()

    def onAction( self, action ):
        if action in [ ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT, ACTION_MOVE_UP, ACTION_MOVE_DOWN ]:
            if xbmc.getCondVisibility( "Control.HasFocus(150)" ):
                if not self.gameLocked:
                    # use tread for allow fire onClick
                    Thread( target=self.onGame, args=( action.getId(), ) ).start()
                    #self.onGame( action.getId() )

        elif action in [ ACTION_SHOW_INFO, ACTION_CONTEXT_MENU, ACTION_QUEUE_ITEM ]:
            if action == ACTION_SHOW_INFO and xbmc.getCondVisibility( "!ControlGroup(8000).HasFocus" ):
                fid = 8000
            elif action == ACTION_CONTEXT_MENU and xbmc.getCondVisibility( "!ControlGroup(9000).HasFocus" ):
                fid = 9000
            elif action == ACTION_QUEUE_ITEM and xbmc.getCondVisibility( "!Control.HasFocus(7000)" ):
                fid = 7000
            else:
                fid = 7000
                if self.list_control_game.size():
                    try: self.list_control_game.selectItem( self.player_position )
                    except: pass
                    fid = 150
            xbmc.executebuiltin( "SetFocus(%i)" % fid )
            #self.setFocusId( fid )

        elif action in CLOSE_WINDOW:
            if self.list_control_game.size():
                if xbmcgui.Dialog().yesno( ADDON_NAME, "Game in progress...", "Are you sure you want to stop walking?" ):
                    self.resetGame()

            elif xbmc.getCondVisibility( "!IsEmpty(window.property(ToBeContinued))" ):
                xbmc.executebuiltin( "CancelAlarm(ToBeContinued,true)" )
                xbmc.executebuiltin( "ClearProperty(ToBeContinued)" )
                xbmc.executebuiltin( "SetFocus(9000)" )

            else:
                self.close_dialog()

    def close_dialog( self ):
        xbmc.executebuiltin( "CancelAlarm(ToBeContinued,true)" )
        xbmc.executebuiltin( "PlayerControl(Stop)" )
        xbmc.sleep( 50 )
        self.close()


def Main():
    w = Dead( "script-TheWalkingDead.xml", ADDON_DIR, "default" )
    w.doModal()
    del w



if ( __name__ == "__main__" ):
    Main()

