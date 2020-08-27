"""
    based on pygame - Python Game Library
    for script.game.arkanoid
    by frost (passion-xbmc.org)
"""

#Modules general
import math
import random
import itertools

from planar import Polygon

from_iterable = itertools.chain.from_iterable

hypot720  = float(math.hypot(1280, 720))
hypot1080 = float(math.hypot(1920, 1080))


def pairwise(iterable, closewith=0):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable+iterable[:closewith])
    next(b, None)
    return list(itertools.izip(a, b))

def border(points, offsetx=0, offsety=0):
    xs, ys = points[::2], points[1::2]
    min_x, max_x = min(xs)-offsetx, max(xs)+offsetx
    min_y, max_y = min(ys)-offsety, max(ys)+offsety
    return [min_x, min_y, max_x, min_y, max_x, max_y, min_x, max_y]

def to_points(poly, offsetx=0, offsety=0):
    if offsetx == offsety == 0:
        return map(round, from_iterable(poly))
    points = []
    for p in poly:
        x, y = tuple(p)
        x += offsetx
        y += offsety
        points += [x, y]
    return map(round, points)

def get_all_points(start_x, start_y, end_x, end_y, steps=hypot1080):
    steps = max(1.0, steps)

    dx = end_x - start_x
    dy = end_y - start_y

    points = []
    for i in range(int(steps)+1):
        pos = (int(start_x + dx*i/steps), int(start_y + dy*i/steps))
        if pos not in points:
            points.append(pos)

    return points

def all_points_to_line(points):
    lines = []
    if len(points) == 4:
        lines.append(get_all_points(*points))
    else:
        for i in range(0, len(points), 2):
            line = points[i:i+4]
            if len(line) < 4:
                line = (line+points)[:4]
            lines.append(get_all_points(*line))
    return lines

def create_polygon(vertex_count, radius, center=(0, 0), angle=0):
    poly = Polygon.regular(vertex_count, radius, center, angle)
    points = to_points(poly)
    return points

def create_star(peak_count, radius1, radius2, center=(0, 0), angle=0):
    star = Polygon.star(peak_count, radius1, radius2, center, angle)
    points = to_points(star)
    return points

def getAngles(A, B, C=0):
    """Returns tuple of 3 angles of triangle"""
    def angle(a, b, c):
        return math.degrees(math.acos((c**2 - b**2 - a**2)/(-2.0 * a * b)))

    C = C or math.hypot(A, B)
    return angle(A, B, C), angle(B, C, A), angle(C, A, B)


class Error( Exception ):
    pass

class Line:
    def __init__(self, x1, y1, x2, y2):
        self.x2 = (x2-x1)
        self.y2 = (y2-y1)
        self.x1 = 0
        self.y1 = 0

        self.angle    = self._angle()
        self.distance = self._distance()

    def _angle(self):
        theta1 = math.atan2(self.y1, self.x1)
        theta2 = math.atan2(self.y2, self.x2)
        return (theta1 - theta2) * (180.0 / math.pi)

    def _distance(self):
        w = max(self.x1, self.x2) - min(self.x1, self.x2)
        h = max(self.y1, self.y2) - min(self.y1, self.y2)
        return math.hypot(w, h)

    def points(self):
        return get_all_points(self.x1, self.y1, self.x2, self.y2, self.distance)

class Rectangle:
    def __init__( self, x, y, w, h ):
        self.x = x
        self.y = y
        self.w = w or 1
        self.h = h or 1
        self.width = self.w
        self.height = self.h

        self.top = self.y
        self.left = self.x
        self.bottom = self.top + self.height
        self.right = self.left + self.width

        self.centerx = self.left + int( self.width/2.0 )
        self.centery = self.top + int( self.height/2.0 )
        self.center = ( self.centerx, self.centery )
        self.size = ( self.width, self.height )

        self.topleft = ( self.left, self.top )
        self.topright = ( self.right, self.top )
        self.bottomleft = ( self.left, self.bottom )
        self.bottomright = ( self.right, self.bottom )

        self.midtop = ( self.centerx, self.top )
        self.midleft = ( self.left, self.centery )
        self.midbottom = ( self.centerx, self.bottom )
        self.midright = ( self.right, self.centery )

    def __repr__( self ):
        return "<rect(%d, %d, %d, %d)>" % ( self.x, self.y, self.w, self.h )

