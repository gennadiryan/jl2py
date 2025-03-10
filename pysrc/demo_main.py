import os

import ctypes
from ctypes import cdll, c_double, c_float, c_int, c_int32, c_int64, c_uint, c_uint32, c_uint64, c_size_t, c_char_p, c_void_p

import numpy as np

# from experimental.main import JuliaLib, CDLLUtils, JuliaVal, JuliaValGC, as_object, ptr_to_arr, arr_to_ptr, get_ctypes_arr, init_JuliaVal, init_JuliaValGC, add_ref, del_ref
from julia.julia_value import init_jl, ptr_to_arr, arr_to_ptr, get_ctypes_arr, JuliaVal, JuliaValGC
from julia.julia_extras import get_global, JuliaType, JuliaNum, JuliaInt, JuliaFloat, JuliaComplex, JuliaSymbol, JuliaVec, JuliaArr, ndarray_from_value, println, getindex

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



if __name__ == '__main__':
    jl = init_jl()

    # predefined values
    
    println = JuliaValGC(jl.eval_string(b'println'))
    getindex = get_global(JuliaValGC(jl.base_module()), 'getindex')
    
    mod_main = JuliaValGC(jl.main_module())
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

    
