from collections import OrderedDict
from collections.abc import Callable, Mapping, MutableMapping
from typing import Any, Generic, List, Optional, Set, Tuple, TypeVar, Union

import sys
import os
import ctypes
from ctypes import cdll, c_double, c_float, c_int, c_int32, c_int64, c_uint, c_uint32, c_uint64, c_size_t, c_char_p, c_void_p

from . import jl
from .lib_julia import init_jl
from .utils import _getattr, _setattr

# from .julia_extras import call_with_kwargs


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

    fns = init_jl()

    def __init__(self, val: int | c_void_p):
        assert isinstance(val, int) or isinstance(val, c_void_p)
        if isinstance(val, c_void_p):
            val = val.value
        
        _setattr(self, 'val', val)

        # _setattr(self, '_convert_to', lambda _: _getattr(_, 'val') if isinstance(_, JuliaVal) else _)
        _setattr(self, '_convert_to', lambda _: _getattr(_, 'val'))
        _setattr(self, '_convert_from', lambda _: JuliaVal(_))
    
    def __getattribute__(self, name):
        if (len(name) == 0) or (len(name) > 0 and name[0] == '_'):
            raise AttributeError(f'{type(self)} object has no attribute {name}')
                
        val = _getattr(self, 'val')
    
        idx = jl.field_index(jl.typeof(val), jl.symbol(name.encode()), 0)
        if idx < 0:
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        
        fld = jl.get_nth_field(val, idx)
        if fld is None:
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        
        return _getattr(self, '_convert_from')(fld)
    
    def __setattr__(self, name, value):
        if (len(name) == 0) or (len(name) > 0 and name[0] == '_'):
            raise AttributeError(f'{type(self)} object has no attribute {name}')

        val = _getattr(self, 'val')

        value = _getattr(self, '_convert_to')(value)

        idx = jl.field_index(jl.typeof(val), jl.symbol(name.encode()), 0)
        if idx < 0:
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        jl.set_nth_field(val, idx, value)
        
        if jl.get_nth_field(val, idx) != value:
            raise ValueError()
    
    def __eq__(self, value):
        if not isinstance(value, JuliaVal):
            return False

        return bool(jl.egal(_getattr(self, '_convert_to')(self), _getattr(value, '_convert_to')(value)))
    
    def __call__(self, *args, **kwargs):
        val = _getattr(self, 'val')

        if len(kwargs) > 0:
            names, values = zip(*list(kwargs.items()))
            return _call_with_kwargs(self, list(args), list(names), list(values))

            # try:
            #     def ptr(value):
            #         return object.__getattribute__(value, 'val')
                
            #     def call_with_kwargs(fn, args, names, vals):
            #         """
            #         TODO: consider using gc push/pop here (especially rather than JuliaValGC wrapping/explicit global rooting)
            #         """

            #         tys = [JuliaValGC(jl.typeof(ptr(_))) for _ in vals]
                    
            #         _fn = ptr(fn)
            #         _args, _vals, _tys = [list(map(ptr, _)) for _ in (args, vals, tys)]

            #         nt = JuliaValGC(get_nt(names, _vals, _tys))
            #         _nt = ptr(nt)
                    
            #         carr_args = get_ctypes_arr(c_void_p, *(_nt, _fn, *_args))
            #         return JuliaValGC(jl.call(jl.kwcall_func(), carr_args, len(args) + 2))

            #     names, values = zip(*list(kwargs.items()))
            #     return call_with_kwargs(self, list(args), list(names), list(values))
            
            # except Exception as e:
            #     pass

        argsptr = get_ctypes_arr(c_void_p, *map(lambda _: _getattr(_, '_convert_to')(_), args))
        nargs = len(args)

        # TODO(jack-champagne): add kwargs call here
        res = jl.call(val, argsptr, nargs) # TODO: handle bad return values (i.e. `res is None` yet no exception thrown)

        # # TODO: replace this block with proper error handling (subsequent block appears not to be working; may need to hold on to show_error pointer ahead of time)
        # if res is None:
        #     raise ValueError()

        # # see github.com/JuliaLang/julia/test/embedding/embedding.c
        # eo = fns.exception_occurred()
        # if eo is not None:
        #     fns.call2(fns.get_global(fns.base_module(), 'showerror'.encode()), fns.stderr_obj(), eo)
        #     fns.printf(fns.stderr_stream(), '\n'.encode())
        #     return None

        # if res is None:
        #     return None

        eo = jl.exception_occurred()
        if eo is not None:
            # fns.call2(fns.get_global(fns.base_module(), fns.symbol(b'showerror')), fns.get_global(fns.base_module(), fns.symbol(b'stderr')), eo)
            jl.call2(jl.get_global(jl.base_module(), jl.symbol(b'showerror')), jl.stderr_obj(), eo)
            jl.printf(jl.stderr_stream(), b'\n')
            raise Exception()
        
        if res is None:
            raise Exception() # should not fall through to here

        return _getattr(self, '_convert_from')(res)

    def __dir__(self,):
        """
        Consider simplifying implementation
        """

        val = _getattr(self, 'val')

        ty = jl.typeof(val)
        ty_name = jl.get_nth_field(ty, jl.field_index(jl.typeof(ty), jl.symbol(b'name'), 0))
        ty_names = jl.get_nth_field(ty_name, jl.field_index(jl.typeof(ty_name), jl.symbol(b'names'), 0))
        ty_names_len = c_size_t.from_address(ty_names)
        
        ty_names_as_symbol = [c_void_p.from_address(ty_names + ctypes.sizeof(ty_names_len) + (ctypes.sizeof(c_void_p) * i)) for i in range(ty_names_len.value)]
        ty_names_as_str = [ctypes.string_at(name_as_symbol.value + (ctypes.sizeof(c_void_p) * 3)).decode() for name_as_symbol in ty_names_as_symbol]

        return ty_names_as_str

    def __repr__(self,):
        val = _getattr(self, 'val')

        fn_repr = jl.get_global(jl.base_module(), jl.symbol(b'repr'))
        val_res = jl.call1(fn_repr, val)
        val_str = ctypes.string_at(jl.string_ptr(val_res)).decode()

        return val_str
    

