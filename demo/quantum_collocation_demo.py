import os
import sys
import platform
# sys.path.append(os.path.split(os.path.realpath(__file__))[0])

from ..main import *

def get_jl():
    libdir = "./jl2py/target/lib"
    libname = "libjl2py.dylib" if platform.system() == "Darwin" else "libjl2py.so"
    libpath = os.path.join(libdir, libname)

    libfuncs = dict(
        # core data types
        jl_typeof=c_void_p, # jl_value_t *

        # basic predicates
        jl_subtype=c_int, # int

        # object identity
        jl_egal=c_int, # int

        # type predicates and basic operations
        jl_isa=c_int, # int
        jl_types_equal=c_int, # int
        jl_type_union=c_void_p, # jl_value_t *
        jl_type_intersection=c_void_p, # jl_value_t *

        # constructors
        jl_new_bits=c_void_p, # jl_value_t *
        jl_new_struct=c_void_p, # jl_value_t *
        jl_symbol=c_void_p, # jl_sym_t *
        # jl_box_{ty}=c_void_p, # jl_value_t *
        jl_box_int32=c_void_p, # jl_value_t *
        jl_box_voidpointer=c_void_p, # jl_value_t *
        jl_box_uint8pointer=c_void_p, # jl_value_t *
        # jl_unbox_{ty}=({ty}, False), # {ty}
        jl_unbox_int32=c_int, # jl_value_t
        jl_unbox_voidpointer=c_void_p, # void *
        jl_unbox_uint8pointer=c_char_p, # uint8_t *
        jl_get_size=c_int, # int

        # structs
        jl_get_nth_field=c_void_p, # jl_value_t *
        jl_set_nth_field=None, # void
        jl_field_isdefined=c_int, # int
        jl_get_field=c_void_p, # jl_value_t *
        jl_value_ptr=c_void_p, # jl_value_t *

        # arrays
        jl_ptr_to_array_1d=c_void_p, # jl_array_t *
        jl_ptr_to_array=c_void_p, # jl_array_t *
        jl_alloc_array_1d=c_void_p, # jl_array_t *
        jl_alloc_array_nd=c_void_p, # jl_array_t *
        jl_pchar_to_array=c_void_p, # jl_array_t *
        jl_pchar_to_string=c_void_p, # jl_value_t *
        jl_array_ptr_1d_push=None, # void
        jl_array_ptr_1d_append=None, # void
        jl_array_ptr=None, # void
        jl_array_eltype=None, # void
        jl_array_rank=c_int, # int

        # strings
        jl_string_ptr=c_char_p, # const char *

        # modules and global variables
        jl_new_module=c_void_p, # jl_value_t *
        jl_get_global=c_void_p, # jl_value_t *
        jl_set_global=None, # void
        jl_set_const=None, # void

        # initialization functions
        julia_init=None, # void
        jl_init=None, # void
        jl_init_with_image=None, # void
        jl_is_initialized=c_int, # int
        jl_atexit_hook=None, # void

        # code loading (parsing + evaluation)
        jl_eval_string=c_void_p, # jl_value_t *
        jl_load=c_void_p, # jl_value_t *
        
        # calling into julia
        jl_call=c_void_p,
        jl_call1=c_void_p,
        jl_call2=c_void_p,
        jl_call3=c_void_p,

        # tasks and exceptions
        jl_exception_occurred=c_void_p,

        # version information
        jl_ver_string=c_char_p, # const char *
    )

    lib = JuliaLib(libpath).__enter__()
    jl = JuliaLibUtils(lib, libfuncs)

    return jl


if __name__ == '__main__':
    jl = get_jl()

    with open('./jl2py/demo/quantum_collocation_demo.jl', 'r') as f:
        jl_source = f.read()
    
    for lines in [[_ for _ in part.split('\n') if len(_) > 0] for part in jl_source.split('\n' * 2)]:
        for line in lines:
            print(f'>>> {line}')
        for line in lines:
            jl.jl_eval_string(str2buf(line))
        print()
        
