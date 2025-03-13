import ctypes
from ctypes import *
from pysrc.julia import init_jl

jl = init_jl()

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

def jl_gc_framedump():
    pgcstack_ptr_addr = jl.get_pgcstack()
    pgcstack_addr = c_void_p.from_address(pgcstack_ptr_addr).value
    pgcstack_addr = 0 if pgcstack_addr is None else pgcstack_addr
    while pgcstack_addr > 0:
        n = c_void_p.from_address(pgcstack_addr).value >> 2
        prev_pgcstack_addr = c_void_p.from_address(pgcstack_addr + (1 * ctypes.sizeof(c_void_p))).value
        prev_pgcstack_addr = 0 if prev_pgcstack_addr is None else prev_pgcstack_addr
        pgcstack = [c_void_p.from_address(pgcstack_addr + ((2 + i) * ctypes.sizeof(c_void_p))).value for i in range(n)]
        pgcstack = [0 if _ is None else _ for _ in pgcstack]
        print(pgcstack_addr, (n, prev_pgcstack_addr, pgcstack))
        pgcstack_addr = prev_pgcstack_addr
    print('Reached end of frame')
    print()


use_gc = True
stk0 = jl_gc_pushargs(3)
c0 = 2
push0 = [lambda _: _, lambda _: [stk0.__setitem__(c0, _), c0 + 1][-1]][int(use_gc)]

println = jl.get_global(jl.base_module(), jl.symbol(b'println')); c0 = push0(println)

ty_mut = jl.eval_string(b'mutable struct pt_mut; x::Int; y::Int; end; pt_mut'); c0 = push0(ty_mut)
ty_immut = jl.eval_string(b'struct pt_immut; x::Int; y::Int; end; pt_immut'); c0 = push0(ty_immut)

jl_gc_framedump()

def test_gc_pushargs(depth=0):
    stk = jl_gc_pushargs(4)
    c = 2
    push = [lambda _: _, lambda _: [stk.__setitem__(c, _), c + 1][-1]][int(use_gc)]

    x = jl.box_int64(4); c = push(x)
    y = jl.box_int64(20); c = push(y)

    carr_args = (c_void_p * 2)(x, y)
    inst_mut = jl.new_structv(ty_mut, carr_args, 2); c = push(inst_mut)
    inst_immut = jl.new_structv(ty_immut, carr_args, 2); c = push(inst_immut)

    jl.call1(println, x)
    jl.call1(println, y)
    jl.call1(println, ty_mut)
    jl.call1(println, ty_immut)
    jl.call1(println, inst_mut)
    jl.call1(println, inst_immut)
    jl.call0(println)

    jl.gc_collect(1)

    jl_gc_framedump()

    if depth > 0:
        test_gc_pushargs(depth=(depth - 1))

    jl.call1(println, x)
    jl.call1(println, y)
    jl.call1(println, ty_mut)
    jl.call1(println, ty_immut)
    jl.call1(println, inst_mut)
    jl.call1(println, inst_immut)
    jl.call0(println)

    jl.gc_collect(1)

    jl_gc_framedump()

    jl_gc_pop()

test_gc_pushargs(depth=1)

jl_gc_framedump()

jl_gc_pop()
