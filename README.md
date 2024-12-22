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
#   Second include path is a result of the Julia "joinpath(Sys.BINDIR, Base.INCLUDEDIR, \"julia\")"
gcc -I./target/include -I/Users/gennadiryan/.julia/juliaup/julia-1.11.2+0.aarch64.apple.darwin14/bin/../include/julia -c -o ./main.o ./main.c
gcc -L./target/lib -L./target/lib/julia -ljulia -ljl2py -o ./main ./main.o
```

#### TODO

Determine whether omitting `#include "julia_init.h` and relying on `#include "julia.h"` is possible, and if so, what performance implications there are (according to how memory is handled).

## Run

### C

```
DYLD_FALLBACK_LIBRARY_PATH=./target/lib:./target/lib/julia ./main
```

### Python

```
DYLD_FALLBACK_LIBRARY_PATH=./target/lib:./target/lib/julia python3 ./main.py
```