class Rect( Rectangle ):
    def __init__( self, x=0, y=0, w=0, h=0 ):
        Rectangle.__init__( self, x, y, w, h )

    def move( self, x, y ):
        Rectangle.__init__( self, x, y, self.w, self.h )

    def resize( self, w, h ):
        Rectangle.__init__( self, self.x, self.y, w, h )

    def collidepoint( self, *xy ):
        """Rect.collidepoint

            test if a point is inside a rectangle
            Rect.collidepoint(x, y): return bool
            Rect.collidepoint((x,y)): return bool

            Returns true if the given point is inside the rectangle.

            A point along the right or bottom edge is not considered to be inside the rectangle.
            inside = x >= self.left and x < self.right and y >= self.top and y < self.bottom
        """
        if len( xy ) == 1:
            try:
                x, y = xy[ 0 ]
            except:
                raise Error, "bad point argument: %r" % ( xy[ 0 ], )
        else:
            try:
                x, y = xy
            except:
                raise Error, "bad coordinates: %r" % ( xy[ 0 ], )
        #for arkanoid include "right and bottom edge"
        inside = x >= self.left and x <= self.right and y >= self.top and y <= self.bottom
        return inside

    def colliderect( self, rect ):
        """Rect.colliderect

              test if two rectangles overlap
              Rect.colliderect(Rect): return bool

              Returns true if any portion of either rectangle overlap.
        """
        rectpos = [ rect.center, rect.midtop, rect.midleft, rect.midbottom, rect.midright, 
            rect.topleft, rect.topright, rect.bottomleft, rect.bottomright ]
        ret = self.collidelist( rectpos )
        return ret

    def collidelist( self, liste ):
        """Rect.collidelist

              test if one point in a list intersects
              Rect.collidelist(list): return index

              Test whether the point collides with any in a sequence of rectangles.
              The index of the first collision found is returned. If no collisions are found None is returned.
        """
        ret = None
        for count, xy in enumerate( liste ):
            if self.collidepoint( xy ):
                ret = count
                break
        return ret

    def collidelistall( self, liste ):
        """Rect.collidelistall

              test if all rectangles in a list intersect
              Rect.collidelistall(list): return indices

              Returns a list of all the indices that contain rectangles that collide with the Rect.
              If no intersecting rectangles are found, an empty list is returned.
        """
        indices = []
        for count, xy in enumerate( liste ):
            if self.collidepoint( xy ):
                indices.append( count )
        return indices

    def collidedict( self, dico ):
        """Rect.collidedict

              test if one rectangle in a dictionary intersects
              Rect.collidedict(dict): return (key, value)

              Returns the key and value of the first dictionary value that collides with the Rect.
              If no collisions are found, None is returned.

              Rect objects are not hashable and cannot be used as keys in a dictionary, only as values.
        """
        ret = None
        for key, value in dico.items():
            if self.colliderect( value ) is not None:
                ret = key, value
                break
        return ret

    def collidedictall( self, dico ):
        """Rect.collidedictall

              test if all rectangles in a dictionary intersect
              Rect.collidedictall(dict): return [(key, value), ...]

              Returns a list of all the key and value pairs that intersect with the Rect.
              If no collisions are found an empty dictionary is returned.

              Rect objects are not hashable and cannot be used as keys in a dictionary, only as values.
        """
        indices = []
        for key, value in dico.items():
            if self.colliderect( value ) is not None:
                indices.append( ( key, value ) )
        return indices

    def collidedirection( self, rect ):
        """Rect.collidedirection
        """
        direction = [ "center", "midtop", "midleft", "midbottom", "midright", "topleft", "topright", "bottomleft", "bottomright" ]
        index = self.colliderect( rect )
        if index is not None:
            return direction[ index ]

class Circle:
    def __init__( self, x, y, r, e=None ):
        self.coords = []
        self._origin = ( x, y, r, e )
        self.circle( x, y, r, e )

    def circle( self, posx, posy, radius, extent=None ):
        position = posx, posy
        angle = 0.0
        fullcircle = 360.0
        invradian = math.pi / ( fullcircle * 0.5 )
        if extent is None:
            extent = fullcircle
        frac = abs( extent ) / fullcircle
        steps = 1 + int( min( 11 + abs( radius ) / 6.0, 59.0 ) * frac )
        #steps *= 2
        w = 1.0 * extent / steps
        w2 = 0.5 * w
        distance = 2.0 * radius * math.sin( w2 * invradian )
        if radius < 0:
            distance, w, w2 = -distance, -w, -w2
        angle = ( angle + w2 ) % fullcircle
        for i in range( steps ):
            x0, y0 = start = position
            x1 = x0 + distance * math.cos( angle * invradian )
            y1 = y0 - distance * math.sin( angle * invradian )

            x0, y0 = position
            position = map( float, ( x1, y1 ) )
            dx = float( x1 - x0 )
            dy = float( y1 - y0 )
            distance2 = math.hypot( dx, dy )
            nhops = int( distance2 )
            try:
                for i in range( 1, 1+nhops ):
                    self.coords.append((
                        x0 + dx * i / nhops,
                        y0 + dy * i / nhops
                        ))
            except:
                pass
            angle = ( angle + w ) % fullcircle
        angle = ( angle + -w2 ) % fullcircle

    def removeDouble(self):
        # cleanup remove double 
        coords = []
        for pos in self.coords:
            pos = map(int, pos)
            if pos not in coords:
                coords.append(pos)
        self.coords = coords

    def __repr__( self ):
        return "<circle(%s,%s)>" % ( self._origin, self.coords )


if  __name__ == "__main__":
    #print Rect( 0, 0, 0, 0 )
    import sys
    sys.path.append("../../")
    import mouse
    import time
    from datetime import timedelta
    st = time.clock()

    radius = 360    
    circ = Circle( 800, 900, radius, -360 )
    coords = circ.coords
    print len(coords)
    circ.removeDouble()
    #coords = circ.coords
    print len(coords)-len(circ.coords)

    coords = circ.coords
    duration = 1.0
    wait = max(.001, duration/(len(coords)+1.0))
    print wait
    #lwait = range(0, len(coords)+1, 2)
    for i, pos in enumerate(coords):
        #print map(int, pos)
        mouse.move(*pos)
        #if i in lwait:
        time.sleep(wait)

    print str(timedelta(0, (time.clock() - st), 0))
    #print min( coords ), max( coords )

    # rect = Rect( 600, 300, 80, 120 )
    # print rect
    # rect.move( 500, 360 )
    # print rect
    # rect.resize( 256, 256 )
    # print rect
    #point = rect.collidelistall( coords )
    
    #center = coords[ int( len( point )/2 ) ]
    #print "centerpoint", center
    #for p in point:
    #    print coords[ p ]

    #print rect
    #print rect.center

    #print rect.midtop
    #print rect.midleft
    #print rect.midbottom
    #print rect.midright

    #print random.triangular(10, 20)
    #print random.triangular(10, 20)
