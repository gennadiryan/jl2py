import numpy as np

from ..julia.julia_value import init_jl, ptr_to_arr, arr_to_ptr, get_ctypes_arr, get_nt, JuliaVal, JuliaValGC
from ..julia.julia_extras import ptr, get_global, call_with_kwargs, JuliaType, JuliaNum, JuliaInt, JuliaFloat, JuliaComplex, JuliaSymbol, JuliaVec, JuliaArr, ndarray_from_value, println, getindex

from . import mod_pic, jl

def traj_to_mat(traj):
    dim_cols, dim_rows = tuple(jl.unbox_int64(ptr(_)) for _ in (traj.dim, traj.T))
    data_vec = ndarray_from_value.cast(traj.datavec)
    data_mat = data_vec.reshape((dim_rows, dim_cols)).transpose()
    return data_mat


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
        self.value = get_global(mod_pic, 'QuantumSystem')(*self.args)


class QuantumControlProblem:
    def solve(self, max_iter: int | None = None, **kwargs) -> None:
        if len(kwargs) > 0:
            raise NotImplementedError()
        
        # if max_iter is not None:
        #     self.value.ipopt_options.max_iter = JuliaInt(max_iter)

        if max_iter is not None:
            fn = get_global(mod_pic, 'solve!')
            args = [self.value,]
            names = ['max_iter']
            vals = [JuliaInt(max_iter)]
            
            # def call_with_kwargs(fn, args, names, vals):
            #     tys = [JuliaType.typeof(_) for _ in vals]
                
            #     _fn = ptr(fn)
            #     _args, _vals, _tys = [list(map(ptr, _)) for _ in (args, vals, tys)]

            #     nt = JuliaValGC(get_nt(jl, names, _vals, _tys))
            #     _nt = ptr(nt)
                
            #     carr_args = get_ctypes_arr(c_void_p, *(_nt, _fn, *_args))
            #     return JuliaValGC(jl.call(jl.kwcall_func(), carr_args, len(args) + 2))
            
            return call_with_kwargs(fn, args, names, vals)

            # return JuliaValGC(call_with_kwargs(jl, fn, args, names, vals, tys))
        
        get_global(mod_pic, 'solve!')(self.value)

def unitary_fidelity(problem: QuantumControlProblem) -> float:
    return JuliaFloat.cast(get_global(mod_pic, 'unitary_fidelity')(problem.value))

def plot_unitary_populations(problem: QuantumControlProblem, display_plot: bool = False):
    plot = get_global(mod_pic, 'plot_unitary_populations')(problem.value.trajectory)
    if display_plot == True:
        display = get_global(mod_pic, 'display')(plot)
    return plot

def display(plot):
    display = get_global(mod_pic, 'display')(plot)
