using PackageCompiler

PackageCompiler.create_library(".", "$(@__DIR__)/../target", lib_name="libjltestpkg", incremental=true, filter_stdlibs=true, force=true, include_lazy_artifacts=true)
