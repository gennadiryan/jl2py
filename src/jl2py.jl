module jl2py

# Write your package code here.

using QuantumCollocation

export _inc32, _inc64, _dec32, _dec64
export demo
# export one_mystruct, get_one_mystruct, get_one_mystruct_to_ptr, dump_one_mystruct_from_ptr, get_mystruct_type


inc32(x::Int32)::Int32 = x + 1
inc64(x::Int64)::Int64 = x + 1
dec32(x::Int32)::Int32 = x - 1
dec64(x::Int64)::Int64 = x - 1

Base.@ccallable _inc32(x::Cint)::Cint = inc32(x)
Base.@ccallable _inc64(x::Clonglong)::Clonglong = inc64(x)
Base.@ccallable _dec32(x::Cint)::Cint = dec32(x)
Base.@ccallable _dec64(x::Clonglong)::Clonglong = dec64(x)

mutable struct mystruct
    x::Int32
    y::Int32
end

Base.@ccallable function demo()::Cvoid
    println("Hello, world!")
end

# global one_mystruct = mystruct(1, 1)

# get_one_mystruct()::mystruct = one_mystruct
# Base.@ccallable get_one_mystruct_to_ptr()::Cptrdiff_t = pointer_from_objref(Ref{mystruct}(one_mystruct))
# Base.@ccallable dump_one_mystruct_from_ptr(ptr::Cptrdiff_t)::Cvoid = println(unsafe_load(Ptr{mystruct}(ptr)))
# # Base.@ccallable dump_one_mystruct_ptr()::Cvoid = println()
# # Base.@ccallable new_mystruct(x::Cint, y::Cint)::Cptrdiff_t = mystruct(x, y)

# get_mystruct_type()::DataType = mystruct

end
