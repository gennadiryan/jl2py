using PackageCompiler

PackageCompiler.create_library(".", "$(@__DIR__)/../target", lib_name="jl2py", incremental=true, filter_stdlibs=true, force=true, include_lazy_artifacts=true, header_files=["$(@__DIR__)/jl2py.h"])
