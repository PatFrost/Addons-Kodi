
# first import pywin32 for initialize site-packages
import pywin32

import win32api
import win32con
import win32gui


def click(x,y):
    print win32api.GetCursorPos()
    win32api.SetCursorPos((x,y))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)
    print win32api.GetCursorPos()


def callback( hwnd, window ):
    if window == win32gui.GetWindowText( hwnd ):
        rect = win32gui.GetWindowRect( hwnd )
        x = rect[ 0 ]
        y = rect[ 1 ]
        w = rect[ 2 ] - x
        h = rect[ 3 ] - y

        click( w/2+x, h/2+y ) # simulate mouse click at center rect

        print "-"*100
        print "Window %s:" % win32gui.GetWindowText( hwnd )
        print " Location: (%d, %d)" % ( x, y )
        print "     Size: (%d, %d)" % ( w, h )
        print "     Rect: %r" % ( rect, )
        print "-"*100

def main():
    win32gui.EnumWindows( callback, "XBMC" )

if __name__ == '__main__':
    main()

