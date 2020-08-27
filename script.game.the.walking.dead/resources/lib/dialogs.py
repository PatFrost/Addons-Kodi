
import sys
globals().update( sys.modules[ "__main__" ].getGlobals() )


class Editor( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        self.grid = sorted( BASE_CHAPTER )

    def onInit( self ):
        self.listitems = [ xbmcgui.ListItem( str( i ) )  for i in range( 100 ) ]
        self.getControl( 150 ).reset()
        self.getControl( 150 ).addItems( self.listitems )
        self.setFocusId( 150 )

    def onFocus( self, controlID ):
        pass

    def onClick( self, controlID ):
        if controlID == 150:
            pos = self.getControl( 150 ).getSelectedPosition()
            buttons = [ "0 - None", "1 - Walker", "2 - Food", "3 - Box", "4 - Weapon" ]
            if not self.grid.count( PLAYER_ID ): buttons.append( "5 - Player" )
            selected  = xbmcgui.Dialog().select( ADDON_NAME, buttons )
            self.setListItem( pos, selected )

    def setListItem( self, pos, selected ):
        if selected == 0:
            self.listitems[ pos ].setIconImage( "" )
            self.grid[ pos ] = NONE_ID

        if selected == 1:
            self.listitems[ pos ].setIconImage( WALKER_IMAGE )
            self.grid[ pos ] = WALKER_ID

        elif selected == 2:
            self.listitems[ pos ].setIconImage( random.choice( FOOD_IMAGE ) )
            self.grid[ pos ] = FOOD_ID

        elif selected == 3:
            self.listitems[ pos ].setIconImage( random.choice( BOX_IMAGES ) )
            self.grid[ pos ] = BOX_ID

        elif selected == 4:
            self.listitems[ pos ].setIconImage( random.choice( WEAPON_IMAGES ) )
            self.grid[ pos ] = WEAPON_ID

        elif selected == 5 and not self.grid.count( PLAYER_ID ):
            self.listitems[ pos ].setIconImage( os.path.join( PEOPLES_DIR, Peoples()[ 0 ][ "image" ] ) )
            self.grid[ pos ] = PLAYER_ID

    def save( self ):
        # not implanted! print only
        if self.grid.count( PLAYER_ID ) and ( self.grid.count( FOOD_ID ) >= self.grid.count( WALKER_ID ) and self.grid.count( BOX_ID ) ):
            print json.dumps( Episode1().setChapter( self.grid ), sort_keys=True ).replace( '"', "" )
            #from glob import glob
            #dpath = ( xbmc.translatePath( "special://screenshots" ) or xbmc.translatePath( "special://temp" ) )
            #screenshots = set( glob( os.path.join( dpath, "screenshot*.*" ) ) )
            #xbmc.executebuiltin( "TakeScreenshot" )
            #xbmc.sleep( 800 )
            #print ( "Window.IsVisible(FileBrowser)", xbmc.getCondVisibility( "Window.IsVisible(FileBrowser)" ) )
            #while xbmc.getCondVisibility( "Window.IsVisible(FileBrowser)" ): time.sleep( .25 )
            #dpath = ( xbmc.translatePath( "special://screenshots" ) or xbmc.translatePath( "special://temp" ) )
            #screenshot = set( glob( os.path.join( dpath, "screenshot*.*" ) ) ).difference( screenshots ).pop()
            #print screenshot


    def onAction( self, action ):
        if action.getId() in CLOSE_DIALOG:
            self.save()
            self.close_dialog()

        else:
            # keyboard action
            buttonCode = action.getButtonCode()
            if not buttonCode: return
            self.onKeyboardAction( ( buttonCode & 0xFF ) )

    def onKeyboardAction( self, keyID ):
        #print "keyboard action (%r,%r,%s)" % ( keyID, chr( keyID ), chr( keyID ) )
        try:
            pos = self.getControl( 150 ).getSelectedPosition()
            # keyboard action - normal - NUM
            if keyID in [ 48, 112 ]: # keyboard action - (48,0) - (112,p)
                self.setListItem( pos, 0 )

            elif keyID in [ 49, 113 ]: # keyboard action - (49,1) - (113,q)
                self.setListItem( pos, 1 )

            elif keyID in [ 50, 114 ]: # keyboard action - (50,2) - (114,r)
                self.setListItem( pos, 2 )

            elif keyID in [ 51, 115 ]: # keyboard action - (51,3) - (115,s)
                self.setListItem( pos, 3 )

            elif keyID in [ 52, 116 ]: # keyboard action - (52,4) - (116,t)
                self.setListItem( pos, 4 )

            elif keyID in [ 53, 117 ]: # keyboard action - (53,5) - (117,u)
                self.setListItem( pos, 5 )

            elif keyID in [ 54, 118 ]: # keyboard action - (54,6) - (118,v)
                self.setListItem( pos, 6 )

            elif keyID in [ 55, 119 ]: # keyboard action - (55,7) - (119,w)
                self.setListItem( pos, 7 )

            elif keyID in [ 56, 120 ]: # keyboard action - (56,8) - (120,x)
                self.setListItem( pos, 8 )

            elif keyID in [ 57, 121 ]: # keyboard action - (57,9) - (121,y)
                self.setListItem( pos, 9 )
        except:
            pass

    def close_dialog( self ):
        xbmc.sleep( 300 )
        self.close()

        
class SelectChapter( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        self.selected  = -1
        self.listitems = {}
        self.chapters  = sorted( Episode1().keys() )
        self.chapter   = 1
        self.game_name = ""
        
        games = []
        game       = "Game %i"
        episode    = LangXBMC( 20359 ) + " %i" % ( 1, )
        strChapter = LangXBMC( 21396 ) + " %i"
        for i in range( 1, 6 ):
            chapter = strChapter % ( int( ADDON.getSetting( "g" + str( i ) ) or "1" ), )
            games.append( " - ".join( [ game % i, episode, chapter ] ) )

        game_selected  = xbmcgui.Dialog().select( ADDON_NAME, games )
        if game_selected >= 0:
            self.game_name = "g" + str( game_selected + 1 )
            strChapter     = ADDON.getSetting( self.game_name ) or "1"
            if strChapter.isdigit() and ( 0 <= int( strChapter ) <= len( self.chapters ) ):
                self.chapter = int( strChapter )
            ADDON.setSetting( self.game_name, str( self.chapter ) )

    def onInit( self ):
        listitems = []
        for c in self.chapters:
            listitem = xbmcgui.ListItem( c.replace( "_0", " " ).replace( "_", " " ).title(), c )
            listitem.setProperty( "locked", ( "", "1" ) [ int( c.split( "_" )[ 1 ] ) > self.chapter ] )
            listitems.append( listitem )

        self.getControl( 50 ).reset()
        self.getControl( 50 ).addItems( listitems )
        self.getControl( 50 ).selectItem( self.chapter - 1 )
        self.setFocusId( 50 )
        self.setGrid()

    def setGrid( self ):
        if not self.listitems.get( self.chapter ):
            listitems = []
            for pos, id in enumerate( Episode1().getChapter( self.chapter ) ):
                listitem = xbmcgui.ListItem( str( pos ), self.chapters[ self.chapter - 1 ] )
                listitems.append( listitem )

                if id == PLAYER_ID:
                    listitem.setIconImage( os.path.join( PEOPLES_DIR, Peoples()[ 0 ][ "image" ] ) )

                elif id == WALKER_ID:
                    listitem.setIconImage( WALKER_IMAGE )

                elif id == FOOD_ID:
                    listitem.setIconImage( random.choice( FOOD_IMAGE ) )

                elif id == BOX_ID:
                    box = random.choice( BOX_IMAGES )
                    listitem.setIconImage( box )

                elif id == WEAPON_ID:
                    item = random.choice( WEAPON_IMAGES[ :self.chapter ] )
                    listitem.setIconImage( item )

            self.listitems[ self.chapter ] = listitems

        self.getControl( 150 ).reset()
        self.getControl( 150 ).addItems( self.listitems[ self.chapter ] )

    def onFocus( self, controlID ):
        pass

    def onClick( self, controlID ):
        if controlID == 50:
            if not bool( self.getControl( 50 ).getSelectedItem().getProperty( "locked" ) ):
                self.selected = self.getControl( 50 ).getSelectedPosition() + 1
                self.close_dialog()

    def onAction( self, action ):
        if xbmc.getCondVisibility( "!StringCompare(Container(50).ListItem.Label2,Container(150).ListItem.Label2)" ):
            try:
                self.chapter = int( xbmc.getInfoLabel( "Container(50).ListItem.Label2" ).split( "_" )[ 1 ] )
                self.setGrid()
            except:
                self.getControl( 150 ).reset()
                print_exc()

        if action.getId() in CLOSE_DIALOG:
            self.close_dialog()

    def close_dialog( self ):
        xbmc.sleep( 300 )
        self.close()


class SideMenuHelp( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        pass

    def onInit( self ):
        pass

    def onFocus( self, controlID ):
        pass

    def onClick( self, controlID ):
        if controlID == 100:# and xbmc.getCondVisibility( "!IsEmpty(Window.Property(FirstTimeRun))" ):
            ADDON.setSetting( "FirstTimeRun", "true" )
            self.close_dialog()

    def onAction( self, action ):
        if action.getId() in CLOSE_DIALOG:
            self.close_dialog()

    def close_dialog( self ):
        xbmc.sleep( 300 )
        self.close()

        
def selectChapter():
    s = SelectChapter( "script-TWD-Select.xml", ADDON_DIR, "default" )
    selected  = s.selected
    game_name = s.game_name
    if game_name:
        s.doModal()
        selected = s.selected
    del s
    return game_name, selected

    
def editor():
    e = Editor( "script-TWD-Editor.xml", ADDON_DIR, "default" )
    e.doModal()
    del e


def info():
    h = SideMenuHelp( "script-TWD-SideMenuHelp.xml", ADDON_DIR, "default" )
    h.doModal()
    del h
