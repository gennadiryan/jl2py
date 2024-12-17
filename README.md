# jl2py

[![Build Status](https://github.com/gennadiryan/jl2py.jl/actions/workflows/CI.yml/badge.svg?branch=main)](https://github.com/gennadiryan/jl2py.jl/actions/workflows/CI.yml?query=branch%3Amain)

## Build

```
# Build ./target/{include,lib,share}
julia ./build/build.jl

# Build main
gcc -I./target/include -c -o ./main.o ./main.c
gcc -L./target/lib -L./target/lib/julia -ljl2py -o ./main ./main.o
```

## Run

### C

```
DYLD_FALLBACK_LIBRARY_PATH=./target/lib:./target/lib/julia ./main
```

### Python

```
DYLD_FALLBACK_LIBRARY_PATH=./target/lib:./target/lib/julia python3 ./main.py
```

