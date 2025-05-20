import sys
import os

import ctypes
from ctypes import *

rootdir = '/Users/gennadiryan/Documents/kestrel/jl2py/target'
bindir = os.path.join(rootdir, 'bin') # placeholder; directory need not exist (only passed since Julia uses JULIA_BINDIR to set default system search paths; may be unnecessary)
libdir = os.path.join(rootdir, 'lib')
depotdir = os.path.join(rootdir, 'share', 'julia') # must be sysimage DEPOT_PATH/LOAD_PATH

libjulia = os.path.join(libdir, 'libjulia.dylib') # can be generic libjulia
libpiccolo = os.path.join(libdir, 'libpiccolo.dylib') # must be sysimage

lib = ctypes.cdll.LoadLibrary(libjulia) # loading libjulia into `_lib`, then loading libpiccolo into `lib`, and proceeding as below, solves the problem of `jl_typeof` being unavailable from lib
lib.jl_init_with_image.argtypes = [c_char_p, c_char_p]
lib.jl_init_with_image.restype = None
lib.jl_eval_string.argtypes = [c_char_p]
lib.jl_eval_string.restype = c_void_p

lib.jl_init_with_image(bindir.encode(), libpiccolo.encode())
