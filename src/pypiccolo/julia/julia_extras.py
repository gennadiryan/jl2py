import os

import ctypes
from ctypes import cdll, c_double, c_float, c_int, c_int32, c_int64, c_uint, c_uint32, c_uint64, c_size_t, c_char_p, c_void_p

import numpy as np

# from experimental.main import JuliaLib, CDLLUtils, JuliaVal, JuliaValGC, as_object, ptr_to_arr, arr_to_ptr, get_ctypes_arr, init_JuliaVal, init_JuliaValGC, add_ref, del_ref
from . import jl
from .julia_value import init_jl, ptr_to_arr, arr_to_ptr, get_nt, get_ctypes_arr, JuliaVal, JuliaValGC
from .utils import _getattr, _setattr

"""
TODO:
    - add support for additional QCPs/problem templates (e.g. unitary sampling problem)
    - add support for customized initial trajectories
    - add more support for/examples of retrieving data from trajectories
    - generalize inputs (as best as possible) to other <: Number types besides ComplexF64 (currently requires special handling due to numpy representation of complex128)

    - add check in JuliaVec.__init__ to validate that eltype is such that `!Base.allocatedinline(eltype)`, or `!isimmutable(eltype) || !isbitstype(eltype)`
    - opposite for JuliaArr.__init__

    - consider making JuliaArr and ndarray_from_value the same class (rely on MRO perhaps?)
    

main.py TODO:
    - get rid of unnecessary args/kwargs expansions (e.g. in get_ctypes_arr), or verify they introduce no performance penalty
    - move definitions of libjulia-related values (cdll instance, asobject wrapper instance, etc.) into module body to ensure that they are imported and run exactly once
    - make ^^ depend on setuptools-related configs
    - handle library checks, (if necessary) first-time Pkg.add(), etc. in setup script
    - figure out why arr_to_ptr returns a flat array and falsely passes dtype tests (not a breaking issue but should be addressed nonetheless)
    - rebuild target with latest Piccolo.jl version

    - clean up ref handling code    

Misc TODO:
    - add QuTIP support

DONE:
    - rebase to integrate Jack's updates
    - add support for the same unitaries/gates as offered by Piccolo.jl

    - add refcounts (shouldn't pose issues if JuliaVal constructors used as intended,
        but theoretically possible in e.g. `x = JuliaInt(4); _x = ptr(x); y = JuliaValGC(y); del y;` that x is GC'ed before it is itself del'ed)
    - add refcounts (for when multiple JuliaVal instances point to same ptr)
    - rethink ref scheme; can just wrap everything in references, or else test for immutables and wrap them only;
        also want a better way to prevent GC while pushing to the `refs` dict/set than just turning on/off the GC

    - write tests comparing ptr_to_arr(..., own=True) vs ptr_to_arr(..., own=False)
    - write functions implementing [Unitary,QuantumState]SmoothPulseProblem
    - write tests based on `@testitem`s from [unitary,quantum_state]_smooth_pulse_problem.jl (to investigate limitations of JuliaVal API as well as to get some ideas for demo tasks, esp. as we plan compare to test QuTIP on the same tasks)

    - get rid of implicit uses of globally defined Julia fns (e.g. getindex)
"""



def ptr(value):
    return object.__getattribute__(value, 'val')

def get_global(module, name): # TODO: error handling is CRUCIAL here
    return JuliaValGC(jl.get_global(ptr(module), jl.symbol(name.encode())))

def get_tparams(ty):
    _ty = ptr(ty)
    _ty_params = jl.get_nth_field(_ty, jl.field_index(jl.typeof(_ty), jl.symbol('parameters'.encode()), 0))
    _ty_params_len = c_size_t.from_address(_ty_params)
    return [JuliaValGC(c_void_p.from_address(_ty_params + ctypes.sizeof(_ty_params_len) + (ctypes.sizeof(c_void_p) * i))) for i in range(_ty_params_len.value)]

def get_svec_len(svec):
    return c_size_t.from_address(ptr(svec))

def get_svec_arr(svec): # no risk of double-free since we use here c_void_p_Array_n.from_address rather than c_void_p_Array_n.__init__ constructor
    return (c_void_p * get_svec_len(svec).value).from_address(ptr(svec) + ctypes.sizeof(c_size_t))

def get_sym_name(sym):
    return ctypes.string_at(ptr(sym) + (ctypes.sizeof(c_void_p) * 3)).decode()


def call_with_kwargs(fn, args, names, vals):
    """
    TODO: consider using gc push/pop here (especially rather than JuliaValGC wrapping/explicit global rooting)
    """

    tys = [JuliaType.typeof(_) for _ in vals]
    
    _fn = ptr(fn)
    _args, _vals, _tys = [list(map(ptr, _)) for _ in (args, vals, tys)]

    nt = JuliaValGC(get_nt(names, _vals, _tys))
    _nt = ptr(nt)
    
    carr_args = get_ctypes_arr(c_void_p, *(_nt, _fn, *_args))
    return JuliaValGC(jl.call(jl.kwcall_func(), carr_args, len(args) + 2))


