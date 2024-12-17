module jl2py

# Write your package code here.

export _inc32, _inc64, _dec32, _dec64

inc32(x::Int32)::Int32 = x + 1
inc64(x::Int64)::Int64 = x + 1
dec32(x::Int32)::Int32 = x - 1
dec64(x::Int64)::Int64 = x - 1

Base.@ccallable _inc32(x::Cint)::Cint = inc32(x)
Base.@ccallable _inc64(x::Clonglong)::Clonglong = inc64(x)
Base.@ccallable _dec32(x::Cint)::Cint = dec32(x)
Base.@ccallable _dec64(x::Clonglong)::Clonglong = dec64(x)

end
