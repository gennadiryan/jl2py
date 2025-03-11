from collections import OrderedDict
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any, Generic, List, Optional, Set, Tuple, TypeVar, Union

import sys
import os
import platform
import random
import ctypes, _ctypes
from ctypes import cdll, c_double, c_float, c_int, c_int32, c_int64, c_uint, c_uint32, c_uint64, c_size_t, c_char_p, c_void_p


class as_object(object):
    def __init__(self, prefix, **kwargs):
        object.__setattr__(self, 'prefix', prefix)
        object.__setattr__(self, 'it', kwargs)
    def __getattribute__(self, name):
        return object.__getattribute__(self, 'it').get(f'{object.__getattribute__(self, 'prefix')}{name}', None)
    def __dir__(self):
        prefix = object.__getattribute__(self, 'prefix')
        return sorted([k[len(prefix):] for k in object.__getattribute__(self, 'it').keys() if k[:len(prefix)] == prefix])


class JuliaLib:
    def __init__(self, libpath):
        self.libpath = libpath
        self.lib = cdll.LoadLibrary(self.libpath)

    def __enter__(self):
        self.lib.init_julia(0, None)
        return self.lib
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lib.shutdown_julia(0)


class CDLLUtils:
    def __init__(self, lib, funcs=None, vars=None):
        self.lib = lib
        self.funcs = dict([(name, self._register_func(name, argtypes=argtypes, restype=restype)) for name, (argtypes, restype) in funcs.items()] if funcs is not None else [])
        self.vars = dict([(name, self._register_var(name, vartype)) for name, vartype in vars.items()] if vars is not None else [])
    
    def _register_func(self, name, argtypes=None, restype=None):
        func = getattr(self.lib, name, None)

        if func is not None:
            func.argtypes = [*argtypes] if argtypes is not None else None
            # func.argtypes = (*argtypes,) if argtypes is not None else None
            func.restype = restype if restype is not None else None

        return func

    def _register_var(self, name, vartype=None):
        if vartype is not None:
            return lambda: vartype.in_dll(self.lib, name)
        
        return None


