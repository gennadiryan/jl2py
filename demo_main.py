import os

import ctypes
from ctypes import cdll, c_double, c_float, c_int, c_int32, c_int64, c_uint, c_uint32, c_uint64, c_size_t, c_char_p, c_void_p

import numpy as np

from experimental.main import JuliaLib, CDLLUtils, JuliaVal, JuliaValGC, as_object, ptr_to_arr, arr_to_ptr, get_ctypes_arr, init_JuliaVal, init_JuliaValGC


"""
TODO:
    - write functions implementing [Unitary,QuantumState]SmoothPulseProblem
    - add support for additional QCPs/problem templates (e.g. unitary sampling problem)
    - add support for customized initial trajectories
    - add more support for/examples of retrieving data from trajectories
    - generalize inputs (as best as possible) to other <: Number types besides ComplexF64 (currently requires special handling due to numpy representation of complex128)

    - write tests comparing ptr_to_arr(..., own=True) vs ptr_to_arr(..., own=False)
    - write tests based on `@testitem`s from [unitary,quantum_state]_smooth_pulse_problem.jl (to investigate limitations of JuliaVal API as well as to get some ideas for demo tasks, esp. as we plan compare to test QuTIP on the same tasks)

main.py TODO:
    - get rid of implicit uses of globally defined Julia fns (e.g. getindex)
    - get rid of unnecessary args/kwargs expansions (e.g. in get_ctypes_arr), or verify they introduce no performance penalty
    - move definitions of libjulia-related values (cdll instance, asobject wrapper instance, etc.) into module body to ensure that they are imported and run exactly once
    - make ^^ depend on setuptools-related configs
    - handle library checks, (if necessary) first-time Pkg.add(), etc. in setup script
    - figure out why arr_to_ptr returns a flat array and falsely passes dtype tests (not a breaking issue but should be addressed nonetheless)
    - rebuild target with latest Piccolo.jl version

Misc TODO:
    - add QuTIP support

DONE:
    - rebase to integrate Jack's updates
    - add support for the same unitaries/gates as offered by Piccolo.jl
"""



def ptr(value):
    return object.__getattribute__(value, 'val')

def get_global(module, name):
    return JuliaValGC(jl.get_global(ptr(module), jl.symbol(name.encode())))

def get_tparams(ty):
    _ty = ptr(ty)
    _ty_params = jl.get_nth_field(_ty, jl.field_index(jl.typeof(_ty), jl.symbol('parameters'.encode()), 0))
    _ty_params_len = c_size_t.from_address(_ty_params)
    return [JuliaValGC(c_void_p.from_address(_ty_params + ctypes.sizeof(_ty_params_len) + (ctypes.sizeof(c_void_p) * i))) for i in range(_ty_params_len.value)]



def dump_paulis():
    ks = 'I X Y Z'.split()
    ret = dict()
    for k in ks:
        pauli = getindex(paulis, JuliaValGC(jl.symbol(k.encode()))) # implicitly uses `paulis` defined in __main__
        ret.setdefault(k, complexf64_to_ndarr(pauli))
    return ret

def dump_gates():
    ks = 'sqrtiSWAP CX CZ H X XI Y Z I'.split()
    ret = dict()
    for k in ks:
        gate = getindex(gates, JuliaValGC(jl.symbol(k.encode()))) # implicitly uses `gates` defined in __main__
        ret.setdefault(k, complexf64_to_ndarr(gate))
    return ret



class QuantumSystem:
    def __init__(
        self,
        h_drift: np.ndarray | None = None,
        h_drives: list[np.ndarray] | None = None,
        **kwargs,
    ) -> None:
        assert (h_drift is None) or (h_drift.dtype == np.dtype('complex128'))
        assert (h_drives is None) or (False not in [h_drive.dtype == np.dtype('complex128') for h_drive in h_drives])

        self.h_drift = ndarr_to_complexf64(h_drift) if h_drift is not None else None
        self.h_drives = ndarrs_to_mat_complexf64(h_drives) if h_drives is not None else None # Julia already handles case of len(h_drives) == 0

        if len(kwargs) > 0:
            raise NotImplementedError()

        self.args = [_ for _ in (self.h_drift, self.h_drives) if _ is not None]
        self.kwargs = dict([_ for _ in kwargs.items()]) # noop for the time being

        self.value = fn_qs(*self.args)



class QuantumControlProblem:
    def solve(self, **kwargs) -> None:
        if len(kwargs) > 0:
            raise NotImplementedError()
        
        fn_solve(self.value)


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

        assert False not in [state_init.dtype == np.dtype('complex128') for state_init in states_init]
        assert False not in [state_goal.dtype == np.dtype('complex128') for state_goal in states_goal]

        self.system = system.value
        self.states_init = ndarrs_to_mat_complexf64(states_init)
        self.states_goal = ndarrs_to_mat_complexf64(states_goal)

        self.T = JuliaValGC(jl.box_int64(T))
        self.dt = JuliaValGC(jl.box_float64(dt)) if not isinstance(dt, np.ndarray) else JuliaValGC(ptr_to_arr(jl, jl.float64_type(), dt.shape, dt.ctypes.data, own=False))

        if len(kwargs) > 0:
            raise NotImplementedError()
        
        self.value = fn_qsspp(self.system, self.states_init, self.states_goal, self.T, self.dt)


