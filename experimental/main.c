#include <stdio.h>

#include "julia.h"
#include "julia_init.h"

// #include "julia_internal.h" // used for jl_atomic_sym


void init_refs();
int add_ref(jl_value_t *);
int del_ref(jl_value_t *);
jl_value_t *get_reft();

void inspect_ty_flags(jl_value_t *);
void inspect_ty_layout(jl_value_t *);

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

// BEGIN imitate JuliaLang/julia src/builtins.c::jl_f_memoryref (which becomes Core.memoryrefnew)

jl_value_t *memoryref(jl_genericmemoryref_t *m, size_t i) {
    size_t sz;

    const jl_datatype_layout_t *layout = ((jl_datatype_t *) jl_typetagof(m->mem))->layout;
    if (layout->flags.arrayelem_isboxed)
        sz = sizeof(jl_value_t *);
    else if (layout->flags.arrayelem_isunion || (layout->size == 0))
        sz = 1;
    else
        sz = layout->size;

    char *data = (char *)(m->ptr_or_offset) + (sz * i);
    // if (data >= m->mem->length) // wrong for all but union (second conditional)
    //     return 0;
    return (jl_value_t *) jl_new_memoryref((jl_value_t *) jl_typetagof(m), m->mem, data);
}

// END

// // BEGIN imitate JuliaLang/julia src/builtins.c::jl_f_memoryref[get,set] (which becomes Core.memoryref[get,set!])

jl_value_t *memoryrefget(jl_genericmemoryref_t *m) {
    return jl_memoryrefget(*m, (jl_tparam0((jl_datatype_t *) jl_typetagof(m->mem)) == ((jl_value_t *) jl_symbol("atomic"))));
}

void memoryrefset(jl_genericmemoryref_t *m, jl_value_t *rhs) {
    // jl_memoryrefset(m, rhs, jl_tparam0(jl_typetagof(m->mem)) == ((jl_value_t *) jl_atomic_sym));
    jl_memoryrefset(*m, rhs, (jl_tparam0((jl_datatype_t *) jl_typetagof(m->mem)) == ((jl_value_t *) jl_symbol("atomic"))));
}

// // END

void test_array_2(void) {
    jl_value_t *println = jl_eval_string("println");

    // jl_value_t *ty = (jl_value_t *) jl_int64_type;
    // int ndims = 2;
    // long dims[2] = {2, 2};
    // long data[4] = {1, 2, 3, 4};

    jl_value_t *ty = (jl_value_t *) jl_int64_type;
    int ndims = 3;
    long dims[3] = {2, 2, 3};
    long data[12] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};

    jl_value_t *val_arr_nd = ptr_to_arr(ty, ndims, dims, (void *) data, 0);
    add_ref(val_arr_nd);

    if (val_arr_nd == 0) {
        printf("Error wrapping ptr as array\n");
        return;
    }

    jl_genericmemoryref_t *val_arr_ref = &((jl_array_t *) val_arr_nd)->ref;
    jl_genericmemory_t *val_arr_mem = val_arr_ref->mem;

    jl_call1(println, val_arr_nd);
    jl_call1(println, (jl_value_t *) val_arr_ref);
    jl_call1(println, (jl_value_t *) val_arr_mem);

    jl_value_t *tag = (jl_value_t *) jl_typetagof(val_arr_mem);
    jl_value_t *param = jl_tparam0(tag);
    jl_value_t *atomic_sym = (jl_value_t *) jl_symbol("atomic");
    jl_value_t *not_atomic_sym = (jl_value_t *) jl_symbol("not_atomic");

    printf("%lu, %lu, %lu\n", (unsigned long) param, (unsigned long) atomic_sym, (unsigned long) not_atomic_sym);

    jl_value_t *ref_10 = memoryref(val_arr_ref, 9);
    memoryrefset((jl_genericmemoryref_t *) ref_10, jl_box_int64(100));
    jl_value_t *val_10 = memoryrefget((jl_genericmemoryref_t *) ref_10);

    jl_call1(println, val_arr_nd);
    jl_call1(println, (jl_value_t *) val_arr_ref);
    jl_call1(println, (jl_value_t *) val_arr_mem);
    jl_call1(println, val_10);
    jl_call1(println, jl_typeof(val_10));
}

