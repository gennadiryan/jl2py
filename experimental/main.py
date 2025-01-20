from collections import OrderedDict
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any, Generic, List, Optional, Set, Tuple, TypeVar, Union

import os
import random
import ctypes, _ctypes
from ctypes import cdll, c_int, c_int32, c_int64, c_uint, c_uint32, c_uint64, c_size_t, c_char_p, c_void_p


class JuliaLib:
    def __init__(self, libpath):
        self.libpath = libpath
        self.lib = cdll.LoadLibrary(self.libpath)

    def __enter__(self):
        self.lib.init_julia(0, None)
        return self.lib
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lib.shutdown_julia(0)


# class JuliaLibUtils:
#     _primitive_types = {c_int,}
#     _reference_types = {c_char_p, c_void_p}

#     def __init__(self, lib, libfuncs):
#         self.lib = lib

#         for k, v in libfuncs.items():
#             assert self._register_func(k, ty=v, ty_is_ref=v in self._reference_types) is not None, f'Failed to register function {k}'

#     def _register_func(self, name: str, ty: Optional[Any] = None, ty_is_ref: Optional[bool] = None) -> Optional[Callable[..., Any]]:
#         if len(name) == 0 or name[0] == '_':
#             return None
        
#         func = getattr(self.lib, name, None)
#         if func is None:
#             return None
        
#         if ty is not None:
#             setattr(func, 'restype', ty)
#             if ty_is_ref:
#                 # func = lambda *args, **kwargs: ctypes.cast(func(*args, **kwargs), ty)
#                 func = (lambda f: (lambda *args, **kwargs: ctypes.cast(f(*args, **kwargs), ty)))(func)
        
#         if getattr(self, name, None) is not None:
#             return None
#         setattr(self, name, func)

#         return getattr(self, name, None)
        

# def str2buf(s: str) -> _ctypes.Array:
#     return ctypes.create_string_buffer(s.encode())

class as_object(object):
    def __init__(self, prefix, **kwargs):
        object.__setattr__(self, 'prefix', prefix)
        object.__setattr__(self, 'it', kwargs)
    def __getattribute__(self, name):
        return object.__getattribute__(self, 'it').get(f'{object.__getattribute__(self, 'prefix')}{name}', None)
    def __dir__(self):
        prefix = object.__getattribute__(self, 'prefix')
        return sorted([k[len(prefix):] for k in object.__getattribute__(self, 'it').keys() if k[:len(prefix)] == prefix])


class CDLLUtils:
    def __init__(self, lib, funcs=None):
        self.lib = lib
        self.funcs = dict([(name, self._register_func(name, argtypes=argtypes, restype=restype)) for name, (argtypes, restype) in funcs.items()] if funcs is not None else [])
        # self.funcs = funcs
    
    def _register_func(self, name, argtypes=None, restype=None):
        func = getattr(self.lib, name, None)

        if func is not None:
            func.argtypes = [*argtypes] if argtypes is not None else None
            # func.argtypes = (*argtypes,) if argtypes is not None else None
            func.restype = restype if restype is not None else None

        return func



# class JuliaVal:
#     """
#     Wrapper class for Julia objects of type T <: Any

#     Attributes:
#         _lib (ctypes.CDLL): shared library from which Julia C API utility functions are accessed
#         _val (ctypes.c_void_p): jl_value_t * underlying the value
#         _convert_to (Callable): handler for converting 

#     TODO:
#         - streamline getting jl_* fns from _lib and setting ctypes type signature (as in JuliaLibUtils)
#         - in __getattribute__, replace _get_field with (_field_idx, _get_nth_field) (akin to (_field_idx, _set_nth_field) in __setattr__)

#         - handle global rooting (to prevent GC on Julia side) at __init__ (and/or __new__?), __del__, __setattr__, and __delattr__
#         - wrap julia library fns (eval_string, call, call[1,2,3], etc.) into Dict or similar structure to simplify their access within methods/avoid polluting each method local namespaces
#         - clarify semantics for _convert_to (currently accepts either raw C ptrs or accesses the _val field of a JuliaVal; used on args upon function call)
#         - determine semantics for _convert_from (used on retvalue after function call)
#         - determine semantics for storing Julia datatypes and their connection with _convert_to, _convert_from implementation
#         - implement __repr__
#         - implement __dir__
#         - optional; implement __eq__ (underlied by jl_egal) and possibly __hash__
#         - optional; implement __lt__/__gt__ if the underlying Julia type allows for it
#         - optional; implement __str__, __format__
#         - catch and forward Julia exceptions

#     DONE:
#         - implement __setattr__
#     """

#     def __init__(self, lib, val):
#         _getattr = lambda *_: object.__getattribute__(self, *_)
#         _setattr = lambda *_: object.__setattr__(self, *_)

