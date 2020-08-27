
# Modules general
import os
import sys
from traceback import print_exc

# Modules XBMC
import xbmc
import xbmcgui
import xbmcvfs
from xbmcaddon import Addon


import gamesdb


# parse argv

# constants
ADDON      = Addon( "script.xbmc.games.scores" )
ADDON_DIR  = ADDON.getAddonInfo( "path" )

GAME_ID   = sys.modules[ "__main__" ].GAME_ID
GAME      = Addon( GAME_ID )
GAME_NAME = GAME.getAddonInfo( "name" )
GAME_ICON = GAME.getAddonInfo( "icon" )
GAME_DIR  = GAME.getAddonInfo( "path" )

LangXBMC  = xbmc.getLocalizedString  # XBMC strings


#https://github.com/xbmc/xbmc/blob/master/xbmc/input/Key.h
ACTION_PARENT_DIR    =   9
ACTION_PREVIOUS_MENU =  10
ACTION_NAV_BACK      =  92
ACTION_CONTEXT_MENU  = 117
CLOSE_DIALOG         = [ ACTION_PARENT_DIR, ACTION_PREVIOUS_MENU, ACTION_NAV_BACK ]#, ACTION_CONTEXT_MENU ]


class DialogContextMenu( xbmcgui.WindowXMLDialog ):
    CONTROLS_BUTTON = range( 1001, 1012 )
    BUTTON_START = 1001
    BUTTON_END   = 1012

    def __init__( self, *args, **kwargs ):
        self.buttons  = kwargs[ "buttons" ]
        self.selected = -1
        self.doModal()

    def onInit( self ):
        try:
            for count, button in enumerate( self.buttons ):
                try:
                    self.getControl( self.BUTTON_START + count ).setLabel( button )
                    self.getControl( self.BUTTON_START + count ).setVisible( True )
                except:
                    pass
            self.setFocusId( self.BUTTON_START )

            for control in range( self.BUTTON_START + count + 1, self.BUTTON_END ):
                try: self.getControl( control ).setVisible( False )
                except: pass
        except:
            print_exc()

    def onFocus( self, controlID ):
        pass

    def onClick( self, controlID ):
        try:
            self.selected = controlID - self.BUTTON_START
            if self.selected < 0: self.selected = -1
        except:
            self.selected = -1
            print_exc()
        self._close_dialog()

    def onAction( self, action ):
        if action in CLOSE_DIALOG + [ ACTION_CONTEXT_MENU ]:
            self.selected = -1
            self._close_dialog()

    def _close_dialog( self ):
        self.close()
        xbmc.sleep( 300 )

def contextmenu( buttons ):
    cm = DialogContextMenu( "script-xbmc-games-contextmenu.xml", ADDON_DIR, buttons=buttons )
    selected = cm.selected
    del cm
    return selected