class JuliaVal:
    """
    Wrapper class for Julia objects of type T <: Any

    Attributes:
        fns (asobject): shared library wrapper from which Julia C API utility functions are accessed
        val (ctypes.c_void_p): jl_value_t * underlying the value
        _convert_to (Callable): handler for converting JuliaVal to raw value (if applicable) (should be removed once support for passing raw values to callables is rescinded)
        _convert_from (Callable): handler for converting raw value to JuliaVal

    TODO:
        - handle global rooting (to prevent GC on Julia side) at __init__ (and/or __new__?), __del__, __setattr__, and __delattr__ (partially implemented with JuliaValGC)
        - clarify semantics for _convert_to (currently accepts either raw C ptrs or accesses the _val field of a JuliaVal; used on args upon function call)
        - determine semantics for _convert_from (used on retvalue after function call)
        - determine semantics for storing Julia datatypes and their connection with _convert_to, _convert_from implementation
        - optional; implement __eq__ (underlied by jl_egal) and possibly __hash__
        - optional; implement __lt__/__gt__ if the underlying Julia type allows for it
        - optional; implement __str__, __format__
        - optional; implement __getitem__ (be careful with semantics; some types expect index, others expect symbol, others do not support it at all)
        - simplify JuliaValGC.__init__ so that it can call JuliaVal.__init__ (reduce boilerplate)
        - consider adding and/or replacing field access with property access (fields are type-specific, properties are value-specific)
        - ^^ consider adding and/or replacing `fieldnames` with `propertynames` (or their C equivalent implementation)
        - typecheck setattr
        - forward Julia exceptions
        - catch and forward Julia exceptions in places other than __call__

    DONE:
        - implement __setattr__

        - streamline getting jl_* fns from _lib and setting ctypes type signature (as in JuliaLibUtils)
        - in __getattribute__, replace _get_field with (_field_idx, _get_nth_field) (akin to (_field_idx, _set_nth_field) in __setattr__)
        - wrap julia library fns (eval_string, call, call[1,2,3], etc.) into Dict or similar structure to simplify their access within methods/avoid polluting each method local namespaces
        - catch and forward Julia exceptions

        - implement __repr__
        - implement __dir__
    """

    fns = None # placeholder

    def __init__(self, val):
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        # _setattr('fns', fns)
        fns = _getattr('fns')
        _setattr('val', val)

        _setattr('_convert_to', lambda _: object.__getattribute__(_, 'val') if isinstance(_, JuliaVal) else _)
        _setattr('_convert_from', lambda _: JuliaVal(_))

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
        # return fld
        # return JuliaVal(fns, fld)
        return _getattr('_convert_from')(fld)
    
    def __setattr__(self, name, value):
        if (len(name) == 0) or (len(name) > 0 and name[0] == '_'):
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
        val = _getattr('val')

        value = _getattr('_convert_to')(value)
        
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
    
    def __call__(self, *args, **kwargs):
        # if len(kwargs) > 0:
        #     print(kwargs)

        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
        val = _getattr('val')

        argsptr = get_ctypes_arr(c_void_p, *map(_getattr('_convert_to'), args))
        nargs = len(args)

        # TODO(jack-champagne): add kwargs call here
        res = fns.call(val, argsptr, nargs) # TODO: handle bad return values (i.e. `res is None` yet no exception thrown)

        # see github.com/JuliaLang/julia/test/embedding/embedding.c
        eo = fns.exception_occurred()
        if eo is not None:
            fns.call2(fns.get_global(fns.base_module(), 'showerror'.encode()), fns.stderr_obj(), eo)
            fns.printf(fns.stderr_stream(), '\n'.encode())
            return None

        # return res
        # return JuliaVal(fns, res)
        return _getattr('_convert_from')(res)

    # def __del__(self,):
    #     pass

    # def __delattr__(self, name):
    #     pass

    def __dir__(self,):
        # return list()

        """
        Consider simplifying implementation
        """

        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
        val = _getattr('val')

        ty = fns.typeof(val)
        ty_name = fns.get_nth_field(ty, fns.field_index(fns.typeof(ty), fns.symbol(b'name'), 0))
        ty_names = fns.get_nth_field(ty_name, fns.field_index(fns.typeof(ty_name), fns.symbol(b'names'), 0))
        ty_names_len = c_size_t.from_address(ty_names)
        
        ty_names_as_symbol = [c_void_p.from_address(ty_names + ctypes.sizeof(ty_names_len) + (ctypes.sizeof(c_void_p) * i)) for i in range(ty_names_len.value)]
        ty_names_as_str = [ctypes.string_at(name_as_symbol.value + (ctypes.sizeof(c_void_p) * 3)).decode() for name_as_symbol in ty_names_as_symbol]

        return ty_names_as_str

    def __repr__(self,):
        # return super().__repr__()

        # jl_base_module = c_void_p.in_dll(lib, 'jl_base_module')

        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
        val = _getattr('val')

        fn_repr = fns.get_global(fns.base_module(), fns.symbol(b'repr'))
        val_res = fns.call1(fn_repr, val)
        val_str = ctypes.string_at(fns.string_ptr(val_res)).decode()

        return val_str
    


# TODO: 
#   - study whether jl.gc_enable really does blow up memory without bound as claimed
#   - study whether jl.gc_enable is necesary at all (via setting breakpoints in jl_gc_alloc and studying which library fns do not cause allocations)
#   - study whether jl_pgcstack (jl_get_current_task()->gcstack, or jl_get_pgcstack()) can be manipulated directly to achieve effect of JL_GC_PUSHARGS macro
"""
jl_pgcstack = jl_current_task->gcstack
JL_GC_ENCODE_PUSHARGS(n) = (((size_t)(n))<<2)
JL_GC_ENCODE_PUSH(n) = ((((size_t)(n))<<2)|1)

jl_value_t **args;
// either
void *__gc_stkf[] = {(void *) JL_GC_ENCODE_PUSH(n), jl_pgcstack, args[0], ..., args[n-1]};
jl_pgcstack = (jl_gcframe_t *) __gc_stkf;
// or
// ??
"""

