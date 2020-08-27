
import os
from sys import modules
from traceback import print_exc
from zlib import compress, decompress
from base64 import decodestring, encodestring
try:
    import json
    json.loads( "[null]" ) # test json
except:
    import simplejson as json


PEOPLES_FILE = os.path.join( "characters", "default", "peoples.json" )
if hasattr( modules[ "__main__" ], "ADDON_DIR" ):
    PEOPLES_FILE = os.path.join( modules[ "__main__" ].ADDON_DIR, "resources", PEOPLES_FILE )
else:
    PEOPLES_FILE = os.path.join( "..", PEOPLES_FILE )
PEOPLES_DIR = os.path.dirname( PEOPLES_FILE )

if hasattr( modules[ "__main__" ], "ADDON" ):
    ADDON = modules[ "__main__" ].ADDON


class Peoples( list ):
    """ customized list, don't raise IndexError exception, return dict() instead """
    def __init__( self ):
        list.extend( self, json.loads( open( PEOPLES_FILE ).read() ) )

    def __getitem__( self, index ):
        if index < len( self ):
            return list.__getitem__( self, index )
        else:
            return dict()

    def getPeople( self, index ):
        people = self[ index ]
        return people


class Game( dict ):
    def __init__( self, name="g0" ):
        self.name = name
        self.save = name.replace( "g", "s", 1 )

        self.peoples = Peoples()

        self[ "move_total" ] = 0
        self[ "chapter" ]    = 1
        self[ "player" ]     = 0 # default : self.peoples[ 0 ]
        self[ "peoples" ]    = [ self.peoples[ 0 ] ] # listpeoples, peoples_added
        self[ "weapons" ]    = [] # listweapons
        self[ "bullets" ]    = 0

        self[ "showgrid" ]       = False
        self[ "criticalzone" ]   = False
        self[ "current_weapon" ] = ""

        self[ "game_over" ]      = False
        #if self.name:
        self.loadGame()

    def getPlayer( self ):
        player = self[ "peoples" ][ self[ "player" ] ]
        if player[ "statut" ] != u'Alive':
            player = {}
            for count, people in enumerate( self[ "peoples" ] ):
                if people[ "statut" ] == u'Alive':
                    self[ "player" ] = count
                    player = people
                    break
        if not player:
            self[ "game_over" ] = True
        return player

    def getPeople( self ):
        people = self.peoples.getPeople( int( self[ "chapter" ] / 2 ) )
        if people:
            c = people.copy()
            for p in self[ "peoples" ]:
                c[ "statut" ] = p[ "statut" ]
                if c == p: people = dict()

        return people

    def loadGame( self ):
        game = dict()
        try:
            if ADDON.getSetting( self.save ):
                game = json.loads( decompress( decodestring( ADDON.getSetting( self.save ) ) ) )
            if game.get( "chapter" ) != int( ADDON.getSetting( self.name ) or "1" ):
                game = dict()
        except:
            print_exc()
        if game:
            self.update( game )
        self.saveGame()

    def saveGame( self ):
        try:
            data = json.dumps( self, sort_keys=True, indent=2 )
            ADDON.setSetting( self.save, encodestring( compress( data ) ) )
            ADDON.setSetting( self.name, str( self[ "chapter" ] ) )
        except:
            print_exc()
