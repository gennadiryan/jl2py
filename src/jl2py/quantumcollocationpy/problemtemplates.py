from .quantumcollocation import QuantumSystem, QuantumControlProblem

from ..julia.julia_value import init_jl, ptr_to_arr, arr_to_ptr, get_ctypes_arr, get_nt, JuliaVal, JuliaValGC
from ..julia.julia_extras import ptr, get_global, call_with_kwargs, JuliaType, JuliaNum, JuliaInt, JuliaFloat, JuliaComplex, JuliaSymbol, JuliaVec, JuliaArr, ndarray_from_value, println, getindex

import numpy as np

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


class UnitaryMinimumTimeProblem(QuantumControlProblem):
    def __init__(
        self,
        prob: QuantumControlProblem,
        system: QuantumSystem,
        final_fidelity: float | None = None,
    ) -> None:
        super().__init__()

        self.prob = prob
        self.system = system

        fn = get_global(mod_qc, 'UnitaryMinimumTimeProblem')
        args = [self.prob.value]
        names = ['final_fidelity'] if final_fidelity is not None else list()
        vals = [JuliaFloat(final_fidelity)] if final_fidelity is not None else list()

        self.value = call_with_kwargs(fn, args, names, vals)

        # self.value = get_global(mod_qc, 'UnitaryMinimumTimeProblem')(self.prob.value, self.system.value)
        

