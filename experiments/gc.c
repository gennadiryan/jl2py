#include <stdio.h>

#include "julia.h"


void jl_gc_push1(jl_value_t *arg1) {
    void *__gc_stkf[] = {(void*)JL_GC_ENCODE_PUSH(1), jl_pgcstack, arg1};                                 \
    jl_pgcstack = (jl_gcframe_t*)__gc_stkf;
}

// void jl_gc_popn(int n) {
//     for (int i = 0; i < n; ++i) jl_gc_pop();
// }


jl_value_t **jl_gc_pushargs(int n) {
    jl_value_t **rts_var = ((jl_value_t**)malloc(((n)+2)*sizeof(jl_value_t*)))+2;
    ((void**)rts_var)[-2] = (void*)(((size_t)(n))<<2);
    ((void**)rts_var)[-1] = jl_pgcstack;
    memset((void*)rts_var, 0, (n)*sizeof(jl_value_t*));
    jl_pgcstack = (jl_gcframe_t*)&(((void**)rts_var)[-2]);
    return rts_var;
}

jl_value_t **_jl_gc_pushargs(size_t n) {
    // // void **values = malloc((2 + n) * sizeof(jl_value_t *));
    // // values[0] = (void *)(n << 2);
    // // values[1] = jl_pgcstack;
    // // memset(values[2], 0, n * sizeof(jl_value_t *));
    // // jl_pgcstack = (jl_gcframe_t *) values;

    // // void **values = ((void**)malloc(((n)+2)*sizeof(void*)))+2;
    // void **values = malloc((2 + n) * sizeof(void *)) + 2;
    // // ((void**)values)[-2] = (void*)(((size_t)(n))<<2);
    // values[-2] = (void *) (n << 2);
    // // ((void**)values)[-1] = jl_pgcstack;
    // values[-1] = jl_pgcstack;
    // // memset((void*)values, 0, (n)*sizeof(jl_value_t*));
    // memset(&values[0], 0, n * sizeof(void *));
    // // jl_pgcstack = (jl_gcframe_t*)&(((void**)values)[-2]);
    // jl_pgcstack = (jl_gcframe_t *) (&(values[-2]));

    printf("%d, %d, %d\n", jl_pgcstack, jl_get_pgcstack(), *(jl_get_pgcstack()));
    printf("%d, %d\n", jl_current_task, jl_get_current_task());
    printf("%d, %d\n", jl_task_gcstack_offset, jl_get_current_task() + jl_task_gcstack_offset);
    printf("%d\n", jl_current_task->gcstack);
    printf("%d\n", (*jl_current_task).gcstack);
    printf("%d\n", &((*jl_current_task).gcstack));
    printf("%d\n", *(jl_get_current_task() + jl_task_gcstack_offset));

    // void **values = malloc((2 + n) * sizeof(void *));
    // values[0] = (void *) (n << 2);
    // // values[1] = jl_pgcstack;
    // values[1] = jl_current_task->gcstack;
    // memset(&(values[2]), 0, n * sizeof(void *));
    // // jl_pgcstack = (jl_gcframe_t *) values;
    // jl_current_task->gcstack = (jl_gcframe_t *) values;

    void **values = malloc((2 + n) * sizeof(void *));
    values[0] = (void *) (n << 2);
    // values[1] = jl_current_task->gcstack;
    values[1] = *(jl_get_pgcstack());
    memset(&(values[2]), 0, n * sizeof(void *));
    *(jl_get_pgcstack()) = (jl_gcframe_t *) values;

    printf("%d, %d\n", values[0], values[1]);
    
    return (jl_value_t **) (values + 2);
}

void jl_gc_pop() {
    jl_pgcstack = jl_pgcstack->prev;
}


void test_gc_pushargs(int nest) {
    jl_value_t *println = jl_get_global(jl_base_module, jl_symbol("println"));

    jl_value_t **values;
    int n = 100;
    int ctr = 0;

    // values = jl_gc_pushargs(n);
    values = _jl_gc_pushargs(6);

    int _x = 4;
    jl_value_t *x = jl_box_int64(_x);
    values[ctr++] = x;

    int _y = 20;
    jl_value_t *y = jl_box_int64(_y);
    values[ctr++] = y;

    jl_value_t *ty_mut = jl_eval_string("mutable struct pt_mut; x::Int; y::Int; end; pt_mut");
    values[ctr++] = ty_mut;
    jl_value_t *ty_immut = jl_eval_string("struct pt_immut; x::Int; y::Int; end; pt_immut");
    values[ctr++] = ty_immut;

    jl_value_t *inst_mut = jl_new_struct((jl_datatype_t *) ty_mut, x, y);
    values[ctr++] = inst_mut;
    jl_value_t *inst_immut = jl_new_struct((jl_datatype_t *) ty_immut, x, y);
    values[ctr++] = inst_immut;

    jl_call1(println, x);
    jl_call1(println, y);
    jl_call1(println, ty_mut);
    jl_call1(println, inst_mut);
    jl_call1(println, ty_immut);
    jl_call1(println, inst_immut);

    jl_gc_collect(1);

    if (nest > 0) test_gc_pushargs(nest - 1);

    // jl_value_t *x2 = jl_box_int64

    jl_call1(println, x);
    jl_call1(println, y);
    jl_call1(println, inst_mut);
    jl_call1(println, inst_immut);

    jl_gc_collect(1);

    // jl_gc_popn(2);
    // JL_GC_POP();
    jl_gc_pop();

    jl_gc_collect(1);

    // jl_call1(println, inst_mut);

    // if (nest > 0) test_gc_pushargs(nest - 1);
}


int main(int argc, char **argv) {
    jl_init();

    // // test_gc_pushargs();
    // // test_gc_pushargs();
    // test_gc_pushargs(1);
    // test_gc_pushargs(2);
    test_gc_pushargs(2);
    jl_printf(jl_stdout_stream(), "success!\n");

    jl_atexit_hook(0);
    return 0;
}