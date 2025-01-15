#include <stdio.h>

#include "julia.h"
#include "julia_init.h"


void init_refs();
int add_ref(jl_value_t *);
int del_ref(jl_value_t *);
jl_value_t *get_reft();

jl_value_t *vals_to_tup(int, jl_value_t **);
jl_value_t *ptr_to_arr(jl_value_t *, int, long *, void *, int);


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

// int add_val(jl_value_t *val) {
//     int gc = jl_gc_enable(0);

//     if (!jl_is_mutable(jl_typeof(val))) {
//         jl_gc_enable(gc);

//         printf("Error: tried to add immutable value to global scope without creating a reference\n");
//         return 1;
//     }

//     jl_value_t *setindex = jl_get_global(jl_base_module, jl_symbol("setindex!"));
//     int res = (jl_call3(setindex, jl_get_global(jl_main_module, jl_symbol("refs")), val, val) == 0);

//     jl_gc_enable(gc);

//     if (res)
//         printf("Error: failed to add value to global scope\n");
//     return res;
// }

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

jl_value_t *get_reft() { // equivalent to jl_eval_string("Base.RefValue{Any}")
    return jl_apply_type1(jl_get_global(jl_base_module, jl_symbol("RefValue")), (jl_value_t *) jl_any_type);
}


void test_segfault(int allow_gc) {
    jl_value_t *println = jl_eval_string("println"); if (!allow_gc) add_ref(println);
    jl_value_t *arr = jl_eval_string("Int32[1, 2, 3]"); if (!allow_gc) add_ref(arr);
    jl_call1(println, arr);
    
    int x = 4, y = 20;
    jl_value_t *x_boxed = jl_box_int32(x), *y_boxed = jl_box_int32(y);

    jl_eval_string("Gc.gc()");

    jl_call1(println, x_boxed);
    jl_call1(println, jl_typeof(x_boxed));
    jl_call1(println, y_boxed);
    jl_call1(println, jl_typeof(y_boxed));
    jl_call1(println, arr);
    jl_call0(println);
}

void test_segfault_main() {
    jl_value_t *println = jl_eval_string("println");

    jl_value_t *my_immut_val = jl_box_int32(420);
    jl_value_t *my_val = jl_eval_string("Int32[3, 2, 1]");

    add_ref(my_val);
    // del_ref(my_val);

    jl_call1(println, my_val);
    jl_call0(println);
    
    jl_eval_string("println(refs)"); // when commented out, segfault occurs at println(my_val); otherwise, my_val is silently corrupted
    jl_eval_string("Gc.gc()");

    test_segfault(0);

    jl_call1(println, my_immut_val);
    jl_call1(println, jl_typeof(my_immut_val));
    jl_call1(println, my_val);

    // test_segfault(1);

    // jl_call1(println, jl_typeof(jl_box_int32(105)));
    // jl_call1(println, my_val);
}

void _test_mutable(jl_value_t *val) {
    jl_value_t *println = jl_eval_string("println");
    jl_value_t *ismutable = jl_eval_string("ismutable");

    jl_call1(println, val);
    jl_call1(println, jl_typeof(val));
    jl_call1(println, jl_call1(ismutable, val));
    printf("%s\n", jl_is_mutable(jl_typeof(val)) ? "true" : "false");
    jl_call1(println, val);
    jl_call0(println);
}

void test_mutable(void) {
    jl_value_t *val_scalar = jl_box_int32(420); //add_ref(val_scalar);
    jl_value_t *val_arr = jl_eval_string("Int32[1, 2, 3]"); //add_ref(val_arr);

    _test_mutable(val_scalar);
    _test_mutable(val_arr);
}

void test_struct(void) {
    jl_new_datatype(jl_symbol("pt_immut"), jl_main_module, jl_any_type, jl_emptysvec, jl_emptysvec, jl_emptysvec, jl_emptysvec, 0, 0, 0);
}

void test_dtypes(void) {
    ;
}

// BEGIN copy from julia/src/array.c

int is_ntuple_long(jl_value_t *v)
{
    if (!jl_is_tuple(v))
        return 0;
    jl_value_t *tt = (jl_value_t*)jl_typetagof(v);
    size_t i, nfields = jl_nparams(tt);
    for (i = 0; i < nfields; i++) {
        if (jl_tparam(tt, i) != (jl_value_t*)jl_long_type) {
            return 0;
        }
    }
    return 1;
}

