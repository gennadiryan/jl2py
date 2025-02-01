import os
import ctypes


class JuliaLib:
    def __init__(self, bindir, libdir, libname='julia', libext='dylib', sysimg=None):
        self.bindir = bindir
        self.libdir = libdir

        self.libpath = os.path.join(bindir, libdir, f'lib{libname}.{libext}')
        self.sysimg = sysimg

        # self.lib = ctypes.cdll.LoadLibrary(self.libpath)
        self.lib = ctypes.CDLL(self.libpath, ctypes.RTLD_GLOBAL)
        self.load_fns()

    def __enter__(self):
        if self.sysimg is None:
            self.lib.jl_init()
        else:
            self.lib.jl_init_with_image(self.bindir.encode(), self.sysimg.encode())
        return self
    
    def eval_string(self, s):
        self.lib.jl_eval_string(s.encode())
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lib.jl_atexit_hook(0)

    def load_fns(self):
        jl_init = self.lib.jl_init
        assert jl_init is not None
        jl_init.argtypes = None
        jl_init.restype = None
        
        jl_atexit_hook = self.lib.jl_atexit_hook
        assert jl_atexit_hook is not None
        jl_atexit_hook.argtypes = [ctypes.c_int,]
        jl_atexit_hook.restype = None

        jl_eval_string = self.lib.jl_eval_string
        assert jl_eval_string is not None
        jl_eval_string.argtypes = [ctypes.c_char_p,]
        jl_eval_string.restype = ctypes.c_void_p



if __name__ == '__main__':
    julia_sys_bindir = "/Users/gennadiryan/.julia/juliaup/julia-1.11.2+0.aarch64.apple.darwin14/bin" # Sys.BINDIR
    julia_base_libdir = "../lib" # Base.LIBDIR
    # julia_libdir = os.path.join(julia_sys_bindir, julia_base_libdir)

    # julia_libname = 'libjulia'
    # julia_libext = 'dylib' # Linux: 'so'; Mac: 'dylib'; Windows: 'dll'
    # julia_libpath = os.path.join(julia_libdir, f'{julia_libname}.{julia_libext}')

    julia_sysimg = None

    with JuliaLib(julia_sys_bindir, julia_base_libdir) as jl:
        jl.eval_string('println("Hello, world!")')