def get_ref_any_type(fns):
    return fns.apply_type1(fns.get_global(fns.base_module(), fns.symbol(b'RefValue')), fns.any_type())


def init_refs(fns):
    # gc = fns.gc_enable(0)

    val = fns.call0(fns.apply_type2(fns.get_global(fns.base_module(), fns.symbol(b'IdDict')), fns.any_type(), get_ref_any_type(fns)))

    var = fns.symbol(b'refs')
    bp = fns.get_binding_wr(fns.main_module(), var, 1)
    fns.checked_assignment(bp, fns.main_module(), var, val)

    # fns.gc_enable(gc)


def add_ref(fns, val):
    # gc = fns.gc_enable(0)

    setindex = fns.get_global(fns.base_module(), fns.symbol(b'setindex!'))
    # res = fns.call3(setindex, fns.get_global(fns.main_module(), fns.symbol(b'refs')), fns.call1(get_ref_any_type(fns), val), val)
    # ref = fns.call1(get_ref_any_type(fns), val)
    ref = fns.new_structv(get_ref_any_type(fns), get_ctypes_arr(c_void_p, val), 1)
    res = fns.call3(setindex, fns.get_global(fns.main_module(), fns.symbol(b'refs')), ref, ref)

    # fns.gc_enable(gc)

    if res is None:
        raise ValueError()
    return ref


def del_ref(fns, val):
    # gc = fns.gc_enable(0)

    delete = fns.get_global(fns.base_module(), fns.symbol(b'delete!'))
    res = fns.call2(delete, fns.get_global(fns.main_module(), fns.symbol(b'refs')), val)

    # fns.gc_enable(gc)

    if res is None:
        raise ValueError()



def ptr_to_arr(fns, eltype, dims, data, own=True):
    """
    Returns an Array{`eltype`, `len(dims)`} with dimensions `dims` and `data` located at data

    Args:
        param1 (type1): desc1.
    
    Returns:
        type0: desc0.
    
    Examples:
        - Given python objects `a`, `l`, and `i`, s.t. `type(a) == list`, `type(l) == type(i) == int`, `l = dims[0] * ... * dims[len(dims) - 1]`, `len(a) = l`, `0 <= i < l`, and `type(a[i]) = int`, let `data = get_ctypes_arr(c_int64, *a)`.
        - Given `np.ndarray` object `a` s.t. `len(a.shape) == 1` and `a.dtype == np.dtype('int64')`, let `data = a.ctypes.data_as(c_void_p)`.
    """

    val_dims = get_ctypes_arr(c_void_p, *map(fns.box_int64, dims))
    val_dims_types = get_ctypes_arr(c_void_p, *((fns.int64_type(),) * len(dims)))

    val_dims_tup_type = fns.apply_tuple_type_v(val_dims_types, len(dims))
    val_dims_tup = fns.new_structv(val_dims_tup_type, val_dims, len(dims))

    val_arr_type = fns.apply_array_type(eltype, len(dims))
    val_arr = fns.ptr_to_array(val_arr_type, data, val_dims_tup, int(own))

    return val_arr


def arr_to_ptr(fns, ctypes_dtype, np_dtype, shape, len, arr):
    import numpy as np

    ptr = fns.unbox_voidpointer(object.__getattribute__(arr.ref.mem.ptr, 'val'))
    ctypes_arr = (ctypes_dtype * len).from_address(ptr)
    np_arr = np.ctypeslib.as_array(ctypes_arr, shape)

    assert np_arr.dtype == np_dtype

    return np_arr



