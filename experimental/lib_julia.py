from .lib_defaults import libpath as default_libpath, libfuncs, libvars
from .lib_utils import CdllLib, _CdllLib


def init_jl(libpath=default_libpath):
    lib = _CdllLib(libpath)
    lib.init_lib(funcs=libfuncs, vars=libvars)
    
    return CdllLib(lib, prefix='jl_')