# import math

# def getAngles(A, B, C=0):
    # def angle(a, b, c):
        # return math.degrees(math.acos((c**2 - b**2 - a**2)/(-2.0 * a * b)))

    # C = C or math.hypot(A, B)
    # return angle(A, B, C), angle(B, C, A), angle(C, A, B)

# angA, angB, angC = map(round, getAngles(6, 6))

# # print (angA + angB + angC)
# # print angA, angB, angC
# # print (angA + angB + angC) == 180.0
# # print
# #assert (angA + angB + angC) == 180.0

# class Line:
    # def __init__(self, x1, y1, x2, y2):
        # self.x2 = (x2-x1)
        # self.y2 = (y2-y1)
        # self.x1 = 0
        # self.y1 = 0

        # self.angle    = self._angle()
        # self.distance = self._distance()

    # def _angle(self):
        # theta1 = math.atan2(self.y1, self.x1)
        # theta2 = math.atan2(self.y2, self.x2)
        # return (theta1 - theta2) * (180.0 / math.pi)

    # def _distance(self):
        # w = max(self.x1, self.x2) - min(self.x1, self.x2)
        # h = max(self.y1, self.y2) - min(self.y1, self.y2)
        # return math.hypot(w, h)

        

# class Vector:
    # def __init__(self, x, y):
        # self.x = x
        # self.y = y
        # self.theta = math.atan2(self.y, self.x)

# v1 = Vector(10, 10)
# v2 = Vector(10, -10)

# r = (v2.theta - v1.theta) * (180.0 / math.pi)

# w = max(v1.x, v2.x)-min(v1.x, v2.x)
# h = max(v1.y, v2.y)-min(v1.y, v2.y)
# d = math.hypot(w, h)

# # if r < 0:
    # # r += 360.0

# # print r
# # print d
# # print

# import cmath
# a_phase = cmath.phase(complex(630, 350)) #math.atan2(x.imag, x.real)
# b_phase = cmath.phase(complex(0, 0))
# print (a_phase - b_phase) * (180.0 / cmath.pi)
# print (b_phase - a_phase) * (180.0 / cmath.pi)
# print 

# line = Line(10, 10, 640, 360)
# print line.angle
# print round(line.distance)+10
# #45.0
# #141.421356237

# import itertools
# def pairwise(iterable, closewith=0):
    # "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    # a, b = itertools.tee(iterable+iterable[:closewith])
    # next(b, None)
    # return list(itertools.izip(a, b))
    
# print pairwise(range(0), 1)


from decimal import Decimal, DefaultContext

def divide(a, b):
    return DefaultContext.divide(Decimal(a),  Decimal(b))
z= divide("-10", 100)
if z:
    print "{}%".format(z)