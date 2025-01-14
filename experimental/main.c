#include <stdio.h>

#include "julia.h"
#include "julia_init.h"


void init_refs();
jl_value_t *get_reft();


void init_refs() {
    int gc = jl_gc_enable(0);

    // jl_value_t *val = jl_call0(jl_get_global(jl_base_module, jl_symbol("IdSet")));
    jl_value_t *val = jl_call0(jl_apply_type2(jl_get_global(jl_base_module, jl_symbol("IdDict")), (jl_value_t *) jl_any_type, get_reft()));

    jl_sym_t *var = jl_symbol("refs");
    jl_binding_t *bp = jl_get_binding_wr(jl_main_module, var, 1);
    jl_checked_assignment(bp, jl_main_module, var, val);

    jl_gc_enable(gc);
}

int add_ref(jl_value_t *val) {
    int gc = jl_gc_enable(0);

    jl_value_t *setindex = jl_get_global(jl_base_module, jl_symbol("setindex!"));
    int res = (jl_call3(setindex, jl_get_global(jl_main_module, jl_symbol("refs")), jl_call1(get_reft(), val), val) == 0);

    jl_gc_enable(gc);

    if (res)
        printf("Error: failed to add value to global scope");
    return res;
}

int del_ref(jl_value_t *val) {
    int gc = jl_gc_enable(0);

    jl_value_t *delete = jl_get_global(jl_base_module, jl_symbol("delete!"));
    int res = (jl_call2(delete, jl_get_global(jl_main_module, jl_symbol("refs")), val) == 0);

    jl_gc_enable(gc);

    if (res)
        printf("Error: failed to remove value from global scope");
    return res;
}

jl_value_t *get_reft() { // equivalent to jl_eval_string("Base.RefValue{Any}")
    return jl_apply_type1(jl_get_global(jl_base_module, jl_symbol("RefValue")), (jl_value_t *) jl_any_type);
}


void test_segfault(int allow_gc) {
    jl_value_t *println = jl_eval_string("println"); if (!allow_gc) add_ref(println);
    jl_value_t *arr = jl_eval_string("Int32[1, 2, 3]"); if (!allow_gc) add_ref(arr);
    jl_call1(println, arr);
    
    int x = 4, y = 20;
    jl_value_t *x_boxed = jl_box_int32(x), *y_boxed = jl_box_int32(y);

    jl_call1(println, x_boxed);
    jl_call1(println, jl_typeof(x_boxed));
    jl_call1(println, y_boxed);
    jl_call1(println, jl_typeof(y_boxed));
    jl_call1(println, arr);
}


int main(int argc, char **argv) {
    init_julia(argc, argv);

    jl_module_t *mod_jl2py, *mod_qc;

    mod_qc = (jl_module_t *) jl_get_global(jl_main_module, jl_symbol("QuantumCollocation"));
    printf("%d\n", mod_qc != 0);

    mod_jl2py = (jl_module_t *) jl_get_global(jl_main_module, jl_symbol("jl2py"));
    mod_qc = (jl_module_t *) jl_get_global(mod_jl2py, jl_symbol("QuantumCollocation"));
    printf("%d\n", mod_qc != 0);

    jl_module_using(jl_main_module, mod_qc);
    mod_qc = (jl_module_t *) jl_get_global(jl_main_module, jl_symbol("QuantumCollocation"));
    printf("%d\n", mod_qc != 0);

    init_refs();

    jl_value_t *my_immut_val = jl_box_int32(420);
    jl_value_t *my_val = jl_eval_string("Int32[3, 2, 1]");
    // add_ref(my_val);
    // jl_eval_string("println(refs)");
    // del_ref(my_val);
    // jl_eval_string("println(refs)");

    test_segfault(0);

    jl_eval_string("println(refs)");

    jl_value_t *println = jl_eval_string("println");
    jl_call1(println, my_immut_val);
    jl_call1(println, jl_typeof(my_immut_val));
    jl_call1(println, my_val);

    shutdown_julia(0);

    return 0;
}