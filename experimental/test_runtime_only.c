#include <stdio.h>

#include "julia.h"

int main(int argc, char **argv) {
    jl_init();

    jl_eval_string("println(\"Hello, world\")");

    jl_atexit_hook(0);

    return 0;
}