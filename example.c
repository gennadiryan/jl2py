#include <stdio.h>

#include "julia.h"
#include "julia_init.h"

jl_value_t *get_global(char *);
void set_global(char *, jl_value_t *);

void init_refs(void);
void add_ref(jl_value_t *);
jl_value_t *wrap(jl_value_t *);
void delete_ref(jl_value_t *);
jl_value_t *get_type_refvalue_any(void);

void test_segfault(void) {
    jl_value_t *println = jl_eval_string("println"); wrap(println);
    jl_value_t *arr = jl_eval_string("Int32[1, 2, 3]"); wrap(arr);
    jl_call1(println, arr);

    int x = 4;
    jl_value_t *x_boxed = jl_box_int32(x);

    jl_call1(println, x_boxed);
    jl_call1(println, jl_typeof(x_boxed));
    jl_call1(println, arr);
}

void test_segfault_2() {
    jl_value_t *arr = jl_eval_string("Int32[1, 2, 3]");
    set_global("arr", arr);
    jl_value_t *println = jl_eval_string("println");
    jl_call1(println, arr);

    int x = 4, y = 20;
    jl_value_t *x_boxed = jl_box_int32(x), *y_boxed = jl_box_int32(y);

    jl_call1(println, x_boxed);
    jl_call1(println, jl_typeof(x_boxed));
    jl_call1(println, arr);

    jl_call1(println, jl_typeof(y_boxed));
}

void do_demo(jl_module_t *mod_qc) {
    jl_value_t *println = jl_eval_string("println");
    wrap(println);

    jl_value_t *cons_qs = jl_get_global(mod_qc, jl_symbol("QuantumSystem"));
    jl_value_t *var_h_drives = jl_eval_string("[PAULIS[:X], PAULIS[:Y]]");
    // var_h_drives = wrap(var_h_drives);
    // set_global("h_drives", var_h_drives);
    jl_call1(println, var_h_drives);
    jl_value_t *qs = jl_call1(cons_qs, var_h_drives);
    // set_global("qs", qs);
    jl_call1(println, qs);
    jl_call0(println);

    jl_value_t *cons_uspp = jl_get_global(mod_qc, jl_symbol("UnitarySmoothPulseProblem"));
    jl_value_t *var_operator = jl_eval_string("GATES[:H]");
    // set_global("operator", var_operator);
    jl_value_t *var_T = jl_box_int64(50); // cannot be Int32, even though USPP accepts julia type Int and supposedly Int <: Int32
    // set_global("T", var_T);
    jl_value_t *var_dt = jl_box_float64(0.2);
    // set_global("dt", var_dt);
    jl_call1(println, qs);
    jl_call1(println, var_operator);
    jl_call1(println, var_T);
    jl_call1(println, var_dt);
    jl_call0(println);

    jl_value_t *args_uspp[4] = {qs, var_operator, var_T, var_dt};
    jl_value_t *qcp = jl_call(cons_uspp, args_uspp, 4);
    // set_global("qcp", qcp);
    jl_call1(println, qcp);

    // jl_call1(println, jl_typeof(var_T));
    jl_call1(println, var_h_drives); // memory leak evident here if var_h_drives is allowed to be garbage-collected
    jl_call1(println, qs);
    jl_call1(println, var_operator);
    jl_call1(println, var_T);
    jl_call1(println, var_dt);
}

void do_demo_2(jl_module_t *mod_qc) {
    jl_value_t *println = jl_eval_string("println"); wrap(println);

    jl_value_t *cons_qs = jl_get_global(mod_qc, jl_symbol("QuantumSystem")); wrap(cons_qs);
    jl_value_t *var_h_drives = jl_eval_string("[PAULIS[:X], PAULIS[:Y]]"); wrap(var_h_drives);
    jl_call1(println, var_h_drives);
    jl_value_t *qs = jl_call1(cons_qs, var_h_drives); wrap(qs);
    jl_call1(println, qs);
    jl_call0(println);

    jl_value_t *cons_uspp = jl_get_global(mod_qc, jl_symbol("UnitarySmoothPulseProblem")); wrap(cons_uspp);
    jl_value_t *var_operator = jl_eval_string("GATES[:H]"); wrap(var_operator);
    jl_value_t *var_T = jl_box_int64(50); wrap(var_T); // must be Int64, not Int32, despite USPP accepting julia type Int (where supposedly Int <: Int32)
    jl_value_t *var_dt = jl_box_float64(0.2); wrap(var_dt);
    jl_call1(println, qs);
    jl_call1(println, var_operator);
    jl_call1(println, var_T);
    jl_call1(println, var_dt);
    jl_call0(println);

    jl_value_t *args_uspp[4] = {qs, var_operator, var_T, var_dt};
    jl_value_t *qcp = jl_call(cons_uspp, args_uspp, 4); wrap(qcp);
    jl_call1(println, qcp);

    jl_call1(println, var_h_drives); // memory leak evident here if var_h_drives is allowed to be garbage-collected
    jl_call1(println, qs);
    jl_call1(println, var_operator);
    jl_call1(println, var_T);
    jl_call1(println, var_dt);

    // jl_value_t *ipopt_opts = wrap(jl_get_field(qcp, "ipopt_options"));

    // int ipopt_opts_idx = jl_field_index((jl_datatype_t *) wrap(jl_typeof(qcp)), (jl_sym_t *) wrap((jl_value_t *) jl_symbol("ipopt_options")), 0);
    // jl_value_t *ipopt_opts = wrap(jl_get_nth_field(qcp, ipopt_opts_idx));
    // int max_iter_itx = jl_field_index((jl_datatype_t *) wrap(jl_typeof(ipopt_opts)), (jl_sym_t *) wrap((jl_value_t *) jl_symbol("max_iter")), 0);
    // jl_value_t *max_iter = wrap(jl_get_nth_field(ipopt_opts, max_iter_itx));

    int ipopt_opts_idx = jl_field_index((jl_datatype_t *) jl_typeof(qcp), jl_symbol("ipopt_options"), 0);
    jl_value_t *ipopt_opts = jl_get_nth_field(qcp, ipopt_opts_idx);
    int max_iter_idx = jl_field_index((jl_datatype_t *) jl_typeof(ipopt_opts), jl_symbol("max_iter"), 0);
    jl_set_nth_field(ipopt_opts, max_iter_idx, jl_box_int64(100));

    jl_value_t *max_iter = jl_get_nth_field(ipopt_opts, max_iter_idx);
    jl_call1(println, max_iter);
    jl_call0(println);

    jl_value_t *fn_solve = jl_get_global(mod_qc, jl_symbol("solve!"));
    jl_call1(fn_solve, qcp);

    jl_value_t *fn_plot = jl_get_global(mod_qc, jl_symbol("plot_unitary_populations"));
    jl_value_t *plot = jl_call1(fn_plot, qcp); wrap(plot);
    jl_call1(println, plot);

    jl_value_t *fn_display = jl_get_global(jl_main_module, jl_symbol("display"));
    jl_call1(fn_display, plot);
}

