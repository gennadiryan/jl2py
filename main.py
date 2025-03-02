from collections import OrderedDict
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any, Generic, List, Optional, Set, Tuple, TypeVar, Union

import os
import random
import ctypes, _ctypes
import platform
from ctypes import cdll, c_int, c_char_p, c_void_p


class JuliaLib:
    def __init__(self, libpath):
        self.libpath = libpath
        self.lib = cdll.LoadLibrary(self.libpath)

    def __enter__(self):
        self.lib.init_julia(0, None)
        return self.lib
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lib.shutdown_julia(0)


class JuliaLibUtils:
    _primitive_types = {c_int,}
    _reference_types = {c_char_p, c_void_p}

    def __init__(self, lib, libfuncs):
        self.lib = lib

        for k, v in libfuncs.items():
            assert self._register_func(k, ty=v, ty_is_ref=v in self._reference_types) is not None, f'Failed to register function {k}'

    def _register_func(self, name: str, ty: Optional[Any] = None, ty_is_ref: Optional[bool] = None) -> Optional[Callable[..., Any]]:
        if len(name) == 0 or name[0] == '_':
            return None
        
        func = getattr(self.lib, name, None)
        if func is None:
            return None
        
        if ty is not None:
            setattr(func, 'restype', ty)
            if ty_is_ref:
                # func = lambda *args, **kwargs: ctypes.cast(func(*args, **kwargs), ty)
                func = (lambda f: (lambda *args, **kwargs: ctypes.cast(f(*args, **kwargs), ty)))(func)
        
        if getattr(self, name, None) is not None:
            return None
        setattr(self, name, func)

        return getattr(self, name, None)
        

def str2buf(s: str) -> _ctypes.Array:
    return ctypes.create_string_buffer(s.encode())


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