class JuliaType(JuliaValGC):
    @staticmethod
    def typeof(value: JuliaValGC) -> JuliaValGC:
        return JuliaType(jl.typeof(ptr(value)))


class JuliaNum(JuliaValGC):
    """
    TODO:
        - make this superclass useful and define things like __int__, __float__, __lt__, __gt__, __add__, __mul__, etc.
    """
    pass

class JuliaInt(JuliaNum):
    def __init__(self, value: int) -> None:
        super().__init__(jl.box_int64(int(value)))
    @staticmethod
    def cast(value: JuliaValGC) -> int:
        return jl.unbox_int64(ptr(value))

class JuliaFloat(JuliaNum):
    def __init__(self, value: float) -> None:
        super().__init__(jl.box_float64(float(value)))
    @staticmethod
    def cast(value: JuliaValGC) -> float:
        return jl.unbox_float64(ptr(value))

class JuliaComplex(JuliaNum):
    def __init__(self, value: complex) -> None:
        super().__init__(jl.call2(jl.get_global(jl.base_module(), ptr(JuliaSymbol('ComplexF64'))), *[ptr(JuliaFloat(_)) for _ in (value.real, value.imag)]))


class JuliaSymbol(JuliaValGC):
    def __init__(self, value: str) -> None:
        super().__init__(jl.symbol(value.encode()))
    @staticmethod
    def cast(value: JuliaValGC) -> str:
        return get_sym_name(value)


class JuliaModule(JuliaValGC):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        _setattr(self, 'getproperty', get_global(JuliaValGC(jl.base_module()), 'getproperty'))
        _setattr(self, 'propertynames', get_global(JuliaValGC(jl.base_module()), 'propertynames'))
    
    def __getattribute__(self, name: str) -> JuliaValGC:
        if (len(name) == 0) or (len(name) > 0 and name[0] == '_'):
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        try:
            getter = _getattr(self, 'getproperty')
        except Exception as e:
            raise AttributeError(f'{type(self)} object has no attribute {name}')
        return getter(self, JuliaSymbol(name))
    
    def __setattr__(self, name: str, value: JuliaValGC) -> None:
        raise NotImplementedError()

    def __dir__(self) -> list[str]:
        props = _getattr(self, 'propertynames')(self)
        props_addr = jl.unbox_voidpointer(ptr(props.ref.mem.ptr))
        props_len = c_int64.from_address(ptr(props.size)).value
        prop_syms = [JuliaValGC(c_void_p.from_address(props_addr + (i * ctypes.sizeof(c_void_p))).value) for i in range(props_len)]

        return sorted(map(get_sym_name, prop_syms))


class JuliaVec(JuliaValGC):
    def __init__(self, vals: list[JuliaVal], eltype: JuliaVal | None = None, own: bool = False) -> None:
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)
        
        eltype = eltype if eltype is not None else JuliaValGC(jl.any_type())
        carr_val = (c_void_p * len(vals))(*map(lambda _: object.__getattribute__(_, 'val'), vals))
        val = ptr_to_arr(object.__getattribute__(eltype, 'val'), (len(vals),), carr_val, own=own)

        super().__init__(val, keep=vals)
        _setattr('carr_val', carr_val) # prevent GC of the memory region storing references to the elements
    
    def __getitem__(self, idx: int) -> JuliaVal:
        # choosing not to directly use `Base.getindex` to avoid multiple dispatch on a function with large method table

        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        val = _getattr('val')

        try:
            itemval = _getattr('carr_val')[idx]
        except IndexError as e:
            raise e

        return _getattr('_convert_from')(itemval)
    
    def __setitem__(self, idx: int, value: JuliaVal) -> None:
        # choosing not to directly use `Base.setindex` to avoid multiple dispatch on a function with large method table

        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        val = _getattr('val')

        try:
            _getattr('carr_val')[idx] = _getattr('_convert_to')(value)
            _getattr('keep')[idx] = value
        except IndexError as e:
            raise e


class JuliaArr(JuliaValGC):
    _dtype_map = dict(
        complex64='ComplexF32',
        complex128='ComplexF64',
        float16='Float16',
        float32='Float32',
        float64='Float64',
        int8='Int8',
        int16='Int16',
        int32='Int32',
        int64='Int64',
        uint8='UInt8',
        uint16='UInt16',
        uint32='UInt32',
        uint64='UInt64',
    )

    def __init__(self, arr: np.ndarray, own: bool = False) -> None:
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        ty_np = arr.dtype
        shape_np = arr.shape
        ptr_np = arr.ctypes.data
        
        if ty_np.name not in _getattr('_dtype_map').keys():
            raise TypeError(f'{arr.dtype} is unsupported')
        
        ty_jl = get_global(JuliaValGC(jl.base_module()), _getattr('_dtype_map')[ty_np.name])
        val = ptr_to_arr(ptr(ty_jl), shape_np[::-1], ptr_np, own=False)
        
        super().__init__(val, keep=[arr])
        
    
