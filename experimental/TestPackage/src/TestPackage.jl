module TestPackage

export greet
export test_kwfunc

greet() = print("Hello World!")

function test_kwfunc(a::Int64, b::Int64; x::Int64=0, y::Int64=0)::Int64
    println((a, b))
    return x + y
end

end # module TestPackage
