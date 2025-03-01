#include <stdio.h>

#include "julia.h"
#include "julia_init.h"

jl_value_t *get_reft() { // equivalent to jl_eval_string("Base.RefValue{Any}")
    return jl_apply_type1(jl_get_global(jl_base_module, jl_symbol("RefValue")), (jl_value_t *) jl_any_type);
}

void init_refs() {
    int gc = jl_gc_enable(0);

    // jl_value_t *val = jl_call0(jl_get_global(jl_base_module, jl_symbol("IdSet")));
    jl_value_t *val = jl_call0(jl_apply_type2(jl_get_global(jl_base_module, jl_symbol("IdDict")), (jl_value_t *) jl_any_type, get_reft()));
    // jl_value_t *val = jl_call0(jl_apply_type2(jl_get_global(jl_base_module, jl_symbol("IdDict")), (jl_value_t *) jl_any_type, (jl_value_t *) jl_any_type));

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
        printf("Error: failed to add reference to global scope\n");
    return res;
}

int del_ref(jl_value_t *val) {
    int gc = jl_gc_enable(0);

    jl_value_t *delete = jl_get_global(jl_base_module, jl_symbol("delete!"));
    int res = (jl_call2(delete, jl_get_global(jl_main_module, jl_symbol("refs")), val) == 0);

    jl_gc_enable(gc);

    if (res)
        printf("Error: failed to remove value/reference from global scope\n");
    return res;
}


int main(int argc, char **argv) {
    init_julia(argc, argv);

    init_refs();

    jl_module_t *mod_jl2py, *mod_qc;

    mod_qc = (jl_module_t *) jl_get_global(jl_main_module, jl_symbol("QuantumCollocation"));
    printf("%d\n", mod_qc != 0);

    mod_jl2py = (jl_module_t *) jl_get_global(jl_main_module, jl_symbol("jl2py"));
    mod_qc = (jl_module_t *) jl_get_global(mod_jl2py, jl_symbol("QuantumCollocation"));
    printf("%d\n", mod_qc != 0);

    jl_module_using(jl_main_module, mod_qc);
    mod_qc = (jl_module_t *) jl_get_global(jl_main_module, jl_symbol("QuantumCollocation"));
    printf("%d\n", mod_qc != 0);

    shutdown_julia(0);

    return 0;
}