class UnitarySmoothPulseProblem(QuantumControlProblem):
    def __init__(
        self,
        system: QuantumSystem,
        operator: np.ndarray,
        T: int,
        dt: float | np.ndarray,
        **kwargs,
    ) -> None:
        super().__init__() # maybe handle kwargs (Piccolo/Ipopt) options here?

        assert operator.dtype == np.dtype('complex128')
        assert (not isinstance(dt, np.ndarray)) or (dt.dtype == np.dtype('float64'))

        self.system = system.value
        self.operator = ndarr_to_complexf64(operator)
        self.T = JuliaValGC(jl.box_int64(T))
        self.dt = JuliaValGC(jl.box_float64(dt)) if not isinstance(dt, np.ndarray) else JuliaValGC(ptr_to_arr(jl, jl.float64_type(), dt.shape, dt.ctypes.data, own=False))

        if len(kwargs) > 0:
            raise NotImplementedError()
        
        self.value = fn_uspp(self.system, self.operator, self.T, self.dt)

    

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

def ndarr_to_complexf64(ndarr):
    return JuliaValGC(ptr_to_arr(jl, ptr(get_complexf64()), ndarr.shape[::-1], ndarr.ctypes.data, own=False))

def ndarrs_to_mat_complexf64(ndarrs):
    # assuming that each ndarr is such that len(ndarr.shape) == 2
    mat_complexf64_arrty = JuliaValGC(jl.apply_array_type(ptr(get_complexf64()), 2))
    return JuliaValGC(ptr_to_arr(jl, ptr(mat_complexf64_arrty), (len(ndarrs),), get_ctypes_arr(c_void_p, *[ptr(ndarr_to_complexf64(ndarr)) for ndarr in ndarrs]), own=False))



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
        
        jl_box_float64=((c_double,), c_void_p),
        jl_box_int64=((c_int64,), c_void_p),
        jl_box_voidpointer=((c_void_p,), c_void_p),
        jl_unbox_float64=((c_void_p,), c_double),
        jl_unbox_int64=((c_void_p,), c_int64),
        jl_unbox_voidpointer=((c_void_p,), c_void_p),
        jl_string_ptr=((c_void_p,), c_char_p),

        jl_egal=((c_void_p, c_void_p,), c_void_p),

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
    
    println = JuliaValGC(jl.eval_string(b'println'))
    getindex = get_global(JuliaValGC(jl.base_module()), 'getindex')
    
    mod_main = JuliaValGC(jl.main_module())
    mod_jl2py = get_global(mod_main, 'jl2py')
    mod_qc = get_global(mod_jl2py, 'QuantumCollocation')

    fn_qs = get_global(mod_qc, 'QuantumSystem')
    fn_qsspp = get_global(mod_qc, 'QuantumStateSmoothPulseProblem')
    fn_uspp = get_global(mod_qc, 'UnitarySmoothPulseProblem')
    fn_umtp = get_global(mod_qc, 'UnitaryMinimumTimeProblem')

    fn_solve = get_global(mod_qc, 'solve!')

    fn_unitary_fidelity = get_global(mod_qc, 'unitary_fidelity') # unitary_fidelity -> unitary_rollout_fidelity since core peeloff
    fn_fidelity = get_global(mod_qc, 'fidelity') # fidelity -> rollout_fidelity since core peeloff
    fn_plot = get_global(mod_qc, 'plot_unitary_populations')
    fn_display = get_global(mod_qc, 'display')


    # inputs
    
    # begin customization

    paulis = get_global(mod_qc, 'PAULIS')
    gates = get_global(mod_qc, 'GATES')

    pauli_x, pauli_y = [getindex(paulis, JuliaValGC(jl.symbol(k.encode()))) for k in 'XY']
    gate_h = getindex(gates, JuliaValGC(jl.symbol('H'.encode())))

    ty_paulis = get_tparams(JuliaValGC(jl.typeof(ptr(paulis))))[1]
    ty_gates = get_tparams(JuliaValGC(jl.typeof(ptr(gates))))[1]

    carr_paulis = get_ctypes_arr(c_void_p, *map(ptr, [pauli_x, pauli_y])) # do not allow to go out of scope until the Julia array created with it is deleted
    arr_paulis = JuliaValGC(ptr_to_arr(jl, ptr(ty_paulis), (2,), carr_paulis, False))

    # end customization

    val_h_drives = arr_paulis
    op = gate_h
    t = JuliaValGC(jl.box_int64(50))
    dt = JuliaValGC(jl.box_float64(0.2))

    
    # computation
    
    syst = fn_qs(val_h_drives)
    prob = fn_uspp(syst, op, t, dt)
    fn_solve(prob)
    plot = fn_plot(prob)
    disp = fn_display(plot)
    
    
    # outputs
    
    dim_cols, dim_rows = tuple(jl.unbox_int64(ptr(_)) for _ in (prob.trajectory.dim, t))
    data_vec = arr_to_ptr(jl, c_double, np.dtype('float64'), (dim_cols * dim_rows,), dim_cols * dim_rows, prob.trajectory.datavec)
    data_mat = data_vec.reshape((dim_rows, dim_cols)).transpose()
    
    rng_a, = [getindex(prob.trajectory.components, JuliaValGC(jl.symbol(_.encode()))) for _ in ('a',)]
    
