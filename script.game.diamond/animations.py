# https://www.python.org/dev/peps/pep-0008/#code-lay-out

# constants animation

TILE_SIZE = 80
SCREEN_HEIGHT = -720

__effects = [
    'effect=slide start=0,0 end={},0 time=1000'.format(TILE_SIZE/2),
    'effect=slide start=0,0 end=-{},0 time=1000 delay=1000'.format(TILE_SIZE),
    'effect=slide start=0,0 end={},0 time=1000 delay=2000'.format(TILE_SIZE/2),
    'effect=fade start=100 end=0 time=4000 delay=1000',
    ]
ANIM_PTS_CONTROL = [('conditional', 'condition=true '+a) for a in __effects]

ANIM_PTS_OUT_SCREEN = 'condition=true effect=slide start=0,{} end=0,{} time=12000 tween=quadratic easing=out' #.format("{}", SCREEN_HEIGHT)

ANIM_DROP_GEM = 'condition=true effect=slide start=0,-{} time=1000 tween=quadratic easing=out'

ANIM_HINT = [(
    'conditional',
    'condition=true effect=zoom end=75 center=auto time=1000 loop=true acceleration=-1.1'
    )]

ANIM_ZOOM_OUT = [
    ('conditional', 'condition=true effect=zoom end=0 center=auto time=1000 delay=200'),
    ('conditional', 'condition=true effect=fade start=100 end=0 time=2000'),
    ]

ANIM_SWAP_RIGHT = [
    'condition=true effect=slide end={},0 time=600 tween=quadratic easing=out'.format(TILE_SIZE),
    'condition=true effect=slide end=-{},0 time=600 tween=quadratic easing=out'.format(TILE_SIZE),
    ]
ANIM_SWAP_LEFT = [
    'condition=true effect=slide end=-{},0 time=600 tween=quadratic easing=out'.format(TILE_SIZE),
    'condition=true effect=slide end={},0 time=600 tween=quadratic easing=out'.format(TILE_SIZE),
    ]
ANIM_SWAP_DOWN = [
    'condition=true effect=slide end=0,{} time=600 tween=quadratic easing=out'.format(TILE_SIZE),
    'condition=true effect=slide end=0,-{} time=600 tween=quadratic easing=out'.format(TILE_SIZE),
    ]
ANIM_SWAP_UP = [
    'condition=true effect=slide end=0,-{} time=600 tween=quadratic easing=out'.format(TILE_SIZE),
    'condition=true effect=slide end=0,{} time=600 tween=quadratic easing=out'.format(TILE_SIZE),
    ]

ANIM_STOP_SWAP = [('conditional', 'condition=true effect=slide end=0,0 time=0')]

ANIM_FIRST_SELECTED = [(
    'conditional',
    'condition=true effect=rotate start=0 end=360 ' \
    'center=auto time=1000 loop=true tween=bounce easing=out',
    )]
    