import sys
import os

import ctypes
from ctypes import cdll, c_double, c_float, c_int, c_int32, c_int64, c_uint, c_uint32, c_uint64, c_size_t, c_char_p, c_void_p

import numpy as np

from pypiccolo.julia import jl
from pypiccolo.julia.julia_value import JuliaVal, JuliaValGC
from pypiccolo.julia.julia_extras import ptr, get_global, call_with_kwargs, JuliaType, JuliaNum, JuliaInt, JuliaFloat, JuliaComplex, JuliaSymbol, JuliaModule, JuliaVec, JuliaArr, ndarray_from_value, println, getindex, setindex, typeof


def dump_paulis(copy=True):
    paulis = get_global(mod_pic, 'PAULIS')
    ks = 'I X Y Z'.split(' ')
    arrs = [ndarray_from_value.cast(getindex(paulis, JuliaSymbol(k))) for k in ks]
    if copy:
        arrs = [_.copy() for _ in arrs]
    return dict(zip(ks, arrs))

def dump_gates(copy=True):
    gates = get_global(mod_pic, 'GATES')
    ks = 'sqrtiSWAP CX CZ H X XI Y Z I'.split(' ')
    arrs = [ndarray_from_value.cast(getindex(gates, JuliaSymbol(k))) for k in ks]
    if copy:
        arrs = [_.copy() for _ in arrs]
    return dict(zip(ks, arrs))


def traj_to_mat(traj):
    dim_cols, dim_rows = tuple(jl.unbox_int64(ptr(_)) for _ in (traj.dim, traj.T))
    data_vec = ndarray_from_value.cast(traj.datavec)
    data_mat = data_vec.reshape((dim_rows, dim_cols)).transpose()
    return data_mat

def traj_to_plt(traj):
    dims, _ = traj.shape
    assert ((dims - 1 - 8) > 0) and (((dims - 1 - 8) % 3) == 0)

    dims_ctrls = (dims - 1 - 8) // 3

    u11 = traj[[0, 2]]
    u12 = traj[[1, 3]]
    u21 = traj[[4, 6]]
    u22 = traj[[5, 7]]

    u11, u12, u21, u22 = [(_ ** 2).sum(axis=0) for _ in (u11, u12, u21, u22)]

    u1 = np.array([u11, u12]).transpose()
    u2 = np.array([u21, u22]).transpose()
    ctrls = np.array(traj[8:8 + dims_ctrls]).transpose()
    
    try:
        import matplotlib.pyplot as plt

        plt.figure()

        plt.subplot(311)
        plt.plot(u1)
        plt.subplot(312)
        plt.plot(u2)
        plt.subplot(313)
        plt.plot(ctrls)
        
        plt.show()
    
    except ModuleNotFoundError as e:
        print('matplotlib.pyplot unavailable')






mod_base = JuliaModule(jl.base_module())
mod_main = JuliaModule(jl.main_module())
mod_pic = JuliaModule(ptr(mod_main.Piccolo))


paulis = dump_paulis()
gates = dump_gates()

drift = JuliaArr(paulis['Z'])
drives = [JuliaArr(paulis[_]) for _ in 'X Y'.split(' ')]
drives = JuliaVec(drives, JuliaType.typeof(drives[0]))

syst = mod_pic.QuantumSystem(drift, drives)
op = JuliaArr(gates['H'])
t = JuliaInt(51)
dt = JuliaFloat(0.2)

pic_opts = call_with_kwargs(mod_pic.PiccoloOptions, [], 'verbose'.split(' '), [JuliaValGC(jl.false())])

# prob = mod_pic.UnitarySmoothPulseProblem(syst, op, t, dt)
prob = call_with_kwargs(mod_pic.UnitarySmoothPulseProblem, [syst, op, t, dt], 'da_bound piccolo_options'.split(' '), [JuliaFloat(1.), pic_opts])

fid_init = mod_pic.unitary_rollout_fidelity(prob.trajectory, syst)
# getattr(mod_pic, 'solve!')(prob)
call_with_kwargs(getattr(mod_pic, 'solve!'), [prob], 'max_iter verbose print_level'.split(), [JuliaInt(100), JuliaValGC(jl.false()), JuliaInt(1)])
fid_final = mod_pic.unitary_rollout_fidelity(prob.trajectory, syst)

fid_init, fid_final = [jl.unbox_float64(ptr(_)) for _ in [fid_init, fid_final]]
assert fid_final > fid_init


# traj = traj_to_mat(prob.trajectory)

# u11 = traj[[0, 2]]
# u12 = traj[[1, 3]]
# u21 = traj[[4, 6]]
# u22 = traj[[5, 7]]

# u11, u12, u21, u22 = [(_ ** 2).sum(axis=0) for _ in (u11, u12, u21, u22)]

# a1 = traj[8]
# a2 = traj[9]

# plt.figure()

# plt.subplot(311)
# plt.plot(np.array([u11, u12]).transpose())

# plt.subplot(312)
# plt.plot(np.array([u21, u22]).transpose())

# plt.subplot(313)
# plt.plot(np.array([a1, a2]).transpose())