// END copy

void test_array(void) {
    // jl_value_t *val_arr = jl_eval_string("Int32[[1, 2], [3, 4]]");

    jl_value_t *println = jl_eval_string("println");

    // jl_value_t *ty = (jl_value_t *) jl_int64_type;
    // int ndims = 2;
    // long dims[2] = {2, 2};
    // long data[4] = {1, 2, 3, 4};

    jl_value_t *ty = (jl_value_t *) jl_int64_type;
    int ndims = 3;
    long dims[3] = {2, 2, 3};
    long data[12] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};

    // jl_value_t *ty = ;
    // int ndims = 2;
    // long dims[2] = {2, 2};
    // jl_value_t *data[4] = {val1, val2, val3, val4};

    // jl_value_t *dims_vals[2] = {jl_box_int64(dims[0]), jl_box_int64(dims[1])};
    // jl_value_t *val_dims = vals_to_tup(2, dims_vals);
    
    // jl_call1(println, val_dims);
    // jl_call1(println, jl_typeof(val_dims));
    // printf("%d\n", is_ntuple_long(val_dims));

    // jl_value_t *val_type_arr_1d = jl_apply_array_type((jl_value_t *) jl_int64_type, 1);
    // jl_call1(println, val_type_arr_1d);

    // jl_array_t *val_arr_1d = jl_ptr_to_array_1d(val_type_arr_1d, (void *) data, 4, 0);
    // printf("%d\n", val_arr_1d != 0);
    // jl_call1(println, (jl_value_t *) val_arr_1d);
    // jl_call1(println, jl_typeof(val_arr_1d));

    // jl_value_t *val_type_arr_nd = jl_apply_array_type((jl_value_t *) jl_int64_type, 2);
    // jl_call1(println, val_type_arr_nd);

    // jl_array_t *val_arr_nd = jl_ptr_to_array(val_type_arr_nd, (void *) data, val_dims, 0);
    // printf("%d\n", val_arr_nd != 0);
    // jl_call1(println, (jl_value_t *) val_arr_nd);
    // jl_call1(println, jl_typeof(val_arr_nd));

    jl_value_t *val_arr_nd = ptr_to_arr(ty, ndims, dims, (void *) data, 0);
    printf("%d\n", val_arr_nd != 0);
    jl_call1(println, (jl_value_t *) val_arr_nd);
    jl_call1(println, jl_typeof(val_arr_nd));
}

void test_custom(void) {
    jl_value_t *println = jl_eval_string("println");
    jl_value_t *getindex = jl_eval_string("getindex");

    jl_eval_string("struct pt_immut\n\tx::Int64\n\ty::Int64\nend");
    jl_eval_string("mutable struct pt_mut\n\tx::Int64\n\ty::Int64\nend");

    jl_value_t *val_ty_immut = jl_eval_string("pt_immut");
    jl_value_t *val_ty_mut = jl_eval_string("pt_mut");

    // long x = 4, y = 20;
    // jl_value_t *x_boxed = jl_box_int64(x), *y_boxed = jl_box_int64(y);
    
    // jl_value_t *val_immut = jl_call2(val_ty_immut, x_boxed, y_boxed);
    // jl_value_t *val_mut = jl_call2(val_ty_mut, x_boxed, y_boxed);
    // jl_call1(println, val_immut);
    // jl_call1(println, val_mut);

    long n = 2;
    jl_value_t *val_ty = val_ty_immut;
    jl_value_t **vals = malloc(n * sizeof(jl_value_t *));
    for (int i = 0; i < n; ++i) {
        // *(vals + i) = jl_call2(val_ty, jl_box_int64(1 + (2 * i)), jl_box_int64(2 + (2 * i)));

        // jl_value_t *flds[2] = {jl_box_int64(1 + (2 * i)), jl_box_int64(2 + (2 * i))}; add_ref(flds[0]); add_ref(flds[1]);
        // *(vals + i) = jl_new_structv((jl_datatype_t *) val_ty, flds, 2); add_ref(vals[i]);

        *(vals + i) = jl_eval_string("pt_immut(1, 2)"); add_ref(vals[i]);

        // jl_value_t *flds[2] = {jl_box_int64(1 + (2 * i)), jl_box_int64(2 + (2 * i))}; add_ref(flds[0]); add_ref(flds[1]);
        // jl_value_t *val_strct = jl_new_struct_uninit((jl_datatype_t *) val_ty); add_ref(val_strct);
        // jl_set_nth_field(val_strct, 0, flds[0]);
        // jl_set_nth_field(val_strct, 1, flds[1]);
        // *(vals + i) = val_strct;
    }
    jl_value_t *val_arr = ptr_to_arr(val_ty, 1, &n, (void *) vals, 0); add_ref(val_arr);
    jl_call1(println, val_arr);
    jl_call1(println, jl_typeof(val_arr));
    jl_call1(println, vals[0]);
    jl_call1(println, jl_call2(getindex, val_arr, jl_box_int64(1)));
    jl_call1(println, jl_get_nth_field(val_arr, 0));

    jl_value_t *extra_strct = jl_eval_string("pt_immut(3, 4)"); add_ref(extra_strct);
    jl_call1(println, extra_strct);

    jl_array_ptr_1d_push((jl_array_t *) val_arr, extra_strct);
    jl_call1(println, val_arr);
    jl_call1(println, extra_strct);
}

