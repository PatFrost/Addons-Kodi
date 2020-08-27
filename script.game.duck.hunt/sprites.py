
import os
import random
from math import *
from traceback import print_exc


BLACK_BIRD = { "flying": "bird2-flying.gif", "shot": "bird2-shot.png", "dropped": "bird2-dropped.gif", "catch": "catch_bird2.png", "pts1":  500, "pts2":  800, "pts3": 1000, "pts4": 1000, "pts5": 1000 }
BLUE_BIRD  = { "flying": "bird1-flying.gif", "shot": "bird1-shot.png", "dropped": "bird1-dropped.gif", "catch": "catch_bird1.png", "pts1": 1000, "pts2": 1500, "pts3": 2000, "pts4": 2000, "pts5": 2000 }
RED_BIRD   = { "flying": "bird3-flying.gif", "shot": "bird3-shot.png", "dropped": "bird3-dropped.gif", "catch": "catch_bird3.png", "pts1": 1500, "pts2": 2400, "pts3": 3000, "pts4": 3000, "pts5": 3000 }
BIRDS      = [ BLACK_BIRD ]*6 + [ BLUE_BIRD ]*4 + [ RED_BIRD ]*2
DISC       = { "pts1":  1000, "pts2":  1500, "pts3":  2000, "pts4":  2000, "pts5":  2000 }
BONUS      = { "pts1": 10000, "pts2": 10000, "pts3": 15000, "pts4": 20000, "pts5": 30000 }



def getPTS( level, DICT ):
    if level <= 5:
        # Rounds 1-5
        return DICT[ "pts1" ]
    elif level <= 10:
        # Rounds 6-10
        return DICT[ "pts2" ]
    elif level <= 15:
        # Rounds 11-15
        return DICT[ "pts3" ]
    elif level <= 20:
        # Rounds 16-20
        return DICT[ "pts4" ]
    elif level >= 21:
        # Rounds 21-99
        return DICT[ "pts5" ]
    return 0


def hasNextRound( level, shooted ):
    if level <= 10:
        # 1 through 10 = 6 out of 10
        return shooted >= 6
    elif level <= 12:
        # 11 through 12 = 7 out of 10
        return shooted >= 7
    elif level <= 14:
        # 13 through 14 = 8 out of 10
        return shooted >= 8
    elif level <= 19:
        # 15 through 19 = 9 out of 10
        return shooted >= 9
    elif level >= 20:
        # 20 through 99 = 10 out of 10
        # 0 and beyond  = 10 out of 10, Game mode B/C only
        return shooted >= 10
    return False


def getSlideCoords( x1, y1, x2, y2, step=1, unique=True ):
    x1, y1   = map( float, ( x1, y1 ) )
    x2, y2   = map( float, ( x2, y2 ) )
    dx, dy   = float( x2 - x1 ), float( y2 - y1 )
    distance = int( hypot( dx, dy ) )
    coords   = []
    for i in range( 1, 1 + distance, step ):
        try:
            x = int( x1 + ( dx * i / distance ) )
            y = int( y1 + ( dy * i / distance ) )
            coord = ( x, y )
            if not unique or coord not in coords:
                coords.append( coord )
            #else:
            #    print coord
        except:
            pass
    return coords


def getSplitScreen( x, y, w, h, c=2, r=2 ):
    #div = fabs( sqrt( c+r ) )
    sqrt_w = w / c
    sqrt_h = h / r
    splited = []
    for a in range( c ):
        for b in range( r ):
            x1 = sqrt_w * a + x
            y1 = sqrt_h * b + y
            x2 = sqrt_w * ( a + 1 )
            y2 = sqrt_h * ( b + 1 )
            splited.append( ( x1, y1, x2, y2 ) )
    return splited


try:
    triangular = random.triangular
