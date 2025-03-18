import ctypes
from ctypes import *
lib = ctypes.cdll.LoadLibrary('/Users/gennadiryan/Documents/kestrel/jl2py/target/lib/libjulia.dylib')
lib.jl_init_with_image.argtypes = [c_char_p, c_char_p]
lib.jl_init_with_image.restype = None
lib.jl_eval_string.argtypes = [c_char_p]
lib.jl_eval_string.restype = c_void_p

lib.jl_init_with_image(b'/Users/gennadiryan/Documents/kestrel/jl2py/target/bin', b'/Users/gennadiryan/Documents/kestrel/jl2py/target/lib/libpiccolo.dylib')