# TODO: 
#   - study whether jl.gc_enable really does blow up memory without bound as claimed
#   - study whether jl.gc_enable is necesary at all (via setting breakpoints in jl_gc_alloc and studying which library fns do not cause allocations)
#   - study whether jl_pgcstack (jl_get_current_task()->gcstack, or jl_get_pgcstack()) can be manipulated directly to achieve effect of JL_GC_PUSHARGS macro

#   """
#   jl_pgcstack = jl_current_task->gcstack
#   JL_GC_ENCODE_PUSHARGS(n) = (((size_t)(n))<<2)
#   JL_GC_ENCODE_PUSH(n) = ((((size_t)(n))<<2)|1)

#   jl_value_t **args;
#   // either
#   void *__gc_stkf[] = {(void *) JL_GC_ENCODE_PUSH(n), jl_pgcstack, args[0], ..., args[n-1]};
#   jl_pgcstack = (jl_gcframe_t *) __gc_stkf;
#   // or
#   // ??
#   """

# def get_ref_any_type(fns):
#     return fns.apply_type1(fns.get_global(fns.base_module(), fns.symbol(b'RefValue')), fns.any_type())


# def init_refs(fns):
#     # gc = fns.gc_enable(0)

#     val = fns.call0(fns.apply_type2(fns.get_global(fns.base_module(), fns.symbol(b'IdDict')), fns.any_type(), get_ref_any_type(fns)))

#     var = fns.symbol(b'refs')
#     bp = fns.get_binding_wr(fns.main_module(), var, 1)
#     fns.checked_assignment(bp, fns.main_module(), var, val)

#     # fns.gc_enable(gc)


# def add_ref(fns, val):
#     # gc = fns.gc_enable(0)

#     setindex = fns.get_global(fns.base_module(), fns.symbol(b'setindex!'))
#     # res = fns.call3(setindex, fns.get_global(fns.main_module(), fns.symbol(b'refs')), fns.call1(get_ref_any_type(fns), val), val)
#     # ref = fns.call1(get_ref_any_type(fns), val)
#     ref = fns.new_structv(get_ref_any_type(fns), get_ctypes_arr(c_void_p, val), 1)
#     res = fns.call3(setindex, fns.get_global(fns.main_module(), fns.symbol(b'refs')), ref, ref)

#     # fns.gc_enable(gc)

#     if res is None:
#         raise ValueError()
#     return ref


# def del_ref(fns, val):
#     # gc = fns.gc_enable(0)

#     delete = fns.get_global(fns.base_module(), fns.symbol(b'delete!'))
#     res = fns.call2(delete, fns.get_global(fns.main_module(), fns.symbol(b'refs')), val)

#     # fns.gc_enable(gc)

#     if res is None:
#         raise ValueError()