jl_value_t *get_global(char *name) {
    jl_module_t *mod = jl_main_module;
    jl_sym_t *var = jl_symbol(name);
    return jl_get_global(mod, var);
}

void set_global(char *name, jl_value_t *val) {
    jl_module_t *mod = jl_main_module;
    jl_sym_t *var = jl_symbol(name);
    jl_binding_t *bp = jl_get_binding_wr(mod, var, 1);
    jl_checked_assignment(bp, mod, var, val);
}

void init_refs() {
    int gc = jl_gc_enable(0);

    // jl_value_t *val = jl_call0(jl_get_global(jl_base_module, jl_symbol("IdSet")));
    jl_value_t *val = jl_call0(jl_apply_type1(jl_get_global(jl_base_module, jl_symbol("IdSet")), get_type_refvalue_any()));

    jl_sym_t *var = jl_symbol("refs");
    jl_binding_t *bp = jl_get_binding_wr(jl_main_module, var, 1);
    jl_checked_assignment(bp, jl_main_module, var, val);

    jl_gc_enable(gc);
}

void add_ref(jl_value_t *val) {
    int gc = jl_gc_enable(0);

    jl_value_t *push = jl_get_global(jl_base_module, jl_symbol("push!"));
    // jl_call2(push, jl_get_global(jl_main_module, jl_symbol("refs")), val);
    jl_call2(push, jl_get_global(jl_main_module, jl_symbol("refs")), jl_call1(get_type_refvalue_any(), val));

    jl_gc_enable(gc);
    
    // return val;
    return;
}

jl_value_t *wrap(jl_value_t *val) {
    add_ref(val);
    return val;
}

void delete_ref(jl_value_t *val) {
    int gc = jl_gc_enable(0);

    jl_value_t *pop = jl_get_global(jl_base_module, jl_symbol("pop!"));

    jl_gc_enable(gc);

    return;
}

jl_value_t *get_type_refvalue_any() { // equivalent to jl_eval_string("Base.RefValue{Any}")
    return jl_apply_type1(jl_get_global(jl_base_module, jl_symbol("RefValue")), (jl_value_t *) jl_any_type);
}

int main(int argc, char **argv) {
    init_julia(argc, argv);


    // jl_module_t *mod = jl_main_module;
    // jl_sym_t *var = jl_symbol("var");
    // jl_binding_t *bp = jl_get_binding_wr(mod, var);
    // jl_checked_assignment(bp, mod, var, val);


    // test_segfault();


    // jl_value_t *x = jl_box_int32(4), *y = jl_box_int32(20);
    // set_global("x", x);
    // jl_eval_string("println(x)");
    // set_global("x", y);
    // jl_eval_string("println(x)");

    // jl_value_t *println = jl_eval_string("println");
    // jl_call1(println, x);
    // jl_call1(println, y);
    // jl_call1(println, jl_typeof(jl_symbol("x")));


    // test_segfault_2();
    // jl_value_t *println = jl_eval_string("println");
    // jl_call1(println, get_global("arr"));

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

    // jl_eval_string("println(refs)");

    // jl_value_t *println = jl_eval_string("println");
    // jl_call1(println, get_type_refvalue_any());
    // jl_value_t *out = jl_call1(get_type_refvalue_any(), jl_box_int64(4));
    // jl_call1(println, out);
    // jl_call1(println, jl_typeof(out));
    // jl_call1(println, jl_get_nth_field(out, 0));

    // add_ref(println);
    // // jl_eval_string("push!(refs, 5)");
    // jl_call1(println, jl_get_global(jl_main_module, jl_symbol("refs")));


    // jl_value_t *println = jl_eval_string("println");
    // jl_eval_string("struct im\n\ta::Int\n\tb::Int\nend");
    // jl_eval_string("mutable struct m\n\ta::Int\n\tb::Int\nend");
    // jl_value_t *im = jl_eval_string("m(1,1)");
    // jl_call1(println, im);
    // jl_value_t *x = jl_box_int64(4), *y = jl_box_int64(20);
    // jl_call1(println, im);
    // jl_call1(println, x);
    // jl_call1(println, jl_typeof(x));
    // jl_call1(println, im);

    test_segfault();

    // // jl_gc_enable(0);
    // // do_demo(mod_qc);
    // do_demo_2(mod_qc);
    // // jl_gc_enable(1);

    shutdown_julia(0);

    return 0;
}