class ndarray_from_value(np.ndarray):
    _dtype_map = dict(
        ComplexF32='complex64',
        ComplexF64='complex128',
        Float16='float16',
        Float32='float32',
        Float64='float64',
        Int8='int8',
        Int16='int16',
        Int32='int32',
        Int64='int64',
        UInt8='uint8',
        UInt16='uint16',
        UInt32='uint32',
        UInt64='uint64',
    )
    _ctypes_dtype_map = dict(
        complex64=('float32', 2),
        complex128=('float64', 2),
        float32=('float32', 1),
        float64=('float64', 1),
        int8=('int8', 1),
        int16=('int16', 1),
        int32=('int32', 1),
        int64=('int64', 1),
        uint8=('uint8', 1),
        uint16=('uint16', 1),
        uint32=('uint32', 1),
        uint64=('uint64', 1),
    )
    #
    # def __init__(self, value: JuliaValGCv2) -> None:
    @staticmethod
    def cast(value: JuliaValGC) -> np.ndarray:
        prod = lambda _: (lambda f: f(f, _))(lambda f, args: 1 if len(args) == 0 else (args[-1] * f(f, args[:-1])))
        #
        arr_ty = JuliaType.typeof(value)
        assert get_sym_name(arr_ty.name.name) == 'Array'
        #
        arr_ty_param = JuliaValGC(get_svec_arr(arr_ty.parameters)[0])
        arr_ty_param_name = JuliaSymbol.cast(arr_ty_param.name.name)
        if arr_ty_param_name == 'Complex':
            complex_ty_param = JuliaValGC(get_svec_arr(arr_ty_param.parameters)[0])
            complex_ty_param_name = JuliaSymbol.cast(complex_ty_param.name.name)
            arr_ty_param_name = 'ComplexF64' if complex_ty_param_name == 'Float64' else ('Complex32' if complex_ty_param_name == 'Float32' else None)
        assert arr_ty_param_name in ndarray_from_value._dtype_map.keys()
        assert ndarray_from_value._dtype_map[arr_ty_param_name] in ndarray_from_value._ctypes_dtype_map.keys()
        #
        dtype = ndarray_from_value._dtype_map[arr_ty_param_name]
        np_dtype = np.dtype(dtype)
        ctypes_dtype, ctypes_factor = ndarray_from_value._ctypes_dtype_map[dtype]
        ctypes_dtype = np.ctypeslib.as_ctypes_type(np.dtype(ctypes_dtype))
        #
        dims = JuliaInt.cast(JuliaValGC(get_svec_arr(arr_ty.parameters)[1]))
        shape = tuple(JuliaInt.cast(getindex(value.size, JuliaInt(i + 1))) for i in range(dims))
        size = prod(shape) * ctypes_factor
        #
        val_ptr = jl.unbox_voidpointer(ptr(value.ref.mem.ptr))
        # # either
        # valptr = ctypes.cast(valptr, ctypes.POINTER(ctypes_dtype))
        # or
        val_arr = (ctypes_dtype * size).from_address(val_ptr)
        np_arr = np.ctypeslib.as_array(val_arr).view(dtype=np_dtype).reshape(shape[::-1])
        assert val_ptr == np_arr.ctypes.data
        #
        # super().__init__(np_arr)
        # assert self.ctypes.data == val_ptr
        # self._jl_value = value
        return np_arr
    

def convert_arg(self, value):
    if isinstance(value, JuliaVal):
        return value
    
    import numbers

    if value is None:
        return JuliaValGC(jl.nothing())
    
    if isinstance(value, bool):
        if value:
            return JuliaValGC(jl.true())
        else:
            return JuliaValGC(jl.false())
    
    if isinstance(value, numbers.Number):
        if isinstance(value, numbers.Real):
            if isinstance(value, numbers.Integral):
                return JuliaInt(value)
            else:
                return JuliaFloat(value)
        else:
            return JuliaComplex(value)

def convert_res(self, value):
    pass


JuliaVal._convert_arg = convert_arg


jl = init_jl()

println = JuliaValGC(jl.eval_string(b'println'))
getindex = get_global(JuliaValGC(jl.base_module()), 'getindex')
setindex = get_global(JuliaValGC(jl.base_module()), 'setindex')
typeof = get_global(JuliaValGC(jl.base_module()), 'typeof')

mod_base = JuliaModule(jl.base_module())
mod_core = JuliaModule(jl.core_module())
mod_main = JuliaModule(jl.main_module())

type_map = dict(
    JuliaInt=jl.int64_type,
    JuliaFloat=jl.float64_type,
)