def get_nt(fns, names, vals, tys):
    assert len(names) == len(vals) == len(tys)
    l = len(names)

    carr_names = get_ctypes_arr(c_void_p, *[fns.symbol(name.encode()) for name in names])
    carr_vals = get_ctypes_arr(c_void_p, *vals)
    carr_tys = get_ctypes_arr(c_void_p, *tys)

    tup_names_ty = fns.apply_tuple_type_v(get_ctypes_arr(c_void_p, *([fns.symbol_type()] * l)), l)
    tup_names = fns.new_structv(tup_names_ty, carr_names, l)
    tup_vals_ty = fns.apply_tuple_type_v(carr_tys, l)
    # tup_vals = fns.new_structv(tup_vals_ty, carr_vals, l)
    nt_ty = fns.apply_type2(fns.namedtuple_type(), tup_names, tup_vals_ty)
    nt = fns.new_structv(nt_ty, carr_vals, l)

    return nt


def call_with_kwargs(fns, fn, args, names, vals, tys):
    l = len(args)

    nt = get_nt(fns, names, vals, tys)
    carr_args = get_ctypes_arr(c_void_p, *(nt, fn, *args))

    return fns.call(fns.kwcall_func(), carr_args, l + 2)



class JuliaValGC(JuliaVal):
    def __init__(self, val):
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        # _setattr('lib', lib)
        # _setattr('fns', fns)
        fns = _getattr('fns')
        _setattr('val', val)

        _setattr('_convert_to', lambda _: object.__getattribute__(_, 'val') if isinstance(_, JuliaVal) else _)
        _setattr('_convert_from', lambda _: JuliaValGC(_))

        add_ref(fns, val)
    
    def __del__(self):
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        # lib = _getattr('lib')
        fns = _getattr('fns')
        val = _getattr('val')

        del_ref(fns, val)



def get_ctypes_arr(ty, *args):
    return (ty * len(args))(*args)



def init_JuliaVal(fns):
    JuliaVal.fns = fns

def init_JuliaValGC(fns):
    init_JuliaVal(fns)
    init_refs(fns)



