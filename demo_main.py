import os

import ctypes
from ctypes import cdll, c_double, c_float, c_int, c_int32, c_int64, c_uint, c_uint32, c_uint64, c_size_t, c_char_p, c_void_p

import numpy as np

from experimental.main import JuliaLib, CDLLUtils, JuliaVal, JuliaValGC, as_object, ptr_to_arr, arr_to_ptr, get_ctypes_arr, init_JuliaVal, init_JuliaValGC, add_ref, del_ref


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
    - get rid of implicit uses of globally defined Julia fns (e.g. getindex)
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
"""



def ptr(value):
    return object.__getattribute__(value, 'val')

def get_global(module, name):
    return JuliaValGCv2(jl.get_global(ptr(module), jl.symbol(name.encode())))

def get_tparams(ty):
    _ty = ptr(ty)
    _ty_params = jl.get_nth_field(_ty, jl.field_index(jl.typeof(_ty), jl.symbol('parameters'.encode()), 0))
    _ty_params_len = c_size_t.from_address(_ty_params)
    return [JuliaValGCv2(c_void_p.from_address(_ty_params + ctypes.sizeof(_ty_params_len) + (ctypes.sizeof(c_void_p) * i))) for i in range(_ty_params_len.value)]

def get_svec_len(svec):
    return c_size_t.from_address(ptr(svec))

def get_svec_arr(svec): # no risk of double-free since we use here c_void_p_Array_n.from_address rather than c_void_p_Array_n.__init__ constructor
    return (c_void_p * get_svec_len(svec).value).from_address(ptr(svec) + ctypes.sizeof(c_size_t))

def get_sym_name(sym):
    return ctypes.string_at(ptr(sym) + (ctypes.sizeof(c_void_p) * 3)).decode()

# def get_reftype_any():
#     return jl.apply_type1(jl.ref_type(), jl.any_type())

# def init_refs():
#     return jl.apply_type1(jl.get_global(jl.base_module(), jl.symbol('IdSet'.encode())), get_reftype_any())

# def add_ref(value):
#     pass


class JuliaValGCv2(JuliaVal):
    def __init__(self, val: int | c_void_p, keep: list | None = None) -> None:
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
        _setattr('val', val)
        _setattr('keep', list() if keep is None else keep) # prevent GC of values depended on by val

        _setattr('_convert_to', lambda _: object.__getattribute__(_, 'val') if isinstance(_, JuliaVal) else _)
        _setattr('_convert_from', lambda _: JuliaValGCv2(_))

        # add_ref(fns, _getattr('ref'))
        _setattr('ref', add_ref(fns, val))
    
    def __eq__(self, value: JuliaVal) -> bool:
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')

        return bool(fns.egal(_getattr('_convert_to')(self), _getattr('_convert_to')(value)))
    
    def __del__(self) -> None:
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
        val = _getattr('val')
        ref = _getattr('ref')

        # del_ref(fns, ref)
        del_ref(fns, ref)


class JuliaType(JuliaValGCv2):
    @staticmethod
    def typeof(value: JuliaValGCv2) -> JuliaValGCv2:
        return JuliaType(jl.typeof(ptr(value)))


class JuliaNum(JuliaValGCv2):
    pass

class JuliaInt(JuliaNum):
    def __init__(self, value: int) -> None:
        super().__init__(jl.box_int64(int(value)))
    @staticmethod
    def cast(value: JuliaValGCv2) -> int:
        return jl.unbox_int64(ptr(value))

class JuliaFloat(JuliaNum):
    def __init__(self, value: float) -> None:
        super().__init__(jl.box_float64(float(value)))
    @staticmethod
    def cast(value: JuliaValGCv2) -> float:
        return jl.unbox_float64(ptr(value))

class JuliaComplex(JuliaNum):
    def __init__(self, value: complex) -> None:
        super().__init__(jl.call2(jl.get_global(jl.base_module(), ptr(JuliaSymbol('ComplexF64'))), *[ptr(JuliaFloat(_)) for _ in (value.real, value.imag)]))


class JuliaSymbol(JuliaValGCv2):
    def __init__(self, value: str) -> None:
        super().__init__(jl.symbol(value.encode()))
    @staticmethod
    def cast(value: JuliaValGCv2) -> str:
        return get_sym_name(value)


class JuliaVec(JuliaValGCv2):
    def __init__(self, vals: list[JuliaVal], eltype: JuliaVal | None = None, own: bool = False) -> None:
        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
        
        eltype = eltype if eltype is not None else JuliaValGCv2(fns.any_type())
        carr_val = (c_void_p * len(vals))(*map(lambda _: object.__getattribute__(_, 'val'), vals))
        val = ptr_to_arr(fns, object.__getattribute__(eltype, 'val'), (len(vals),), carr_val, own=own)

        super().__init__(val, keep=vals)
        _setattr('carr_val', carr_val) # prevent GC of the memory region storing references to the elements
    
    def __getitem__(self, idx: int) -> JuliaVal:
        # choosing not to directly use `Base.getindex` to avoid multiple dispatch on a function with large method table

        _getattr = lambda *_: object.__getattribute__(self, *_)
        _setattr = lambda *_: object.__setattr__(self, *_)

        fns = _getattr('fns')
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

        fns = _getattr('fns')
        val = _getattr('val')

        try:
            _getattr('carr_val')[idx] = _getattr('_convert_to')(value)
            _getattr('keep')[idx] = value
        except IndexError as e:
            raise e


class JuliaArr(JuliaValGCv2):
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

        fns = _getattr('fns')

        ty_np = arr.dtype
        shape_np = arr.shape
        ptr_np = arr.ctypes.data
        
        if ty_np.name not in _getattr('_dtype_map').keys():
            raise TypeError(f'{arr.dtype} is unsupported')
        
        ty_jl = get_global(JuliaValGCv2(jl.base_module()), _getattr('_dtype_map')[ty_np.name])
        val = ptr_to_arr(fns, ptr(ty_jl), shape_np[::-1], ptr_np, own=False)
        
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
    def cast(value: JuliaValGCv2) -> np.ndarray:
        prod = lambda _: (lambda f: f(f, _))(lambda f, args: 1 if len(args) == 0 else (args[-1] * f(f, args[:-1])))
        #
        arr_ty = JuliaType.typeof(value)
        assert get_sym_name(arr_ty.name.name) == 'Array'
        #
        arr_ty_param = JuliaValGCv2(get_svec_arr(arr_ty.parameters)[0])
        arr_ty_param_name = JuliaSymbol.cast(arr_ty_param.name.name)
        if arr_ty_param_name == 'Complex':
            complex_ty_param = JuliaValGCv2(get_svec_arr(arr_ty_param.parameters)[0])
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
        dims = JuliaInt.cast(JuliaValGCv2(get_svec_arr(arr_ty.parameters)[1]))
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









        






# def dump_paulis():
#     # paulis = get_global(mod_qc, 'PAULIS')
#     ks = 'I X Y Z'.split()
#     ret = dict()
#     for k in ks:
#         pauli = getindex(paulis, JuliaValGCv2(jl.symbol(k.encode()))) # implicitly uses `paulis` defined in __main__
#         ret.setdefault(k, complexf64_to_ndarr(pauli))
#     return ret

# def dump_gates():
#     # gates = get_global(mod_qc, 'GATES')
#     ks = 'sqrtiSWAP CX CZ H X XI Y Z I'.split()
#     ret = dict()
#     for k in ks:
#         gate = getindex(gates, JuliaValGCv2(jl.symbol(k.encode()))) # implicitly uses `gates` defined in __main__
#         ret.setdefault(k, complexf64_to_ndarr(gate))
#     return ret


def dump_paulis(copy=True):
    paulis = get_global(mod_qc, 'PAULIS')
    ks = 'I X Y Z'.split(' ')
    arrs = [ndarray_from_value.cast(getindex(paulis, JuliaSymbol(k))) for k in ks]
    if copy:
        arrs = [_.copy() for _ in arrs]
    return dict(zip(ks, arrs))

def dump_gates(copy=True):
    gates = get_global(mod_qc, 'GATES')
    ks = 'sqrtiSWAP CX CZ H X XI Y Z I'.split(' ')
    arrs = [ndarray_from_value.cast(getindex(gates, JuliaSymbol(k))) for k in ks]
    if copy:
        arrs = [_.copy() for _ in arrs]
    return dict(zip(ks, arrs))


class QuantumSystem:
    def __init__(
        self,
        h_drift: np.ndarray | None = None,
        h_drives: list[np.ndarray] | None = None,
        **kwargs,
    ) -> None:
        assert (h_drift is None) or (h_drift.dtype == np.dtype('complex128')) # loosen this restriction possibly
        assert (h_drives is None) or (False not in [h_drive.dtype == np.dtype('complex128') for h_drive in h_drives]) # ditto
        #
        # self.h_drift = ndarr_to_complexf64(h_drift) if h_drift is not None else None
        # self.h_drives = ndarrs_to_mat_complexf64(h_drives) if h_drives is not None else None # Julia already handles case of len(h_drives) == 0
        self.h_drift = JuliaArr(h_drift) if h_drift is not None else None
        self.h_drives = [JuliaArr(h_drive) for h_drive in h_drives] if (h_drives is not None) and (len(h_drives) > 0) else None
        if self.h_drives is not None:
            h_drives_ty = JuliaType.typeof(self.h_drives[0])
            self.h_drives = JuliaVec(self.h_drives, h_drives_ty)
        #
        if len(kwargs) > 0:
            raise NotImplementedError()
        #
        self.args = [_ for _ in (self.h_drift, self.h_drives) if _ is not None]
        self.kwargs = dict([_ for _ in kwargs.items()]) # noop for the time being
        #
        # self.value = fn_qs(*self.args)
        self.value = get_global(mod_qc, 'QuantumSystem')(*self.args)



class QuantumControlProblem:
    def solve(self, **kwargs) -> None:
        if len(kwargs) > 0:
            raise NotImplementedError()
        #
        # fn_solve(self.value)
        get_global(mod_qc, 'solve!')(self.value)


class QuantumStateSmoothPulseProblem(QuantumControlProblem):
    def __init__(
        self,
        system: QuantumSystem,
        states_init: list[np.ndarray],
        states_goal: list[np.ndarray],
        T: int,
        dt: float | np.ndarray,
        **kwargs,
    ) -> None:
        super().__init__() # maybe handle kwargs (Piccolo/Ipopt) options here?

        assert len(states_init) > 0
        assert len(states_goal) > 0

        assert False not in [state_init.dtype == np.dtype('complex128') for state_init in states_init]
        assert False not in [state_goal.dtype == np.dtype('complex128') for state_goal in states_goal]

        self.system = system
        # self.states_init = ndarrs_to_mat_complexf64(states_init)
        # self.states_goal = ndarrs_to_mat_complexf64(states_goal)
        self.states_init, self.states_goal = [JuliaVec(states, JuliaType.typeof(states[0])) for states in [[JuliaArr(state) for state in states] for states in (states_init, states_goal)]]

        # self.T = JuliaValGC(jl.box_int64(T))
        self.T = JuliaInt(T)
        # self.dt = JuliaValGC(jl.box_float64(dt)) if not isinstance(dt, np.ndarray) else JuliaValGC(ptr_to_arr(jl, jl.float64_type(), dt.shape, dt.ctypes.data, own=False))
        self.dt = JuliaFloat(dt)

        if len(kwargs) > 0:
            raise NotImplementedError()
        
        self.value = get_global(mod_qc, 'QuantumStateSmoothPulseProblem')(self.system.value, self.states_init, self.states_goal, self.T, self.dt)


class UnitarySmoothPulseProblem(QuantumControlProblem):
    def __init__(
        self,
        system: QuantumSystem,
        operator: np.ndarray,
        T: int,
        # dt: float | np.ndarray, # TODO
        dt: float,
        **kwargs,
    ) -> None:
        super().__init__() # maybe handle kwargs (Piccolo/Ipopt) options here?

        assert operator.dtype == np.dtype('complex128')
        # assert (not isinstance(dt, np.ndarray)) or (dt.dtype == np.dtype('float64')) # TODO

        # self.system = system.value
        # self.operator = ndarr_to_complexf64(operator)
        # self.T = JuliaValGC(jl.box_int64(T))
        # self.dt = JuliaValGC(jl.box_float64(dt)) if not isinstance(dt, np.ndarray) else JuliaValGC(ptr_to_arr(jl, jl.float64_type(), dt.shape, dt.ctypes.data, own=False))
        
        self.system = system
        self.operator = JuliaArr(operator)
        self.T = JuliaInt(T)
        self.dt = JuliaFloat(dt)

        if len(kwargs) > 0:
            raise NotImplementedError()
        
        self.value = get_global(mod_qc, 'UnitarySmoothPulseProblem')(self.system.value, self.operator, JuliaInt(T), JuliaFloat(dt))



def get_complexf64():
    return get_global(JuliaValGC(jl.base_module()), 'ComplexF64')

def complexf64_to_ndarr(arr):
    # prod = lambda f, args: 1 if len(args) == 0 else (args[-1] * f(f, args[:-1]))
    prod = lambda _: (lambda f: f(f, _))(lambda f, args: 1 if len(args) == 0 else (args[-1] * f(f, args[:-1])))

    shape = tuple(jl.unbox_int64(ptr(getindex(arr.size, JuliaValGC(jl.box_int64(i + 1))))) for i in range(2))
    size = prod(shape)

    arr = arr_to_ptr(jl, c_double, np.dtype('float64'), (*shape, 2), size * 2, arr)
    arr = arr.reshape((size, 2)).astype('complex128')
    arr = (arr[:, 0] + (arr[:, 1] * 1j)).reshape(shape[::-1]).transpose(tuple(range(len(shape)))[::-1])
    return arr

def ndarr_to_complexf64(ndarr, own=False):
    return JuliaValGC(ptr_to_arr(jl, ptr(get_complexf64()), ndarr.shape[::-1], ndarr.ctypes.data, own=own))

def ndarrs_to_mat_complexf64(ndarrs, own=False):
    # assuming that each ndarr is such that len(ndarr.shape) == 2
    mat_complexf64_arrty = JuliaValGC(jl.apply_array_type(ptr(get_complexf64()), 2))
    return JuliaValGC(ptr_to_arr(jl, ptr(mat_complexf64_arrty), (len(ndarrs),), get_ctypes_arr(c_void_p, *[ptr(ndarr_to_complexf64(ndarr)) for ndarr in ndarrs]), own=own))



# def demo_dump_complexf64_ndarr():
#     arr = JuliaValGC(jl.eval_string('ComplexF64[0:3;;4:7;;8:11;;;12:15;;16:19;;20:23;;;]'.encode())) # arr.size === (4, 3, 2)
#     ndarr = arr_to_ptr(jl, c_double, np.dtype('float64'), (48,), 48, arr)
#     ndarr = ndarr.reshape((24, 2)).astype('complex128')
#     ndarr = (ndarr[:, 0] + (ndarr[:, 1] * 1j)).reshape((2, 3, 4)).transpose((2, 1, 0)) # arr.size == (4, 3, 2)
#     return ndarr
        


if __name__ == '__main__':
    libdir = "/Users/gennadiryan/.julia/dev/jl2py/target/lib"
    libname = "libjl2py.dylib"
    libpath = os.path.join(libdir, libname)

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
        
        jl_box_bool=((ctypes.c_int8,), c_void_p),
        jl_box_float64=((c_double,), c_void_p),
        jl_box_int64=((c_int64,), c_void_p),
        jl_box_voidpointer=((c_void_p,), c_void_p),
        jl_unbox_bool=((ctypes.c_void_p,), ctypes.c_int8),
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
        jl_float64_type=c_void_p,
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
    

    # predefined values
    
    println = JuliaValGCv2(jl.eval_string(b'println'))
    getindex = get_global(JuliaValGCv2(jl.base_module()), 'getindex')
    
    mod_main = JuliaValGCv2(jl.main_module())
    mod_jl2py = get_global(mod_main, 'jl2py')
    mod_qc = get_global(mod_jl2py, 'QuantumCollocation')

    # fn_qs = get_global(mod_qc, 'QuantumSystem')
    # fn_qsspp = get_global(mod_qc, 'QuantumStateSmoothPulseProblem')
    # fn_uspp = get_global(mod_qc, 'UnitarySmoothPulseProblem')
    # fn_umtp = get_global(mod_qc, 'UnitaryMinimumTimeProblem')

    # fn_solve = get_global(mod_qc, 'solve!')

    # fn_unitary_fidelity = get_global(mod_qc, 'unitary_fidelity') # unitary_fidelity -> unitary_rollout_fidelity since core peeloff
    # fn_fidelity = get_global(mod_qc, 'fidelity') # fidelity -> rollout_fidelity since core peeloff
    # fn_plot = get_global(mod_qc, 'plot_unitary_populations')
    # fn_display = get_global(mod_qc, 'display')


    # # inputs
    
    # # begin customization

    # paulis = get_global(mod_qc, 'PAULIS')
    # gates = get_global(mod_qc, 'GATES')

    # pauli_x, pauli_y = [getindex(paulis, JuliaValGC(jl.symbol(k.encode()))) for k in 'XY']
    # gate_h = getindex(gates, JuliaValGC(jl.symbol('H'.encode())))

    # ty_paulis = get_tparams(JuliaValGC(jl.typeof(ptr(paulis))))[1]
    # ty_gates = get_tparams(JuliaValGC(jl.typeof(ptr(gates))))[1]

    # carr_paulis = get_ctypes_arr(c_void_p, *map(ptr, [pauli_x, pauli_y])) # do not allow to go out of scope until the Julia array created with it is deleted
    # arr_paulis = JuliaValGC(ptr_to_arr(jl, ptr(ty_paulis), (2,), carr_paulis, False))

    # # end customization

    # val_h_drives = arr_paulis
    # op = gate_h
    # t = JuliaValGC(jl.box_int64(50))
    # dt = JuliaValGC(jl.box_float64(0.2))

    
    # # computation
    
    # syst = fn_qs(val_h_drives)
    # prob = fn_uspp(syst, op, t, dt)
    # fn_solve(prob)
    # plot = fn_plot(prob)
    # disp = fn_display(plot)
    
    
    # # outputs
    
    # dim_cols, dim_rows = tuple(jl.unbox_int64(ptr(_)) for _ in (prob.trajectory.dim, t))
    # data_vec = arr_to_ptr(jl, c_double, np.dtype('float64'), (dim_cols * dim_rows,), dim_cols * dim_rows, prob.trajectory.datavec)
    # data_mat = data_vec.reshape((dim_rows, dim_cols)).transpose()
    
    # rng_a, = [getindex(prob.trajectory.components, JuliaValGC(jl.symbol(_.encode()))) for _ in ('a',)]
    


    # _paulis, paulis = dump_paulis()
    # _gates, gates = dump_gates()

    # syst = QuantumSystem(h_drives=[paulis['X'], paulis['Y']])
    # prob = UnitarySmoothPulseProblem(syst, gates['H'], 50, 0.2)
    # prob.solve()

    # quit()

    # fid = fn_unitary_fidelity(prob.value.trajectory, syst.value)
    # print(f'Final fidelity: {fid}')

    # plot = fn_plot(prob.value.trajectory)
    # disp = fn_display(plot)

    # # dim_cols, dim_rows = tuple(jl.unbox_int64(ptr(_)) for _ in (prob.value.trajectory.dim, t))
    # # data_vec = arr_to_ptr(jl, c_double, np.dtype('float64'), (dim_cols * dim_rows,), dim_cols * dim_rows, prob.value.trajectory.datavec)
    # # data_mat = data_vec.reshape((dim_rows, dim_cols)).transpose()
    
    # # rng_a, = [getindex(prob.value.trajectory.components, JuliaValGC(jl.symbol(_.encode()))) for _ in ('a',)]
    


    # Remember to ask about "libc++abi: terminating due to uncaught exception of type Ipopt::RESTORATION_MAXITER_EXCEEDED"


    paulis = dump_paulis(copy=True)
    gates = dump_gates(copy=True)


    def demo_unitary_smooth_pulse_problem():
        system = QuantumSystem(h_drives=[paulis['X'], paulis['Y']])
        problem = UnitarySmoothPulseProblem(system, gates['H'], 50, 0.2)
        problem.value.ipopt_options.max_iter = JuliaInt(50) # hack until we finish implementing kwargs and/or IpoptOptions/PiccoloOptions

        fidelity_initial = JuliaFloat.cast(get_global(mod_qc, 'unitary_fidelity')(problem.value))
        problem.solve()
        fidelity_final = JuliaFloat.cast(get_global(mod_qc, 'unitary_fidelity')(problem.value))
        assert fidelity_final > fidelity_initial
        print(f'unitary_fidelity=(before={fidelity_initial},after={fidelity_final})')
        print()

        plot = get_global(mod_qc, 'plot_unitary_populations')(problem.value.trajectory)
        display = get_global(mod_qc, 'display')(plot)

        return problem.value.trajectory


    def demo_quantum_state_smooth_pulse_problem():
        system = QuantumSystem(h_drift=(0.1 * gates['Z']), h_drives=[gates['X'], gates['Y']])
        state_init = np.array([1., 0.], dtype=np.dtype('complex128'))
        state_goal = np.array([0., 1.], dtype=np.dtype('complex128'))
        problem = QuantumStateSmoothPulseProblem(system, [state_init], [state_goal], 50, 0.2)
        problem.value.ipopt_options.max_iter = JuliaInt(50) # hack until we finish implementing kwargs and/or IpoptOptions/PiccoloOptions
        
        fidelity_initial = JuliaFloat.cast(get_global(mod_qc, 'fidelity')(problem.value.trajectory, system.value))
        problem.solve()
        fidelity_final = JuliaFloat.cast(get_global(mod_qc, 'fidelity')(problem.value.trajectory, system.value))
        assert fidelity_final > fidelity_initial
        print(f'fidelity=(before={fidelity_initial},after={fidelity_final})')
        print()

        return problem.value.trajectory


    # demo_unitary_smooth_pulse_problem()
    # demo_quantum_state_smooth_pulse_problem()
    # print('Done!')

    unitary_traj = demo_unitary_smooth_pulse_problem()
    jl.gc_collect(1)
    quantum_state_traj = demo_quantum_state_smooth_pulse_problem()
    jl.gc_collect(1)
    print('Done!')

    # kts = JuliaValGCv2(jl.eval_string(b'[typeof(k.x) for k in keys(refs)]'))
    # val = object.__getattribute__(kts, '__repr__')()

    