void test_tuple(void) {
    jl_value_t *println = jl_eval_string("println");

    int x = 4, y = 20;
    jl_value_t *x_boxed = jl_box_int64(x), *y_boxed = jl_box_int64(y);
    jl_value_t *val_pair[2] = {x_boxed, y_boxed};

    jl_svec_t *val_svec = jl_svec(2, jl_typeof(x_boxed), jl_typeof(y_boxed));
    jl_value_t *val_ptrarr[2] = {jl_typeof(x_boxed), jl_typeof(y_boxed)}; // can replace with {jl_int64_type, jl_int64_type}, since jl_typeof(jl_box_int64(0)) == (jl_value_t *) jl_int64_type, as expected
    jl_call1(println, (jl_value_t *) val_svec);

    jl_value_t *tup_type_from_ptrarr = jl_apply_tuple_type_v(val_ptrarr, 2);
    jl_value_t *tup_type_from_svec = jl_apply_tuple_type(val_svec, 1);
    jl_call1(println, tup_type_from_ptrarr);
    jl_call1(println, tup_type_from_svec);

    jl_value_t *val_types[2] = {(jl_value_t *) jl_int64_type, (jl_value_t *) jl_int64_type};
    jl_value_t *tup_type = jl_apply_tuple_type_v(val_types, 2);
    jl_call1(println, tup_type);

    jl_value_t *val_tup = jl_new_structv((jl_datatype_t *) tup_type, val_pair, 2);
    jl_call1(println, val_tup);

    jl_call1(println, vals_to_tup(2, val_pair));
}


jl_value_t *vals_to_tup(int n, jl_value_t **vals) {
    jl_value_t **val_types = malloc(n * sizeof(jl_value_t *));

    for (int i = 0; i < n; ++i)
        *(val_types + i) = (jl_value_t *) jl_typeof(vals[i]);

    jl_value_t *tup_type = jl_apply_tuple_type_v(val_types, n);
    jl_value_t *val = jl_new_structv((jl_datatype_t *) tup_type, vals, n);

    return val;
}

jl_value_t *ptr_to_arr(jl_value_t *ty, int ndims, long *dims, void *data, int own) {
    jl_value_t *println = jl_eval_string("println");

    jl_value_t **val_dims = malloc(ndims * sizeof(jl_value_t *));
    jl_value_t **val_dims_types = malloc(ndims * sizeof(jl_value_t *));

    for (int i = 0; i < ndims; ++i) {
        *(val_dims + i) = jl_box_int64(dims[i]);
        *(val_dims_types + i) = (jl_value_t *) jl_int64_type;
    }

    jl_value_t *val_dims_tup_type = jl_apply_tuple_type_v(val_dims_types, ndims);
    jl_value_t *val_dims_tup = jl_new_structv((jl_datatype_t *) val_dims_tup_type, val_dims, ndims);

    jl_value_t *val_arr_type = jl_apply_array_type(ty, ndims);
    jl_value_t *val_arr = (jl_value_t *) jl_ptr_to_array(val_arr_type, data, val_dims_tup, own);

    return val_arr;
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

    // test_segfault_main();
    // test_mutable();

    // test_tuple();
    // test_array();
    test_custom();

    shutdown_julia(0);

    return 0;
}