# cmd = "DYLD_FALLBACK_LIBRARY_PATH=target/lib:target/lib/julia python3 main.py"
if __name__ == '__main__':
    libdir = "target/lib"
    libname = "libjl2py.dylib" if platform.system() == "Darwin" else "libjl2py.so"
    libpath = os.path.join(libdir, libname)

    # libfuncs = dict(
    #     # # core data types
    #     # jl_typeof=c_void_p, # jl_value_t *

    #     # # basic predicates
    #     # jl_subtype=c_int, # int

    #     # # object identity
    #     # jl_egal=c_int, # int

    #     # # type predicates and basic operations
    #     # jl_isa=c_int, # int
    #     # jl_types_equal=c_int, # int
    #     # jl_type_union=c_void_p, # jl_value_t *
    #     # jl_type_intersection=c_void_p, # jl_value_t *

    #     # # constructors
    #     # jl_new_bits=c_void_p, # jl_value_t *
    #     # jl_new_struct=c_void_p, # jl_value_t *
    #     jl_symbol=c_void_p, # jl_sym_t *
    #     # # jl_box_{ty}=c_void_p, # jl_value_t *
    #     # jl_box_voidpointer=c_void_p, # jl_value_t *
    #     # jl_box_uint8pointer=c_void_p, # jl_value_t *
    #     # # jl_unbox_{ty}=({ty}, False), # {ty}
    #     jl_unbox_voidpointer=c_void_p, # void *
    #     # jl_unbox_uint8pointer=c_char_p, # uint8_t *
    #     # jl_get_size=c_int, # int

    #     # # structs
    #     # jl_get_nth_field=c_void_p, # jl_value_t *
    #     # jl_set_nth_field=None, # void
    #     # jl_field_isdefined=c_int, # int
    #     # jl_get_field=c_void_p, # jl_value_t *
    #     # jl_value_ptr=c_void_p, # jl_value_t *

    #     # # arrays
    #     # jl_ptr_to_array_1d=c_void_p, # jl_array_t *
    #     # jl_ptr_to_array=c_void_p, # jl_array_t *
    #     # jl_pchar_to_array=c_void_p, # jl_array_t *
    #     # jl_pchar_to_string=c_void_p, # jl_value_t *
    #     # jl_array_ptr_1d_push=None, # void
    #     # jl_array_ptr_1d_append=None, # void
    #     # jl_array_ptr=None, # void
    #     # jl_array_eltype=None, # void
    #     # jl_array_rank=c_int, # int

    #     # # strings
    #     jl_string_ptr=c_char_p, # const char *

    #     # # modules and global variables
    #     # jl_new_module=c_void_p, # jl_value_t *
    #     jl_get_global=c_void_p, # jl_value_t *
    #     # jl_set_global=None, # void
    #     # jl_set_const=None, # void

    #     # # initialization functions
    #     # julia_init=None, # void
    #     jl_init=None, # void
    #     jl_init_with_image=None, # void
    #     jl_is_initialized=c_int, # int
    #     jl_atexit_hook=None, # void

    #     # # code loading (parsing + evaluation)
    #     jl_eval_string=c_void_p, # jl_value_t *
    #     # jl_load=c_void_p, # jl_value_t *
        
    #     # # calling into julia
    #     jl_call=c_void_p,
    #     jl_call1=c_void_p,
    #     jl_call2=c_void_p,
    #     jl_call3=c_void_p,

    #     # # tasks and exceptions
    #     jl_exception_occurred=c_void_p,

    #     # # version information
    #     jl_ver_string=c_char_p, # const char *
    # )

    libfuncs = dict(
        # core data types
        jl_typeof=c_void_p, # jl_value_t *

        # basic predicates
        jl_subtype=c_int, # int

        # object identity
        jl_egal=c_int, # int

        # type predicates and basic operations
        jl_isa=c_int, # int
        jl_types_equal=c_int, # int
        jl_type_union=c_void_p, # jl_value_t *
        jl_type_intersection=c_void_p, # jl_value_t *

        # constructors
        jl_new_bits=c_void_p, # jl_value_t *
        jl_new_struct=c_void_p, # jl_value_t *
        jl_symbol=c_void_p, # jl_sym_t *
        # jl_box_{ty}=c_void_p, # jl_value_t *
        jl_box_int32=c_void_p, # jl_value_t *
        jl_box_voidpointer=c_void_p, # jl_value_t *
        jl_box_uint8pointer=c_void_p, # jl_value_t *
        # jl_unbox_{ty}=({ty}, False), # {ty}
        jl_unbox_int32=c_int, # jl_value_t
        jl_unbox_voidpointer=c_void_p, # void *
        jl_unbox_uint8pointer=c_char_p, # uint8_t *
        jl_get_size=c_int, # int

        # structs
        jl_get_nth_field=c_void_p, # jl_value_t *
        jl_set_nth_field=None, # void
        jl_field_isdefined=c_int, # int
        jl_get_field=c_void_p, # jl_value_t *
        jl_value_ptr=c_void_p, # jl_value_t *

        # arrays
        jl_ptr_to_array_1d=c_void_p, # jl_array_t *
        jl_ptr_to_array=c_void_p, # jl_array_t *
        jl_alloc_array_1d=c_void_p, # jl_array_t *
        jl_alloc_array_nd=c_void_p, # jl_array_t *
        jl_pchar_to_array=c_void_p, # jl_array_t *
        jl_pchar_to_string=c_void_p, # jl_value_t *
        jl_array_ptr_1d_push=None, # void
        jl_array_ptr_1d_append=None, # void
        jl_array_ptr=None, # void
        jl_array_eltype=None, # void
        jl_array_rank=c_int, # int

        # strings
        jl_string_ptr=c_char_p, # const char *

        # modules and global variables
        jl_new_module=c_void_p, # jl_value_t *
        jl_get_global=c_void_p, # jl_value_t *
        jl_set_global=None, # void
        jl_set_const=None, # void

        # initialization functions
        julia_init=None, # void
        jl_init=None, # void
        jl_init_with_image=None, # void
        jl_is_initialized=c_int, # int
        jl_atexit_hook=None, # void

        # code loading (parsing + evaluation)
        jl_eval_string=c_void_p, # jl_value_t *
        jl_load=c_void_p, # jl_value_t *
        
        # calling into julia
        jl_call=c_void_p,
        jl_call1=c_void_p,
        jl_call2=c_void_p,
        jl_call3=c_void_p,

        # tasks and exceptions
        jl_exception_occurred=c_void_p,

        # version information
        jl_ver_string=c_char_p, # const char *
    )

    lib = JuliaLib(libpath).__enter__()
    jl = JuliaLibUtils(lib, libfuncs)
