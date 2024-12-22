#include <stdio.h>

#include "julia.h"
#include "julia_init.h"
#include "jl2py.h"

int main(int argc, char *argv[]) {
    // int x, y;

    init_julia(argc, argv);

    // x = 3;
    // y = _inc32(x);
    // printf("(%d, %d)\n", x, y);

    // jl_value_t *refs = jl_eval_string("refs = IdDict()");
    // jl_function_t *setindex = jl_get_function(jl_base_module, "setindex!");
    // jl_value_t *var;
    
    // jl_value_t *ty = jl_eval_string("typeof(jl2py.mystruct(1,1))");
    // JL_GC_PUSH1(&ty);
    // jl_value_t *st = jl_new_struct((jl_datatype_t *) ty, 1, 2);
    // JL_GC_PUSH1(&st);
    // jl_function_t *prntf = jl_get_function(jl_base_module, "println");
    // jl_call1(prntf, st, 1);
    // jl_call3(setindex, refs, ty, ty);
    // jl_value_t *st = jl_new_struct((jl_datatype_t *) ty, 1, 2);
    // JL_GC_PUSH1(&st);
    // jl_is_datatype(ty);

    int x = 4, y = 20;
    jl_value_t *x_boxed = jl_box_int32(x), *y_boxed = jl_box_int32(y);
    jl_value_t *type_int = jl_typeof(x_boxed);

    jl_value_t *ty = jl_eval_string("typeof(jl2py.mystruct(1,1))");

    // jl_function_t *prntf = jl_get_function(jl_base_module, "println");
    jl_function_t *prntln = (jl_function_t *) jl_get_global(jl_base_module, jl_symbol("println"));
    jl_call1(prntln, ty);

    jl_value_t *jl2py = jl_get_global(jl_main_module, jl_symbol("jl2py"));
    printf("(%d, %d)\n", jl_is_module(jl2py), jl_is_datatype(jl2py));
    jl_value_t *mystrct = jl_get_global((jl_module_t *) jl2py, jl_symbol("mystruct"));
    printf("(%d, %d)\n", jl_is_module(mystrct), jl_is_datatype(mystrct));
    jl_value_t *st = jl_new_struct((jl_datatype_t *) mystrct, x_boxed, y_boxed);
    jl_value_t *res = jl_call1(prntln, st);

    jl_value_t *mod = jl_eval_string("Main");
    jl_value_t *jl2py2 = jl_get_global((jl_module_t *) mod, jl_symbol("jl2py"));
    printf("(%d, %d)\n", jl_is_module(jl2py2), jl_is_datatype(jl2py2));

    jl_call1(prntln, x_boxed);
    jl_call1(prntln, type_int);

    // void *buf = malloc(sizeof(int) * 100);
    // jl_array_t *arr = jl_ptr_to_array_1d(type_int, buf, 9, 0);

    // jl_array_t *arr = jl_alloc_array_1d(type_int, (size_t) 0);

    // jl_value_t *st = jl_new_struct((jl_datatype_t *) ty, jl_box_int32(1), jl_box_int32(2));
    // {jl_call1(prntln, st);}

    shutdown_julia(0);
    // free(buf);
    return 0;
}