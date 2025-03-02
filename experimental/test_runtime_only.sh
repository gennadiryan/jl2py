export JULIA_SYS_BINDIR="/Users/gennadiryan/.julia/juliaup/julia-1.11.2+0.aarch64.apple.darwin14/bin"
export JULIA_BASE_INCLUDEDIR="../include"
export JULIA_BASE_LIBDIR="../lib"

gcc -I${JULIA_SYS_BINDIR}/${JULIA_BASE_INCLUDEDIR}/julia -c -o ./experimental/test_runtime_only.o ./experimental/test_runtime_only.c
gcc -L${JULIA_SYS_BINDIR}/${JULIA_BASE_LIBDIR} -L${JULIA_SYS_BINDIR}/${JULIA_BASE_LIBDIR}/julia -ljulia -o ./experimental/test_runtime_only ./experimental/test_runtime_only.o
DYLD_FALLBACK_LIBRARY_PATH=${JULIA_SYS_BINDIR}/${JULIA_BASE_LIBDIR}:${JULIA_SYS_BINDIR}/${JULIA_BASE_LIBDIR}/julia ./experimental/test_runtime_only