#         _setattr('_lib', lib)
#         _setattr('_val', val)

#         _setattr('_convert_to', lambda _: object.__getattribute__(_, '_val') if isinstance(_, JuliaVal) else _)

#         _setattr('_eval_string', get_fn_eval_string(lib))
#         _setattr('_call', get_fn_call(lib))
#         _setattr('_call1', get_fn_call1(lib))
#         _setattr('_call2', get_fn_call2(lib))
#         _setattr('_call3', get_fn_call3(lib))
#         _setattr('_typeof', get_fn_typeof(lib))
#         _setattr('_symbol', get_fn_symbol(lib))
#         _setattr('_field_index', get_fn_field_index(lib))
#         _setattr('_get_field', get_fn_get_field(lib))
#         _setattr('_set_nth_field', get_fn_set_nth_field(lib))

#         # _setattr('_val_getproperty', _getattr('_eval_string')(b'getproperty'))
    
#     def __getattribute__(self, name):
#         if (len(name) == 0) or (len(name) > 0 and name[0] == '_'):
#             raise AttributeError(f'{type(self)} object has no attribute {name}')
        
#         _getattr = lambda *_: object.__getattribute__(self, *_)
#         _setattr = lambda *_: object.__setattr__(self, *_)
        
#         _val = _getattr('_val')

#         # _eval_string = _getattr('_eval_string')
#         # _call1 = _getattr('_call1')
#         # _call2 = _getattr('_call2')
#         # _symbol = _getattr('_symbol')
#         _get_field = _getattr('_get_field')
        
#         # _val_getproperty = _getattr('_val_getproperty') # has sig jl_value_t *getproperty(jl_value_t *, jl_sym_t *); equivalent to getfield() unless overloaded by user-defined struct

#         # _prop = _call2(_val_getproperty, _val, _symbol(name.encode())) # TODO: replace with jl_get_field() call
#         _prop = _get_field(_val, name.encode()) # TODO: replace with jl_get_nth_field (for consistency, particularly wrt error handling)
#         if _prop is None:
#             raise AttributeError(f'{type(self)} object has no attribute {name}')
#         return _prop
    
#     def __setattr__(self, name, value):
#         if (len(name) == 0) or (len(name) > 0 and name[0] == '_'):
#             raise AttributeError(f'{type(self)} object has no attribute {name}')
        
#         _getattr = lambda *_: object.__getattribute__(self, *_)
#         _setattr = lambda *_: object.__setattr__(self, *_)
        
#         _val = _getattr('_val')

#         _typeof = _getattr('_typeof')
#         _symbol = _getattr('_symbol')
#         _field_index = _getattr('_field_index')
#         _set_nth_field = _getattr('_set_nth_field')

#         idx = _field_index(_typeof(_val), _symbol(name.encode()), 0) # TODO: err = 1; allow native Julia error to propagate properly
#         if idx < 0:
#             raise AttributeError(f'{type(self)} object has no attribute {name}')
#         _set_nth_field(_val, idx, value) # TODO: catch occurrence of value not being a valid (jl_value_t *), in which case field assignment fails silently (can be as simple as raising exception if not _get_nth_field(_val, idx) != value)
    
#     def __call__(self, *args, **kwds):
#         _getattr = lambda *_: object.__getattribute__(self, *_)
#         _setattr = lambda *_: object.__setattr__(self, *_)

#         _val = _getattr('_val')
#         _call = _getattr('_call')

#         _args = get_ctypes_arr(c_void_p, *map(_getattr('_convert_to'), args))
#         _nargs = len(args)

#         _res = _call(_val, _args, _nargs) # TODO: handle bad return values and possibly exceptions
#         return _res