def jl_gc_pushargs(n):
    pgcstack_ptr_addr = jl.get_pgcstack()
    new_pgcstack = (c_void_p * (2 + n))(n << 2, c_void_p.from_address(pgcstack_ptr_addr), *([0] * n))
    new_pgcstack_addr_ptr = c_void_p(ctypes.addressof(new_pgcstack))
    new_pgcstack_addr_ptr_addr = ctypes.addressof(new_pgcstack_addr_ptr)
    ctypes.memmove(pgcstack_ptr_addr, new_pgcstack_addr_ptr_addr, ctypes.sizeof(c_void_p))
    return new_pgcstack

def jl_gc_pop():
    pgcstack_ptr_addr = jl.get_pgcstack()
    pgcstack_addr = c_void_p.from_address(pgcstack_ptr_addr).value
    pgcstack_addr = 0 if pgcstack_addr is None else pgcstack_addr
    if pgcstack_addr > 0:
        old_pgcstack_addr_ptr = c_void_p.from_address(pgcstack_addr + (1 * ctypes.sizeof(c_void_p)))
        ctypes.memmove(pgcstack_ptr_addr, ctypes.addressof(old_pgcstack_addr_ptr), ctypes.sizeof(c_void_p))


def init_refs():
    try:
        gcstack = jl_gc_pushargs(3)

        reft = jl.get_global(jl.base_module(), jl.symbol(b'RefValue'))
        reft = jl.apply_type1(reft, jl.any_type())
        gcstack[2] = reft

        idsett = jl.get_global(jl.base_module(), jl.symbol(b'IdSet'))
        idsett = jl.apply_type1(idsett, reft)
        gcstack[3] = idsett
        
        refs = jl.call0(idsett)
        gcstack[4] = refs

        var = jl.symbol(b'refs')
        bp = jl.get_binding_wr(jl.main_module(), var, 1)
        jl.checked_assignment(bp, jl.main_module(), var, refs)

    finally:
        jl_gc_pop()


def add_ref(value):
    try:
        gcstack = jl_gc_pushargs(3)

        gcstack[2] = value

        reft = jl.get_global(jl.base_module(), jl.symbol(b'RefValue'))
        reft = jl.apply_type1(reft, jl.any_type())
        gcstack[3] = reft

        carr_args = (c_void_p * 1)(value)
        ref = jl.new_structv(reft, carr_args, 1)
        gcstack[4] = ref
        
        res = jl.call2(jl.get_global(jl.base_module(), jl.symbol(b'push!')), jl.get_global(jl.main_module(), jl.symbol(b'refs')), ref)

        return ref

    finally:
        jl_gc_pop()


def del_ref(ref):
    res = jl.call2(jl.get_global(jl.base_module(), jl.symbol(b'pop!')), jl.get_global(jl.main_module(), jl.symbol(b'refs')), ref)
    
    if res != ref:
        raise ValueError()



def ptr_to_arr(eltype, dims, data, own=True):
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

    val_dims = get_ctypes_arr(c_void_p, *map(jl.box_int64, dims))
    val_dims_types = get_ctypes_arr(c_void_p, *((jl.int64_type(),) * len(dims)))

    val_dims_tup_type = jl.apply_tuple_type_v(val_dims_types, len(dims))
    val_dims_tup = jl.new_structv(val_dims_tup_type, val_dims, len(dims))

    val_arr_type = jl.apply_array_type(eltype, len(dims))
    val_arr = jl.ptr_to_array(val_arr_type, data, val_dims_tup, int(own))

    return val_arr


def arr_to_ptr(ctypes_dtype, np_dtype, shape, len, arr):
    """
    TODO: remove this fn or else integrate it into ndarray_from_value
    """

    import numpy as np

    ptr = jl.unbox_voidpointer(_getattr(arr.ref.mem.ptr, 'val'))
    ctypes_arr = (ctypes_dtype * len).from_address(ptr)
    np_arr = np.ctypeslib.as_array(ctypes_arr, shape)

    assert np_arr.dtype == np_dtype

    return np_arr



def get_nt(names, vals, tys):
    """
    TODO: consider using gc push/pop here
    """

    assert len(names) == len(vals) == len(tys)
    l = len(names)

    carr_names = get_ctypes_arr(c_void_p, *[jl.symbol(name.encode()) for name in names])
    carr_vals = get_ctypes_arr(c_void_p, *vals)
    carr_tys = get_ctypes_arr(c_void_p, *tys)

    tup_names_ty = jl.apply_tuple_type_v(get_ctypes_arr(c_void_p, *([jl.symbol_type()] * l)), l)
    tup_names = jl.new_structv(tup_names_ty, carr_names, l)
    tup_vals_ty = jl.apply_tuple_type_v(carr_tys, l)
    # tup_vals = fns.new_structv(tup_vals_ty, carr_vals, l)
    nt_ty = jl.apply_type2(jl.namedtuple_type(), tup_names, tup_vals_ty)
    nt = jl.new_structv(nt_ty, carr_vals, l)

    return nt


