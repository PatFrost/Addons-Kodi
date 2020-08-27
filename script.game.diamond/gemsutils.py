
from copy import deepcopy
from traceback import print_exc


# index match excludes_X and limit_Y
match_excludes_X = range(6, 63, 8) + range(7, 64, 8)
match_limit_Y    = range(48)
def get_match_gems(gems):
    rem_gems = [] # for debug
    set_gems = set()
    for i, gem in enumerate(gems):
        if i in match_limit_Y:
            if gems[i+8] == gems[i+16] == gem:
                rem_gems.append((i, i+8, i+16, gem))
                set_gems.update([i, i+8, i+16])

        if i not in match_excludes_X:
            if gems[i+1] == gems[i+2] == gem:
                rem_gems.append((i, i+1, i+2, gem))
                set_gems.update([i, i+1, i+2])

    #print rem_gems
    #print sorted(set_gems) #gems
    return sorted(set_gems)


def get_hint(gems):
    excludes_X = (1, range(7, 64, 8))
    excludes_Y = (8, range(56, 64))
    excludes   = [excludes_X, excludes_Y]

    hint = None
    gems_copy = deepcopy(gems)
    for i, gem in enumerate(gems_copy):
        for i_plus, exclude in excludes:
            if i not in exclude:
                # move + and get get_match_gems
                a, b = gems[i], gems[i+i_plus]
                gems[i], gems[i+i_plus] = b, a
                rem_gems = get_match_gems(gems)
                if rem_gems:
                    hint = (i, i+i_plus)
                    #print gems
                    #print i, rem_gems
                gems = deepcopy(gems_copy)
                if hint is not None:
                    break
        if hint is not None:
            break
    gems = deepcopy(gems_copy)
    return hint


# index plus
limit_plus = range(9, 15) + range(17, 23) + range(25, 31) + range(33, 39) + range(41, 47) + range(49, 55)
def has_plus(gems):
    # return center of plus
    center_plus = []
    try:
        for gem in gems:
            if gem in limit_plus and gem-1 in gems and gem+1 in gems and gem-8 in gems and gem+8 in gems:
                center_plus.append(gem)
    except:
        print_exc()
    return center_plus


# index corner top left
limit_TL = range(0,  6) + range(8, 14) + range(16, 22) + range(24, 30) + range(32, 38) + range(40, 46)
# index corner top right
limit_TR = range(2,  8) + range(10, 16) + range(18, 24) + range(26, 32) + range(34, 40) + range(42, 48)
# index corner bottom left
limit_BL = range(16, 22) + range(24, 30) + range(32, 38) + range(40, 46) + range(48, 54) + range(56, 62)
# index corner bottom right
limit_BR = range(18, 24) + range(26, 32) + range(34, 40) + range(42, 48) + range(50, 56) + range(58, 64)
def has_L(gems):
    # return corner of L
    corner = []
    try:
        for gem in gems:
            if gem in limit_TL and gem+1 in gems and gem+2 in gems and gem+8 in gems and gem+16 in gems:
                corner.append(gem)
            if gem in limit_TR and gem-1 in gems and gem-2 in gems and gem+8 in gems and gem+16 in gems:
                corner.append(gem)
            if gem in limit_BL and gem+1 in gems and gem+2 in gems and gem-8 in gems and gem-16 in gems:
                corner.append(gem)
            if gem in limit_BR and gem-1 in gems and gem-2 in gems and gem-8 in gems and gem-16 in gems:
                corner.append(gem)
    except:
        print_exc()
    return corner


