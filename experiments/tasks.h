#define container_of(ptr, type, member) ((type *) ((char *)(ptr) - offsetof(type, member)))

typedef struct _jl_task_t {
    JL_DATA_TYPE
    jl_value_t *next; // invasive linked list for scheduler
    jl_value_t *queue; // invasive linked list for scheduler
    jl_value_t *tls;
    jl_value_t *donenotify;
    jl_value_t *result;
    jl_value_t *scope;
    jl_function_t *start;
    // 4 byte padding on 32-bit systems
    // uint32_t padding0;
    uint64_t rngState[JL_RNG_SIZE];
    _Atomic(uint8_t) _state;
    uint8_t sticky; // record whether this Task can be migrated to a new thread
    _Atomic(uint8_t) _isexception; // set if `result` is an exception to throw or that we exited with
    // 1 byte padding
    // uint8_t padding1;
    // multiqueue priority
    uint16_t priority;

// hidden state:

    // id of owning thread - does not need to be defined until the task runs
    _Atomic(int16_t) tid;
    // threadpool id
    int8_t threadpoolid;
    // Reentrancy bits
    // Bit 0: 1 if we are currently running inference/codegen
    // Bit 1-2: 0-3 counter of how many times we've reentered inference
    // Bit 3: 1 if we are writing the image and inference is illegal
    uint8_t reentrant_timing;
    // 2 bytes of padding on 32-bit, 6 bytes on 64-bit
    // uint16_t padding2_32;
    // uint48_t padding2_64;
    // saved gc stack top for context switches
    jl_gcframe_t *gcstack;
    size_t world_age;
    // quick lookup for current ptls
    jl_ptls_t ptls; // == jl_all_tls_states[tid]
#ifdef USE_TRACY
    const char *name;
#endif
    // saved exception stack
    jl_excstack_t *excstack;
    // current exception handler
    jl_handler_t *eh;
    // saved thread state
    jl_ucontext_t ctx;
    void *stkbuf; // malloc'd memory (either copybuf or stack)
    size_t bufsz; // actual sizeof stkbuf
    unsigned int copy_stack:31; // sizeof stack for copybuf
    unsigned int started:1;
} jl_task_t;

#define JL_TASK_STATE_RUNNABLE 0
#define JL_TASK_STATE_DONE     1
#define JL_TASK_STATE_FAILED   2

JL_DLLEXPORT JL_CONST_FUNC jl_gcframe_t **(jl_get_pgcstack)(void) JL_GLOBALLY_ROOTED JL_NOTSAFEPOINT;
#define jl_current_task (container_of(jl_get_pgcstack(), jl_task_t, gcstack))

extern JL_DLLIMPORT int jl_task_gcstack_offset;
extern JL_DLLIMPORT int jl_task_ptls_offset;

#define jl_root_task (jl_current_task->ptls->root_task)
JL_DLLEXPORT jl_task_t *jl_get_current_task(void) JL_GLOBALLY_ROOTED JL_NOTSAFEPOINT;
