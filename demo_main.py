import os

import ctypes
from ctypes import cdll, c_double, c_float, c_int, c_int32, c_int64, c_uint, c_uint32, c_uint64, c_size_t, c_char_p, c_void_p

from experimental.main import JuliaLib, CDLLUtils, JuliaVal, JuliaValGC, as_object, ptr_to_arr, arr_to_ptr, get_ctypes_arr, init_JuliaVal, init_JuliaValGC


"""
TODO:
    - rebase to integrate Jack's updates
    - add support for additional QCPs/problem templates (e.g. unitary sampling problem)
    - add support for customized initial trajectories
    - add more support for/examples of retrieving data from trajectories
"""


# class UnitarySmoothPulseProblem:
#     def __init__(self, system, operator, t, dt):
#         self._system = system
#         self._operator = operator
#         self._t = JuliaValGC(jl.box_int64(t))
#         self._dt = JuliaValGC(jl.box_float64(dt))

#         self.value = fn_uspp(self._system, self._operator, self._t, self._dt)



def ptr(value):
    return object.__getattribute__(value, 'val')

def get_global(module, name):
    return JuliaValGC(jl.get_global(ptr(module), jl.symbol(name.encode())))

def get_tparams(ty):
    _ty = ptr(ty)
    _ty_params = jl.get_nth_field(_ty, jl.field_index(jl.typeof(_ty), jl.symbol('parameters'.encode()), 0))
    _ty_params_len = c_size_t.from_address(_ty_params)
    return [JuliaValGC(c_void_p.from_address(_ty_params + ctypes.sizeof(_ty_params_len) + (ctypes.sizeof(c_void_p) * i))) for i in range(_ty_params_len.value)]



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
    getindex = get_global(JuliaValGC(jl.base_module()), 'getindex')
    
    mod_main = JuliaValGC(jl.main_module())
    mod_jl2py = get_global(mod_main, 'jl2py')
    mod_qc = get_global(mod_jl2py, 'QuantumCollocation')

    fn_qs = get_global(mod_qc, 'QuantumSystem')
    fn_uspp = get_global(mod_qc, 'UnitarySmoothPulseProblem')

    fn_solve = get_global(mod_qc, 'solve!')

    fn_plot = get_global(mod_qc, 'plot_unitary_populations')
    fn_display = get_global(mod_qc, 'display')


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

    syst = fn_qs(val_h_drives)
    prob = fn_uspp(syst, op, t, dt)
    fn_solve(prob)
    plot = fn_plot(prob)
    disp = fn_display(plot)

    import numpy as np
    
    dim_cols, dim_rows = tuple(jl.unbox_int64(ptr(_)) for _ in (prob.trajectory.dim, t))
    data_vec = arr_to_ptr(jl, c_double, np.dtype('float64'), (dim_cols * dim_rows,), dim_cols * dim_rows, prob.trajectory.datavec)
    data_mat = data_vec.reshape((dim_rows, dim_cols)).transpose()
    
    rng_a, = [getindex(prob.trajectory.components, JuliaValGC(jl.symbol(_.encode()))) for _ in ('a',)]
    