void test_array_3(void) {
    jl_value_t *println = jl_eval_string("println");

    // jl_value_t *ty = (jl_value_t *) jl_int64_type;
    // int ndims = 2;
    // long dims[2] = {2, 2};
    // long data[4] = {1, 2, 3, 4};

    // jl_value_t *ty = (jl_value_t *) jl_int64_type;
    // int ndims = 3;
    // long dims[3] = {2, 2, 3};
    // long data[12] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12};

    // jl_value_t *val_arr_nd = ptr_to_arr(ty, ndims, dims, (void *) data, 0);
    // add_ref(val_arr_nd);
    
    jl_value_t *val_arr_nd = jl_eval_string("Union{Int64, Float64}[1, 2, 3, 4, 5, 6, 7, 8, 9, 10., 11, 12]");
    add_ref(val_arr_nd);

    if (val_arr_nd == 0) {
        printf("Error wrapping ptr as array\n");
        return;
    }

    jl_genericmemoryref_t *val_arr_ref = &((jl_array_t *) val_arr_nd)->ref;
    jl_genericmemory_t *val_arr_mem = val_arr_ref->mem;

    jl_call1(println, val_arr_nd);
    jl_call1(println, (jl_value_t *) val_arr_ref);
    jl_call1(println, (jl_value_t *) val_arr_mem);

    jl_value_t *tag = (jl_value_t *) jl_typetagof(val_arr_mem);
    jl_value_t *param = jl_tparam0(tag);
    jl_value_t *atomic_sym = (jl_value_t *) jl_symbol("atomic");
    jl_value_t *not_atomic_sym = (jl_value_t *) jl_symbol("not_atomic");

    printf("%lu, %lu, %lu\n", (unsigned long) param, (unsigned long) atomic_sym, (unsigned long) not_atomic_sym);

    jl_value_t *ref_10 = memoryref(val_arr_ref, 9);
    memoryrefset((jl_genericmemoryref_t *) ref_10, jl_box_int64(100));
    jl_value_t *val_10 = memoryrefget((jl_genericmemoryref_t *) ref_10);

    jl_call1(println, val_arr_nd);
    jl_call1(println, (jl_value_t *) val_arr_ref);
    jl_call1(println, (jl_value_t *) val_arr_mem);
    jl_call1(println, val_10);
    jl_call1(println, jl_typeof(val_10));
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

        jl_value_t *flds[2] = {jl_box_int64(1 + (2 * i)), jl_box_int64(2 + (2 * i))}; add_ref(flds[0]); add_ref(flds[1]);
        *(vals + i) = jl_new_structv((jl_datatype_t *) val_ty, flds, 2); add_ref(vals[i]);

        // *(vals + i) = jl_eval_string("pt_immut(1, 2)"); add_ref(vals[i]);

        // jl_value_t *flds[2] = {jl_box_int64(1 + (2 * i)), jl_box_int64(2 + (2 * i))}; add_ref(flds[0]); add_ref(flds[1]);
        // jl_value_t *val_strct = jl_new_struct_uninit((jl_datatype_t *) val_ty); add_ref(val_strct);
        // jl_set_nth_field(val_strct, 0, flds[0]);
        // jl_set_nth_field(val_strct, 1, flds[1]);
        // *(vals + i) = val_strct;
    }
    jl_value_t *val_arr = ptr_to_arr(val_ty, 1, &n, (void *) vals, 1); add_ref(val_arr);
    jl_call1(println, val_arr);
    jl_call1(println, jl_typeof(val_arr));
    jl_call1(println, vals[0]);
    jl_call1(println, jl_call2(getindex, val_arr, jl_box_int64(1)));
    jl_call1(println, jl_get_nth_field(val_arr, 0));
    jl_call1(println, jl_get_nth_field(val_arr, 1));

    jl_value_t *extra_strct = jl_eval_string("pt_immut(3, 4)"); add_ref(extra_strct);
    jl_call1(println, extra_strct);

    // jl_array_ptr_1d_push((jl_array_t *) val_arr, extra_strct);
    // jl_call1(println, val_arr);
    // jl_call1(println, extra_strct);

    jl_value_t *val_arr_2 = (jl_value_t *) jl_alloc_array_1d(jl_typeof(val_arr), 0); add_ref(val_arr_2);
    jl_array_ptr_1d_push((jl_array_t *) val_arr_2, extra_strct);
    jl_call1(println, val_arr_2);
    jl_call1(println, extra_strct);

    printf("%0lx\n", (long) vals);
    printf("%0lx\n", (long) &(((jl_array_t *) val_arr)->ref));
    printf("%0lx\n", (long) (&(((jl_array_t *) val_arr)->ref))->ptr_or_offset);
    printf("%0lx\n", (long) (&(((jl_array_t *) val_arr)->ref))->mem);
    printf("%0lx\n", (long) (&(((jl_array_t *) val_arr)->ref))->mem->ptr);
    printf("%d\n", ((jl_datatype_t *) (jl_typetagof((&(((jl_array_t *) val_arr)->ref))->mem)))->layout->size);
    printf("%d\n", ((jl_datatype_t *) (jl_typetagof((&(((jl_array_t *) val_arr)->ref))->mem)))->layout->flags.arrayelem_isboxed);

    jl_call0(println);
}