except:
    def triangular( low=0.0, high=1.0, mode=None ):
        """random.triangular(...) not implanted in python 2.4
        Triangular distribution.

        Continuous distribution bounded by given lower and upper limits,
        and having a given mode value in-between.

        http://en.wikipedia.org/wiki/Triangular_distribution
        """
        u = random.random()
        #c = 0.5 if mode is None else (mode - low) / (high - low) # (if/else) same line in python 2.5 to 3.xx only
        if mode is None: c = 0.5 
        else: c = ( mode - low ) / ( high - low )
        if u > c:
            u = 1.0 - u
            c = 1.0 - c
            low, high = high, low
        return low + ( high - low ) * ( u * c ) ** 0.5

def randomPosition( min_x, min_y, max_x, max_y ):
    x = triangular( min_x, max_x )
    y = triangular( min_y, max_y )
    return x, y


class Circle:
    def __init__( self, x, y, r, e=None, unique=True, step=1 ):
        self.coords  = []
        self._origin = ( x, y, r, e )
        self.circle( x, y, r, e, unique=unique )
        if step > 1: self.step( step )

    def circle( self, posx, posy, radius, extent=None, unique=True ):
        position = posx, posy
        angle = 0.0
        fullcircle = 360.0
        invradian = pi / ( fullcircle * 0.5 )
        if extent is None:
            extent = fullcircle
        frac = abs( extent ) / fullcircle
        steps = 1 + int( min( 11 + abs( radius ) / 6.0, 59.0 ) * frac )
        w = 1.0 * extent / steps
        w2 = 0.5 * w
        distance = 2.0 * radius * sin( w2 * invradian )
        if radius < 0:
            distance, w, w2 = -distance, -w, -w2
        angle = ( angle + w2 ) % fullcircle
        for i in range( steps ):
            x0, y0 = start = position
            x1 = x0 + distance * cos( angle * invradian )
            y1 = y0 - distance * sin( angle * invradian )

            x0, y0 = position
            position = map( float, ( x1, y1 ) )
            dx = float( x1 - x0 )
            dy = float( y1 - y0 )
            distance2 = hypot( dx, dy )
            nhops = int( distance2 )
            try:
                for i in range( 1, 1+nhops ):
                    x, y = x0 + dx * i / nhops, y0 + dy * i / nhops
                    coord = map( int, map( round, ( x, y ) ) )
                    #coord = map( int, ( x, y ) )
                    #coord = ( x, y )
                    if not unique or coord not in self.coords:
                        self.coords.append( coord )
                    #else:
                    #    print coord

            except:
                pass
            angle = ( angle + w ) % fullcircle
        angle = ( angle + -w2 ) % fullcircle

    def step( self, step=1 ):
        if step > 1:
            coords = []
            for i in range( 0, len( self.coords ), step ):
                coords.append( self.coords[ i ] )
            self.coords = coords

    def __repr__( self ):
        return "<circle(%s,%s)>" % ( self._origin, self.coords )




if __name__ == '__main__':
    #for i in range( 257 ):
    #    print ( i, chr( i ) ) #(None or 0) & 0xFF
    #raise
    flyingHeight = 480
    bgWidth = 1280
    birdWidth = 80

    screensplit = getSplitScreen( 0, 0, bgWidth, flyingHeight )
    random.shuffle( screensplit )

    x1, y1 = -birdWidth, random.randrange( 0, flyingHeight )
    for x, y, w, h in screensplit:
        x2, y2 = randomPosition( x, y, w, h )

        slide = getSlideCoords( x1, y1, x2, y2 )

        print "Direction = %s" % ( "right", "left" )[ x1 > x2 ]
        print ( x, w, y, h )
        print ( x1, y1 ), ( x2, y2 )
        #print slide[ 0 ], slide[ -1 ]
        print len( slide )
        #for x, y in slide:
        #    print x, y
        print "-"*50

        x1, y1 = x2, y2
        break

    x2, y2 = bgWidth, y1
    slide = getSlideCoords( x1, y1, x2, y2 )

    print "Direction = %s" % ( "right", "left" )[ x1 > x2 ]
    print
    print ( x1, y1 ), ( x2, y2 )
    print slide[ 0 ], slide[ -1 ]
    print len( slide )

    for i in range( 0, len( slide ), 2 ):
        print slide[ i ]
    print "-"*50