if __name__ == '__main__':
    rootdir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))

    # libdir = "./target/lib"
    libdir = os.path.join(rootdir, 'target', 'lib')
    # libname = "libjl2py.dylib" if platform.system() == "Darwin" else "libjl2py.so"
    libname = 'jl2py'
    libext = 'dylib' if sys.platform == 'darwin' else 'so'
    libfile = (os.path.extsep).join(('lib{}'.format(libname), libext))
    libpath = os.path.join(libdir, libfile)

    libfuncs = dict(
        jl_eval_string=((c_char_p,), c_void_p),
        
        jl_call=((c_void_p, c_void_p, c_uint32,), c_void_p),
        jl_call0=((c_void_p,) * 1, c_void_p),
        jl_call1=((c_void_p,) * 2, c_void_p),
        jl_call2=((c_void_p,) * 3, c_void_p),
        jl_call3=((c_void_p,) * 4, c_void_p),

        jl_symbol=((c_char_p,), c_void_p),
        
        jl_typeof=((c_void_p,), c_void_p),

        jl_field_index=((c_void_p, c_void_p, c_int,), c_int),
        jl_get_field=((c_void_p, c_char_p,), c_void_p),
        jl_get_nth_field=((c_void_p, c_size_t,), c_void_p),
        jl_set_nth_field=((c_void_p, c_size_t, c_void_p,), None),
        
        jl_box_float64=((c_double,), c_void_p),
        jl_box_int64=((c_int64,), c_void_p),
        jl_box_voidpointer=((c_void_p,), c_void_p),
        jl_unbox_float64=((c_void_p,), c_double),
        jl_unbox_int64=((c_void_p,), c_int64),
        jl_unbox_voidpointer=((c_void_p,), c_void_p),
        jl_string_ptr=((c_void_p,), c_char_p),

        jl_egal=((c_void_p, c_void_p,), c_int),

        jl_gc_enable=((c_int,), c_int),
        jl_gc_is_enabled=(None, c_int),
        jl_gc_collect=((c_int,), None),
        jl_gc_queue_root=((c_void_p,), None),

        jl_get_binding_wr=((c_void_p, c_void_p, c_int,), c_void_p),
        jl_get_global=((c_void_p, c_void_p,), c_void_p),
        jl_checked_assignment=((c_void_p, c_void_p, c_void_p, c_void_p,), None),

        jl_apply_type=((c_void_p, c_void_p, c_size_t,), c_void_p),
        jl_apply_type1=((c_void_p,) * 2, c_void_p),
        jl_apply_type2=((c_void_p,) * 3, c_void_p),
        jl_apply_type3=((c_void_p,) * 4, c_void_p),

        jl_apply_tuple_type_v=((c_void_p, c_size_t,), c_void_p),
        jl_new_structv=((c_void_p, c_void_p, c_uint32,), c_void_p),
        jl_apply_array_type=((c_void_p, c_size_t,), c_void_p),
        jl_ptr_to_array=((c_void_p, c_void_p, c_void_p, c_int,), c_void_p),

        jl_exception_occurred=(None, c_void_p),

        jl_printf=((c_void_p, c_char_p,), c_int),
        jl_stderr_stream=(None, c_void_p),
        jl_stderr_obj=(None, c_void_p),

        jl_get_current_task=(None, c_void_p),

        jl_get_pgcstack=(None, c_void_p),
    )
    libvars = dict(
        jl_core_module=c_void_p,
        jl_base_module=c_void_p,
        jl_main_module=c_void_p,
        jl_top_module=c_void_p,


        jl_any_type=c_void_p,
        jl_type_type=c_void_p,
        jl_typename_type=c_void_p,
        jl_type_typename=c_void_p,
        jl_symbol_type=c_void_p,
        jl_simplevector_type=c_void_p,
        jl_tuple_typename=c_void_p,
        jl_anytuple_type=c_void_p,
        jl_emptytuple_type=c_void_p,
        jl_anytuple_type_type=c_void_p,
        jl_function_type=c_void_p,
        jl_module_type=c_void_p,
        jl_densearray_type=c_void_p,
        jl_array_type=c_void_p,
        jl_array_typename=c_void_p,
        jl_genericmemory_type=c_void_p,
        jl_genericmemory_typename=c_void_p,
        jl_genericmemoryref_type=c_void_p,
        jl_genericmemoryref_typename=c_void_p,
        jl_weakref_type=c_void_p,
        jl_abstractstring_type=c_void_p,
        jl_string_type=c_void_p,

        jl_bool_type=c_void_p,
        jl_uint8_type=c_void_p,
        jl_int64_type=c_void_p,
        jl_nothing_type=c_void_p,
        jl_voidpointer_type=c_void_p,
        jl_uint8pointer_type=c_void_p,
        jl_pointer_type=c_void_p,
        jl_ref_type=c_void_p,
        jl_pointer_typename=c_void_p,
        jl_namedtuple_type=c_void_p,
        jl_namedtuple_typename=c_void_p,

        jl_empty_svec=c_void_p,
        jl_emptytuple=c_void_p,
        jl_true=c_void_p,
        jl_false=c_void_p,
        jl_nothing=c_void_p,
        jl_kwcall_func=c_void_p,
        
        # jl_libdl_dlopen_func=c_void_p,
    )

    lib = JuliaLib(libpath).__enter__()
    libutils = CDLLUtils(lib, funcs=libfuncs, vars=libvars)

    jl = as_object('jl_', **(libutils.funcs), **(libutils.vars))
    init_JuliaValGC(jl)

    println = JuliaValGC(jl.eval_string(b'println'))