void test_custom_2(void) {
    jl_value_t *println = jl_eval_string("println");
    jl_value_t *ty_immut = jl_eval_string("pt_immut");

    jl_value_t *elem = jl_eval_string("elem1 = pt_immut(1, 2)");
    jl_value_t *extra_strct = jl_eval_string("elem2 = pt_immut(3, 4)"); add_ref(extra_strct);
    jl_value_t *entries[2] = {jl_box_int64(4), jl_box_int64(20)};
    jl_value_t *extra_strct_2 = jl_new_structv((jl_datatype_t *) ty_immut, entries, 2);
    jl_call1(println, extra_strct_2);
    // jl_value_t *val = jl_eval_string("val = pt_immut[]"); add_ref(val);
    jl_value_t *val = (jl_value_t *) jl_alloc_array_1d(jl_apply_array_type(ty_immut, 1), 0); add_ref(val); // same effect as above
    // jl_array_ptr_1d_push((jl_array_t *) val, elem);



    // jl_eval_string("push!(val, elem2)");
    jl_call2(jl_eval_string("push!"), val, extra_strct_2);
    jl_call2(jl_eval_string("push!"), val, extra_strct);
    // jl_eval_string("push!(val, elem2)");

    jl_call1(println, jl_typeof(val));
    jl_call1(println, val);

    printf("%0lx\n", (long) elem);
    printf("%0lx\n", (long) &(((jl_array_t *) val)->ref));
    printf("%0lx\n", (long) (&(((jl_array_t *) val)->ref))->ptr_or_offset);
    printf("%0lx\n", (long) (&(((jl_array_t *) val)->ref))->mem);
    printf("%0lx\n", (long) (&(((jl_array_t *) val)->ref))->mem->ptr);
    printf("%ld\n", (long) jl_array_data(val, void *));
    printf("%ld\n", (long) jl_array_data(val, void *)[0]);
    printf("%ld\n", (long) jl_array_data(val, void *)[1]);
    printf("%ld\n", (long) jl_array_data(val, void *)[2]);
    printf("%ld\n", (long) jl_array_data(val, void *)[3]);
    // printf("%ld\n", (long) jl_array_data(val, void *)[4]);
    // printf("%ld\n", (long) jl_array_data(val, void *)[5]);
    printf("%d\n", ((jl_datatype_t *) (jl_typetagof((&(((jl_array_t *) val)->ref))->mem)))->layout->size);

    jl_call0(println);
}