class Scores( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        self.last_focus_mode = ""
        self.setListItems()

    def onInit( self ): 
        self.setProperty( "gametitle", GAME_NAME )
        self.setProperty( "gameicon",  GAME_ICON )
        self.setContainers()

    def setContainers( self ):
        try:
            self.getControl( 50 ).reset()
            if self.menu:
                self.getControl( 50 ).addItems( self.menu )
            if self.getControl( 50 ).size():
                self.setListScores()
                self.setFocusId( 50 )
        except:
            print_exc()

    def setListItems( self ):
        self.menu = []
        self.defaults = {}
        self.listscores = {}
        try:
            self.scores = gamesdb.getScores( GAME_ID, keys=1 )
            # score keys: (idScore, idUser, score, level, perfect, strMode, strTimePlayed, strDate, online, strGameId, strNickName, strAvatar)
            for score in self.scores:
                mode = score[ "strMode" ]
                if mode not in self.defaults:
                    self.menu.append( xbmcgui.ListItem( mode ) )
                    self.defaults[ mode ] = True
                    self.listscores[ mode ] = []

                li = xbmcgui.ListItem( score[ "strNickName" ], str( score[ "score" ] ) )
                if score[ "strAvatar" ]: li.setIconImage( score[ "strAvatar" ] )
                li.setProperty( "idUser",     str( score[ "idUser" ] ) )
                li.setProperty( "idScore",    str( score[ "idScore" ] ) )
                li.setProperty( "score",      str( score[ "score" ] ) )
                li.setProperty( "level",      str( score[ "level" ]    or "" ) )
                li.setProperty( "perfect",    str( score[ "perfect" ]  or "" ) )
                li.setProperty( "mode",       score[ "strMode" ]       or "" )
                li.setProperty( "timeplayed", score[ "strTimePlayed" ] or "" )
                li.setProperty( "date",       score[ "strDate" ]       or "" )
                li.setProperty( "online",     str( score[ "online" ]   or "" ) )

                self.listscores[ mode ].append( li )
        except:
            print_exc()

    def setListScores( self, force=False ):
        try:
            if not self.getControl( 50 ).size(): return
            focus_mode = self.getControl( 50 ).getSelectedItem().getLabel()
            if force or self.last_focus_mode != focus_mode:
                self.last_focus_mode = focus_mode
                self.getControl( 150 ).reset()
                if self.defaults[ focus_mode ]:
                    self.getControl( 150 ).addItems( self.listscores[ focus_mode ] )

                self.getControl( 13 ).setSelected( not self.defaults[ focus_mode ] )
            self.getControl( 10 ).setEnabled( False in self.defaults.values() )
        except:
            print_exc()

    def onFocus( self, controlID ):
        pass

    def onClick( self, controlID ):
        try:
            if controlID == 150:
                self.onContextMenu()

            elif controlID == 10:
                if xbmcgui.Dialog().yesno( "Confirm scores delete", "Delete these scores?", "Deleting scores cannot be undone!" ):
                    # save change and close is ok
                    changed = False
                    for mode, default in self.defaults.items():
                        if not default:
                            OK = gamesdb.removeScores( GAME_ID, mode )
                            if OK: changed = True
                    if changed:
                        self._close_dialog()

            elif controlID == 11:
                self._close_dialog()

            elif controlID == 13:
                focus_mode = self.getControl( 50 ).getSelectedItem().getLabel()
                if self.listscores[ focus_mode ]:
                    self.defaults[ focus_mode ] = not self.defaults[ focus_mode ]
                    self.setListScores( True )
                else:
                    self.getControl( 13 ).setSelected( 0 )

        except:
            print_exc()

    def onContextMenu( self ):
        try:
            refresh = False
            # show context menu
            listitem = self.getControl( 150 ).getSelectedItem()
            listitem.select( 1 )
            buttons = [ "Delete Score", "Set Avatar" ]
            # show context menu
            selected = contextmenu( buttons )

            if selected == 0:
                really = " - ".join( [ listitem.getLabel(), listitem.getLabel2() ] )
                if xbmcgui.Dialog().yesno( "Confirm score delete", LangXBMC( 433 ) % really, "Deleting score cannot be undone!" ):
                    refresh = gamesdb.removeScore( int( listitem.getProperty( "idScore" ) ) )

            elif selected == 1:
                # Set Avatar
                default = xbmc.getInfoLabel( "Container(150).ListItem.Icon" )
                strAvatar = xbmcgui.Dialog().browse( 2, "Browse for Avatar", "files", "", False, False, default )
                if strAvatar and strAvatar != default:
                    refresh = gamesdb.setUserAvatar( int( listitem.getProperty( "idUser" ) ), strAvatar )
                    #if refresh: listitem.setIconImage( strAvatar )

            listitem.select( 0 )
            if refresh:
                self.last_focus_mode = ""
                self.setListItems()
                self.setContainers()
        except:
            print_exc()

    def onAction( self, action ):
        if xbmc.getCondVisibility( 'Control.HasFocus(50)' ):
            self.setListScores()

        if action == ACTION_CONTEXT_MENU and xbmc.getCondVisibility( 'Control.HasFocus(150)' ):
            self.onContextMenu()

        elif action in CLOSE_DIALOG:
            self._close_dialog()

    def _close_dialog( self, t=500 ):
        self.close()
        if t: xbmc.sleep( t )


def Main():
    try:
        skin       = xbmc.getSkinDir()
        skin_dir   = GAME_DIR
        xml        = "%s-scores.xml" % GAME_ID.replace( ".", "-" )
        addon_xml  = os.path.join( skin_dir, "resources", "skins", "%s", "%s", xml )
        if   xbmcvfs.exists( "special://skin/720p/" + xml ):        scores_xml = xml
        elif xbmcvfs.exists( "special://skin/1080i/" + xml ):       scores_xml = xml
        elif xbmcvfs.exists( addon_xml % ( skin, "720p" ) ):        scores_xml = xml
        elif xbmcvfs.exists( addon_xml % ( skin, "1080i" ) ):       scores_xml = xml
        elif xbmcvfs.exists( addon_xml % ( "default", "720p" ) ):   scores_xml = xml
        elif xbmcvfs.exists( addon_xml % ( "default", "1080i" ) ):  scores_xml = xml
        else: scores_xml, skin_dir = "script-xbmc-games-scores.xml", ADDON_DIR
        sc = Scores( scores_xml, skin_dir )
    except:
        print locals()
        print_exc()
        #sc = Scores( "script-xbmc-games-scores.xml", ADDON_DIR )
    sc.doModal()
    del sc



if __name__ == '__main__':
    Main()