# index center top
limit_T = range(1,  7) + range(9, 15) + range(17, 23) + range(25, 31) + range(33, 39) + range(41, 47)
# index center bottom
limit_B = range(17, 23) + range(25, 31) + range(33, 39) + range(41, 47) + range(49, 55) + range(57, 63)
# index center left
limit_L = range(8, 14) + range(16, 22) + range(24, 30) + range(32, 38) + range(40, 46) + range(48, 54)
# index center right
limit_R = range(10, 16) + range(18, 24) + range(26, 32) + range(34, 40) + range(42, 48) + range(50, 56)
def has_T(gems):
    # return center of T
    center_t = []
    try:
        for gem in gems:
            if gem in limit_T and gem-1 in gems and gem+1 in gems and gem+8 in gems and gem+16 in gems:
                center_t.append(gem)
            if gem in limit_B and gem-1 in gems and gem+1 in gems and gem-8 in gems and gem-16 in gems:
                center_t.append(gem)
            if gem in limit_L and gem+1 in gems and gem+2 in gems and gem-8 in gems and gem+8 in gems:
                center_t.append(gem)
            if gem in limit_R and gem-1 in gems and gem-2 in gems and gem-8 in gems and gem+8 in gems:
                center_t.append(gem)
    except:
        print_exc()
    return center_t


def get_explosion(bomb_index):
    explosion = [bomb_index]
    # first check corner
    if bomb_index == 0:
        explosion += [bomb_index+1, bomb_index+8, bomb_index+9]
    elif bomb_index == 7:
        explosion += [bomb_index-1, bomb_index+7, bomb_index+8]
    elif bomb_index == 56:
        explosion += [bomb_index-8, bomb_index-7, bomb_index+1]
    elif bomb_index == 63:
        explosion += [bomb_index-9, bomb_index-8, bomb_index-1]
    else:
        if bomb_index in range(8, 56, 8):
            for i in [-8, -7, 1, 8, 9]:
                explosion.append(bomb_index + i)

        elif bomb_index in range(15, 63, 8):
            for i in [-9, -8, -1, 7, 8]:
                explosion.append(bomb_index + i)

        else:
            for i in [-9, -8, -7, -1, 1, 7, 8, 9]:
                add_index = bomb_index + i
                if 0 <= add_index <= 63:
                    explosion.append(add_index)

    return explosion


'''
def splitlist(iterable, start=0, step=8, end=0):
    """Return a list containing an slice of iterable.
    start (!) defaults to 0.; step is split index, (!) defaults to 8.; end (!) defaults to 0.
    For example, splitlist(range(4)) returns [[0, 1, 2, 3]].
    """
    try:
        splited = []
        if end <= 0:
            end = len(iterable)

        for index in xrange(step, end, step):
            splited.append(iterable[start:index])
            start = index
        splited.append(iterable[start:end])

        return splited
    except:
        print_exc()

    return [iterable]

#import random
#GEMS = range(1, 6)
#random.shuffle(GEMS)
#gems = [random.choice(GEMS) for i in range(64)]

gems = [
    1, 3, 1, 1, 2, 2, 4, 4,
    4, 2, 4, 5, 4, 3, 1, 2,
    1, 4, 1, 2, 4, 2, 2, 1,
    3, 5, 4, 4, 3, 1, 2, 2,
    3, 4, 3, 3, 4, 3, 1, 3,
    2, 1, 4, 2, 5, 2, 5, 5,
    3, 5, 1, 4, 1, 4, 5, 1,
    5, 2, 4, 2, 5, 4, 1, 4
]
import time
t1 = time.time()
print get_hint(gems)
print time.time() - t1

#rem_gems = get_match_gems(gems)
#print rem_gems
#print has_T(rem_gems)
'''


#import random
#bomb_index = random.choice(range(64))
#print get_explosion(1)

#get_explosion(7)
#get_explosion(56)
#get_explosion(63)

#print splitlist(range(64))
# [0,  1,  2,  3,  4,  5,  6, 7],
# [8,  9, 10, 11, 12, 13, 14, 15],
# [16, 17, 18, 19, 20, 21, 22, 23],
# [24, 25, 26, 27, 28, 29, 30, 31],
# [32, 33, 34, 35, 36, 37, 38, 39],
# [40, 41, 42, 43, 44, 45, 46, 47],
# [48, 49, 50, 51, 52, 53, 54, 55],
# [56, 57, 58, 59, 60, 61, 62, 63]