void test_custom_3(void) {
    jl_value_t *println = jl_eval_string("println");
    jl_value_t *ty_immut = jl_eval_string("pt_immut");

    jl_value_t *elem = jl_eval_string("elem1 = pt_immut(1, 2)");
    jl_value_t *extra_strct = jl_eval_string("elem2 = pt_immut(3, 4)"); add_ref(extra_strct);
    jl_value_t *entries[2] = {jl_box_int64(4), jl_box_int64(20)};
    jl_value_t *extra_strct_2 = jl_new_structv((jl_datatype_t *) ty_immut, entries, 2);
    jl_call1(println, extra_strct_2);

    // jl_value_t *val = jl_eval_string("val = pt_immut[]"); add_ref(val);
    // jl_value_t *val = (jl_value_t *) jl_alloc_array_1d(jl_apply_array_type(ty_immut, 1), 0); add_ref(val); // same effect as above
    jl_value_t *val = (jl_value_t *) jl_alloc_array_1d(jl_array_any_type, 0); add_ref(val); // same effect as above
    // jl_array_ptr_1d_push((jl_array_t *) val, elem);



    // jl_eval_string("push!(val, elem2)");
    jl_call2(jl_eval_string("push!"), val, extra_strct_2);
    jl_call2(jl_eval_string("push!"), val, extra_strct);
    // jl_eval_string("push!(val, elem2)");

    jl_call1(println, jl_typeof(val));
    jl_call1(println, val);

    printf("%0lx\n", (long) elem);
    printf("%0lx\n", (long) &(((jl_array_t *) val)->ref));
    printf("%0lx\n", (long) (&(((jl_array_t *) val)->ref))->ptr_or_offset);
    printf("%0lx\n", (long) (&(((jl_array_t *) val)->ref))->mem);
    printf("%0lx\n", (long) (&(((jl_array_t *) val)->ref))->mem->ptr);
    printf("%ld\n", (long) jl_array_data(val, void *));
    printf("%ld\n", (long) jl_array_data(val, void *)[0]);
    printf("%ld\n", (long) jl_array_data(val, void *)[1]);
    printf("%ld\n", (long) jl_array_data(val, void *)[2]);
    printf("%ld\n", (long) jl_array_data(val, void *)[3]);
    jl_call1(println, (jl_value_t *) (jl_array_data(val, void *)[0]));
    jl_call1(println, (jl_value_t *) (jl_array_data(val, void *)[1]));
    // printf("%ld\n", (long) jl_array_data(val, void *)[4]);
    // printf("%ld\n", (long) jl_array_data(val, void *)[5]);
    printf("%d\n", ((jl_datatype_t *) (jl_typetagof((&(((jl_array_t *) val)->ref))->mem)))->layout->size);

    jl_call0(println);
}

