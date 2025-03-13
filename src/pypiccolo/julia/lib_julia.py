from .lib_defaults import libpath as default_libpath, libfuncs, libvars
from .lib_utils import CdllLib, _CdllLib


# def init_jl(libpath=default_libpath):
#     lib = _CdllLib(libpath)
#     lib.init_lib(funcs=libfuncs, vars=libvars)
    
#     return CdllLib(lib, prefix='jl_')

class init_jl:
    """
    This class can only be "instantiated" once, when it instantiates the shared library upon which the package depends
    Every subsequent "instantiation" of the class returns the same shared library
    TODO: move this funcitonality somewhere more appropriate (like CdllLib), so that the class returns an object of its own type (adhering to Pythonic norms)
    """

    jl = None

    def __new__(cls, libpath=default_libpath):
        if cls.jl is None:
            try:
                lib = _CdllLib(libpath)
                lib.init_lib(funcs=libfuncs, vars=libvars)

                cls.jl = CdllLib(lib, prefix='jl_')
            except OSError as e:
                raise e
        
        return cls.jl