# def call_with_kwargs(fns, fn, args, names, vals, tys):
#     l = len(args)

#     nt = get_nt(fns, names, vals, tys) # this should probably be stored in refs until jl_call() has returned
#     carr_args = get_ctypes_arr(c_void_p, *(nt, fn, *args))

#     return fns.call(fns.kwcall_func(), carr_args, l + 2)


def _call_with_kwargs(fn, args, names, vals):
    """
    TODO: consider using gc push/pop here (especially rather than JuliaValGC wrapping/explicit global rooting)
    """

    def ptr(value):
        return object.__getattribute__(value, 'val')

    tys = [JuliaValGC(jl.typeof(ptr(_))) for _ in vals]
    
    _fn = ptr(fn)
    _args, _vals, _tys = [list(map(ptr, _)) for _ in (args, vals, tys)]

    nt = JuliaValGC(get_nt(names, _vals, _tys))
    _nt = ptr(nt)
    
    carr_args = get_ctypes_arr(c_void_p, *(_nt, _fn, *_args))
    return JuliaValGC(jl.call(jl.kwcall_func(), carr_args, len(args) + 2))



class JuliaValGC(JuliaVal):
    def __init__(self, val, keep=None):
        _setattr(self, 'val', val)
        _setattr(self, 'keep', list() if keep is None else keep) # prevent GC of values depended on by val

        # _setattr(self, '_convert_to', lambda _: _getattr(_, 'val') if isinstance(_, JuliaVal) else _)
        _setattr(self, '_convert_to', lambda _: _getattr(_, 'val'))
        _setattr(self, '_convert_from', lambda _: JuliaValGC(_))

        _setattr(self, 'ref', add_ref(val))
    
    def __del__(self):
        ref = _getattr(self, 'ref')

        del_ref(ref)


# class JuliaValGCv2(JuliaVal):
#     def __init__(self, val: int | c_void_p, keep: list | None = None) -> None:
#         # _getattr = lambda *_: object.__getattribute__(self, *_)
#         # _setattr = lambda *_: object.__setattr__(self, *_)

#         fns = _getattr(self, 'fns')
#         _setattr(self, 'val', val)
#         _setattr(self, 'keep', list() if keep is None else keep) # prevent GC of values depended on by val

#         _setattr(self, '_convert_to', lambda _: _getattr(_, 'val') if isinstance(_, JuliaVal) else _)
#         _setattr(self, '_convert_from', lambda _: JuliaValGCv2(_))

#         # add_ref(fns, _getattr('ref'))
#         _setattr(self, 'ref', add_ref(fns, val))
    
#     def __eq__(self, value: JuliaVal) -> bool:
#         # _getattr = lambda *_: object.__getattribute__(self, *_)
#         # _setattr = lambda *_: object.__setattr__(self, *_)

#         fns = _getattr(self, 'fns')

#         return bool(fns.egal(_getattr(self, '_convert_to')(self), _getattr(self, '_convert_to')(value)))
    
#     def __del__(self) -> None:
#         # _getattr = lambda *_: object.__getattribute__(self, *_)
#         # _setattr = lambda *_: object.__setattr__(self, *_)

#         fns = _getattr(self, 'fns')
#         val = _getattr(self, 'val')
#         ref = _getattr(self, 'ref')

#         # del_ref(fns, ref)
#         del_ref(fns, ref)




def get_ctypes_arr(ty, *args):
    return (ty * len(args))(*args)


init_refs()


# TODO: 
#   - diagnose __main__.JuliaValGC != pypiccolo.julia.julia_value.JuliaValGC
#   - clean up __init__ of JuliaVal (if val isinstance ctypes.c_void_p) then val = val.value

# DONE:
#   - switch from fns to importing jl

# # if __name__ == '__main__':
# jl = init_jl()

# println = JuliaValGC(jl.eval_string(b'println'))

# jl.eval_string(b'mutable struct pt_mut; x::Int; y::Int; end;')
# jl.eval_string(b'struct pt_immut; x::Int; y::Int; end;')

# ty_mut = JuliaValGC(jl.eval_string(b'pt_mut'))
# ty_immut = JuliaValGC(jl.eval_string(b'pt_immut'))

# arr = [JuliaValGC(jl.box_int64(_)) for _ in range(100)]