class JuliaVal:
    """
    Wrapper class for Julia objects of type T <: Any

    Attributes:
        _lib (ctypes.CDLL): shared library from which Julia C API utility functions are accessed
        _val (ctypes.c_void_p): jl_value_t * underlying the value
        _convert_to (Callable): handler for converting 

    TODO:
        - streamline getting jl_* fns from _lib and setting ctypes type signature (as in JuliaLibUtils)
        - in __getattribute__, replace _get_field with (_field_idx, _get_nth_field) (akin to (_field_idx, _set_nth_field) in __setattr__)

        - handle global rooting (to prevent GC on Julia side) at __init__ (and/or __new__?), __del__, __setattr__, and __delattr__
        - wrap julia library fns (eval_string, call, call[1,2,3], etc.) into Dict or similar structure to simplify their access within methods/avoid polluting each method local namespaces
        - clarify semantics for _convert_to (currently accepts either raw C ptrs or accesses the _val field of a JuliaVal; used on args upon function call)
        - determine semantics for _convert_from (used on retvalue after function call)
        - determine semantics for storing Julia datatypes and their connection with _convert_to, _convert_from implementation
        - implement __repr__
        - implement __dir__
        - optional; implement __eq__ (underlied by jl_egal) and possibly __hash__
        - optional; implement __lt__/__gt__ if the underlying Julia type allows for it
        - optional; implement __str__, __format__
        - catch and forward Julia exceptions

    DONE:
        - implement __setattr__
    """

    def __init__(self, fns, val):
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        _setattr('fns', fns)
        _setattr('val', val)

        _setattr('_convert_to', lambda _: object.__getattribute__(_, 'value') if isinstance(_, JuliaVal) else _)

        # _setattr('_eval_string', get_fn_eval_string(lib))
        # _setattr('_call', get_fn_call(lib))
        # _setattr('_call1', get_fn_call1(lib))
        # _setattr('_call2', get_fn_call2(lib))
        # _setattr('_call3', get_fn_call3(lib))
        # _setattr('_typeof', get_fn_typeof(lib))
        # _setattr('_symbol', get_fn_symbol(lib))
        # _setattr('_field_index', get_fn_field_index(lib))
        # _setattr('_get_field', get_fn_get_field(lib))
        # _setattr('_set_nth_field', get_fn_set_nth_field(lib))

        # _setattr('_val_getproperty', _getattr('_eval_string')(b'getproperty'))
    
    def __getattribute__(self, name):
        if (len(name) == 0) or (len(name) > 0 and name[0] == '_'):
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)
        
        fns = _getattr('fns')
        val = _getattr('val')

        # # _eval_string = _getattr('_eval_string')
        # # _call1 = _getattr('_call1')
        # # _call2 = _getattr('_call2')
        # # _symbol = _getattr('_symbol')
        # _get_field = _getattr('_get_field')
        
        # # _val_getproperty = _getattr('_val_getproperty') # has sig jl_value_t *getproperty(jl_value_t *, jl_sym_t *); equivalent to getfield() unless overloaded by user-defined struct

        # # _prop = _call2(_val_getproperty, _val, _symbol(name.encode())) # TODO: replace with jl_get_field() call
        # _prop = _get_field(_val, name.encode()) # TODO: replace with jl_get_nth_field (for consistency, particularly wrt error handling)
        # if _prop is None:
        #     raise AttributeError(f'{type(self)} object has no attribute {name}')
        # return _prop
    
        # fld = fns.get_field(val, name.encode())
        idx = fns.field_index(fns.typeof(val), fns.symbol(name.encode()), 0)
        # if fld is None:
        if idx < 0:
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        fld = fns.get_nth_field(val, idx)
        if fld is None:
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        return fld
    
    def __setattr__(self, name, value):
        if (len(name) == 0) or (len(name) > 0 and name[0] == '_'):
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
        val = _getattr('val')
        
        # _typeof = _getattr('_typeof')
        # _symbol = _getattr('_symbol')
        # _field_index = _getattr('_field_index')
        # _set_nth_field = _getattr('_set_nth_field')

        # idx = _field_index(_typeof(_val), _symbol(name.encode()), 0) # TODO: err = 1; allow native Julia error to propagate properly
        # if idx < 0:
        #     raise AttributeError(f'{type(self)} object has no attribute {name}')
        # _set_nth_field(_val, idx, value) # TODO: catch occurrence of value not being a valid (jl_value_t *), in which case field assignment fails silently (can be as simple as raising exception if not _get_nth_field(_val, idx) != value)

        idx = fns.field_index(fns.typeof(val), fns.symbol(name.encode()), 0)
        if idx < 0:
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        fns.set_nth_field(val, idx, value)
        # fld = fns.get_nth_field(val, idx)
        # if fld is None:
        #     raise AttributeError(f'{type(self)} object has no attribute {name}')
        # if fns.get_nth_field(val, idx) != value:
        #     raise ValueError()
        if fns.get_nth_field(val, idx) != value:
            raise ValueError()
    
    def __call__(self, *args, **kwds):
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
        val = _getattr('val')

        args = get_ctypes_arr(c_void_p, *map(_getattr('_convert_to'), args))
        nargs = len(args)

        res = fns.call(val, args, nargs) # TODO: handle bad return values and possibly exceptions
        return res
    

def init_refs(lib, fns):
    jl_base_module = c_void_p.in_dll(lib, 'jl_base_module')
    jl_main_module = c_void_p.in_dll(lib, 'jl_main_module')

    jl_any_value = c_void_p.in_dll(lib, 'jl_any_value')

    # fns.

# def get_fn_eval_string(lib):
#     jl_eval_string = lib.jl_eval_string
#     jl_eval_string.argtypes = [c_char_p,]
#     jl_eval_string.restype = c_void_p
#     return jl_eval_string

# def get_fn_call(lib):
#     jl_call = lib.jl_call
#     jl_call.argtypes = [c_void_p, c_void_p, c_uint32]
#     jl_call.restype = c_void_p
#     return jl_call