void test_custom_4(void) {
    jl_value_t *println = jl_eval_string("println");
    jl_value_t *push = jl_eval_string("push!");

    jl_value_t *ty_union_immut = jl_eval_string("Union{Int, pt_immut}");
    jl_value_t *ty_union_mut = jl_eval_string("Union{Int, Vector{Int}}");
    jl_value_t *ty_union = ty_union_mut;
    jl_call1(println, ty_union);

    jl_value_t *val_arr = (jl_value_t *) jl_alloc_array_1d(jl_apply_array_type(ty_union, 1), 0); add_ref(val_arr);
    jl_call2(push, val_arr, jl_box_int64(4));
    jl_call2(push, val_arr, jl_box_int64(20));
    jl_call1(println, val_arr);

    printf("%d\n", ((jl_datatype_t *) (jl_typetagof((&(((jl_array_t *) val_arr)->ref))->mem)))->layout->flags.arrayelem_isboxed);
    printf("%d\n", ((jl_datatype_t *) jl_typetagof((((jl_array_t *) val_arr)->ref).mem))->layout->flags.arrayelem_isboxed);
    printf("%d\n", ((jl_datatype_t *) ty_union)->layout->flags.arrayelem_isboxed);

    jl_value_t *ty_strct_immut = jl_eval_string("pt_immut");
    jl_value_t *ty_strct_arr_immut = jl_apply_array_type(ty_strct_immut, 1);
    jl_value_t *ty_strct_mut = jl_eval_string("pt_mut");
    jl_value_t *ty_strct_arr_mut = jl_apply_array_type(ty_strct_mut, 1);

    jl_value_t *ty_mem_immut = jl_svecref(((jl_datatype_t *) jl_svecref(((jl_datatype_t *) ty_strct_arr_immut)->types, 0))->types, 1);
    jl_call1(println, ty_mem_immut);

    // jl_value_t *ty_mut_tys = (jl_value_t *) ((jl_datatype_t *) ty_strct_arr_mut)->types;
    // jl_call1(println, ty_mut_tys);
    // jl_value_t *ty_memref_mut = jl_svecref(ty_mut_tys, 0);
    // jl_call1(println, ty_memref_mut);
    // jl_value_t *ty_memref_mut_tys = (jl_value_t *) ((jl_datatype_t *) ty_memref_mut)->types;
    // jl_call1(println, ty_memref_mut_tys);
    // jl_value_t *ty_mem_mut = jl_svecref(ty_memref_mut_tys, 1);
    // jl_call1(println, ty_mem_mut);

    jl_value_t *ty_mem_mut = jl_svecref(((jl_datatype_t *) jl_svecref(((jl_datatype_t *) ty_strct_arr_mut)->types, 0))->types, 1);
    jl_call1(println, ty_mem_mut);

    int n_tys = 6;
    jl_value_t *tys[6] = {ty_strct_immut, ty_strct_mut, ty_strct_arr_immut, ty_strct_arr_mut, ty_mem_immut, ty_mem_mut};
    
    for (int i = 0; i < n_tys; ++i) {
        inspect_ty_flags(tys[i]);
        inspect_ty_layout(tys[i]);
    }
    // ty_cur = ty_strct_mut;
    // inspect_ty_flags(ty_strct);
    // inspect_ty_layout(ty_strct);


    jl_call0(println);
}

