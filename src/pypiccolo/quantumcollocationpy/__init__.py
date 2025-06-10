from ..julia.julia_value import init_jl, ptr_to_arr, arr_to_ptr, get_ctypes_arr, get_nt, JuliaVal, JuliaValGC
from ..julia.julia_extras import ptr, get_global, call_with_kwargs, JuliaType, JuliaNum, JuliaInt, JuliaFloat, JuliaComplex, JuliaSymbol, JuliaVec, JuliaArr, ndarray_from_value, println, getindex

from ..julia import jl

jl = init_jl()
mod_core = JuliaValGC(jl.core_module())
mod_base = JuliaValGC(jl.base_module())
mod_main = JuliaValGC(jl.main_module())
# mod_jl2py = get_global(mod_main, 'jl2py')
# mod_qc = get_global(mod_jl2py, 'QuantumCollocation')
mod_pic = get_global(mod_main, 'Piccolo')

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

PAULIS = dump_paulis()
GATES = dump_gates()



