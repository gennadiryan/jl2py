# jl2py

[![Build Status](https://github.com/gennadiryan/jl2py.jl/actions/workflows/CI.yml/badge.svg?branch=main)](https://github.com/gennadiryan/jl2py.jl/actions/workflows/CI.yml?query=branch%3Amain)

## Build

```
# Build ./target/{include,lib,share}
julia ./build/build.jl

# Build main
gcc -I./target/include -c -o ./main.o ./main.c
gcc -L./target/lib -L./target/lib/julia -ljl2py -o ./main ./main.o

# Build main with use of libjulia header files (e.g. "julia.h").
#   Second include path is a result of the Julia "joinpath(Sys.BINDIR, Base.INCLUDEDIR, "julia")"
gcc -I./target/include -I/Users/gennadiryan/.julia/juliaup/julia-1.11.2+0.aarch64.apple.darwin14/bin/../include/julia -c -o ./main.o ./main.c

# On linux, to configure dynamic linker bindings, you must add the shared library to the LD_LIBRARY_PATH env variable like so
# (LINUX SPECIFIC)
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:./target/lib

# compile into target (all platforms)
gcc -L./target/lib -L./target/lib/julia -ljulia -ljl2py -o ./main ./main.o
```

When complete, the `target/include` directory should consist of `julia_init.h` (libjulia headers) and `jl2py.h` (Julia/C FFI headers). The `target/lib` directory should likewise consist of `libjulia.[libext]` (up to version) and `libjl2py.[libext]`, along with a directory `target/lib/julia` of `libjulia` `*.[libext]` library files (`[libext]` is platform-dependent; that is, `dylib` on OSX, `so` on Linux, and `dll` on Windows; the `DYLD_FALLBACK_LIBRARY_PATH` environment variable is likewise).

#### TODO

Determine whether omitting `#include "julia_init.h"` and relying on `#include "julia.h"` is possible, and if so, what performance implications there are (according to how memory is handled).

## Run

### C

```
DYLD_FALLBACK_LIBRARY_PATH=./target/lib:./target/lib/julia ./main
```

### Python

```
DYLD_FALLBACK_LIBRARY_PATH=./target/lib:./target/lib/julia python3 ./main.py
```

`main.py` is responsible for registering many useful `libjulia` functions with a Python/ctypes wrapper. Modifying the command to `python3 -i ./main.py` allows for a REPL-like environment from which various `libjulia` methods may be invoked.

#### Demos

<!-- ```
DYLD_FALLBACK_LIBRARY_PATH=jl2py/target/lib:jl2py/target/lib/julia python3 -m jl2py.demo.quantum_collocation_demo
``` -->

```
PYTHOH_PATH=/Users/gennadiryan/Documents/kestrel/jl2py/src DYLD_FALLBACK_LIBRARY_PATH=/Users/gennadiryan/.julia/dev/jl2py/target/lib:/Users/gennadiryan/.julia/dev/jl2py/target/lib/julia JULIA_LIBRARY_PATH=/Users/gennadiryan/.julia/dev/jl2py/target/lib python -i src/demo_main.py
```

```
PYTHONPATH=/Users/gennadiryan/Documents/kestrel/jl2py/src DYLD_FALLBACK_LIBRARY_PATH=/Users/gennadiryan/.julia/dev/jl2py/target/lib:/Users/gennadiryan/.julia/dev/jl2py/target/lib/julia JULIA_LIBRARY_PATH=/Users/gennadiryan/.julia/dev/jl2py/target/lib python -i tests/test.py
```

#### TODOs

- Consider whether Cython is preferable to ctypes

##### Comments

The demo uses `jl_eval_string` to execute line-by-line the demo script from the `QuantumCollocation` `README.md`.
