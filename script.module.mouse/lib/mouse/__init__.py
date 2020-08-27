
import sys

# The mouseModule is where we reference the platform-specific functions.
if sys.platform == 'win32':
    from .mouse_win import *
    
elif sys.platform == 'darwin':
    from .mouse_osx import *
    
else:
    from .mouse_x11 import *