void test_custom_5(void) {
    jl_value_t *println = jl_eval_string("println");
    jl_call0(println);

    jl_value_t *ty_strct_immut = jl_eval_string("pt_immut");
    jl_value_t *ty_strct_mut = jl_eval_string("pt_mut");
    jl_value_t *ty_strct = ty_strct_immut;

    jl_value_t *entries[2] = {jl_box_int64(4), jl_box_int64(19)};
    jl_value_t *val_strct = jl_new_structv((jl_datatype_t *) ty_strct, entries, 2); add_ref(val_strct);
    // jl_value_t *val_strct = jl_new_struct_uninit((jl_datatype_t *) ty_immut); add_ref(val_strct);

    jl_value_t *fld = jl_get_field(val_strct, "x");
    jl_call1(println, jl_typeof(fld));
    jl_call1(println, fld);

    // jl_set_nth_field(val_strct, 1, jl_box_int64(20));
    jl_call1(println, val_strct);

    unsigned long offset0 = jl_field_offset((jl_datatype_t *) ty_strct, 0);
    unsigned long size0 = jl_field_size((jl_datatype_t *) ty_strct, 0);
    unsigned long offset1 = jl_field_offset((jl_datatype_t *) ty_strct, 1);
    unsigned long size1 = jl_field_size((jl_datatype_t *) ty_strct, 1);
    printf("%lu, %lu; %lu, %lu\n", offset0, size0, offset1, size1);

    // don't forget jl_ptr_offset()
    printf("%u, %u, %d, %d, %d\n", jl_field_offset((jl_datatype_t *) ty_strct, 0), jl_field_size((jl_datatype_t *) ty_strct, 0), jl_field_isptr((jl_datatype_t *) ty_strct, 0), jl_field_isatomic((jl_datatype_t *) ty_strct, 0), jl_field_isconst((jl_datatype_t *) ty_strct, 0));
    
    long raw0 = *((long *) ((char *) val_strct + offset0));
    long raw1 = *((long *) ((char *) val_strct + offset1));
    printf("%ld, %ld\n", raw0, raw1);

    jl_call0(println);

    ////

    // *((jl_value_t **)(((char *) val_strct) + offset))

    jl_eval_string("struct vec_cont a::Vector{Int64} end");
    jl_value_t *ptr_strct = jl_eval_string("vec_cont([1, 2, 3])"); add_ref(ptr_strct);
    jl_call1(println, jl_typeof(ptr_strct));
    jl_call1(println, ptr_strct);

    inspect_ty_flags(jl_typeof(ptr_strct));
    inspect_ty_layout(jl_typeof(ptr_strct));
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


char *char_to_binstr(char bt) {
    char *binstr = malloc(sizeof(char) * 9);
    for (int i = 0; i < 8; ++i)
        binstr[8 - i - 1] = ((bt >> i) & 0x1) ? '1' : '0';
    binstr[8] = '\0';
    return binstr;
}

void inspect_ty_flags(jl_value_t *val_ty) {
    jl_datatype_t *ty = (jl_datatype_t *) val_ty;

    // int flags[11];

    printf(
        "(%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d)\n",
        ty->hasfreetypevars,
        ty->isconcretetype,
        ty->isdispatchtuple,
        ty->isbitstype,
        ty->zeroinit,
        ty->has_concrete_subtype,
        ty->maybe_subtype_of_cache,
        ty->isprimitivetype,
        ty->ismutationfree,
        ty->isidentityfree,
        ty->smalltag
    );
    printf("\n");
}

void inspect_ty_layout(jl_value_t *val_ty) {
    const jl_datatype_layout_t *ty_layout = ((jl_datatype_t *) val_ty)->layout;

    printf(
        "(%u,%u,%u,%08x,%hu,%04x)\n",
        ty_layout->size,
        ty_layout->nfields,
        ty_layout->npointers,
        ty_layout->first_ptr,
        ty_layout->alignment,
        *((unsigned short *) &(ty_layout->flags))
    );

    char flags = *((const char *) &(ty_layout->flags));
    printf(
        "(%d,%d,%d,%d,%d)\n",
        (flags >> 0) & 0x1,
        (flags >> 1) & 0x3,
        (flags >> 3) & 0x1,
        (flags >> 4) & 0x1,
        (flags >> 5) & 0x1
    );

    // printf(
    //     "(%d,%d,%d,%d)\n",
    //     ty_layout->flags.haspadding,
    //     ty_layout->flags.fielddesc_type,
    //     ty_layout->flags.arrayelem_isboxed,
    //     ty_layout->flags.arrayelem_isunion
    //     // ty_layout->flags.isbitsegal
    // );
    // char *flag_ptr = (char *) &(ty_layout->flags);
    // printf("%s\n", char_to_binstr(flag_ptr[0]));

    printf("\n");
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

    jl_value_t *val_dims_tup_type = jl_apply_tuple_type_v(val_dims_types, ndims); // Tuple{Int64, ...} datatype for dimensions
    jl_value_t *val_dims_tup = jl_new_structv((jl_datatype_t *) val_dims_tup_type, val_dims, ndims); // Tuple{Int64, ...} instantiated

    jl_value_t *val_arr_type = jl_apply_array_type(ty, ndims); // Array{T, N} datatype for T=ty, N=ndims
    jl_value_t *val_arr = (jl_value_t *) jl_ptr_to_array(val_arr_type, data, val_dims_tup, own); // Array{T, N} instantiated

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

    // // test_segfault_main();
    // // test_mutable();

    // // test_tuple();
    // // test_array();
    // test_custom();
    // test_custom_2();
    // test_custom_3();
    // test_custom_4();
    // test_custom_5();

    // test_array_2();
    test_array_3();

    shutdown_julia(0);

    return 0;
}