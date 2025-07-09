import os
import ctypes

from .utils import _getattr, _setattr


class _CdllLib:
    # TODO: Improve error handling on failure to load library
    def __init__(self, libpath):
        try:
            # libjulia = os.path.join(os.path.split(libpath)[0], 'libjulia.dylib')
            # self.lib = ctypes.cdll.LoadLibrary(libjulia)
            # self.libpath = libpath
            self.lib = ctypes.cdll.LoadLibrary(libpath)
        except OSError as e:
            raise e
        finally:
            self.lib_needs_shutdown = False

    def init_lib(self, funcs=None, vars=None):
        self.lib.init_julia(0, None)

        # self.lib.jl_init_with_image.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        # self.lib.jl_init_with_image.restype = None
        # self.lib.jl_init_with_image('/Users/gennadiryan/Documents/kestrel/jl2py/target/bin'.encode(), '/Users/gennadiryan/Documents/kestrel/jl2py/target/lib/libpiccolo.dylib'.encode())
        # # self.lib.jl_init_with_image(os.path.join(os.path.split(os.path.split(self.libpath)[0])[0], 'bin').encode(), os.path.join(os.path.split(self.libpath)[0], 'libpiccolo.dylib').encode())
        
        self.lib_needs_shutdown = True
        # print('Success')

        # self.funcs = dict([(name, self._register_func(name, argtypes=argtypes, restype=restype)) for name, (argtypes, restype) in funcs.items()] if funcs is not None else [])
        # self.vars = dict([(name, self._register_var(name, vartype)) for name, vartype in vars.items()] if vars is not None else [])
        self.funcs = self.register_funcs(funcs)
        self.vars = self.register_vars(vars)

    def shutdown_lib(self):
        if self.lib_needs_shutdown:
            # # self.lib.shutdown_julia(0)
            # self.lib.jl_atexit_hook(0)
            # # print('Shutdown julia')
            
            self.lib.shutdown_julia(0)

    def register_funcs(self, funcs):
        return dict([(name, func) for name, func in ([(name, self.register_func(name, argtypes=argtypes, restype=restype)) for name, (argtypes, restype) in funcs.items()] if funcs is not None else []) if func is not None])

    def register_func(self, name, argtypes=None, restype=None):
        func = getattr(self.lib, name, None)

        if func is not None:
            func.argtypes = [*argtypes] if argtypes is not None else None
            func.restype = restype if restype is not None else None
            # return lambda *args, **kwargs: (lambda _: restype(_) if restype is not None else _)(getattr(self.lib, name, None)(*args, **kwargs))
            # return lambda *args, **kwargs: getattr(self.lib, name, None)(*args, **kwargs)
            return func

        return None
    
    def register_vars(self, vars):
        return dict([(name, var) for name, var in ([(name, self.register_var(name, vartype)) for name, vartype in vars.items()] if vars is not None else []) if var is not None])

    def register_var(self, name, vartype=None):
        if vartype is not None:
            return lambda: vartype.in_dll(self.lib, name)
        
        return None
    
    def __del__(self):
        self.shutdown_lib()
        # print('Bye!')
    

class CdllLib(object):
    def __init__(self, lib, prefix=''):
        _setattr(self, 'lib', lib)
        _setattr(self, 'prefix', prefix)
        _setattr(self, 'attrs', dict(**lib.funcs, **lib.vars))
    
    def __getattribute__(self, name):
        return _getattr(self, 'attrs').get('{}{}'.format(_getattr(self, 'prefix'), name), None)
    
    def __dir__(self):
        prefix = _getattr(self, 'prefix')
        return sorted([k[len(prefix):] for k in _getattr(self, 'attrs').keys() if k[:len(prefix)] == prefix])