# def get_fn_call1(lib):
#     jl_call1 = lib.jl_call1
#     jl_call1.argtypes = [c_void_p, c_void_p]
#     jl_call1.restype = c_void_p
#     return jl_call1

# def get_fn_call2(lib):
#     jl_call2 = lib.jl_call2
#     jl_call2.argtypes = [c_void_p, c_void_p, c_void_p]
#     jl_call2.restype = c_void_p
#     return jl_call2

# def get_fn_call3(lib):
#     jl_call3 = lib.jl_call3
#     jl_call3.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p]
#     jl_call3.restype = c_void_p
#     return jl_call3

# def get_fn_typeof(lib):
#     jl_typeof = lib.jl_typeof
#     jl_typeof.argtypes = [c_void_p,]
#     jl_typeof.restype = c_void_p
#     return jl_typeof

# def get_fn_symbol(lib):
#     jl_symbol = lib.jl_symbol
#     jl_symbol.argtypes = [c_char_p,]
#     jl_symbol.restype = c_void_p
#     return jl_symbol

# def get_fn_field_index(lib):
#     jl_field_index = lib.jl_field_index
#     jl_field_index.argtypes = [c_void_p, c_void_p, c_int]
#     jl_field_index.restype = c_int
#     return jl_field_index

# def get_fn_get_field(lib):
#     jl_get_field = lib.jl_get_field
#     jl_get_field.argtypes = [c_void_p, c_char_p]
#     jl_get_field.restype = c_void_p
#     return jl_get_field

# def get_fn_set_nth_field(lib):
#     jl_set_nth_field = lib.jl_set_nth_field
#     jl_set_nth_field.argtypes = [c_void_p, c_size_t, c_void_p]
#     jl_set_nth_field.restype = None
#     return jl_set_nth_field


# def get_fn_box_int64(lib):
#     jl_box_int64 = lib.jl_box_int64
#     jl_box_int64.argtypes = [c_int64,]
#     jl_box_int64.restype = c_void_p
#     return jl_box_int64



def get_ctypes_arr(ty, *args):
    return (ty * len(args))(*args)


# def run_experimental(lib):
#     jl_eval = get_fn_eval_string(lib)
#     jl_call1 = get_fn_call1(lib)
#     println = jl_eval(b'println')

#     return jl_eval, jl_call1, println


# def run():
#     libdir = "target/lib"
#     libname = "libjl2py.dylib"
#     libpath = os.path.join(libdir, libname)

#     with JuliaLib(libpath) as jl2py:
#         x = 3
#         y = jl2py._inc32(x)
#         print('({}, {})'.format(x, y))

#         # libfunc = '_inc32'
#         # for i in range(100):
#         #     x = int(random.random() * 100)
#         #     print('(x, f(x)) = ({}, {})'.format(x, (getattr(jl2py, libfunc))(x)))


# map_abcs = dict([*map(lambda _: _[::-1], enumerate('abc'))])


# cmd = "DYLD_FALLBACK_LIBRARY_PATH=target/lib:target/lib/julia python3 main.py"
if __name__ == '__main__':
    libdir = "/Users/gennadiryan/.julia/dev/jl2py/target/lib"
    libname = "libjl2py.dylib"
    libpath = os.path.join(libdir, libname)

    libfuncs = dict(
        jl_eval_string=((c_char_p,), c_void_p),
        
        jl_call=((c_void_p, c_void_p, c_uint32,), c_void_p),
        jl_call1=((c_void_p,) * 2, c_void_p),
        jl_call2=((c_void_p,) * 3, c_void_p),
        jl_call3=((c_void_p,) * 4, c_void_p),

        jl_symbol=((c_char_p,), c_void_p),
        
        jl_typeof=((c_void_p,), c_void_p),

        jl_field_index=((c_void_p, c_void_p, c_int,), c_int),
        jl_get_field=((c_void_p, c_char_p,), c_void_p),
        jl_get_nth_field=((c_void_p, c_size_t,), c_void_p),
        jl_set_nth_field=((c_void_p, c_size_t, c_void_p,), None),
        
        jl_box_int64=((c_int64,), c_void_p),


        # # init_refs()
        # # jl_=((,), None),

        # jl_gc_enable=((,), None),

        # jl_get_binding_wr=((,), None),
        # jl_get_global=((,), None),
        # jl_checked_assignment=((,), None),

        # jl_apply_type2=((,), None),
    )

    lib = JuliaLib(libpath).__enter__()
    libutils = CDLLUtils(lib, funcs=libfuncs)
    # libfuncs = libutils.funcs

    # jl_eval, jl_call1, println = run_experimental(lib)
    # jl = box('jl_', **libfuncs)

    jl = as_object('jl_', **(libutils.funcs))
