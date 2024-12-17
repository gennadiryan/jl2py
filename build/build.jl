using PackageCompiler

PackageCompiler.create_library(".", "$(@__DIR__)/../target", lib_name="jl2py", incremental=false, filter_stdlibs=true, force=true, header_files=["$(@__DIR__)/jl2py.h"])
