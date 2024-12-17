#include <stdio.h>

#include "julia_init.h"
#include "jl2py.h"

int main(int argc, char *argv[]) {
    int x, y;

    init_julia(argc, argv);

    x = 3;
    y = _inc32(x);
    printf("(%d, %d)\n", x, y);

    shutdown_julia(0);
    return 0;
}