import os
import random
from ctypes import cdll


class JuliaLib:
    def __init__(self, libpath):
        self.libpath = libpath
        self.lib = cdll.LoadLibrary(self.libpath)

    def __enter__(self):
        self.lib.init_julia(0, None)
        return self.lib
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lib.shutdown_julia(0)


def run():
    libdir = "target/lib"
    libname = "libjl2py.dylib"
    libpath = os.path.join(libdir, libname)
    # libpath = os.path.join("/Users/gennadiryan/Documents/kestrel", libdir, libname)

    libfunc = '_inc32'

    with JuliaLib(libpath) as jl2py:
        for i in range(100):
            x = int(random.random() * 100)
            print('(x, f(x)) = ({}, {})'.format(x, (getattr(jl2py, libfunc))(x)))


# cmd = "DYLD_FALLBACK_LIBRARY_PATH=target/lib:target/lib/julia python3 main.py"
if __name__ == '__main__':
    run()
